// Main JavaScript for the Google Play Review Scraper

// Global variables
let currentSessionId = null;
let currentPage = 1;
let totalPages = 1;

// DOM Elements
const scrapeForm = document.getElementById('scrape-form');
const resultsSection = document.getElementById('results-section');
const loadingIndicator = document.getElementById('loading');
const alertContainer = document.getElementById('alert-container');

// Utility functions
function showLoading() {
    if (loadingIndicator) {
        loadingIndicator.style.display = 'block';
    }
}

function hideLoading() {
    if (loadingIndicator) {
        loadingIndicator.style.display = 'none';
    }
}

function showAlert(message, type) {
    if (alertContainer) {
        alertContainer.textContent = message;
        alertContainer.className = `alert alert-${type === 'error' ? 'danger' : type === 'info' ? 'info' : 'success'}`;
        alertContainer.classList.remove('hidden');
        
        // Hide after 5 seconds
        setTimeout(() => {
            alertContainer.classList.add('hidden');
        }, 5000);
    }
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Set up form submission handler
    if (scrapeForm) {
        scrapeForm.addEventListener('submit', handleScrapeSubmit);
    }
    
    // Set up rating filter buttons (single select)
    const ratingButtons = document.querySelectorAll('.rating-btn');
    ratingButtons.forEach(button => {
        button.addEventListener('click', function() {
            // Remove active class from all buttons
            ratingButtons.forEach(btn => btn.classList.remove('active'));
            
            // Toggle current button
            if (!this.classList.contains('was-active')) {
                this.classList.add('active');
                this.classList.add('was-active');
            } else {
                this.classList.remove('was-active');
            }
            
            // Update was-active status for all buttons
            ratingButtons.forEach(btn => {
                if (btn !== this) {
                    btn.classList.remove('was-active');
                }
            });
        });
    });
});

// Handle form submission
    function handleScrapeSubmit(event) {
        event.preventDefault();
        
        const formData = new FormData(event.target);
        const appId = formData.get('app_id');
        const count = formData.get('count');
        const lang = formData.get('lang');
        const country = formData.get('country');
        const sort = formData.get('sort');
        
        // Get selected rating filter (single selection)
        const selectedRating = document.querySelector('.rating-btn.active');
        const filterScore = selectedRating ? parseInt(selectedRating.dataset.rating) : null;
        
        if (!appId) {
            alert('Masukkan Google Play App ID!');
            return;
        }
        
        // Show loading state
        const submitBtn = event.target.querySelector('button[type="submit"]');
        const originalText = submitBtn.textContent;
        submitBtn.textContent = 'Processing...';
        submitBtn.disabled = true;
        
        // Show progress container
        document.getElementById('progress-container').style.display = 'block';
        document.getElementById('results-section').style.display = 'none';
        
        // Start scraping process
        startScraping(appId, count, lang, country, sort, filterScore, submitBtn, originalText);
    }

// Start the complete scraping workflow
async function startScraping(appId, lang, country, count, filterScore, submitBtn, originalText) {
    try {
        // Step 1: Start scraping
        showAlert('Memulai scraping reviews...', 'info');
        const scrapeResult = await scrapeReviews(appId, lang, country, filterScore, count);
        currentSessionId = scrapeResult.session_id;
        
        // Step 2: Monitor progress
        await monitorScrapeProgress(currentSessionId);
        
        // Step 3: Load results
        await loadResults(currentSessionId);
        
        showAlert('Scraping berhasil diselesaikan!', 'success');
        
    } catch (error) {
        console.error('Scraping error:', error);
        showAlert('Error: ' + error.message, 'error');
    } finally {
        // Reset button state
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
        hideLoading();
    }
}

// Scrape reviews from the backend
async function scrapeReviews(appId, lang, country, filterScore, count) {
    const requestBody = {
        app_id: appId,
        lang: lang,
        country: country,
        count: parseInt(count)
    };
    
    // Only include filter_score if it's not null (to avoid filtering when no rating selected)
    if (filterScore !== null) {
        requestBody.filter_score = filterScore;
    }
    
    const response = await fetch('/api/scrape', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody)
    });
    
    if (!response.ok) {
        throw new Error('Failed to start scraping');
    }
    
    return await response.json();
}

