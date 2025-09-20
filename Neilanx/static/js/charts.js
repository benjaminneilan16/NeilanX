// NeilanX Charts.js Implementation
// Handles all chart visualizations for sentiment analysis data

document.addEventListener('DOMContentLoaded', function() {
    // Chart.js global configuration
    Chart.defaults.font.family = "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif";
    Chart.defaults.color = '#6B7280';
    Chart.defaults.plugins.legend.labels.usePointStyle = true;
    Chart.defaults.plugins.legend.labels.padding = 20;

    // Brand colors from CSS variables
    const brandColors = {
        primary: '#2A77D4',
        secondary: '#111827',
        success: '#10B981',
        warning: '#F59E0B',
        danger: '#EF4444',
        light: '#F9FAFB',
        gray: '#6B7280'
    };

    // Sentiment color mapping
    const sentimentColors = {
        positive: brandColors.success,
        negative: brandColors.danger,
        neutral: brandColors.warning
    };

    // Swedish labels
    const swedishLabels = {
        positive: 'Positiva',
        negative: 'Negativa',
        neutral: 'Neutrala',
        noData: 'Inga data tillgängliga',
        loading: 'Laddar data...',
        error: 'Fel vid laddning av data'
    };

    // Global chart instances
    let sentimentChart = null;
    let trendChart = null;
    let keywordChart = null;

    // Initialize sentiment distribution chart
    function initSentimentChart(canvasId, data = null) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chartData = data || {
            positive: 0,
            negative: 0,
            neutral: 0
        };

        const total = chartData.positive + chartData.negative + chartData.neutral;
        
        if (total === 0) {
            showEmptyChart(ctx, swedishLabels.noData);
            return null;
        }

        const chart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: [
                    `${swedishLabels.positive} (${chartData.positive})`,
                    `${swedishLabels.negative} (${chartData.negative})`,
                    `${swedishLabels.neutral} (${chartData.neutral})`
                ],
                datasets: [{
                    data: [chartData.positive, chartData.negative, chartData.neutral],
                    backgroundColor: [
                        sentimentColors.positive,
                        sentimentColors.negative,
                        sentimentColors.neutral
                    ],
                    borderWidth: 2,
                    borderColor: '#ffffff',
                    hoverBorderWidth: 3,
                    hoverBorderColor: '#ffffff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 20,
                            usePointStyle: true,
                            generateLabels: function(chart) {
                                const data = chart.data;
                                if (data.labels.length && data.datasets.length) {
                                    return data.labels.map((label, i) => {
                                        const meta = chart.getDatasetMeta(0);
                                        const style = meta.controller.getStyle(i);
                                        const value = data.datasets[0].data[i];
                                        const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                        
                                        return {
                                            text: `${label} (${percentage}%)`,
                                            fillStyle: style.backgroundColor,
                                            strokeStyle: style.borderColor,
                                            lineWidth: style.borderWidth,
                                            pointStyle: 'circle',
                                            hidden: isNaN(value) || meta.data[i].hidden,
                                            index: i
                                        };
                                    });
                                }
                                return [];
                            }
                        }
                    },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                const label = context.label.split(' (')[0]; // Remove count from label
                                const value = context.parsed;
                                const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                                return `${label}: ${value} recensioner (${percentage}%)`;
                            }
                        },
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        borderColor: brandColors.primary,
                        borderWidth: 1
                    }
                },
                animation: {
                    animateRotate: true,
                    duration: 800,
                    easing: 'easeOutCubic'
                }
            }
        });

        return chart;
    }

    // Initialize trend chart (line chart for time-based data)
    function initTrendChart(canvasId, data = null) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data ? data.labels : [],
                datasets: [{
                    label: swedishLabels.positive,
                    data: data ? data.positive : [],
                    borderColor: sentimentColors.positive,
                    backgroundColor: sentimentColors.positive + '20',
                    fill: false,
                    tension: 0.4
                }, {
                    label: swedishLabels.negative,
                    data: data ? data.negative : [],
                    borderColor: sentimentColors.negative,
                    backgroundColor: sentimentColors.negative + '20',
                    fill: false,
                    tension: 0.4
                }, {
                    label: swedishLabels.neutral,
                    data: data ? data.neutral : [],
                    borderColor: sentimentColors.neutral,
                    backgroundColor: sentimentColors.neutral + '20',
                    fill: false,
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        grid: {
                            display: true,
                            color: '#E5E7EB'
                        }
                    }
                },
                plugins: {
                    legend: {
                        position: 'top'
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff'
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });

        return chart;
    }

    // Initialize keyword frequency chart (bar chart)
    function initKeywordChart(canvasId, data = null) {
        const ctx = document.getElementById(canvasId);
        if (!ctx) return null;

        const chart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data ? data.keywords : [],
                datasets: [{
                    label: 'Frekvens',
                    data: data ? data.frequencies : [],
                    backgroundColor: brandColors.primary + '80',
                    borderColor: brandColors.primary,
                    borderWidth: 1,
                    borderRadius: 4,
                    borderSkipped: false
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            stepSize: 1
                        }
                    },
                    x: {
                        ticks: {
                            maxRotation: 45,
                            minRotation: 0
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        titleColor: '#ffffff',
                        bodyColor: '#ffffff',
                        callbacks: {
                            label: function(context) {
                                return `${context.label}: ${context.parsed.y} gånger`;
                            }
                        }
                    }
                }
            }
        });

        return chart;
    }

    // Show empty chart state
    function showEmptyChart(canvas, message) {
        const ctx = canvas.getContext('2d');
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        
        ctx.font = '16px Inter, sans-serif';
        ctx.fillStyle = brandColors.gray;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        
        const centerX = canvas.width / 2;
        const centerY = canvas.height / 2;
        
        ctx.fillText(message, centerX, centerY);
    }

    // Update chart data
    function updateChart(chart, newData) {
        if (!chart) return;

        if (chart.config.type === 'doughnut') {
            const total = newData.positive + newData.negative + newData.neutral;
            chart.data.datasets[0].data = [newData.positive, newData.negative, newData.neutral];
            chart.data.labels = [
                `${swedishLabels.positive} (${newData.positive})`,
                `${swedishLabels.negative} (${newData.negative})`,
                `${swedishLabels.neutral} (${newData.neutral})`
            ];
        }
        
        chart.update('active');
    }

    // Fetch sentiment data from API
    async function fetchSentimentData(uploadId) {
        try {
            const response = await fetch(`/api/sentiment_data/${uploadId}`);
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error('Error fetching sentiment data:', error);
            return null;
        }
    }

    // Initialize charts on dashboard
    function initDashboardCharts() {
        // Get sentiment data from template or API
        const sentimentData = window.dashboardData ? window.dashboardData.sentiment : null;
        
        // Initialize main sentiment chart
        sentimentChart = initSentimentChart('sentimentChart', sentimentData);
        
        // Initialize other charts if containers exist
        if (document.getElementById('trendChart')) {
            trendChart = initTrendChart('trendChart');
        }
        
        if (document.getElementById('keywordChart')) {
            keywordChart = initKeywordChart('keywordChart');
        }
    }

    // Export chart as image
    function exportChart(chartInstance, filename = 'chart.png') {
        if (!chartInstance) return;
        
        const url = chartInstance.toBase64Image();
        const link = document.createElement('a');
        link.download = filename;
        link.href = url;
        link.click();
    }

    // Resize charts on window resize
    function handleResize() {
        if (sentimentChart) sentimentChart.resize();
        if (trendChart) trendChart.resize();
        if (keywordChart) keywordChart.resize();
    }

    // Public API for global access
    window.NeilanXCharts = {
        initSentimentChart: initSentimentChart,
        initTrendChart: initTrendChart,
        initKeywordChart: initKeywordChart,
        updateChart: updateChart,
        exportChart: exportChart,
        fetchSentimentData: fetchSentimentData,
        
        // Chart instances
        get sentimentChart() { return sentimentChart; },
        get trendChart() { return trendChart; },
        get keywordChart() { return keywordChart; }
    };

    // For backward compatibility with dashboard.html
    window.updateDashboardChart = function(data) {
        updateChart(sentimentChart, data);
    };

    // Initialize charts when DOM is ready
    initDashboardCharts();

    // Handle window resize
    window.addEventListener('resize', handleResize);

    // Handle chart export buttons
    document.querySelectorAll('.export-chart-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const chartType = this.dataset.chart;
            const filename = this.dataset.filename || 'chart.png';
            
            switch(chartType) {
                case 'sentiment':
                    exportChart(sentimentChart, filename);
                    break;
                case 'trend':
                    exportChart(trendChart, filename);
                    break;
                case 'keyword':
                    exportChart(keywordChart, filename);
                    break;
            }
        });
    });
});

