const API_BASE = '/api/game';
let sessionId = null;
let selectedLang = null;

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
const hintBtn = document.getElementById('hint-btn');
const shuffleBtn = document.getElementById('shuffle-btn');
const shareScoreBtnGameover = document.getElementById('share-score-btn-gameover');
const shareScoreBtnSummary = document.getElementById('share-score-btn-summary');

// Language Buttons
const langBtns = document.querySelectorAll('.lang-btn');

// UI Elements
const currentWordsList = document.getElementById('current-words-list');
const livesContainer = document.getElementById('lives-container');
const roundScoreEl = document.getElementById('round-score');
const totalScoreEl = document.getElementById('total-score');
const finalScoreEl = document.getElementById('final-score');
let timeRemainingEl = document.getElementById('time-remaining');
const toastContainer = document.getElementById('toast-container');
const instructionText = document.getElementById('instruction-text');
const contextHeader = document.getElementById('context-header');

let timerInterval = null;
let currentTimeRemaining = 0;

// Init
document.addEventListener('DOMContentLoaded', () => {
    console.log("App initialized");
    timeRemainingEl = document.getElementById('time-remaining');
    const langBtns = document.querySelectorAll('.lang-btn');
    console.log("Found lang buttons:", langBtns.length);

    langBtns.forEach(btn => {
        btn.addEventListener('click', (e) => {
            console.log("Clicked language:", btn.dataset.lang);
            selectLanguage(btn.dataset.lang, btn);
        });
    });

    startBtn.addEventListener('click', startGame);
    restartBtn.addEventListener('click', startGame);
    backToMenuBtn.addEventListener('click', showMainMenu);
    summaryBackBtn.addEventListener('click', showMainMenu);
    quitBtn.addEventListener('click', quitGame);
    submitBtn.addEventListener('click', submitWord);
    hintBtn.addEventListener('click', showHint);

    console.log("Checking for shuffle button:", shuffleBtn);
    if (shuffleBtn) {
        console.log("Adding click listener to shuffle button");
        shuffleBtn.addEventListener('click', shuffleWords);
    } else {
        console.error("Shuffle button not found in DOM!");
    }

    if (shareScoreBtnGameover) {
        shareScoreBtnGameover.addEventListener('click', () => shareScore(finalScoreEl.textContent));
    }
    if (shareScoreBtnSummary) {
        shareScoreBtnSummary.addEventListener('click', () => shareScore(summaryScoreEl.textContent));
    }

    // Check for auto-start parameters (seed + lang)
    const params = new URLSearchParams(window.location.search);
    const urlLang = params.get('lang');
    let autoStarted = false;

    console.log(`DEBUG Init: search=${window.location.search}, lang=${urlLang}`);

    if (urlLang && ['en', 'de', 'ru'].includes(urlLang)) {
        console.log("Auto-starting game with language:", urlLang);
        selectedLang = urlLang;

        langBtns.forEach(b => {
            b.style.border = 'none';
            b.style.opacity = '0.7';

            if (b.dataset.lang === urlLang) {
                b.style.border = '2px solid var(--accent)';
                b.style.opacity = '1';
            }
        });

        // Auto-click start logic
        instructionText.textContent = getInstructionText(selectedLang);
        startBtn.textContent = getStartBtnText(selectedLang);
        wordInput.placeholder = getInputPlaceholder(selectedLang);
        submitBtn.textContent = getSubmitBtnText(selectedLang);
        if (contextHeader) contextHeader.textContent = getContextHeader(selectedLang);

        // Immediate start
        startGame();
        autoStarted = true;
    }

    wordInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            submitWord();
        }
    });

    // Initial Load
    if (!autoStarted) {
        showMainMenu();
    }
});

// Helper to get text without selecting (for auto-start usage)
function getStartBtnText(lang) {
    const btnTexts = {
        'en': "Start Game",
        'de': "Spiel Starten",
        'ru': "Начать игру"
    };
    return btnTexts[lang] || btnTexts['en'];
}

function getInstructionText(lang) {
    const texts = {
        'en': "• Target a word with its synonym to get the maximum score.",
        'de': "• Nutze Synonyme zu den gezeigten Wörtern, um die maximale Punktzahl zu erreichen.",
        'ru': "• Используйте синонимы к словам, чтобы набрать максимум очков."
    };
    return texts[lang] || texts['en'];
}

