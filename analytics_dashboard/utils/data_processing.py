"""
Data Processing Utilities for Analytics Dashboard
Provides helpers for type inference, summaries, group-by, time-series resampling, and column validation.
"""

import pandas as pd
import numpy as np
from typing import Optional, Literal, Any
from pathlib import Path


def load_file(file_path: str | Path) -> pd.DataFrame:
    """Load CSV or Excel file into a pandas DataFrame."""
    path = Path(file_path)
    
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path)
    elif path.suffix.lower() in ['.xlsx', '.xls']:
        return pd.read_excel(path, engine='openpyxl')
    else:
        raise ValueError(f"Unsupported file type: {path.suffix}")


def infer_column_types(df: pd.DataFrame) -> dict[str, list[str]]:
    """
    Detect and categorize columns by type.
    Returns dict with 'numeric', 'categorical', 'datetime' keys.
    """
    result = {
        'numeric': [],
        'categorical': [],
        'datetime': []
    }
    
    for col in df.columns:
        # Try to convert to datetime
        if df[col].dtype == 'object':
            try:
                pd.to_datetime(df[col], errors='raise')
                result['datetime'].append(col)
                continue
            except (ValueError, TypeError):
                pass
        
        # Check if already datetime
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            result['datetime'].append(col)
        # Check if numeric
        elif pd.api.types.is_numeric_dtype(df[col]):
            result['numeric'].append(col)
        # Otherwise categorical
        else:
            result['categorical'].append(col)
    
    return result


def get_summary(df: pd.DataFrame) -> dict[str, Any]:
    """
    Get dataset overview with row count, columns, null counts, and basic stats.
    """
    column_info = []
    for col in df.columns:
        info = {
            'name': col,
            'dtype': str(df[col].dtype),
            'null_count': int(df[col].isnull().sum()),
            'non_null_count': int(df[col].notna().sum())
        }
        
        # Add basic stats for numeric columns
        if pd.api.types.is_numeric_dtype(df[col]):
            info['min'] = float(df[col].min()) if not pd.isna(df[col].min()) else None
            info['max'] = float(df[col].max()) if not pd.isna(df[col].max()) else None
            info['mean'] = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
            info['std'] = float(df[col].std()) if not pd.isna(df[col].std()) else None
        
        # Add unique count for categorical
        if df[col].dtype == 'object':
            info['unique_count'] = int(df[col].nunique())
        
        column_info.append(info)
    
    return {
        'row_count': len(df),
        'column_count': len(df.columns),
        'columns': column_info,
        'column_types': infer_column_types(df)
    }


def validate_column(df: pd.DataFrame, column: str) -> bool:
    """Safely validate if a column exists in the DataFrame."""
    return column in df.columns


def validate_columns(df: pd.DataFrame, columns: list[str]) -> tuple[bool, list[str]]:
    """Validate multiple columns. Returns (all_valid, missing_columns)."""
    missing = [col for col in columns if col not in df.columns]
    return len(missing) == 0, missing


def get_bar_chart_data(df: pd.DataFrame, column: str, limit: int = 20) -> dict[str, Any]:
    """
    Get aggregated data for bar charts.
    Returns value counts for the specified column.
    """
    if not validate_column(df, column):
        raise ValueError(f"Column '{column}' not found in dataset")
    
    # Get value counts
    value_counts = df[column].value_counts().head(limit)
    
    return {
        'labels': [str(label) for label in value_counts.index.tolist()],
        'values': value_counts.values.tolist(),
        'column': column
    }


