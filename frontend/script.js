const toggle = document.getElementById('dark-toggle');
const body = document.body;

toggle.innerHTML = '🌙'; // Start in dark mode

toggle.addEventListener('click', () => {
  body.classList.toggle('light');
  toggle.innerHTML = body.classList.contains('light') ? '☀️' : '🌙';
});

// ==================== CONFIGURATION ====================
const MAX_WORDS = 512;
const API_BASE_URL = 'http://127.0.0.1:8000/api/v1'; // Your backend API
const textarea = document.getElementById('single-text');
const wordCount = document.getElementById('word-count');

// CORRECT LABEL MAPPING from your model:
// Based on: ["economic", "entertainment", "life", "politic", "sport", "technology"]
const LABEL_MAPPING = {
  'LABEL_0': 'សេដ្ឋកិច្ច / Economic',
  'LABEL_1': 'កម្សាន្ត / Entertainment', 
  'LABEL_2': 'ជីវិត / Life',
  'LABEL_3': 'នយោបាយ / Politic',
  'LABEL_4': 'កីឡា / Sport',
  'LABEL_5': 'បច្ចេកវិទ្យា / Technology'
};

// Also create English-only mapping for display
const LABEL_ENGLISH = {
  'LABEL_0': 'Economic',
  'LABEL_1': 'Entertainment',
  'LABEL_2': 'Life',
  'LABEL_3': 'Politic',
  'LABEL_4': 'Sport',
  'LABEL_5': 'Technology'
};

// ==================== UTILITY FUNCTIONS ====================
function updateWordCount() {
  const words = textarea.value.trim().split(/\s+/).filter(w => w.length > 0);
  const count = words.length;
  wordCount.textContent = `${count} / ${MAX_WORDS} words`;

  if (count > MAX_WORDS) {
    wordCount.classList.add('word-limit-warning');
    textarea.value = words.slice(0, MAX_WORDS).join(' ');
    updateWordCount();
    alert(`Text automatically limited to ${MAX_WORDS} words.`);
  } else {
    wordCount.classList.remove('word-limit-warning');
  }
}

textarea.addEventListener('input', updateWordCount);
updateWordCount();

// ==================== PREDICTION FUNCTION ====================
document.getElementById('predict-single').addEventListener('click', async () => {
  const text = textarea.value.trim();
  if (!text) return alert('Please enter some text');

  // Show loader
  document.getElementById('loader-single').style.display = 'block';
  document.getElementById('single-result').style.display = 'none';

  try {
    // Make API call to backend
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        text_input: text,
        feedback: null  // No initial feedback
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();
    
    // Display result with correct label
    const label = result.label_classified;
    document.getElementById('pred-label').textContent = 
      `${LABEL_MAPPING[label] || label} (${LABEL_ENGLISH[label] || label})`;
    
    // Store prediction ID for feedback
    document.getElementById('single-result').dataset.predictionId = result.id;
    
    // Show result section
    document.getElementById('single-result').style.display = 'block';
    
    // Reset feedback UI
    document.getElementById('like-btn').classList.remove('liked');
    document.getElementById('dislike-btn').classList.remove('disliked');
    document.getElementById('feedback-status').textContent = 'No feedback given yet';
    
    // Show all possible categories in a table
    const table = document.getElementById('prob-table');
    table.innerHTML = `
      <tr><th>Category</th><th>Khmer</th><th>English</th><th>Status</th></tr>
      ${Object.entries(LABEL_MAPPING).map(([key, khmerLabel]) => `
        <tr ${key === label ? 'style="font-weight: bold; background: #f0fdf4;"' : ''}>
          <td>${key}</td>
          <td>${khmerLabel.split(' / ')[0]}</td>
          <td>${khmerLabel.split(' / ')[1]}</td>
          <td>${key === label ? '✅ Predicted' : ''}</td>
        </tr>
      `).join('')}
    `;

  } catch (error) {
    console.error('Prediction error:', error);
    alert(`Error: ${error.message}\n\nMake sure the backend is running at ${API_BASE_URL}`);
  } finally {
    // Hide loader
    document.getElementById('loader-single').style.display = 'none';
    
    // Load updated history
    loadHistory();
  }
});

