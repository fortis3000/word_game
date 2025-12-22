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
const shareScoreBtnGameover = document.getElementById('share-score-btn-gameover');
const shareScoreBtnSummary = document.getElementById('share-score-btn-summary');

// Language Buttons
const langBtns = document.querySelectorAll('.lang-btn');

// UI Elements
const currentWordsList = document.getElementById('current-words-list');
const roundScoreEl = document.getElementById('round-score');
const totalScoreEl = document.getElementById('total-score');
const finalScoreEl = document.getElementById('final-score');
const toastContainer = document.getElementById('toast-container');
const instructionText = document.getElementById('instruction-text');

// Init
document.addEventListener('DOMContentLoaded', () => {
    console.log("App initialized");
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
        'en': "Explore semantic relationships. Find words closely related to the hidden context.",
        'de': "Erforsche semantische Zusammenhänge. Finde Wörter, die dem versteckten Kontext nahe stehen.",
        'ru': "Исследуйте смысловые связи. Найдите слова, близкие к скрытому контексту."
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
    const texts = {
        'en': "Explore semantic relationships. Find words closely related to the hidden context.",
        'de': "Erforsche semantische Zusammenhänge. Finde Wörter, die dem versteckten Kontext nahe stehen.",
        'ru': "Исследуйте смысловые связи. Найдите слова, близкие к скрытому контексту."
    };
    instructionText.textContent = texts[selectedLang] || texts['en'];

    // Update button text
    const btnTexts = {
        'en': "Start Game",
        'de': "Spiel Starten",
        'ru': "Начать игру"
    };
    startBtn.textContent = btnTexts[selectedLang] || btnTexts['en'];
}

function showMainMenu() {
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

    roundScoreEl.textContent = state.round_score;
    totalScoreEl.textContent = state.total_score;
}

function handleGameOver(state) {
    gameArea.classList.add('hidden');
    gameOverScreen.classList.remove('hidden');
    finalScoreEl.textContent = state.total_score;
}