// Utility functions for chart data processing
function processSentimentData(reviews) {
    const counts = { positive: 0, negative: 0, neutral: 0 };
    
    reviews.forEach(review => {
        const sentiment = review.sentiment || 'neutral';
        if (counts.hasOwnProperty(sentiment)) {
            counts[sentiment]++;
        }
    });
    
    return counts;
}

function processKeywordData(reviews, maxKeywords = 10) {
    const keywordCounts = {};
    
    reviews.forEach(review => {
        let keywords = [];
        if (review.keywords) {
            try {
                keywords = typeof review.keywords === 'string' 
                    ? JSON.parse(review.keywords) 
                    : review.keywords;
            } catch (e) {
                keywords = [];
            }
        }
        
        keywords.forEach(keyword => {
            keywordCounts[keyword] = (keywordCounts[keyword] || 0) + 1;
        });
    });
    
    // Sort and get top keywords
    const sortedKeywords = Object.entries(keywordCounts)
        .sort(([,a], [,b]) => b - a)
        .slice(0, maxKeywords);
    
    return {
        keywords: sortedKeywords.map(([keyword]) => keyword),
        frequencies: sortedKeywords.map(([, count]) => count)
    };
}

function processTrendData(reviews, timeFrame = 'daily') {
    const grouped = {};
    
    reviews.forEach(review => {
        let date = review.review_date || review.processed_at;
        if (!date) return;
        
        // Group by timeframe
        let key;
        const dateObj = new Date(date);
        
        switch(timeFrame) {
            case 'daily':
                key = dateObj.toISOString().split('T')[0];
                break;
            case 'weekly':
                const week = Math.floor(dateObj.getTime() / (7 * 24 * 60 * 60 * 1000));
                key = `Vecka ${week}`;
                break;
            case 'monthly':
                key = `${dateObj.getFullYear()}-${String(dateObj.getMonth() + 1).padStart(2, '0')}`;
                break;
            default:
                key = dateObj.toISOString().split('T')[0];
        }
        
        if (!grouped[key]) {
            grouped[key] = { positive: 0, negative: 0, neutral: 0 };
        }
        
        const sentiment = review.sentiment || 'neutral';
        grouped[key][sentiment]++;
    });
    
    // Sort by date and prepare chart data
    const sortedKeys = Object.keys(grouped).sort();
    
    return {
        labels: sortedKeys,
        positive: sortedKeys.map(key => grouped[key].positive),
        negative: sortedKeys.map(key => grouped[key].negative),
        neutral: sortedKeys.map(key => grouped[key].neutral)
    };
}

// Export utility functions
window.NeilanXChartUtils = {
    processSentimentData,
    processKeywordData,
    processTrendData
};
