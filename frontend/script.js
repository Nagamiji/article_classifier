// ==================== CONFIGURATION ====================
// Auto-detect environment and set API URL
const getApiBaseUrl = () => {
  // If we're likely behind nginx / reverse proxy (no port or standard http/https ports)
  if (window.location.port === '' || 
      window.location.port === '80' || 
      window.location.port === '443') {
    return '/api/v1';  // Relative path → nginx will proxy to backend
  }
  // Otherwise assume local development (direct backend access)
  return 'http://localhost:8000/api/v1';
};

const CONFIG = {
  API_BASE_URL: getApiBaseUrl(),
  MAX_WORDS: 512,
  ENVIRONMENT: (window.location.port === '' || 
                window.location.port === '80' || 
                window.location.port === '443') ? 'production' : 'development'
};

console.log(`Running in ${CONFIG.ENVIRONMENT} mode`);
console.log(`API Base URL: ${CONFIG.API_BASE_URL}`);

const MAX_WORDS = CONFIG.MAX_WORDS;
const API_BASE_URL = CONFIG.API_BASE_URL;

// CORRECT LABEL MAPPING from your model
const LABEL_MAPPING = {
  'LABEL_0': 'សេដ្ឋកិច្ច / Economic',
  'LABEL_1': 'កម្សាន្ត / Entertainment', 
  'LABEL_2': 'ជីវិត / Life',
  'LABEL_3': 'នយោបាយ / Politic',
  'LABEL_4': 'កីឡា / Sport',
  'LABEL_5': 'បច្ចេកវិទ្យា / Technology'
};

const LABEL_ENGLISH = {
  'LABEL_0': 'Economic',
  'LABEL_1': 'Entertainment',
  'LABEL_2': 'Life',
  'LABEL_3': 'Politic',
  'LABEL_4': 'Sport',
  'LABEL_5': 'Technology'
};

// ==================== DARK MODE TOGGLE ====================
const toggle = document.getElementById('dark-toggle');
const body = document.body;

toggle.innerHTML = '🌙'; // Start in dark mode

toggle.addEventListener('click', () => {
  body.classList.toggle('light');
  toggle.innerHTML = body.classList.contains('light') ? '☀️' : '🌙';
});

// ==================== DOM ELEMENTS ====================
const textarea = document.getElementById('single-text');
const wordCount = document.getElementById('word-count');

// ==================== KHMER WORD COUNTING WITH BACKEND ====================
let wordCountTimeout = null;
let lastSegmentedText = '';
let currentWordCount = 0;
let isCountingWords = false;
let lastRequestTime = 0;

/**
 * Count Khmer words using backend API with khmernltk
 */
async function countKhmerWords(text) {
  if (!text || text.trim().length === 0) {
    return { count: 0, truncated: false, words: [], cleaned_text: '' };
  }

  try {
    const response = await fetch(`${API_BASE_URL}/segment`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text_input: text,
        max_words: MAX_WORDS
      })
    });

    if (!response.ok) {
      console.warn('Segment API failed, falling back to simple counting');
      // Fallback to simple space-based counting
      const words = text.trim().split(/\s+/).filter(w => w.length > 0);
      return { 
        count: words.length, 
        truncated: false, 
        words: words,
        cleaned_text: text 
      };
    }

    const result = await response.json();
    return {
      count: result.khmer_word_count,
      truncated: result.truncated,
      words: result.khmer_words || [],
      cleaned_text: result.cleaned_text || text
    };

  } catch (error) {
    console.warn('Error counting words, using fallback:', error);
    // Fallback to simple counting
    const words = text.trim().split(/\s+/).filter(w => w.length > 0);
    return { 
      count: words.length, 
      truncated: false, 
      words: words,
      cleaned_text: text 
    };
  }
}

/**
 * Update word count - called immediately for paste, debounced for typing
 */
async function updateWordCount(immediate = false) {
  const text = textarea.value;
  
  // Clear previous timeout
  if (wordCountTimeout) {
    clearTimeout(wordCountTimeout);
  }

  // Show loading indicator
  if (!isCountingWords) {
    wordCount.textContent = '⏳ Counting...';
    isCountingWords = true;
  }

  // Function to actually count words
  const doCount = async () => {
    try {
      lastRequestTime = Date.now();
      const result = await countKhmerWords(text);
      currentWordCount = result.count;
      
      // Update display
      wordCount.textContent = `${result.count} / ${MAX_WORDS} words`;
      isCountingWords = false;

      // Handle truncation
      if (result.truncated) {
        wordCount.classList.add('word-limit-warning');
        
        // Truncate textarea to cleaned text (already truncated by backend)
        if (result.cleaned_text && result.cleaned_text !== text) {
          textarea.value = result.cleaned_text;
          lastSegmentedText = result.cleaned_text;
          
          // Show alert only once per truncation
          if (text !== lastSegmentedText) {
            alert(`⚠️ Text automatically limited to ${MAX_WORDS} Khmer words.`);
          }
        }
      } else if (result.count > MAX_WORDS) {
        // Extra safety check - should not happen if backend works correctly
        wordCount.classList.add('word-limit-warning');
        
        // Reconstruct text from first MAX_WORDS words
        if (result.words && result.words.length > 0) {
          const truncatedWords = result.words.slice(0, MAX_WORDS);
          textarea.value = truncatedWords.join('');
          
          // Recount after truncation
          setTimeout(() => updateWordCount(true), 100);
        }
      } else {
        wordCount.classList.remove('word-limit-warning');
      }
    } catch (error) {
      console.error('Word count error:', error);
      wordCount.textContent = `? / ${MAX_WORDS} words`;
      wordCount.classList.remove('word-limit-warning');
      isCountingWords = false;
    }
  };

  // If immediate (paste event), count right away
  if (immediate) {
    await doCount();
  } else {
    // For typing, use shorter debounce (150ms instead of 300ms)
    wordCountTimeout = setTimeout(doCount, 150);
  }
}

