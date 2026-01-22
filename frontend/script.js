// ==================== CONFIGURATION ====================
const CONFIG = {
  API_BASE_URL: '/api/v1',
  MAX_WORDS: 512,
  DEBUG: false,
  REQUEST_TIMEOUT: 15000,
  MAX_RETRIES: 3,
  MAX_INPUT_LENGTH: 5000
};

console.log(`🌐 API Base URL: ${CONFIG.API_BASE_URL}`);
console.log(`🔧 Debug mode: ${CONFIG.DEBUG}`);

const MAX_WORDS = CONFIG.MAX_WORDS;
const API_BASE_URL = CONFIG.API_BASE_URL;

// Label mappings
const LABEL_ENGLISH = {
  'LABEL_0': 'Economic',
  'LABEL_1': 'Entertainment',
  'LABEL_2': 'Life',
  'LABEL_3': 'Politic',
  'LABEL_4': 'Sport',
  'LABEL_5': 'Technology',
  'UNKNOWN': 'Unknown'
};

const LABEL_KHMER = {
  'LABEL_0': 'សេដ្ឋកិច្ច',
  'LABEL_1': 'កម្សាន្ត',
  'LABEL_2': 'ជីវិត',
  'LABEL_3': 'នយោបាយ',
  'LABEL_4': 'កីឡា',
  'LABEL_5': 'បច្ចេកវិទ្យា',
  'UNKNOWN': 'មិនស្គាល់'
};

let currentPage = 1;
let totalPages = 1;
let isLoading = false;

// ==================== UTILITY FUNCTIONS ====================

// Get CSRF token from cookies
function getCookie(name) {
  const value = `; ${document.cookie}`;
  const parts = value.split(`; ${name}=`);
  if (parts.length === 2) return parts.pop().split(';').shift();
  return null;
}

// Sanitize input text
function sanitizeInput(text) {
  if (!text) return '';
  
  // Trim and normalize whitespace
  text = text.trim().replace(/\s+/g, ' ');
  
  // Limit length
  if (text.length > CONFIG.MAX_INPUT_LENGTH) {
    text = text.substring(0, CONFIG.MAX_INPUT_LENGTH);
    console.warn(`Input truncated to ${CONFIG.MAX_INPUT_LENGTH} characters`);
  }
  
  return text;
}

// Fetch with timeout
async function fetchWithTimeout(url, options, timeout = CONFIG.REQUEST_TIMEOUT) {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeout);
  
  try {
    const response = await fetch(url, {
      ...options,
      signal: controller.signal
    });
    clearTimeout(id);
    return response;
  } catch (error) {
    clearTimeout(id);
    throw error;
  }
}

// Fetch with retry logic
async function fetchWithRetry(url, options, maxRetries = CONFIG.MAX_RETRIES) {
  for (let i = 0; i < maxRetries; i++) {
    try {
      const response = await fetchWithTimeout(url, options);
      
      if (response.ok) {
        return response;
      }
      
      // If it's a server error, retry
      if (response.status >= 500) {
        if (CONFIG.DEBUG) {
          console.warn(`Attempt ${i + 1} failed with ${response.status}, retrying...`);
        }
        
        if (i < maxRetries - 1) {
          // Exponential backoff
          const delay = 1000 * Math.pow(2, i);
          await new Promise(resolve => setTimeout(resolve, delay));
          continue;
        }
      }
      
      // If it's a client error (4xx), don't retry
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      
    } catch (error) {
      if (i === maxRetries - 1) throw error;
      
      if (CONFIG.DEBUG) {
        console.warn(`Attempt ${i + 1} failed: ${error.message}, retrying...`);
      }
      
      // Exponential backoff for network errors
      const delay = 1000 * Math.pow(2, i);
      await new Promise(resolve => setTimeout(resolve, delay));
    }
  }
}

