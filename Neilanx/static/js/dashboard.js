// Dashboard JavaScript functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Auto-refresh functionality for processing uploads
    function checkUploadStatus() {
        const processingUploads = document.querySelectorAll('[data-status="processing"]');
        
        if (processingUploads.length > 0) {
            // Refresh page every 30 seconds if there are processing uploads
            setTimeout(() => {
                window.location.reload();
            }, 30000);
        }
    }

    // Initialize status checking
    checkUploadStatus();

    // Smooth scrolling for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // Copy to clipboard functionality
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(function() {
            // Show success message
            const toast = new bootstrap.Toast(document.createElement('div'));
            // Could implement toast notifications here
        });
    }

    // Format numbers for display
    function formatNumber(num) {
        return new Intl.NumberFormat('sv-SE').format(num);
    }

    // Update any number displays
    document.querySelectorAll('.format-number').forEach(el => {
        const num = parseInt(el.textContent);
        if (!isNaN(num)) {
            el.textContent = formatNumber(num);
        }
    });

    // Handle dynamic content loading
    function loadSentimentData(uploadId) {
        fetch(`/api/sentiment_data/${uploadId}`)
            .then(response => response.json())
            .then(data => {
                updateSentimentChart(data);
            })
            .catch(error => {
                console.error('Error loading sentiment data:', error);
            });
    }

    // Chart update function
    function updateSentimentChart(data) {
        // This would be called by charts.js
        if (window.updateDashboardChart) {
            window.updateDashboardChart(data);
        }
    }

    // File upload progress (if needed)
    function showUploadProgress() {
        const progressBar = document.getElementById('uploadProgress');
        if (progressBar) {
            progressBar.style.display = 'block';
            // Simulate progress
            let progress = 0;
            const interval = setInterval(() => {
                progress += 10;
                progressBar.style.width = progress + '%';
                if (progress >= 100) {
                    clearInterval(interval);
                }
            }, 500);
        }
    }

    // Search and filter functionality
    const searchInput = document.getElementById('reviewSearch');
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const reviewRows = document.querySelectorAll('.review-row');
            
            reviewRows.forEach(row => {
                const reviewText = row.querySelector('.review-text').textContent.toLowerCase();
                if (reviewText.includes(searchTerm)) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Sentiment filter
    const sentimentFilter = document.getElementById('sentimentFilter');
    if (sentimentFilter) {
        sentimentFilter.addEventListener('change', function() {
            const selectedSentiment = this.value;
            const reviewRows = document.querySelectorAll('.review-row');
            
            reviewRows.forEach(row => {
                const sentiment = row.dataset.sentiment;
                if (selectedSentiment === '' || sentiment === selectedSentiment) {
                    row.style.display = '';
                } else {
                    row.style.display = 'none';
                }
            });
        });
    }

    // Export functionality
    function exportData(format) {
        // This would trigger server-side export
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = '/export';
        
        const formatInput = document.createElement('input');
        formatInput.type = 'hidden';
        formatInput.name = 'format';
        formatInput.value = format;
        
        form.appendChild(formatInput);
        document.body.appendChild(form);
        form.submit();
        document.body.removeChild(form);
    }

    // Add export button handlers
    document.querySelectorAll('.export-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const format = this.dataset.format;
            exportData(format);
        });
    });

    // Real-time updates (WebSocket would be ideal)
    function checkForUpdates() {
        // Poll for updates every 60 seconds
        setInterval(() => {
            fetch('/api/status')
                .then(response => response.json())
                .then(data => {
                    if (data.hasUpdates) {
                        // Show notification about new data
                        showUpdateNotification();
                    }
                })
                .catch(error => {
                    console.error('Error checking for updates:', error);
                });
        }, 60000);
    }

    function showUpdateNotification() {
        const notification = document.createElement('div');
        notification.className = 'alert alert-info alert-dismissible fade show position-fixed top-0 end-0 m-3';
        notification.style.zIndex = '1050';
        notification.innerHTML = `
            <i class="fas fa-info-circle me-2"></i>
            Nya data tillgängliga. <a href="#" onclick="window.location.reload()">Uppdatera sidan</a>
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.body.appendChild(notification);
        
        // Auto-remove after 10 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 10000);
    }

    // Initialize update checking
    checkForUpdates();

    // Keyboard shortcuts
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + U for upload
        if ((e.ctrlKey || e.metaKey) && e.key === 'u') {
            e.preventDefault();
            window.location.href = '/upload';
        }
        
        // Ctrl/Cmd + R for reports
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            window.location.href = '/reports';
        }
    });

    // Mobile menu improvements
    const navbarToggler = document.querySelector('.navbar-toggler');
    const navbarCollapse = document.querySelector('.navbar-collapse');
    
    if (navbarToggler && navbarCollapse) {
        // Close mobile menu when clicking outside
        document.addEventListener('click', function(e) {
            if (!navbarCollapse.contains(e.target) && !navbarToggler.contains(e.target)) {
                if (navbarCollapse.classList.contains('show')) {
                    navbarToggler.click();
                }
            }
        });
    }
});

// Global utility functions
window.NeilanX = {
    formatNumber: function(num) {
        return new Intl.NumberFormat('sv-SE').format(num);
    },
    
    formatDate: function(date) {
        return new Intl.DateTimeFormat('sv-SE').format(new Date(date));
    },
    
    showAlert: function(message, type = 'info') {
        const alertContainer = document.getElementById('alert-container') || document.body;
        const alert = document.createElement('div');
        alert.className = `alert alert-${type} alert-dismissible fade show`;
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        alertContainer.appendChild(alert);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (alert.parentNode) {
                alert.remove();
            }
        }, 5000);
    }
};