// ==================== FEEDBACK FUNCTION ====================
async function sendFeedback(feedbackValue) {
  const predictionId = document.getElementById('single-result').dataset.predictionId;
  if (!predictionId) {
    alert('No prediction to give feedback on. Make a prediction first.');
    return;
  }

  try {
    // Send feedback with correct format (as JSON object with feedback field)
    const response = await fetch(`${API_BASE_URL}/predictions/${predictionId}/feedback`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ 
        feedback: feedbackValue  // This matches FeedbackRequest schema
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `HTTP ${response.status}`);
    }

    const result = await response.json();
    console.log('Feedback success:', result);
    
    // Update UI based on feedback
    if (feedbackValue) {
      document.getElementById('like-btn').classList.add('liked');
      document.getElementById('dislike-btn').classList.remove('disliked');
      document.getElementById('feedback-status').textContent = 'Thank you! You liked this prediction 👍';
    } else {
      document.getElementById('dislike-btn').classList.add('disliked');
      document.getElementById('like-btn').classList.remove('liked');
      document.getElementById('feedback-status').textContent = 'Sorry! You disliked this prediction 👎';
    }

    // Reload history to show updated feedback
    loadHistory();

  } catch (error) {
    console.error('Feedback error:', error);
    alert(`Error sending feedback: ${error.message}`);
  }
}

// Add event listeners for feedback buttons
document.getElementById('like-btn').addEventListener('click', () => sendFeedback(true));
document.getElementById('dislike-btn').addEventListener('click', () => sendFeedback(false));

// ==================== HISTORY FUNCTION ====================
async function loadHistory() {
  const tbody = document.querySelector('#history-table tbody');
  const noHistory = document.getElementById('no-history');
  const loader = document.getElementById('loader-history');
  
  // Show loader
  loader.style.display = 'block';
  tbody.innerHTML = '';
  document.getElementById('history-table').style.display = 'none';
  noHistory.style.display = 'none';

  try {
    // Fetch predictions from API
    const response = await fetch(`${API_BASE_URL}/predictions`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    const predictions = await response.json();

    if (predictions.length === 0) {
      noHistory.style.display = 'block';
      document.getElementById('history-table').style.display = 'none';
    } else {
      // Sort by most recent first
      predictions.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
      
      // Display up to 10 most recent predictions
      predictions.slice(0, 10).forEach(pred => {
        const tr = tbody.insertRow();
        
        // Format time
        const time = new Date(pred.created_at);
        const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const dateStr = time.toLocaleDateString();
        tr.insertCell().textContent = `${dateStr} ${timeStr}`;
        
        // Text preview (first 30 chars)
        const textPreview = pred.text_input.length > 30 
          ? pred.text_input.substring(0, 30) + '...' 
          : pred.text_input;
        tr.insertCell().textContent = textPreview;
        
        // Predicted topic with correct label
        const label = pred.label_classified;
        tr.insertCell().textContent = LABEL_ENGLISH[label] || label;
        
        // Feedback
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
          feedbackCell.innerHTML = 
            '<button class="small-feedback-btn" onclick="giveFeedback(' + pred.id + ', true)">👍</button> ' +
            '<button class="small-feedback-btn" onclick="giveFeedback(' + pred.id + ', false)">👎</button>';
        }
      });
      
      document.getElementById('history-table').style.display = 'table';
      noHistory.style.display = 'none';
    }

  } catch (error) {
    console.error('Error loading history:', error);
    noHistory.textContent = 'Error loading history. Please try again.';
    noHistory.style.display = 'block';
  } finally {
    loader.style.display = 'none';
  }
}

// Function to give feedback from history table
window.giveFeedback = async function(predictionId, feedbackValue) {
  try {
    // Use the same format as sendFeedback
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
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    const result = await response.json();
    console.log('History feedback success:', result);
    
    // Reload history to show updated feedback
    loadHistory();
    
    // Show success message
    alert(`Feedback ${feedbackValue ? '👍 liked' : '👎 disliked'} submitted!`);
    
  } catch (error) {
    console.error('Feedback error:', error);
    alert(`Error submitting feedback: ${error.message}\n\nNote: Make sure backend is running with updated routes.`);
  }
};