function getInputPlaceholder(lang) {
    const texts = {
        'en': "Type a word close to one or several on the screen...",
        'de': "Tippe ein Wort ein, das einem oder mehreren auf dem Schirm ähnelt...",
        'ru': "Введите слово, близкое к одному или нескольким на экране..."
    };
    return texts[lang] || texts['en'];
}

function getSubmitBtnText(lang) {
    const texts = {
        'en': "Submit",
        'de': "Senden",
        'ru': "Отправить"
    };
    return texts[lang] || texts['en'];
}

function getContextHeader(lang) {
    const texts = {
        'en': "Current Context",
        'de': "Aktueller Kontext",
        'ru': "Текущий контекст"
    };
    return texts[lang] || texts['en'];
}

function shareScore(score) {
    if (window.Telegram && window.Telegram.WebApp) {
        try {
            const params = new URLSearchParams(window.location.search);
            const seed = params.get('seed') || 'random';

            // Format: score <score> <seed>
            const query = `score ${score} ${seed}`;

            console.log("Switching to inline query with:", query);

            // This opens the chat selection menu to share the result
            window.Telegram.WebApp.switchInlineQuery(query, ['users', 'groups', 'channels']);
        } catch (e) {
            console.error("switchInlineQuery failed:", e);
            showToast(`Error: ${e.message}`, 'error');
            alert(`Error: ${e.message}`);
        }
    } else {
        const msg = "Feature only available in Telegram!";
        showToast(msg, "warning");
        alert(msg);
    }
}

function selectLanguage(lang, btn) {
    if (!lang) return;
    selectedLang = lang;

    // Highlight button
    langBtns.forEach(b => {
        b.style.border = 'none';
        b.style.opacity = '0.7';
    });
    btn.style.border = '2px solid var(--accent)';
    btn.style.opacity = '1';

    // Show start button and instruction
    startBtn.classList.remove('hidden');
    instructionText.classList.remove('hidden');

    // Update instructions based on language
    instructionText.textContent = getInstructionText(selectedLang);
    wordInput.placeholder = getInputPlaceholder(selectedLang);
    submitBtn.textContent = getSubmitBtnText(selectedLang);
    if (contextHeader) contextHeader.textContent = getContextHeader(selectedLang);

    // Update button text
    startBtn.textContent = getStartBtnText(selectedLang);
}

function showMainMenu() {
    stopTimer();
    startScreen.classList.remove('hidden');
    gameArea.classList.add('hidden');
    gameOverScreen.classList.add('hidden');
    summaryScreen.classList.add('hidden');

    // Reset selection state mostly for UI cleanliness, but keeping selectedLang if they just paused is fine.
    // If we want to force re-selection:
    selectedLang = null;
    startBtn.classList.add('hidden');
    instructionText.classList.add('hidden');
    langBtns.forEach(b => {
        b.style.border = 'none';
        b.style.opacity = '1';
    });
}

function showHint() {
    const hints = {
        'en': "Type words that are semantically similar to the displayed words!",
        'de': "Tippe Wörter ein, die den angezeigten Wörtern inhaltlich ähnlich sind!",
        'ru': "Вводите слова, которые по смыслу похожи на отображаемые!"
    };
    showToast(hints[selectedLang] || hints['en'], 'info');
}

async function shuffleWords() {
    console.log("shuffleWords called. SessionId:", sessionId);
    if (!sessionId) {
        console.warn("No session ID, cannot shuffle.");
        return;
    }

    // Optional: Optimistic check (though API will also check)
    // const currentScore = parseInt(totalScoreEl.textContent || '0');
    // if (currentScore < 200) ...

    try {
        const response = await fetch(`${API_BASE}/${sessionId}/shuffle`, {
            method: 'POST'
        });

        if (response.status === 400) {
            // Not enough points
            const errMsgs = {
                'en': "Not enough points! Need 200.",
                'de': "Nicht genug Punkte! Benötigt werden 200.",
                'ru': "Недостаточно очков! Нужно 200."
            };
            showToast(errMsgs[selectedLang] || errMsgs['en'], 'warning');
            return;
        }

        if (!response.ok) throw new Error('Failed to shuffle');

        const gameState = await response.json();
        updateUI(gameState);

        const successMsgs = {
            'en': "Words shuffled! -200 pts",
            'de': "Wörter gemischt! -200 Pkt",
            'ru': "Слова перемешаны! -200 очков"
        };
        showToast(successMsgs[selectedLang] || successMsgs['en'], 'success');

    } catch (error) {
        console.error('Error shuffling words:', error);
        showToast('Error shuffling words.', 'error');
    }
}

