const API_BASE = '/api/game';
let sessionId = null;

const startScreen = document.getElementById('start-screen');
const gameArea = document.getElementById('game-area');
const gameOverScreen = document.getElementById('game-over-screen');
const summaryScreen = document.getElementById('summary-screen');
const summaryBackBtn = document.getElementById('summary-back-btn');
const summaryScoreEl = document.getElementById('summary-score');
const summaryWordsFoundEl = document.getElementById('summary-words-found');
const wordInput = document.getElementById('word-input');
const startBtn = document.getElementById('start-btn');
const quitBtn = document.getElementById('quit-btn');
const restartBtn = document.getElementById('restart-btn');
const backToMenuBtn = document.getElementById('back-to-menu-btn');
const submitBtn = document.getElementById('submit-btn');

// UI Elements
const currentWordsList = document.getElementById('current-words-list');
const roundScoreEl = document.getElementById('round-score');
const totalScoreEl = document.getElementById('total-score');
const finalScoreEl = document.getElementById('final-score');
const toastContainer = document.getElementById('toast-container');

startBtn.addEventListener('click', startGame);
restartBtn.addEventListener('click', startGame);
backToMenuBtn.addEventListener('click', showMainMenu);
summaryBackBtn.addEventListener('click', showMainMenu);
quitBtn.addEventListener('click', quitGame);
submitBtn.addEventListener('click', submitWord);

wordInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') {
        submitWord();
    }
});

async function startGame() {
    try {
        const response = await fetch(`${API_BASE}/start`, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to start game');

        const data = await response.json();
        sessionId = data.session_id;

        // Reset UI
        wordInput.value = '';

        updateUI(data.game_state);

        showGameArea();
        wordInput.focus();
        showToast('Game Started! Good Luck!', 'info');
    } catch (error) {
        console.error('Error starting game:', error);
        showToast('Could not start game. Please try again.', 'warning');
    }
}

async function quitGame() {
    if (!sessionId) {
        showMainMenu();
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/${sessionId}/stop`, { method: 'POST' });
        if (response.ok) {
            const stats = await response.json();
            showSummaryScreen(stats);
        } else {
            showMainMenu();
        }
    } catch (error) {
        console.warn('Error stopping game session:', error);
        showMainMenu();
    } finally {
        sessionId = null;
    }
}

function showSummaryScreen(stats) {
    gameArea.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
    startScreen.classList.add('hidden');
    summaryScreen.classList.remove('hidden');

    summaryScoreEl.textContent = stats.total_score;
    summaryWordsFoundEl.textContent = stats.words_found;
}

function showMainMenu() {
    gameArea.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
    summaryScreen.classList.add('hidden');
    startScreen.classList.remove('hidden');
}

function showGameArea() {
    startScreen.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
    summaryScreen.classList.add('hidden');
    gameArea.classList.remove('hidden');
}

async function submitWord() {
    const word = wordInput.value.trim();

    if (!word) {
        showToast('Please type a word!', 'warning');
        wordInput.focus();
        return;
    }

    if (!sessionId) return;

    try {
        const response = await fetch(`${API_BASE}/${sessionId}/play`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word })
        });

        if (response.status === 400) {
            const errData = await response.json();
            // Assuming the backend sends { detail: "..." }
            if (errData.detail && (errData.detail.includes("too similar") || errData.detail.includes("already on screen"))) {
                showToast('Word is already on screen!', 'warning');
            } else {
                showToast(errData.detail || 'Invalid Move', 'warning');
            }
            wordInput.value = '';
            wordInput.focus();
            return;
        }

        if (!response.ok) throw new Error('Failed to submit word');

        const gameState = await response.json();
        const removedCount = gameState.removed_words.length;

        updateUI(gameState);
        wordInput.value = '';
        wordInput.focus();

        // Feedback Messages
        if (removedCount === 0) {
            showToast('Good try, but no match.', 'info');
        } else if (removedCount === 1) {
            showToast('Great! You found one!', 'success');
        } else {
            showToast(`Amazing! Multi-hit combo: ${removedCount} words!`, 'success');
        }

        if (gameState.game_over) {
            handleGameOver(gameState);
        }

    } catch (error) {
        console.error('Error submitting word:', error);
        showToast('Error submitting word. Please try again.', 'warning');
    }
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = 'fadeOut 0.3s ease-out forwards';
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
}

function updateUI(state) {
    // Start State reset
    if (state.round_score === 0 && state.total_score === 0 && state.removed_words.length === 0) {
        currentWordsList.innerHTML = ''; // Clear for fresh start
    }

    // Current Words
    currentWordsList.innerHTML = '';
    state.current_words.forEach(word => {
        const li = document.createElement('li');
        li.textContent = word;
        li.className = 'word-item';

        // Highlight if it's a newly added word
        if (state.added_words && state.added_words.includes(word)) {
            li.classList.add('new-word');
        }

        currentWordsList.appendChild(li);
    });

    // Update Score
    roundScoreEl.textContent = state.round_score;
    totalScoreEl.textContent = state.total_score;
}

function handleGameOver(state) {
    gameArea.classList.add('hidden');
    gameOverScreen.classList.remove('hidden');
    finalScoreEl.textContent = state.total_score;
}
