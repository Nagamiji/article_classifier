
// ==================== CONFIGURATION ====================
const CONFIG = {
  API_BASE_URL: '/api/v1',
  MAX_WORDS: 512,
};

console.log(`🌐 API Base URL: ${CONFIG.API_BASE_URL}`);

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

// ==================== DARK MODE TOGGLE ====================
const toggle = document.getElementById('dark-toggle');
const body = document.body;
if (toggle) {
  toggle.innerHTML = '🌙';
  toggle.addEventListener('click', () => {
    body.classList.toggle('light');
    toggle.innerHTML = body.classList.contains('light') ? '☀️' : '🌙';
  });
}

// ==================== WORD COUNTING ====================
function updateWordCount() {
  const textElement = document.getElementById('single-text');
  const wordCountEl = document.getElementById('word-count');
  
  if (!textElement || !wordCountEl) return;
  
  const text = textElement.value;
  const words = text.trim().split(/\s+/).filter(w => w.length > 0);
  const wordCount = words.length;
  
  wordCountEl.textContent = `${wordCount} / ${MAX_WORDS} words`;
  
  if (wordCount > MAX_WORDS) {
    wordCountEl.classList.add('word-limit-warning');
  } else {
    wordCountEl.classList.remove('word-limit-warning');
  }
}

// Initialize word count
const singleTextElement = document.getElementById('single-text');
if (singleTextElement) {
  singleTextElement.addEventListener('input', updateWordCount);
  updateWordCount();
}

// ==================== PREDICTION FUNCTION ====================
document.getElementById('predict-single').addEventListener('click', async () => {
  const textElement = document.getElementById('single-text');
  if (!textElement) return;
  
  const text = textElement.value.trim();
  if (!text) {
    alert('⚠️ Please enter some text');
    return;
  }

  const predictBtn = document.getElementById('predict-single');
  predictBtn.disabled = true;
  predictBtn.textContent = 'Predicting...';
  
  document.getElementById('loader-single').style.display = 'block';
  document.getElementById('single-result').style.display = 'none';

  try {
    console.log('📤 Sending prediction request...');
    const response = await fetch(`${API_BASE_URL}/predict`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ 
        text_input: text,
        feedback: null
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
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
    
    // Load updated history
    loadHistory();

  } catch (error) {
    console.error('❌ Prediction error:', error);
    alert(`❌ Prediction failed: ${error.message}`);
  } finally {
    document.getElementById('loader-single').style.display = 'none';
    predictBtn.disabled = false;
    predictBtn.textContent = 'Predict Topic';
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

  try {
    const response = await fetch(`${API_BASE_URL}/predictions/${predictionId}/feedback`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
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
    
  } catch (error) {
    console.error('❌ Feedback error:', error);
    alert(`❌ Feedback failed: ${error.message}`);
  }
}

// Setup feedback buttons
document.getElementById('like-btn').addEventListener('click', () => sendFeedback(true));
document.getElementById('dislike-btn').addEventListener('click', () => sendFeedback(false));

// ==================== HISTORY FUNCTION (SIMPLE - NO SORTING) ====================
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

  try {
    const response = await fetch(`${API_BASE_URL}/predictions?page=${currentPage}&limit=10`);
    
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
      // Display predictions in the order they come from the backend
      predictions.forEach(pred => {
        const tr = document.createElement('tr');
        
        // Time
        const time = new Date(pred.created_at);
        const timeStr = time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const dateStr = time.toLocaleDateString();
        
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
          feedbackHTML = '<span style="color: #10b981;">👍</span>';
        } else if (pred.feedback === false) {
          feedbackHTML = '<span style="color: #ef4444;">👎</span>';
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
          <td>${dateStr} ${timeStr}</td>
          <td title="${text}">${preview}</td>
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
  } finally {
    loader.style.display = 'none';
  }
}

// ==================== PAGINATION CONTROLS ====================
function updatePaginationControls() {
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');
  const pageInfo = document.getElementById('page-info');
  
  if (prevBtn) {
    prevBtn.disabled = currentPage <= 1;
  }
  
  if (nextBtn) {
    nextBtn.disabled = currentPage >= totalPages;
  }
  
  if (pageInfo) {
    pageInfo.textContent = `Page ${currentPage} of ${totalPages}`;
  }
}

// ==================== HISTORY TABLE FEEDBACK ====================
window.giveFeedback = async function(predictionId, feedbackValue) {
  try {
    const response = await fetch(`${API_BASE_URL}/predictions/${predictionId}/feedback`, {
      method: 'POST',
      headers: { 
        'Content-Type': 'application/json',
        'Accept': 'application/json'
      },
      body: JSON.stringify({ feedback: feedbackValue })
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    
    // Reload history
    loadHistory();
    
    // Show success message
    alert(`✅ Feedback ${feedbackValue ? 'liked' : 'disliked'} submitted!`);
    
  } catch (error) {
    console.error('❌ Feedback error:', error);
    alert(`❌ Feedback failed: ${error.message}`);
  }
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
  console.log('🚀 Khmer Text Classifier initialized');
  
  // Setup pagination listeners
  const prevBtn = document.getElementById('prev-page');
  const nextBtn = document.getElementById('next-page');
  const refreshBtn = document.getElementById('refresh-history');
  
  if (prevBtn) {
    prevBtn.addEventListener('click', () => {
      if (currentPage > 1) {
        currentPage--;
        loadHistory();
      }
    });
  }
  
  if (nextBtn) {
    nextBtn.addEventListener('click', () => {
      if (currentPage < totalPages) {
        currentPage++;
        loadHistory();
      }
    });
  }
  
  if (refreshBtn) {
    refreshBtn.addEventListener('click', () => {
      loadHistory();
      refreshBtn.textContent = '↻ Refreshing...';
      setTimeout(() => {
        refreshBtn.textContent = '↻ Refresh';
      }, 1000);
    });
  }
  
  // Initial load
  loadHistory();
});

console.log('📝 Script loaded successfully');