// ==================== INITIALIZATION ====================
// Load history on page load
document.addEventListener('DOMContentLoaded', () => {
  loadHistory();
  
  // Check API connection and update status indicator
  fetch(`${API_BASE_URL}/health`)
    .then(response => response.json())
    .then(data => {
      if (data.status === 'healthy') {
        console.log('✅ Backend API is connected');
        // Update status indicator if it exists
        const statusEl = document.getElementById('api-status');
        if (statusEl) {
          statusEl.textContent = '✅ API Connected';
          statusEl.style.background = '#10b981';
          statusEl.style.color = 'white';
        }
      }
    })
    .catch(error => {
      console.warn('⚠️ Backend API not reachable:', error.message);
      
      // Update status indicator if it exists
      const statusEl = document.getElementById('api-status');
      if (statusEl) {
        statusEl.textContent = '❌ API Unavailable';
        statusEl.style.background = '#ef4444';
        statusEl.style.color = 'white';
      }
      
      // Only show alert on first load if API is critical
      if (!localStorage.getItem('api-warning-shown')) {
        alert(`⚠️ Backend API not reachable at ${API_BASE_URL}\n\nMake sure the backend is running with: docker-compose up -d`);
        localStorage.setItem('api-warning-shown', 'true');
      }
    });
  
  // Add API status indicator if not exists
  if (!document.getElementById('api-status')) {
    const statusDiv = document.createElement('div');
    statusDiv.id = 'api-status';
    statusDiv.style.position = 'fixed';
    statusDiv.style.top = '10px';
    statusDiv.style.right = '10px';
    statusDiv.style.padding = '5px 10px';
    statusDiv.style.borderRadius = '20px';
    statusDiv.style.fontSize = '12px';
    statusDiv.style.fontWeight = '600';
    statusDiv.style.zIndex = '1000';
    statusDiv.style.background = '#f3f4f6';
    statusDiv.textContent = 'Checking API...';
    document.body.appendChild(statusDiv);
  }
});

// --- Khmer word count + 512-limit enforcement via backend /segment ---

async function fetchKhmerWordCount(text, maxWords = 512) {
  try {
    const res = await fetch('/api/v1/segment', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ text_input: text, max_words: maxWords })
    });

    if (!res.ok) {
      console.error('Segment endpoint returned error', await res.text());
      return null;
    }

    // { khmer_word_count, khmer_words, truncated, cleaned_text }
    return await res.json();
  } catch (err) {
    console.error('Failed to fetch khmer word count', err);
    return null;
  }
}

// Simple debounce to avoid calling API on every keystroke instantly
function debounce(fn, delay = 250) {
  let t = null;
  return (...args) => {
    clearTimeout(t);
    t = setTimeout(() => fn(...args), delay);
  };
}

// Wire to your HTML elements
const txtEl = document.querySelector('#single-text');
const wordCountEl = document.querySelector('#word-count');

if (txtEl) {
  const onInput = debounce(async () => {
    const text = txtEl.value || '';
    const payload = await fetchKhmerWordCount(text, 512);

    if (!payload) return;

    // Update word count UI (Khmer word count based on backend)
    const count = payload.khmer_word_count ?? 0;
    if (wordCountEl) wordCountEl.textContent = `${count} / 512 words`;

    // If backend says truncated, enforce 512 words by replacing textarea value
    // Use cleaned_text (already cleaned) + khmer_words to rebuild the truncated text.
    if (payload.truncated) {
      // If your backend returns khmer_words list of clusters/words, join them.
      // This will keep only the first 512 Khmer words/clusters.
      if (Array.isArray(payload.khmer_words) && payload.khmer_words.length > 0) {
        const truncatedText = payload.khmer_words.join(' ');
        // Only set if different to prevent cursor jump too often
        if (txtEl.value !== truncatedText) {
          const prevPos = txtEl.selectionStart;
          txtEl.value = truncatedText;
          // Put cursor at end (simplest + stable)
          txtEl.selectionStart = txtEl.selectionEnd = Math.min(prevPos, txtEl.value.length);
        }
      } else if (typeof payload.cleaned_text === 'string' && payload.cleaned_text.length > 0) {
        // fallback: if khmer_words missing, at least replace with cleaned_text
        txtEl.value = payload.cleaned_text;
      }

      // Optional: add a visual warning style if you want
      txtEl.classList.add('limit-reached');
    } else {
      txtEl.classList.remove('limit-reached');
    }
  }, 250);

  txtEl.addEventListener('input', onInput);

  // Run once on load (in case textarea has prefilled text)
  onInput();
}
