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

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    // Set up form submission handler
    if (scrapeForm) {
        scrapeForm.addEventListener('submit', handleScrapeSubmit);
    }
    
    // Set up rating filter buttons
    const ratingButtons = document.querySelectorAll('.rating-btn');
    ratingButtons.forEach(button => {
        button.addEventListener('click', function() {
            this.classList.toggle('active');
        });
    });
});

// Handle form submission
async function handleScrapeSubmit(event) {
    event.preventDefault();
    
    // Get form data
    const formData = new FormData(scrapeForm);
    const appId = formData.get('app_id');
    const lang = formData.get('lang');
    const country = formData.get('country');
    const count = formData.get('count');
    
    // Get selected ratings
    const selectedRatings = [];
    document.querySelectorAll('.rating-btn.active').forEach(button => {
        selectedRatings.push(parseInt(button.dataset.rating));
    });
    
    // Validate input
    if (!appId) {
        showAlert('Please enter an App ID', 'danger');
        return;
    }
    
    // Show loading indicator
    showLoading(true);
    hideResults();
    showAlert('', 'hidden'); // Clear any previous alerts
    
    try {
        // If no ratings selected, scrape all ratings
        if (selectedRatings.length === 0) {
            // Scrape for each rating 1-5
            const promises = [];
            for (let i = 1; i <= 5; i++) {
                promises.push(scrapeReviews(appId, lang, country, i, Math.ceil(count/5)));
            }
            
            const results = await Promise.all(promises);
            
            // Find the session with the most reviews or the first one
            let bestResult = results[0];
            for (const result of results) {
                if (result.session_id) {
                    bestResult = result;
                    break;
                }
            }
            
            currentSessionId = bestResult.session_id;
        } else {
            // Scrape for selected ratings
            // For simplicity, we'll scrape for the first selected rating
            // In a full implementation, you might want to scrape for all selected ratings
            const filterScore = selectedRatings[0];
            const result = await scrapeReviews(appId, lang, country, filterScore, count);
            currentSessionId = result.session_id;
        }
        
        // Process the reviews
        await processReviews(currentSessionId);
        
        // Show results
        showResults();
        await loadStatistics(currentSessionId);
        await loadWordCloud(currentSessionId);
        await loadRatingChart(currentSessionId);
        await loadReviews(currentSessionId, 1);
        
    } catch (error) {
        console.error('Error during scraping:', error);
        showAlert('Error occurred during scraping: ' + error.message, 'danger');
        showLoading(false);
    }
}

// Scrape reviews from the backend
async function scrapeReviews(appId, lang, country, filterScore, count) {
    const response = await fetch('/api/scrape', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            app_id: appId,
            lang: lang,
            country: country,
            filter_score: filterScore,
            count: parseInt(count)
        })
    });
    
    if (!response.ok) {
        throw new Error('Failed to start scraping');
    }
    
    return await response.json();
}

// Process reviews (preprocessing)
async function processReviews(sessionId) {
    // In a full implementation, this would call an API endpoint
    // to preprocess the reviews
    // For now, we'll just simulate this with a delay
    return new Promise(resolve => {
        setTimeout(() => {
            resolve({status: 'completed'});
        }, 2000);
    });
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
        document.getElementById('total-reviews').textContent = stats.total_reviews;
        document.getElementById('average-rating').textContent = stats.average_rating;
        
        // Update most common words
        const wordsContainer = document.getElementById('most-common-words');
        wordsContainer.innerHTML = '';
        for (const [word, count] of Object.entries(stats.most_common_words)) {
            const wordTag = document.createElement('span');
            wordTag.className = 'word-tag';
            wordTag.textContent = `${word} (${count})`;
            wordsContainer.appendChild(wordTag);
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
    paginationContainer.innerHTML = '';
    
    // Previous button
    const prevButton = document.createElement('button');
    prevButton.className = 'pagination-btn';
    prevButton.textContent = 'Previous';
    prevButton.disabled = currentPage === 1;
    prevButton.addEventListener('click', () => {
        if (currentPage > 1) {
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
            loadReviews(currentSessionId, i);
        });
        paginationContainer.appendChild(pageButton);
    }
    
    // Next button
    const nextButton = document.createElement('button');
    nextButton.className = 'pagination-btn';
    nextButton.textContent = 'Next';
    nextButton.disabled = currentPage === totalPages;
    nextButton.addEventListener('click', () => {
        if (currentPage < totalPages) {
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