/**
 * Analytics Dashboard - JavaScript
 * Handles chart rendering and API interactions
 */

// Chart instances
let barChart = null;
let pieChart = null;
let lineChart = null;

// Chart.js default configuration
Chart.defaults.color = '#adb5bd';
Chart.defaults.borderColor = 'rgba(255, 255, 255, 0.1)';

// Color palette for charts
const chartColors = [
    'rgba(102, 126, 234, 0.8)',   // Primary purple
    'rgba(118, 75, 162, 0.8)',    // Secondary purple
    'rgba(46, 204, 113, 0.8)',    // Green
    'rgba(52, 152, 219, 0.8)',    // Blue
    'rgba(241, 196, 15, 0.8)',    // Yellow
    'rgba(231, 76, 60, 0.8)',     // Red
    'rgba(155, 89, 182, 0.8)',    // Violet
    'rgba(26, 188, 156, 0.8)',    // Teal
    'rgba(230, 126, 34, 0.8)',    // Orange
    'rgba(149, 165, 166, 0.8)'    // Gray
];

const chartBorderColors = chartColors.map(c => c.replace('0.8', '1'));

/**
 * Fetch data from API with error handling
 */
async function fetchAPI(url) {
    try {
        const response = await fetch(url);
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'API request failed');
        }
        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message, 'error');
        throw error;
    }
}

/**
 * Render Bar Chart
 */
async function renderBarChart(column) {
    const canvas = document.getElementById('barChart');
    const emptyState = document.getElementById('barChartEmpty');
    
    if (!column) {
        canvas.style.display = 'none';
        emptyState.style.display = 'block';
        if (barChart) {
            barChart.destroy();
            barChart = null;
        }
        return;
    }
    
    try {
        const data = await fetchAPI(`/api/chart/bar?column=${encodeURIComponent(column)}`);
        
        canvas.style.display = 'block';
        emptyState.style.display = 'none';
        
        if (barChart) {
            barChart.destroy();
        }
        
        barChart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: data.labels,
                datasets: [{
                    label: column,
                    data: data.values,
                    backgroundColor: chartColors,
                    borderColor: chartBorderColors,
                    borderWidth: 1,
                    borderRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(33, 37, 41, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#adb5bd',
                        borderColor: 'rgba(102, 126, 234, 0.5)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 0
                        }
                    }
                }
            }
        });
    } catch (error) {
        canvas.style.display = 'none';
        emptyState.style.display = 'block';
    }
}

/**
 * Render Pie Chart
 */
async function renderPieChart(column) {
    const canvas = document.getElementById('pieChart');
    const emptyState = document.getElementById('pieChartEmpty');
    
    if (!column) {
        canvas.style.display = 'none';
        emptyState.style.display = 'block';
        if (pieChart) {
            pieChart.destroy();
            pieChart = null;
        }
        return;
    }
    
    try {
        const data = await fetchAPI(`/api/chart/pie?column=${encodeURIComponent(column)}`);
        
        canvas.style.display = 'block';
        emptyState.style.display = 'none';
        
        if (pieChart) {
            pieChart.destroy();
        }
        
        pieChart = new Chart(canvas, {
            type: 'doughnut',
            data: {
                labels: data.labels,
                datasets: [{
                    data: data.values,
                    backgroundColor: chartColors,
                    borderColor: 'rgba(33, 37, 41, 1)',
                    borderWidth: 2,
                    hoverOffset: 10
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                        labels: {
                            padding: 15,
                            usePointStyle: true,
                            pointStyle: 'circle'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(33, 37, 41, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#adb5bd',
                        borderColor: 'rgba(102, 126, 234, 0.5)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12
                    }
                },
                cutout: '60%'
            }
        });
    } catch (error) {
        canvas.style.display = 'none';
        emptyState.style.display = 'block';
    }
}

/**
 * Render Line Chart
 */
async function renderLineChart(dateCol, valueCol, agg) {
    const canvas = document.getElementById('lineChart');
    const emptyState = document.getElementById('lineChartEmpty');
    
    if (!dateCol || !valueCol) {
        canvas.style.display = 'none';
        emptyState.style.display = 'block';
        if (lineChart) {
            lineChart.destroy();
            lineChart = null;
        }
        return;
    }
    
    try {
        const url = `/api/chart/line?date_col=${encodeURIComponent(dateCol)}&value_col=${encodeURIComponent(valueCol)}&agg=${agg}`;
        const data = await fetchAPI(url);
        
        canvas.style.display = 'block';
        emptyState.style.display = 'none';
        
        if (lineChart) {
            lineChart.destroy();
        }
        
        lineChart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: data.labels,
                datasets: [{
                    label: `${valueCol} (${agg})`,
                    data: data.values,
                    borderColor: 'rgba(102, 126, 234, 1)',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    borderWidth: 2,
                    fill: true,
                    tension: 0.4,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointBorderWidth: 2,
                    pointRadius: 4,
                    pointHoverRadius: 6
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        backgroundColor: 'rgba(33, 37, 41, 0.9)',
                        titleColor: '#fff',
                        bodyColor: '#adb5bd',
                        borderColor: 'rgba(102, 126, 234, 0.5)',
                        borderWidth: 1,
                        cornerRadius: 8,
                        padding: 12,
                        mode: 'index',
                        intersect: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: 'rgba(255, 255, 255, 0.05)'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        },
                        ticks: {
                            maxTicksLimit: 12,
                            maxRotation: 45
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
    } catch (error) {
        canvas.style.display = 'none';
        emptyState.style.display = 'block';
    }
}

/**
 * Initialize Dashboard
 */
document.addEventListener('DOMContentLoaded', () => {
    // Bar Chart column selector
    const barColumn = document.getElementById('barColumn');
    if (barColumn) {
        barColumn.addEventListener('change', (e) => {
            renderBarChart(e.target.value);
        });
    }
    
    // Pie Chart column selector
    const pieColumn = document.getElementById('pieColumn');
    if (pieColumn) {
        pieColumn.addEventListener('change', (e) => {
            renderPieChart(e.target.value);
        });
    }
    
    // Line Chart controls
    const lineDateCol = document.getElementById('lineDateCol');
    const lineValueCol = document.getElementById('lineValueCol');
    const lineAgg = document.getElementById('lineAgg');
    const renderLineBtn = document.getElementById('renderLineBtn');
    
    function updateLineChartButton() {
        if (lineDateCol && lineValueCol && renderLineBtn) {
            renderLineBtn.disabled = !(lineDateCol.value && lineValueCol.value);
        }
    }
    
    if (lineDateCol) {
        lineDateCol.addEventListener('change', updateLineChartButton);
    }
    if (lineValueCol) {
        lineValueCol.addEventListener('change', updateLineChartButton);
    }
    
    if (renderLineBtn) {
        renderLineBtn.addEventListener('click', () => {
            renderLineChart(
                lineDateCol.value,
                lineValueCol.value,
                lineAgg.value
            );
        });
    }
    
    // Hide all canvases initially and show empty states
    const canvases = ['barChart', 'pieChart', 'lineChart'];
    canvases.forEach(id => {
        const canvas = document.getElementById(id);
        if (canvas) {
            canvas.style.display = 'none';
        }
    });
});