// Track events (for analytics)
function trackEvent(eventName, properties = {}) {
  // Google Analytics (if available)
  if (window.gtag) {
    window.gtag('event', eventName, properties);
  }
  
  // Custom event logging
  if (CONFIG.DEBUG) {
    console.log(`📊 Event: ${eventName}`, properties);
  }
}

// Format date for display
function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('en-GB', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

// ==================== DARK MODE TOGGLE ====================
const toggle = document.getElementById('dark-toggle');
const body = document.body;

if (toggle) {
  // Initialize dark mode from localStorage
  const isLightMode = localStorage.getItem('theme') === 'light';
  if (isLightMode) {
    body.classList.add('light');
    toggle.innerHTML = '☀️';
  } else {
    toggle.innerHTML = '🌙';
  }
  
  toggle.addEventListener('click', () => {
    const isLight = body.classList.toggle('light');
    toggle.innerHTML = isLight ? '☀️' : '🌙';
    
    // Save preference
    localStorage.setItem('theme', isLight ? 'light' : 'dark');
    
    trackEvent('theme_toggled', { theme: isLight ? 'light' : 'dark' });
  });
}

// ==================== PREDICTION FUNCTION ====================
document.getElementById('predict-single').addEventListener('click', async () => {
  // Prevent multiple simultaneous requests
  if (isLoading) {
    alert('A prediction is already in progress. Please wait.');
    return;
  }
  
  const textElement = document.getElementById('single-text');
  if (!textElement) return;
  
  let text = textElement.value.trim();
  if (!text) {
    alert('⚠️ Please enter some text');
    return;
  }
  
  // Sanitize input
  text = sanitizeInput(text);
  if (text.length === 0) {
    alert('⚠️ Please enter valid text');
    return;
  }
  
  isLoading = true;
  const predictBtn = document.getElementById('predict-single');
  const originalText = predictBtn.textContent;
  
  predictBtn.disabled = true;
  predictBtn.textContent = 'Predicting...';
  
  document.getElementById('loader-single').style.display = 'block';
  document.getElementById('single-result').style.display = 'none';
  
  trackEvent('prediction_requested', { 
    text_length: text.length,
    timestamp: new Date().toISOString()
  });

  try {
    console.log('📤 Sending prediction request...');
    
    // Get CSRF token
    const csrfToken = getCookie('csrftoken');
    
    const response = await fetchWithRetry(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(csrfToken && { 'X-CSRFToken': csrfToken })
      },
      body: JSON.stringify({ 
        text_input: text,
        feedback: null
      })
    });
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }
    
    const result = await response.json();
    console.log('✅ Prediction result:', result);
    
    const label = result.label_classified || 'UNKNOWN';
    const accuracy = result.accuracy || 0;
    
    document.getElementById('pred-label').textContent = `${LABEL_KHMER[label] || label} / ${LABEL_ENGLISH[label] || label}`;
    document.getElementById('pred-accuracy').textContent = `${accuracy.toFixed(2)} %`;
    
    document.getElementById('single-result').dataset.predictionId = result.id;
    document.getElementById('single-result').style.display = 'block';
    
    // Reset feedback UI
    document.getElementById('like-btn').classList.remove('liked');
    document.getElementById('dislike-btn').classList.remove('disliked');
    document.getElementById('feedback-status').textContent = 'No feedback given yet';
    document.getElementById('feedback-status').style.color = '';
    
    // Update probability table
    updateProbabilityTable(label);
    
    // Track successful prediction
    trackEvent('prediction_completed', {
      predictionId: result.id,
      label: label,
      accuracy: accuracy,
      timestamp: new Date().toISOString()
    });
    
    // Load updated history
    loadHistory();

  } catch (error) {
    console.error('❌ Prediction error:', error);
    
    // User-friendly error messages
    let errorMessage = 'Prediction failed';
    if (error.name === 'AbortError') {
      errorMessage = 'Request timeout. Please try again.';
    } else if (error.message.includes('HTTP 5')) {
      errorMessage = 'Server error. Please try again later.';
    } else if (error.message.includes('HTTP 4')) {
      errorMessage = 'Invalid request. Please check your input.';
    } else if (error.message.includes('NetworkError') || error.message.includes('Failed to fetch')) {
      errorMessage = 'Network error. Please check your connection.';
    } else {
      errorMessage = `Prediction failed: ${error.message}`;
    }
    
    alert(`❌ ${errorMessage}`);
    
    // Track error
    trackEvent('prediction_error', {
      error: error.message,
      timestamp: new Date().toISOString()
    });
  } finally {
    isLoading = false;
    document.getElementById('loader-single').style.display = 'none';
    predictBtn.disabled = false;
    predictBtn.textContent = originalText;
  }
});