// Monitor scraping progress
async function monitorScrapeProgress(sessionId) {
    return new Promise((resolve, reject) => {
        const checkProgress = async () => {
            try {
                const response = await fetch(`/api/scrape/status/${sessionId}`);
                if (!response.ok) {
                    throw new Error('Failed to check progress');
                }
                
                const status = await response.json();
                showAlert(`Status: ${status.status} (${status.review_count} reviews)`, 'info');
                
                if (status.status === 'completed') {
                    resolve(status);
                } else if (status.status === 'failed') {
                    reject(new Error('Scraping failed'));
                } else {
                    // Continue checking after 2 seconds
                    setTimeout(checkProgress, 2000);
                }
            } catch (error) {
                reject(error);
            }
        };
        
        checkProgress();
    });
}

// Load all results
async function loadResults(sessionId) {
    try {
        // Set current session for pagination
        currentSessionId = sessionId;
        
        // Show results section
        if (resultsSection) {
            resultsSection.style.display = 'block';
        }
        
        // Load statistics, wordcloud, chart, and reviews
        await Promise.all([
            loadStatistics(sessionId),
            loadWordCloud(sessionId),
            loadRatingChart(sessionId),
            loadReviews(sessionId)
        ]);
        
    } catch (error) {
        console.error('Error loading results:', error);
        showAlert('Error loading results: ' + error.message, 'error');
    }
}

// Load statistics
async function loadStatistics(sessionId) {
    try {
        const response = await fetch(`/api/statistics/${sessionId}`);
        if (!response.ok) {
            throw new Error('Failed to load statistics');
        }
        
        const stats = await response.json();

        // Update UI with statistics
        const totalReviewsEl = document.getElementById('total-reviews');
        if (totalReviewsEl) {
            totalReviewsEl.textContent = typeof stats.total_reviews !== 'undefined' ? stats.total_reviews : '-';
        }

        const averageRatingEl = document.getElementById('average-rating');
        if (averageRatingEl) {
            averageRatingEl.textContent = typeof stats.average_rating !== 'undefined' ? stats.average_rating : '-';
        }

        const reviewPeriodEl = document.getElementById('review-period');
        if (reviewPeriodEl) {
            const period = stats.review_period || {};
            const start = period.start;
            const end = period.end;

            if (start && end) {
                reviewPeriodEl.textContent = start === end ? start : `${start} - ${end}`;
            } else if (start) {
                reviewPeriodEl.textContent = start;
            } else if (end) {
                reviewPeriodEl.textContent = end;
            } else {
                reviewPeriodEl.textContent = '-';
            }
        }

        // Update most common words
        const wordsContainer = document.getElementById('most-common-words');
        if (wordsContainer) {
            wordsContainer.innerHTML = '';
            const wordStats = stats.most_common_words || {};
            const entries = Object.entries(wordStats);
            if (entries.length === 0) {
                const emptyState = document.createElement('span');
                emptyState.className = 'word-tag empty';
                emptyState.textContent = 'Tidak ada kata populer';
                wordsContainer.appendChild(emptyState);
            } else {
                for (const [word, count] of entries) {
                    const wordTag = document.createElement('span');
                    wordTag.className = 'word-tag';
                    wordTag.textContent = `${word} (${count})`;
                    wordsContainer.appendChild(wordTag);
                }
            }
        }

        // Update app information card
        const appInfoSection = document.getElementById('app-info-section');
        if (appInfoSection) {
            const appInfo = stats.app_info || {};
            if (appInfo && (appInfo.title || appInfo.app_id)) {
                appInfoSection.style.display = 'block';

                const titleEl = document.getElementById('app-info-title');
                if (titleEl) {
                    titleEl.textContent = appInfo.title || appInfo.app_id || '-';
                }

                const versionEl = document.getElementById('app-info-version');
                if (versionEl) {
                    versionEl.textContent = appInfo.version ? `Versi: ${appInfo.version}` : 'Versi tidak diketahui';
                }

                const descriptionEl = document.getElementById('app-info-description');
                if (descriptionEl) {
                    descriptionEl.textContent = appInfo.description || 'Tidak ada deskripsi tersedia.';
                }

                const genreEl = document.getElementById('app-info-genre');
                if (genreEl) {
                    genreEl.textContent = appInfo.genre || '-';
                }

                const genreIdEl = document.getElementById('app-info-genre-id');
                if (genreIdEl) {
                    genreIdEl.textContent = appInfo.genre_id || '-';
                }

                const localeEl = document.getElementById('app-info-locale');
                if (localeEl) {
                    const localeParts = [appInfo.lang, appInfo.country].filter(Boolean);
                    localeEl.textContent = localeParts.length ? localeParts.join('-').toUpperCase() : '-';
                }

                const appIdEl = document.getElementById('app-info-app-id');
                if (appIdEl) {
                    appIdEl.textContent = appInfo.app_id || '';
                }
            } else {
                appInfoSection.style.display = 'none';
            }
        }
        
    } catch (error) {
        console.error('Error loading statistics:', error);
    }
}