// Attach event listeners
textarea.addEventListener('input', () => updateWordCount(false));

// Handle paste events immediately for real-time feel
textarea.addEventListener('paste', (e) => {
  // Let the paste happen first
  setTimeout(() => updateWordCount(true), 10);
});

// Initial count
updateWordCount(true);

// ==================== PREDICTION FUNCTION ====================
document.getElementById('predict-single').addEventListener('click', async () => {
  const text = textarea.value.trim();
  if (!text) {
    alert('⚠️ Please enter some text');
    return;
  }

  // Check word count before predicting
  if (currentWordCount === 0) {
    alert('⚠️ Please enter some Khmer or English text');
    return;
  }

  // Show loader
  document.getElementById('loader-single').style.display = 'block';
  document.getElementById('single-result').style.display = 'none';

  try {
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text_input: text,
        feedback: null
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP error ${response.status}`);
    }

    const result = await response.json();
    
    const label = result.label_classified;
    const labelText = LABEL_MAPPING[label] || label;
    
    document.getElementById('pred-label').textContent = labelText;

    // Display accuracy (confidence)
    const accuracy = result.accuracy;
    document.getElementById('pred-accuracy').textContent =
      accuracy !== null && accuracy !== undefined
        ? `${accuracy.toFixed(2)} %`
        : 'N/A';
    
    // Store prediction ID for feedback
    document.getElementById('single-result').dataset.predictionId = result.id;
    
    document.getElementById('single-result').style.display = 'block';
    
    // Reset feedback UI
    document.getElementById('like-btn').classList.remove('liked');
    document.getElementById('dislike-btn').classList.remove('disliked');
    document.getElementById('feedback-status').textContent = 'No feedback given yet';
    
    // Show probability table
    const table = document.getElementById('prob-table');
    table.innerHTML = `
      <tr>
        <th>Category</th>
        <th>Khmer</th>
        <th>English</th>
        <th>Status</th>
      </tr>
      ${Object.entries(LABEL_MAPPING).map(([key, fullLabel]) => {
        const parts = fullLabel.split(' / ');
        const khmer = parts[0];
        const english = parts[1];
        const isSelected = key === label;
        
        return `
          <tr ${isSelected ? 'style="font-weight: bold; background: #f0fdf4;"' : ''}>
            <td>${key}</td>
            <td>${khmer}</td>
            <td>${english}</td>
            <td>${isSelected ? '✅ Predicted' : ''}</td>
          </tr>
        `;
      }).join('')}
    `;

  } catch (error) {
    console.error('Prediction error:', error);
    alert(`❌ Error: ${error.message}\n\nAPI endpoint: ${API_BASE_URL}/predict\nEnvironment: ${CONFIG.ENVIRONMENT}\n\nPlease check:\n• Backend is running\n• Database is connected\n• Model is loaded`);
  } finally {
    document.getElementById('loader-single').style.display = 'none';
    loadHistory();
  }
});

// ==================== FEEDBACK FUNCTION ====================
async function sendFeedback(feedbackValue) {
  const predictionId = document.getElementById('single-result').dataset.predictionId;
  if (!predictionId) {
    alert('⚠️ No prediction to give feedback on. Make a prediction first.');
    return;
  }

  try {
    const response = await fetch(`${API_BASE_URL}/predictions/${predictionId}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        feedback: feedbackValue 
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
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

    // Reload history to show updated feedback
    loadHistory();

  } catch (error) {
    console.error('Feedback error:', error);
    alert(`❌ Error sending feedback: ${error.message}`);
  }
}

document.getElementById('like-btn').addEventListener('click', () => sendFeedback(true));
document.getElementById('dislike-btn').addEventListener('click', () => sendFeedback(false));

// ==================== HISTORY FUNCTION ====================
async function loadHistory() {
  const tbody = document.querySelector('#history-table tbody');
  const noHistory = document.getElementById('no-history');
  const loader = document.getElementById('loader-history');
  
  if (!tbody || !noHistory || !loader) {
    console.warn('History elements not found in DOM');
    return;
  }
  
  loader.style.display = 'block';
  tbody.innerHTML = '';
  document.getElementById('history-table').style.display = 'none';
  noHistory.style.display = 'none';

  try {
    const response = await fetch(`${API_BASE_URL}/predictions`);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const predictions = await response.json();

    if (predictions.length === 0) {
      noHistory.style.display = 'block';
      noHistory.textContent = 'No predictions yet. Make your first prediction!';
    } else {
      predictions
        .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
        .slice(0, 10)
        .forEach(pred => {
          const tr = tbody.insertRow();
          
          // Time column
          const time = new Date(pred.created_at);
          const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
          const dateStr = time.toLocaleDateString();
          tr.insertCell().textContent = `${dateStr} ${timeStr}`;
          
          // Text preview column
          const preview = pred.text_input.length > 30 
            ? pred.text_input.substring(0, 30) + '…' 
            : pred.text_input;
          tr.insertCell().textContent = preview;
          
          // Label column
          const label = pred.label_classified;
          tr.insertCell().textContent = LABEL_ENGLISH[label] || label;
          
          // Accuracy column
          const accuracyCell = tr.insertCell();
          accuracyCell.textContent =
            pred.accuracy !== null && pred.accuracy !== undefined
              ? `${pred.accuracy.toFixed(2)} %`
              : 'N/A';
          
          // Feedback column
          const feedbackCell = tr.insertCell();
          if (pred.feedback === true) {
            feedbackCell.innerHTML = '👍 Good';
            feedbackCell.style.color = '#10b981';
            feedbackCell.style.fontWeight = 'bold';
          } else if (pred.feedback === false) {
            feedbackCell.innerHTML = '👎 Bad';
            feedbackCell.style.color = '#ef4444';
            feedbackCell.style.fontWeight = 'bold';
          } else {
            feedbackCell.innerHTML = `
              <button class="small-feedback-btn" onclick="giveFeedback(${pred.id}, true)">👍</button>
              <button class="small-feedback-btn" onclick="giveFeedback(${pred.id}, false)">👎</button>
            `;
          }
        });
      
      document.getElementById('history-table').style.display = 'table';
    }

  } catch (error) {
    console.error('History load error:', error);
    noHistory.textContent = '❌ Error loading history. Is the backend running?';
    noHistory.style.display = 'block';
    noHistory.style.color = '#ef4444';
  } finally {
    loader.style.display = 'none';
  }
}

// Global function for feedback buttons in history table
window.giveFeedback = async function(predictionId, feedbackValue) {
  try {
    const response = await fetch(`${API_BASE_URL}/predictions/${predictionId}/feedback`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ feedback: feedbackValue })
    });

    if (!response.ok) {
      const err = await response.text();
      throw new Error(`HTTP ${response.status}: ${err}`);
    }

    loadHistory();
    
    const feedbackText = feedbackValue ? '👍 liked' : '👎 disliked';
    alert(`✅ Feedback ${feedbackText} submitted!`);
    
  } catch (error) {
    console.error(error);
    alert(`❌ Feedback failed: ${error.message}`);
  }
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Khmer Text Classifier initialized');
  console.log(`📡 Environment: ${CONFIG.ENVIRONMENT}`);
  console.log(`🔗 API Base URL: ${CONFIG.API_BASE_URL}`);
  
  // Load prediction history
  loadHistory();

  // Check API health & show status
  fetch(`${API_BASE_URL}/health`)
    .then(r => r.json())
    .then(data => {
      if (data.status === 'healthy') {
        const el = document.getElementById('api-status');
        if (el) {
          el.textContent = '✅ API Connected';
          el.style.background = '#10b981';
          el.style.color = 'white';
          el.style.padding = '4px 8px';
          el.style.borderRadius = '4px';
          el.style.fontSize = '12px';
        }
        console.log('✅ Backend API is healthy');
        console.log('✅ Khmer word segmentation with khmernltk is enabled!');
        
        // Log model info
        if (data.model_loaded) {
          console.log('✅ ML Model is loaded and ready');
        }
      }
    })
    .catch(err => {
      console.warn('⚠️ API not reachable:', err);
      const el = document.getElementById('api-status');
      if (el) {
        el.textContent = '❌ API Unavailable';
        el.style.background = '#ef4444';
        el.style.color = 'white';
        el.style.padding = '4px 8px';
        el.style.borderRadius = '4px';
        el.style.fontSize = '12px';
      }
      
      // One-time warning (don't spam user on every page load)
      if (!sessionStorage.getItem('api-warning-shown')) {
        setTimeout(() => {
          alert(`⚠️ Cannot reach backend API\n\nAPI URL: ${API_BASE_URL}\nEnvironment: ${CONFIG.ENVIRONMENT}\n\nPlease check:\n✓ Backend container is running\n✓ Port mapping is correct\n✓ Nginx proxy is configured\n\nRun: docker-compose up -d`);
        }, 1000);
        sessionStorage.setItem('api-warning-shown', 'true');
      }
    });
});

// ==================== UTILITY FUNCTIONS ====================

/**
 * Format timestamp for display
 */
function formatTimestamp(timestamp) {
  const date = new Date(timestamp);
  return date.toLocaleString();
}

/**
 * Truncate text for preview
 */
function truncateText(text, maxLength = 30) {
  if (text.length <= maxLength) return text;
  return text.substring(0, maxLength) + '…';
}

console.log('📝 Script loaded successfully');