def get_line_chart_data(
    df: pd.DataFrame,
    date_col: str,
    value_col: str,
    agg: Literal['sum', 'avg', 'count'] = 'sum',
    resample_period: Optional[str] = None
) -> dict[str, Any]:
    """
    Get time-series data for line charts with optional resampling.
    
    Args:
        df: DataFrame
        date_col: Column containing dates
        value_col: Column containing values to aggregate
        agg: Aggregation method ('sum', 'avg', 'count')
        resample_period: Pandas resample period (e.g., 'D', 'W', 'M', 'Y')
    """
    valid, missing = validate_columns(df, [date_col, value_col])
    if not valid:
        raise ValueError(f"Columns not found: {missing}")
    
    # Create a copy and convert date column
    temp_df = df[[date_col, value_col]].copy()
    temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce')
    temp_df = temp_df.dropna(subset=[date_col])
    temp_df = temp_df.set_index(date_col).sort_index()
    
    # Determine resample period if not specified
    if resample_period is None:
        date_range = (temp_df.index.max() - temp_df.index.min()).days
        if date_range > 365 * 2:
            resample_period = 'ME'  # Monthly
        elif date_range > 90:
            resample_period = 'W'  # Weekly
        else:
            resample_period = 'D'  # Daily
    
    # Apply aggregation
    if agg == 'sum':
        result = temp_df[value_col].resample(resample_period).sum()
    elif agg == 'avg':
        result = temp_df[value_col].resample(resample_period).mean()
    elif agg == 'count':
        result = temp_df[value_col].resample(resample_period).count()
    else:
        raise ValueError(f"Invalid aggregation method: {agg}")
    
    # Clean up NaN values
    result = result.fillna(0)
    
    return {
        'labels': [d.strftime('%Y-%m-%d') for d in result.index],
        'values': result.values.tolist(),
        'date_column': date_col,
        'value_column': value_col,
        'aggregation': agg
    }


def get_pie_chart_data(df: pd.DataFrame, column: str, limit: int = 10) -> dict[str, Any]:
    """
    Get distribution data for pie charts.
    Groups smaller categories into 'Other' if exceeding limit.
    """
    if not validate_column(df, column):
        raise ValueError(f"Column '{column}' not found in dataset")
    
    value_counts = df[column].value_counts()
    
    if len(value_counts) > limit:
        top_values = value_counts.head(limit - 1)
        other_sum = value_counts.iloc[limit - 1:].sum()
        labels = [str(label) for label in top_values.index.tolist()] + ['Other']
        values = top_values.values.tolist() + [other_sum]
    else:
        labels = [str(label) for label in value_counts.index.tolist()]
        values = value_counts.values.tolist()
    
    return {
        'labels': labels,
        'values': values,
        'column': column
    }


def get_group_by_data(
    df: pd.DataFrame,
    group_col: str,
    value_col: str,
    agg: Literal['sum', 'avg', 'count', 'min', 'max'] = 'sum',
    limit: int = 20
) -> dict[str, Any]:
    """
    Get grouped aggregation data.
    """
    valid, missing = validate_columns(df, [group_col, value_col])
    if not valid:
        raise ValueError(f"Columns not found: {missing}")
    
    agg_map = {
        'sum': 'sum',
        'avg': 'mean',
        'count': 'count',
        'min': 'min',
        'max': 'max'
    }
    
    result = df.groupby(group_col)[value_col].agg(agg_map[agg]).head(limit)
    
    return {
        'labels': [str(label) for label in result.index.tolist()],
        'values': result.values.tolist(),
        'group_column': group_col,
        'value_column': value_col,
        'aggregation': agg
    }


def filter_by_date_range(
    df: pd.DataFrame,
    date_col: str,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
) -> pd.DataFrame:
    """Filter DataFrame by date range."""
    if not validate_column(df, date_col):
        raise ValueError(f"Column '{date_col}' not found in dataset")
    
    temp_df = df.copy()
    temp_df[date_col] = pd.to_datetime(temp_df[date_col], errors='coerce')
    
    if start_date:
        temp_df = temp_df[temp_df[date_col] >= pd.to_datetime(start_date)]
    if end_date:
        temp_df = temp_df[temp_df[date_col] <= pd.to_datetime(end_date)]
    
    return temp_df


def export_to_csv(df: pd.DataFrame) -> str:
    """Export DataFrame to CSV string."""
    return df.to_csv(index=False)