async function startGame() {
    if (!selectedLang) {
        showToast('Please select a language first!', 'warning');
        return;
    }

    try {
        const params = new URLSearchParams(window.location.search);
        const seed = params.get('seed');

        let url = `${API_BASE}/start?lang=${selectedLang}`;
        if (seed) {
            url += `&seed=${seed}`;
        }

        const response = await fetch(url, { method: 'POST' });
        if (!response.ok) throw new Error('Failed to start game');

        const data = await response.json();
        sessionId = data.session_id;

        // Reset UI
        wordInput.value = '';

        updateUI(data.game_state);

        showGameArea();
        wordInput.focus();

        const startMsgs = {
            'en': 'Game Started! Good Luck!',
            'de': 'Spiel gestartet! Viel Erfolg!',
            'ru': 'Игра началась! Удачи!'
        };
        showToast(startMsgs[selectedLang] || startMsgs['en'], 'info');
    } catch (error) {
        console.error('Error starting game:', error);
        showToast('Could not start game. Please try again.', 'warning');
    }
}

async function quitGame() {
    stopTimer();
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
    if (state.round_score === 0 && state.total_score === 0 && state.removed_words.length === 0) {
        currentWordsList.innerHTML = '';
    }

    currentWordsList.innerHTML = '';
    state.current_words.forEach(word => {
        const li = document.createElement('li');
        li.textContent = word;
        li.className = 'word-item';

        if (state.added_words && state.added_words.includes(word)) {
            li.classList.add('new-word');
        }

        currentWordsList.appendChild(li);
    });

    roundScoreEl.textContent = state.round_score > 0 ? `+${state.round_score}` : state.round_score;
    totalScoreEl.textContent = state.total_score;
    
    if (state.time_remaining !== undefined) {
        currentTimeRemaining = Math.floor(state.time_remaining);
        if (timeRemainingEl) timeRemainingEl.textContent = formatTime(currentTimeRemaining);
        startTimer();
    }
    
    if (livesContainer) {
        livesContainer.innerHTML = '';
        const currentLives = state.lives !== undefined ? state.lives : 5;
        const totalLives = 5; // Assuming 5 is max lives
        
        for (let i = 0; i < totalLives; i++) {
            const heart = document.createElement('span');
            heart.className = `heart ${i < currentLives ? 'active' : ''}`;
            heart.textContent = '♥';
            livesContainer.appendChild(heart);
        }
    }
}

function handleGameOver(state) {
    stopTimer();
    gameArea.classList.add('hidden');
    gameOverScreen.classList.remove('hidden');
    finalScoreEl.textContent = state.total_score;
    
    const gameOverTitle = gameOverScreen.querySelector('h2');
    const gameOverMsg = gameOverScreen.querySelector('p');
    
    if (state.lives <= 0) {
        if (gameOverTitle) gameOverTitle.textContent = "Game Over!";
        if (gameOverMsg) gameOverMsg.textContent = "You ran out of lives!";
    } else if (state.time_remaining !== undefined && state.time_remaining <= 0) {
        if (gameOverTitle) gameOverTitle.textContent = "Time's Up!";
        if (gameOverMsg) gameOverMsg.textContent = `You scored ${state.total_score} points!`;
    } else {
        if (gameOverTitle) gameOverTitle.textContent = "You Won!";
        if (gameOverMsg) gameOverMsg.textContent = "You found all the words!";
    }
}

function formatTime(seconds) {
    const m = Math.floor(seconds / 60);
    const s = Math.floor(seconds % 60);
    return `${m}:${s < 10 ? '0' : ''}${s}`;
}

function startTimer() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
        currentTimeRemaining -= 1;
        if (currentTimeRemaining <= 0) {
            currentTimeRemaining = 0;
            clearInterval(timerInterval);
            if (timeRemainingEl) timeRemainingEl.textContent = "0:00";
        } else {
            if (timeRemainingEl) timeRemainingEl.textContent = formatTime(currentTimeRemaining);
        }
    }, 1000);
}

function stopTimer() {
    if (timerInterval) {
        clearInterval(timerInterval);
        timerInterval = null;
    }
}
