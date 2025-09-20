// Centralized Onboarding Controller
document.addEventListener('DOMContentLoaded', function() {
    // Read server-side state from data attributes
    const showOnboardingModal = document.body.dataset.showOnboarding === 'true';
    const showTutorial = document.body.dataset.showTutorial === 'true';
    const isLoggedIn = document.body.dataset.loggedIn === 'true';
    
    // Ensure mutual exclusion - never show both
    if (showTutorial) {
        // Server says to show tutorial, don't show modal
        console.log('Onboarding: Showing tutorial overlay, skipping modal');
        return;
    }
    
    if (showOnboardingModal && isLoggedIn) {
        // Server explicitly says to show onboarding modal
        console.log('Onboarding: Showing modal for logged-in user');
        setTimeout(() => {
            const modalElement = document.getElementById('onboardingModal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
        }, 1000);
        return;
    }
    
    // For anonymous users, check localStorage
    const onboardingCompleted = localStorage.getItem('neilanx_onboarding_completed');
    const hasExistingTutorial = document.getElementById('tutorialOverlay') !== null;
    
    if (!onboardingCompleted && !isLoggedIn && !hasExistingTutorial) {
        console.log('Onboarding: Showing modal for anonymous user');
        setTimeout(() => {
            const modalElement = document.getElementById('onboardingModal');
            if (modalElement) {
                const modal = new bootstrap.Modal(modalElement);
                modal.show();
            }
        }, 1500);
    }
});

// Demo functions for onboarding
function loadSampleData() {
    fetch('/api/demo_data')
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                if (window.NeilanX && window.NeilanX.showAlert) {
                    window.NeilanX.showAlert('Kunde inte ladda demodata: ' + data.error, 'error');
                } else {
                    alert('Kunde inte ladda demodata: ' + data.error);
                }
                return;
            }
            
            // Display demo data in dashboard format
            updateDemoDisplay(data);
            if (window.NeilanX && window.NeilanX.showAlert) {
                window.NeilanX.showAlert('Demodata laddad! Se resultaten nedan.', 'success');
            } else {
                alert('Demodata laddad! Se resultaten nedan.');
            }
        })
        .catch(error => {
            console.error('Error loading demo data:', error);
            if (window.NeilanX && window.NeilanX.showAlert) {
                window.NeilanX.showAlert('Ett fel uppstod vid laddning av demodata.', 'error');
            } else {
                alert('Ett fel uppstod vid laddning av demodata.');
            }
        });
}

function handleDemoUpload() {
    // Trigger download of sample CSV
    const link = document.createElement('a');
    link.href = '/api/demo_csv';
    link.download = 'exempel_recensioner.csv';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    if (window.NeilanX && window.NeilanX.showAlert) {
        window.NeilanX.showAlert('Exempel-CSV nedladdad! Ladda upp den för att testa systemet.', 'info');
    } else {
        alert('Exempel-CSV nedladdad! Ladda upp den för att testa systemet.');
    }
}

function updateDemoDisplay(data) {
    // Find demo containers and update them
    const reviewContainer = document.getElementById('demoReviewsContainer');
    const chartContainer = document.getElementById('demoChartContainer');
    
    if (reviewContainer && data.reviews) {
        reviewContainer.innerHTML = '';
        data.reviews.slice(0, 5).forEach(review => {
            const reviewElement = document.createElement('div');
            reviewElement.className = 'card mb-2';
            reviewElement.innerHTML = `
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <p class="mb-1">${review.review_text}</p>
                            <small class="text-muted">
                                <i class="fas fa-star text-warning"></i> ${review.rating}/5
                                - ${review.platform}
                            </small>
                        </div>
                        <span class="badge bg-${getSentimentColor(review.sentiment)}">${review.sentiment}</span>
                    </div>
                </div>
            `;
            reviewContainer.appendChild(reviewElement);
        });
    }
    
    if (chartContainer && data.sentiment_summary) {
        updateDemoChart(data.sentiment_summary);
    }
}

function getSentimentColor(sentiment) {
    switch(sentiment) {
        case 'positive': return 'success';
        case 'negative': return 'danger';
        default: return 'secondary';
    }
}

function updateDemoChart(sentimentData) {
    // Basic chart update for demo
    const chartContainer = document.getElementById('demoChartContainer');
    if (!chartContainer) return;
    
    chartContainer.innerHTML = `
        <div class="row text-center">
            <div class="col-4">
                <div class="bg-success bg-opacity-10 rounded p-3">
                    <h4 class="text-success mb-0">${sentimentData.positive || 0}</h4>
                    <small class="text-muted">Positiva</small>
                </div>
            </div>
            <div class="col-4">
                <div class="bg-secondary bg-opacity-10 rounded p-3">
                    <h4 class="text-secondary mb-0">${sentimentData.neutral || 0}</h4>
                    <small class="text-muted">Neutrala</small>
                </div>
            </div>
            <div class="col-4">
                <div class="bg-danger bg-opacity-10 rounded p-3">
                    <h4 class="text-danger mb-0">${sentimentData.negative || 0}</h4>
                    <small class="text-muted">Negativa</small>
                </div>
            </div>
        </div>
    `;
}

// Make functions globally available
window.loadSampleData = loadSampleData;
window.handleDemoUpload = handleDemoUpload;
window.updateDemoDisplay = updateDemoDisplay;