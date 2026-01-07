const toggle = document.getElementById('dark-toggle');
const body = document.body;

toggle.innerHTML = '🌙'; // Start in dark mode

toggle.addEventListener('click', () => {
  body.classList.toggle('light');
  toggle.innerHTML = body.classList.contains('light') ? '☀️' : '🌙';
});

const MAX_WORDS = 512;
const textarea = document.getElementById('single-text');
const wordCount = document.getElementById('word-count');
const LABELS = ['life', 'entertainment', 'politic', 'economic', 'technology', 'sport'];

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

document.getElementById('predict-single').addEventListener('click', async () => {
  if (!textarea.value.trim()) return alert('Please enter some text');

  document.getElementById('loader-single').style.display = 'block';
  document.getElementById('single-result').style.display = 'none';

  // Fake delay for demo
  await new Promise(r => setTimeout(r, 1500));

  // Mock data
  const mockProbs = [0.05, 0.08, 0.03, 0.78, 0.02, 0.04];
  const maxIdx = mockProbs.indexOf(Math.max(...mockProbs));
  document.getElementById('pred-label').textContent = `${LABELS[maxIdx]} (${(mockProbs[maxIdx] * 100).toFixed(1)}%)`;

  document.getElementById('single-result').style.display = 'block';
  document.getElementById('loader-single').style.display = 'none';

  // Reset feedback
  document.getElementById('like-btn').classList.remove('liked');
  document.getElementById('dislike-btn').classList.remove('disliked');
  document.getElementById('feedback-status').textContent = 'No feedback given yet';

  // Probability table
  const table = document.getElementById('prob-table');
  table.innerHTML = '<tr><th>Topic</th><th>Probability</th></tr>';
  mockProbs.forEach((p, i) => {
    const row = table.insertRow();
    row.insertCell(0).textContent = LABELS[i];
    row.insertCell(1).textContent = (p * 100).toFixed(1) + '%';
    if (i === maxIdx) row.style.fontWeight = 'bold';
  });

  loadHistory();
});

document.getElementById('like-btn').addEventListener('click', () => {
  document.getElementById('like-btn').classList.add('liked');
  document.getElementById('dislike-btn').classList.remove('disliked');
  document.getElementById('feedback-status').textContent = 'Thank you! You liked this prediction 👍';
});

document.getElementById('dislike-btn').addEventListener('click', () => {
  document.getElementById('dislike-btn').classList.add('disliked');
  document.getElementById('like-btn').classList.remove('liked');
  document.getElementById('feedback-status').textContent = 'Sorry! You disliked this prediction 👎';
});

function loadHistory() {
  const tbody = document.querySelector('#history-table tbody');
  tbody.innerHTML = '';
  const mock = [
    { time: 'Just now', text: 'ព័ត៌មានសេដ្ឋកិច្ច...', topic: 'economic', feedback: true },
    { time: '1 hour ago', text: 'កីឡាបាល់ទាត់...', topic: 'sport', feedback: false },
    { time: '2 hours ago', text: 'តារាភាពយន្ត...', topic: 'entertainment', feedback: null }
  ];
  mock.forEach(m => {
    const tr = tbody.insertRow();
    tr.insertCell().textContent = m.time;
    tr.insertCell().textContent = m.text;
    tr.insertCell().textContent = m.topic;
    const cell = tr.insertCell();
    if (m.feedback === true) cell.innerHTML = '👍 Good';
    else if (m.feedback === false) cell.innerHTML = '👎 Bad';
    else cell.textContent = '-';
  });
  document.getElementById('history-table').style.display = 'table';
  document.getElementById('loader-history').style.display = 'none';
}

loadHistory();