// Load wordcloud
async function loadWordCloud(sessionId) {
    try {
        const response = await fetch(`/api/wordcloud/${sessionId}`);
        if (!response.ok) {
            throw new Error('Failed to load wordcloud');
        }
        
        // Create object URL for the image
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        // Update image source
        const imgElement = document.getElementById('wordcloud-image');
        imgElement.src = imageUrl;
        imgElement.onload = () => URL.revokeObjectURL(imageUrl);
        
    } catch (error) {
        console.error('Error loading wordcloud:', error);
    }
}

// Load rating chart
async function loadRatingChart(sessionId) {
    try {
        const response = await fetch(`/api/rating-chart/${sessionId}`);
        if (!response.ok) {
            throw new Error('Failed to load rating chart');
        }
        
        // Create object URL for the image
        const blob = await response.blob();
        const imageUrl = URL.createObjectURL(blob);
        
        // Update image source
        const imgElement = document.getElementById('rating-chart');
        imgElement.src = imageUrl;
        imgElement.onload = () => URL.revokeObjectURL(imageUrl);
        
    } catch (error) {
        console.error('Error loading rating chart:', error);
    }
}

// Load reviews data
async function loadReviews(sessionId, page = 1) {
    try {
        const response = await fetch(`/api/reviews/${sessionId}?page=${page}&limit=10`);
        if (!response.ok) {
            throw new Error('Failed to load reviews');
        }
        
        const data = await response.json();
        
        // Update pagination
        currentPage = data.pagination.page;
        totalPages = data.pagination.total_pages;
        updatePagination();
        
        // Update reviews table
        const tbody = document.querySelector('#reviews-table tbody');
        tbody.innerHTML = '';
        
        data.reviews.forEach(review => {
            const row = document.createElement('tr');
            
            // Create star rating display
            let stars = '';
            for (let i = 1; i <= 5; i++) {
                if (i <= review.score) {
                    stars += '★';
                } else {
                    stars += '☆';
                }
            }
            
            row.innerHTML = `
                <td>${review.user_name || 'Anonymous'}</td>
                <td><span class="rating-stars">${stars}</span></td>
                <td>${new Date(review.at).toLocaleDateString()}</td>
                <td>${review.content.substring(0, 100)}${review.content.length > 100 ? '...' : ''}</td>
            `;
            
            tbody.appendChild(row);
        });
        
    } catch (error) {
        console.error('Error loading reviews:', error);
    } finally {
        showLoading(false);
    }
}

// Update pagination controls
function updatePagination() {
    const paginationContainer = document.getElementById('pagination');
    if (!paginationContainer) {
        console.error('Pagination container not found');
        return;
    }
    
    paginationContainer.innerHTML = '';
    
    // Skip pagination if no session or only 1 page
    if (!currentSessionId || totalPages <= 1) {
        return;
    }
    
    // Previous button
    const prevButton = document.createElement('button');
    prevButton.className = 'pagination-btn';
    prevButton.textContent = 'Previous';
    prevButton.disabled = currentPage === 1;
    prevButton.addEventListener('click', () => {
        if (currentPage > 1 && currentSessionId) {
            loadReviews(currentSessionId, currentPage - 1);
        }
    });
    paginationContainer.appendChild(prevButton);
    
    // Page buttons
    const startPage = Math.max(1, currentPage - 2);
    const endPage = Math.min(totalPages, startPage + 4);
    
    for (let i = startPage; i <= endPage; i++) {
        const pageButton = document.createElement('button');
        pageButton.className = `pagination-btn ${i === currentPage ? 'active' : ''}`;
        pageButton.textContent = i;
        pageButton.addEventListener('click', () => {
            if (currentSessionId && i !== currentPage) {
                loadReviews(currentSessionId, i);
            }
        });
        paginationContainer.appendChild(pageButton);
    }
    
    // Next button
    const nextButton = document.createElement('button');
    nextButton.className = 'pagination-btn';
    nextButton.textContent = 'Next';
    nextButton.disabled = currentPage >= totalPages;
    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages && currentSessionId) {
            loadReviews(currentSessionId, currentPage + 1);
        }
    });
    paginationContainer.appendChild(nextButton);
}

