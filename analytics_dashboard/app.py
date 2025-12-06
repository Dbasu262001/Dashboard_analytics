"""
Analytics Dashboard - FastAPI Application
A web-based analytics dashboard for CSV/XLSX data visualization.
"""

import os
import shutil
from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, Request, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from utils.data_processing import (
    load_file,
    get_summary,
    get_bar_chart_data,
    get_line_chart_data,
    get_pie_chart_data,
    export_to_csv,
    infer_column_types,
)

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".xls"}
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# Initialize FastAPI app
app = FastAPI(
    title="Analytics Dashboard",
    description="Web-based analytics dashboard for data visualization",
    version="1.0.0",
)

# Mount static files
app.mount(
    "/static", StaticFiles(directory=Path(__file__).parent / "static"), name="static"
)

# Initialize templates
templates = Jinja2Templates(directory=Path(__file__).parent / "templates")


class DatasetManager:
    """Singleton to manage the current dataset in memory."""

    _instance = None
    _df: Optional[pd.DataFrame] = None
    _filename: Optional[str] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @property
    def df(self) -> Optional[pd.DataFrame]:
        return self._df

    @df.setter
    def df(self, value: pd.DataFrame):
        self._df = value

    @property
    def filename(self) -> Optional[str]:
        return self._filename

    @filename.setter
    def filename(self, value: str):
        self._filename = value

    @property
    def has_data(self) -> bool:
        return self._df is not None

    def clear(self):
        self._df = None
        self._filename = None


# Global dataset manager
dataset_manager = DatasetManager()


def validate_file(file: UploadFile) -> tuple[bool, str]:
    """Validate file type and size."""
    # Check file extension
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return (
            False,
            f"Invalid file type. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    return True, ""


# ============== Web Routes ==============


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Redirect to upload or dashboard based on data availability."""
    if dataset_manager.has_data:
        return RedirectResponse(url="/dashboard", status_code=302)
    return RedirectResponse(url="/upload", status_code=302)


@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Render the file upload page."""
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "max_size_mb": MAX_FILE_SIZE // (1024 * 1024),
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
        },
    )


@app.post("/upload")
async def upload_file(request: Request, file: UploadFile = File(...)):
    """Handle file upload, validate, save, and load into memory."""
    # Validate file type
    is_valid, error_msg = validate_file(file)
    if not is_valid:
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "error": error_msg,
                "max_size_mb": MAX_FILE_SIZE // (1024 * 1024),
                "allowed_extensions": list(ALLOWED_EXTENSIONS),
            },
            status_code=400,
        )

    # Read file content and check size
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "error": f"File too large. Maximum size is {MAX_FILE_SIZE // (1024 * 1024)}MB",
                "max_size_mb": MAX_FILE_SIZE // (1024 * 1024),
                "allowed_extensions": list(ALLOWED_EXTENSIONS),
            },
            status_code=400,
        )

    # Save file
    file_path = DATA_DIR / file.filename
    with open(file_path, "wb") as f:
        f.write(content)

    # Load into DataFrame
    try:
        df = load_file(file_path)
        dataset_manager.df = df
        dataset_manager.filename = file.filename
    except Exception as e:
        # Clean up file on error
        file_path.unlink(missing_ok=True)
        return templates.TemplateResponse(
            "upload.html",
            {
                "request": request,
                "error": f"Error reading file: {str(e)}",
                "max_size_mb": MAX_FILE_SIZE // (1024 * 1024),
                "allowed_extensions": list(ALLOWED_EXTENSIONS),
            },
            status_code=400,
        )

    # Redirect to dashboard with success message
    return RedirectResponse(url="/dashboard?upload_success=1", status_code=303)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request, upload_success: bool = False):
    """Render the dashboard with summary and chart controls."""
    if not dataset_manager.has_data:
        return RedirectResponse(url="/upload", status_code=302)

    summary = get_summary(dataset_manager.df)
    column_types = infer_column_types(dataset_manager.df)

    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "filename": dataset_manager.filename,
            "summary": summary,
            "column_types": column_types,
            "upload_success": upload_success,
        },
    )


@app.get("/export.csv")
async def export_csv():
    """Download the current dataset as CSV."""
    if not dataset_manager.has_data:
        raise HTTPException(status_code=404, detail="No dataset loaded")

    csv_content = export_to_csv(dataset_manager.df)

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=export.csv"},
    )


# ============== API Routes ==============


@app.get("/api/summary")
async def api_summary():
    """Get dataset overview as JSON."""
    if not dataset_manager.has_data:
        raise HTTPException(status_code=404, detail="No dataset loaded")

    return get_summary(dataset_manager.df)


@app.get("/api/chart/bar")
async def api_bar_chart(column: str = Query(..., description="Column to aggregate")):
    """Get bar chart data for a column."""
    if not dataset_manager.has_data:
        raise HTTPException(status_code=404, detail="No dataset loaded")

    try:
        return get_bar_chart_data(dataset_manager.df, column)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/chart/line")
async def api_line_chart(
    date_col: str = Query(..., description="Date column"),
    value_col: str = Query(..., description="Value column"),
    agg: str = Query("sum", description="Aggregation: sum, avg, or count"),
):
    """Get line chart data for time series."""
    if not dataset_manager.has_data:
        raise HTTPException(status_code=404, detail="No dataset loaded")

    if agg not in ["sum", "avg", "count"]:
        raise HTTPException(
            status_code=400, detail="Invalid aggregation. Use: sum, avg, count"
        )

    try:
        return get_line_chart_data(dataset_manager.df, date_col, value_col, agg)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/api/chart/pie")
async def api_pie_chart(
    column: str = Query(..., description="Column for distribution")
):
    """Get pie chart data for column distribution."""
    if not dataset_manager.has_data:
        raise HTTPException(status_code=404, detail="No dataset loaded")

    try:
        return get_pie_chart_data(dataset_manager.df, column)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============== Error Handlers ==============


@app.exception_handler(404)
async def not_found_handler(request: Request, exc: HTTPException):
    """Handle 404 errors."""
    if request.url.path.startswith("/api/"):
        return {"error": "Not found", "detail": str(exc.detail)}
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "error": "Page not found",
            "max_size_mb": MAX_FILE_SIZE // (1024 * 1024),
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
        },
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc: Exception):
    """Handle 500 errors."""
    if request.url.path.startswith("/api/"):
        return {"error": "Internal server error"}
    return templates.TemplateResponse(
        "upload.html",
        {
            "request": request,
            "error": "An unexpected error occurred",
            "max_size_mb": MAX_FILE_SIZE // (1024 * 1024),
            "allowed_extensions": list(ALLOWED_EXTENSIONS),
        },
        status_code=500,
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