// ==================== UPDATE PROBABILITY TABLE ====================
function updateProbabilityTable(selectedLabel) {
  const table = document.getElementById('prob-table');
  if (!table) return;
  
  let html = '<tr><th>Category</th><th>Khmer</th><th>English</th><th>Status</th></tr>';
  
  for (const [key, khmerLabel] of Object.entries(LABEL_KHMER)) {
    if (key === 'UNKNOWN') continue;
    
    const isSelected = key === selectedLabel;
    const englishLabel = LABEL_ENGLISH[key] || key;
    
    html += `
      <tr ${isSelected ? 'style="font-weight: bold; background: #f0fdf4;"' : ''}>
        <td>${key}</td>
        <td>${khmerLabel}</td>
        <td>${englishLabel}</td>
        <td>${isSelected ? '✅ Predicted' : ''}</td>
      </tr>
    `;
  }
  
  table.innerHTML = html;
}

// ==================== FEEDBACK FUNCTION ====================
async function sendFeedback(feedbackValue) {
  const singleResult = document.getElementById('single-result');
  if (!singleResult) {
    alert('⚠️ Make a prediction first');
    return;
  }
  
  const predictionId = singleResult.dataset.predictionId;
  if (!predictionId) {
    alert('⚠️ Make a prediction first');
    return;
  }

  trackEvent('feedback_submitted', {
    predictionId: predictionId,
    feedback: feedbackValue,
    timestamp: new Date().toISOString()
  });

  try {
    const csrfToken = getCookie('csrftoken');
    
    const response = await fetchWithRetry(`${API_BASE_URL}/predictions/${predictionId}/feedback`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(csrfToken && { 'X-CSRFToken': csrfToken })
      },
      body: JSON.stringify({ feedback: feedbackValue })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    // Update UI
    if (feedbackValue) {
      document.getElementById('like-btn').classList.add('liked');
      document.getElementById('dislike-btn').classList.remove('disliked');
      document.getElementById('feedback-status').textContent = '✅ Thank you! You liked this prediction 👍';
      document.getElementById('feedback-status').style.color = '#10b981';
    } else {
      document.getElementById('dislike-btn').classList.add('disliked');
      document.getElementById('like-btn').classList.remove('liked');
      document.getElementById('feedback-status').textContent = '❌ Sorry! You disliked this prediction 👎';
      document.getElementById('feedback-status').style.color = '#ef4444';
    }
    
    // Reload history
    loadHistory();
    
    trackEvent('feedback_success', {
      predictionId: predictionId,
      feedback: feedbackValue,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Feedback error:', error);
    alert(`❌ Feedback failed: ${error.message}`);
    
    trackEvent('feedback_error', {
      predictionId: predictionId,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
}

// Setup feedback buttons
document.getElementById('like-btn').addEventListener('click', () => sendFeedback(true));
document.getElementById('dislike-btn').addEventListener('click', () => sendFeedback(false));

// ==================== HISTORY FUNCTION ====================
async function loadHistory() {
  const tbody = document.querySelector('#history-table tbody');
  const noHistory = document.getElementById('no-history');
  const loader = document.getElementById('loader-history');
  const table = document.getElementById('history-table');
  const paginationControls = document.getElementById('pagination-controls');
  
  if (!tbody || !noHistory || !loader || !table) {
    console.error('History elements not found');
    return;
  }
  
  loader.style.display = 'block';
  tbody.innerHTML = '';
  table.style.display = 'none';
  noHistory.style.display = 'none';
  if (paginationControls) paginationControls.style.display = 'none';

  trackEvent('history_load_started', {
    page: currentPage,
    timestamp: new Date().toISOString()
  });

  try {
    const csrfToken = getCookie('csrftoken');
    
    const response = await fetchWithRetry(`${API_BASE_URL}/predictions?page=${currentPage}&limit=10`, {
      method: 'GET',
      headers: { 
        'Accept': 'application/json',
        ...(csrfToken && { 'X-CSRFToken': csrfToken })
      }
    });
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    const data = await response.json();
    console.log('History data:', data);
    
    let predictions = [];
    if (data.predictions && Array.isArray(data.predictions)) {
      predictions = data.predictions;
      totalPages = data.total_pages || 1;
    }
    
    if (predictions.length === 0) {
      noHistory.textContent = 'No predictions yet. Make your first prediction!';
      noHistory.style.display = 'block';
    } else {
      // Display predictions
      predictions.forEach(pred => {
        const tr = document.createElement('tr');
        
        // Time
        const timeStr = formatDate(pred.created_at);
        
        // Text preview
        const text = pred.text_input || '';
        const preview = text.length > 30 ? text.substring(0, 30) + '…' : text;
        
        // Label
        const label = pred.label_classified || 'UNKNOWN';
        const labelText = LABEL_ENGLISH[label] || label;
        
        // Accuracy
        const accuracy = pred.accuracy || 0;
        
        // Feedback
        let feedbackHTML = '';
        if (pred.feedback === true) {
          feedbackHTML = '<span style="color: #10b981;" title="Liked">👍</span>';
        } else if (pred.feedback === false) {
          feedbackHTML = '<span style="color: #ef4444;" title="Disliked">👎</span>';
        } else {
          const predId = pred.id;
          if (predId) {
            feedbackHTML = `
              <button class="small-feedback-btn" onclick="giveFeedback(${predId}, true)" title="Like">👍</button>
              <button class="small-feedback-btn" onclick="giveFeedback(${predId}, false)" title="Dislike">👎</button>
            `;
          }
        }
        
        tr.innerHTML = `
          <td>${timeStr}</td>
          <td title="${text.replace(/"/g, '&quot;')}">${preview}</td>
          <td>${labelText}</td>
          <td>${accuracy.toFixed(2)} %</td>
          <td>${feedbackHTML}</td>
        `;
        
        tbody.appendChild(tr);
      });
      
      table.style.display = 'table';
      
      // Update pagination
      updatePaginationControls();
      
      if (paginationControls && totalPages > 1) {
        paginationControls.style.display = 'flex';
      }
    }

    trackEvent('history_load_success', {
      page: currentPage,
      count: predictions.length,
      total_pages: totalPages,
      timestamp: new Date().toISOString()
    });

  } catch (error) {
    console.error('❌ History load error:', error);
    
    noHistory.innerHTML = `
      <div style="text-align: center; padding: 20px; color: #ef4444;">
        <div style="font-size: 24px; margin-bottom: 10px;">❌</div>
        <strong>Error loading history</strong><br>
        <small style="display: block; margin: 10px 0;">${error.message}</small>
        <button onclick="loadHistory()" style="
          padding: 8px 16px; 
          background: var(--primary); 
          color: white; 
          border: none; 
          border-radius: 4px; 
          cursor: pointer;
          margin-top: 10px;
        ">
          Retry
        </button>
      </div>
    `;
    noHistory.style.display = 'block';
    
    trackEvent('history_load_error', {
      page: currentPage,
      error: error.message,
      timestamp: new Date().toISOString()
    });
    
  } finally {
    loader.style.display = 'none';
  }
}

// ==================== PAGINATION CONTROLS ====================
function updatePaginationControls() {
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');
  const pageInfo = document.getElementById('page-info');
  const pageInput = document.getElementById('page-input');
  
  if (prevBtn) {
    prevBtn.disabled = currentPage <= 1;
  }
  
  if (nextBtn) {
    nextBtn.disabled = currentPage >= totalPages;
  }
  
  if (pageInfo) {
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  }
  
  if (pageInput) {
    pageInput.value = currentPage;
    pageInput.max = totalPages;
  }
}

// ==================== HISTORY TABLE FEEDBACK ====================
window.giveFeedback = async function(predictionId, feedbackValue) {
  if (!predictionId) {
    alert('⚠️ Invalid prediction');
    return;
  }

  trackEvent('history_feedback_submitted', {
    predictionId: predictionId,
    feedback: feedbackValue,
    timestamp: new Date().toISOString()
  });

  try {
    const csrfToken = getCookie('csrftoken');
    
    const response = await fetchWithRetry(`${API_BASE_URL}/predictions/${predictionId}/feedback`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        ...(csrfToken && { 'X-CSRFToken': csrfToken })
      },
      body: JSON.stringify({ feedback: feedbackValue })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    // Reload history
    loadHistory();
    
    // Show success message
    const message = feedbackValue ? 'liked' : 'disliked';
    alert(`✅ Feedback ${message} submitted!`);
    
    trackEvent('history_feedback_success', {
      predictionId: predictionId,
      feedback: feedbackValue,
      timestamp: new Date().toISOString()
    });
    
  } catch (error) {
    console.error('❌ Feedback error:', error);
    alert(`❌ Feedback failed: ${error.message}`);
    
    trackEvent('history_feedback_error', {
      predictionId: predictionId,
      error: error.message,
      timestamp: new Date().toISOString()
    });
  }
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Khmer Text Classifier initialized');
  
  // Setup pagination listeners
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');
  const refreshBtn = document.getElementById('refresh-history');
  const goToPageBtn = document.getElementById('go-to-page');
  const pageInput = document.getElementById('page-input');
  
  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        loadHistory();
        trackEvent('pagination_prev', { page: currentPage });
      }
    });
  }
  
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (currentPage < totalPages) {
        currentPage++;
        loadHistory();
        trackEvent('pagination_next', { page: currentPage });
      }
    });
  }
  
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadHistory();
      refreshBtn.textContent = '↻ Refreshing...';
      trackEvent('history_refresh', { timestamp: new Date().toISOString() });
      
      setTimeout(() => {
        refreshBtn.textContent = '↻ Refresh';
      }, 1000);
    });
  }
  
  if (goToPageBtn && pageInput) {
    goToPageBtn.addEventListener('click', () => {
      const page = parseInt(pageInput.value);
      if (page >= 1 && page <= totalPages && page !== currentPage) {
        currentPage = page;
        loadHistory();
        trackEvent('pagination_jump', { page: currentPage });
      }
    });
    
    pageInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        goToPageBtn.click();
      }
    });
  }
  
  // Auto-refresh history every 30 seconds
  setInterval(() => {
    if (document.getElementById('history-table').style.display !== 'none') {
      loadHistory();
    }
  }, 30000);
  
  // Initial load
  loadHistory();
  
  // Track page view
  trackEvent('page_view', {
    url: window.location.href,
    timestamp: new Date().toISOString()
  });
});

// Service Worker registration for PWA (optional)
if ('serviceWorker' in navigator && CONFIG.API_BASE_URL.startsWith('https')) {
  window.addEventListener('load', () => {
    navigator.serviceWorker.register('/service-worker.js')
      .then(registration => {
        console.log('✅ ServiceWorker registered:', registration.scope);
      })
      .catch(error => {
        console.log('❌ ServiceWorker registration failed:', error);
      });
  });
}

console.log('📝 Script loaded successfully');