// Show/hide results section
function showResults() {
    if (resultsSection) {
        resultsSection.style.display = 'block';
    }
}

function hideResults() {
    if (resultsSection) {
        resultsSection.style.display = 'none';
    }
}

// Show/hide loading indicator
function showLoading(show) {
    if (loadingIndicator) {
        loadingIndicator.style.display = show ? 'block' : 'none';
    }
}

// Show alert message
function showAlert(message, type = 'info') {
    if (alertContainer) {
        alertContainer.className = `alert alert-${type}`;
        alertContainer.textContent = message;
        alertContainer.style.display = message ? 'block' : 'none';
    }
}

// Progress management functions
function updateProgress(step, percentage, message) {
    // Update progress bar
    const progressFill = document.getElementById('progress-fill');
    const progressPercentage = document.getElementById('progress-percentage');
    const progressMessage = document.getElementById('progress-message');
    
    if (progressFill) progressFill.style.width = percentage + '%';
    if (progressPercentage) progressPercentage.textContent = percentage + '%';
    if (progressMessage) progressMessage.textContent = message;
    
    // Update steps
    for (let i = 1; i <= 4; i++) {
        const stepEl = document.getElementById(`step-${i}`);
        if (stepEl) {
            stepEl.classList.remove('active', 'completed');
            
            if (i < step) {
                stepEl.classList.add('completed');
            } else if (i === step) {
                stepEl.classList.add('active');
            }
        }
    }
}

function hideProgress() {
    const progressContainer = document.getElementById('progress-container');
    if (progressContainer) {
        progressContainer.style.display = 'none';
    }
}

function showError(message) {
    hideProgress();
    showAlert('Error: ' + message, 'danger');
}

async function startScraping(appId, count, lang, country, sort, filterScore, submitBtn, originalText) {
    try {
        // Step 1: Initialize scraping
        updateProgress(1, 10, 'Memulai scraping reviews...');
        await sleep(500);
        
        // Step 2: Scrape data
        updateProgress(2, 30, 'Mengambil data dari Google Play Store...');
        
        const scrapeData = {
            app_id: appId,
            count: parseInt(count),
            lang: lang,
            country: country,
            sort: sort
        };
        
        if (filterScore) {
            scrapeData.filter_score = filterScore;
        }
        
        const response = await fetch('/api/scrape', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(scrapeData)
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const result = await response.json();
        
        if (result.error) {
            throw new Error(result.error);
        }
        
        // Step 3: Process data
        updateProgress(3, 60, 'Menyimpan dan memproses data...');
        await sleep(1000);
        
        // Step 4: Generate visualizations
        updateProgress(4, 90, 'Membuat visualisasi...');
        await sleep(1000);
        
        // Set current session ID for pagination
        currentSessionId = result.session_id;
        
        // Wait for scraping to complete before loading results
        await monitorScrapeProgress(result.session_id);
        
        // Load and display results
        await loadResults(result.session_id);
        
        // Show download button
        const downloadBtn = document.getElementById('download-csv-btn');
        if (downloadBtn) {
            downloadBtn.style.display = 'inline-block';
            downloadBtn.onclick = () => downloadCSV(result.session_id);
        }
        
        // Complete
        updateProgress(4, 100, 'Selesai!');
        await sleep(500);
        
        hideProgress();
        document.getElementById('results-section').style.display = 'block';
        
        showAlert('Reviews berhasil di-scrape!', 'success');
        
    } catch (error) {
        console.error('Scraping error:', error);
        showError(error.message);
    } finally {
        // Reset button
        submitBtn.textContent = originalText;
        submitBtn.disabled = false;
    }
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Download reviews as CSV
function downloadCSV(sessionId) {
    try {
        // Create download link
        const link = document.createElement('a');
        link.href = `/api/download/reviews/${sessionId}`;
        link.download = `reviews_${sessionId}.csv`;
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        
        showAlert('Download CSV dimulai...', 'success');
        
    } catch (error) {
        console.error('Download error:', error);
        showAlert('Gagal mendownload CSV: ' + error.message, 'error');
    }
}
