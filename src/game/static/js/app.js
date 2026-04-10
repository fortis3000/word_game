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
const startActions = document.getElementById('start-actions');
const howToPlayBtn = document.getElementById('how-to-play-btn');
const howToPlayModal = document.getElementById('how-to-play-modal');
const closeModalBtn = document.getElementById('close-modal-btn');
const quitBtn = document.getElementById('quit-btn');
const restartBtn = document.getElementById('restart-btn');
const backToMenuBtn = document.getElementById('back-to-menu-btn');
const submitBtn = document.getElementById('submit-btn');
const infoBtn = document.getElementById('info-btn');
const shuffleBtn = document.getElementById('shuffle-btn');
const shareScoreBtnGameover = document.getElementById('share-score-btn-gameover');
const shareScoreBtnSummary = document.getElementById('share-score-btn-summary');

const countdownOverlay = document.getElementById('countdown-overlay');
const countdownText = document.getElementById('countdown-text');

// Language Buttons
const langBtns = document.querySelectorAll('.lang-btn');

// UI Elements
const currentWordsList = document.getElementById('current-words-list');
const livesHeart = document.getElementById('lives-heart');
const livesCount = document.getElementById('lives-count');
const roundScoreEl = document.getElementById('round-score');
const totalScoreEl = document.getElementById('total-score');
const finalScoreEl = document.getElementById('final-score');
const timeRemainingEl = document.getElementById('time-remaining');
const toastContainer = document.getElementById('toast-container');

let timerInterval = null;
let currentTimeRemaining = 0;

// Init — iOS viewport management
// On iOS Safari, the keyboard does NOT resize the layout viewport.
// position:fixed elements are anchored to the layout viewport, NOT the visual viewport.
// iOS scrolls the layout viewport upward to show the focused input — this causes
// the fixed body to scroll out of view. Our defense:
// 1. Size body to visualViewport.height so content fits above keyboard
// 2. NEVER set body.top (it would push content down, not up)
// 3. Prevent page scrolling via touchmove and scroll listeners
// 4. Force window.scrollTo(0,0) constantly to fight iOS's native scroll
function setViewportHeight() {
    let vh = window.innerHeight;
    
    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.viewportStableHeight) {
        vh = window.Telegram.WebApp.viewportStableHeight;
    } else if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.viewportHeight) {
        vh = window.Telegram.WebApp.viewportHeight;
    } else if (window.visualViewport) {
        vh = window.visualViewport.height;
    }
    
    document.documentElement.style.setProperty('--app-height', `${vh}px`);
    
    // Aggressively reset scroll — iOS may have scrolled the page to show the input
    window.scrollTo(0, 0);
    document.documentElement.scrollTop = 0;
    document.body.scrollTop = 0;
}

document.addEventListener('DOMContentLoaded', () => {
    
    // Telegram WebApp specific initializations
    if (window.Telegram && window.Telegram.WebApp) {
        window.Telegram.WebApp.expand();
        window.Telegram.WebApp.onEvent('viewportChanged', setViewportHeight);
    }
    
    setViewportHeight();
    if (window.visualViewport) {
        window.visualViewport.addEventListener('resize', setViewportHeight);
        window.visualViewport.addEventListener('scroll', () => {
            // When iOS scrolls the visual viewport (keyboard opening), fight it
            window.scrollTo(0, 0);
        });
    }
    window.addEventListener('resize', setViewportHeight);
    
    // Block ALL page-level scrolling.
    // The words-container has overflow-y:auto for its own scrolling.
    // But the page itself should never scroll.
    document.addEventListener('touchmove', (e) => {
        // Allow scrolling inside .words-container, block everything else
        if (!e.target.closest('.words-container')) {
            e.preventDefault();
        }
    }, { passive: false });
    
    // Catch any scroll that sneaks through
    window.addEventListener('scroll', () => {
        window.scrollTo(0, 0);
    });

    // When input gets focus, iOS will try to scroll. Fight it after keyboard settles.
    wordInput.addEventListener('focusin', () => {
        setTimeout(() => {
            window.scrollTo(0, 0);
            document.documentElement.scrollTop = 0;
            document.body.scrollTop = 0;
        }, 100);
        // Second pass after keyboard animation completes
        setTimeout(() => {
            window.scrollTo(0, 0);
        }, 500);
    });

    langBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            selectLanguage(btn.dataset.lang, btn);
        });
    });

    startBtn.addEventListener('click', startGame);
    howToPlayBtn.addEventListener('click', openHowToPlay);
    closeModalBtn.addEventListener('click', closeHowToPlay);
    howToPlayModal.addEventListener('click', (e) => {
        if (e.target === howToPlayModal) {
            closeHowToPlay();
        }
    });
    restartBtn.addEventListener('click', startGame);
    backToMenuBtn.addEventListener('click', showMainMenu);
    summaryBackBtn.addEventListener('click', showMainMenu);
    quitBtn.addEventListener('click', quitGame);
    submitBtn.addEventListener('click', submitWord);
    infoBtn.addEventListener('click', openHowToPlay);

    wordInput.addEventListener('input', () => {
        if (isValidInput(wordInput.value)) {
            submitBtn.classList.add('visible');
        } else {
            submitBtn.classList.remove('visible');
        }
    });

    shuffleBtn.addEventListener('click', shuffleWords);

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

    if (urlLang && ['en', 'de', 'ru'].includes(urlLang)) {
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
        updateStaticText(selectedLang);

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

    // Desktop zoom hint (show once)
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    if (!isTouchDevice && window.innerWidth > 768 && !localStorage.getItem('zoomHintShown')) {
        setTimeout(() => {
            const isMac = navigator.platform.toUpperCase().indexOf('MAC') >= 0;
            const key = isMac ? '⌘' : 'Ctrl';
            showToast(`💡 Tip: Use ${key} + / ${key} − to scale the game to your liking`, 'info');
            localStorage.setItem('zoomHintShown', '1');
        }, 1500);
    }
});




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
    startActions.classList.remove('hidden');

    updateStaticText(selectedLang);
}

function updateStaticText(lang) {
    // Main Screen
    startBtn.textContent = getText('startBtn', lang);
    howToPlayBtn.title = getText('howToPlayBtn', lang);

    // Tutorial
    updateTextContent('tutorial-title', getText('tutorialTitle', lang));
    const tutorialImg = document.getElementById('tutorial-img');
    if (tutorialImg) {
        tutorialImg.src = getText('tutorialImg', lang);
    }

    if (document.getElementById('main-title')) {
        document.getElementById('main-title').textContent = getText('mainTitle', lang);
    }

    // How to Play Modal
    updateTextContent('how-to-play-title', getText('howToPlayTitle', lang));
    updateTextContent('how-to-play-intro', getText('howToPlayIntro', lang));
    updateTextContent('how-to-play-rules-header', getText('howToPlayRulesHeader', lang));
    updateHTMLContent('how-to-play-rule1', getText('howToPlayRule1', lang));
    updateHTMLContent('how-to-play-rule2', getText('howToPlayRule2', lang));
    updateHTMLContent('how-to-play-rule3', getText('howToPlayRule3', lang));
    updateHTMLContent('how-to-play-rule4', getText('howToPlayRule4', lang));
    updateHTMLContent('how-to-play-rule5', getText('howToPlayRule5', lang));
    updateHTMLContent('how-to-play-outro', getText('howToPlayOutro', lang));

    // Game Area
    updateTextContent('game-title', getText('gameTitle', lang));

    // Labels
    updateTextContent('lives-label', getText('lives', lang));
    updateTextContent('time-label', getText('time', lang));
    updateTextContent('score-label', getText('score', lang));

    // buttons
    wordInput.placeholder = getText('placeholder', lang);

    // Game Over / Summary Static
    updateTextContent('final-score-label', getText('finalScore', lang));
    updateTextContent('summary-score-label', getText('totalScore', lang));
    updateTextContent('words-found-label', getText('wordsFound', lang));
    updateTextContent('summary-title', getText('sessionEnded', lang));

    // Action Buttons
    restartBtn.textContent = getText('playAgain', lang);
    backToMenuBtn.textContent = getText('mainMenu', lang);
    summaryBackBtn.textContent = getText('backToMenu', lang);

    if (shareScoreBtnGameover) shareScoreBtnGameover.textContent = getText('shareScore', lang);
    if (shareScoreBtnSummary) shareScoreBtnSummary.textContent = getText('shareScore', lang);

    // Tooltips
    if (shuffleBtn) shuffleBtn.title = getText('shuffleTooltip', lang);
    if (infoBtn) infoBtn.title = getText('infoTooltip', lang);

    // Document Title
    document.title = getText('gameTitle', lang);

    // Countdown
    updateTextContent('countdown-label', getText('countdownLabel', lang));
}

function updateTextContent(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
}

function updateHTMLContent(id, html) {
    const el = document.getElementById(id);
    if (el) el.innerHTML = html;
}

const ALL_SCREENS = [startScreen, gameArea, gameOverScreen, summaryScreen];

function showScreen(activeEl) {
    ALL_SCREENS.forEach(el => {
        el.classList.toggle('hidden', el !== activeEl);
    });
}

function showMainMenu() {
    stopTimer();
    showScreen(startScreen);

    selectedLang = null;
    startActions.classList.add('hidden');
    langBtns.forEach(b => {
        b.style.border = 'none';
        b.style.opacity = '1';
    });
}

async function openHowToPlay() {
    howToPlayModal.classList.remove('hidden');
    if (sessionId) {
        stopTimer(); // Pause client-side timer
        try {
            await fetch(`${API_BASE}/${sessionId}/pause`, { method: 'POST' });
        } catch (e) {
            console.warn('Could not pause game server-side', e);
        }
    }
}

async function closeHowToPlay() {
    howToPlayModal.classList.add('hidden');
    if (sessionId) {
        startTimer(); // Resume client-side timer
        try {
            await fetch(`${API_BASE}/${sessionId}/resume`, { method: 'POST' });
        } catch (e) {
            console.warn('Could not resume game server-side', e);
        }
    }
}



async function shuffleWords() {
    if (!sessionId || shuffleBtn.disabled) {
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
            return;
        }

        if (!response.ok) throw new Error('Failed to shuffle');

        const gameState = await response.json();
        updateUI(gameState);
    } catch (error) {
        console.error('Error shuffling words:', error);
    }
}

function runCountdown(seconds) {
    return new Promise(resolve => {
        countdownOverlay.classList.remove('hidden');
        let count = seconds;
        countdownText.textContent = count;

        const interval = setInterval(() => {
            count--;
            if (count > 0) {
                countdownText.textContent = count;
            } else {
                clearInterval(interval);
                countdownOverlay.classList.add('hidden');
                resolve();
            }
        }, 1000);
    });
}

async function startGame() {
    if (!selectedLang) {
        showToast(getText('selectLangWarning', selectedLang), 'warning');
        return;
    }

    await runCountdown(3);

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

        wordInput.value = '';
        submitBtn.classList.remove('visible');

        updateUI(data.game_state);
        showScreen(gameArea);
        wordInput.focus();
    } catch (error) {
        console.error('Error starting game:', error);
        showToast(getText('startError', selectedLang), 'warning');
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
        showToast(getText('stopError', selectedLang), 'error');
    } finally {
        sessionId = null;
    }
}

function showSummaryScreen(stats) {
    showScreen(summaryScreen);
    summaryScoreEl.textContent = stats.total_score;
    summaryWordsFoundEl.textContent = stats.words_found;
}

function showError() {
    wordInput.classList.add('input-error', 'shake');
    setTimeout(() => {
        wordInput.classList.remove('input-error', 'shake');
    }, 500);
}

async function submitWord() {
    const word = wordInput.value;

    if (!isValidInput(word)) {
        showError();
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
            showError();
            wordInput.value = '';
            submitBtn.classList.remove('visible');
            wordInput.focus();
            return;
        }

        if (!response.ok) throw new Error('Failed to submit word');

        const gameState = await response.json();
        const removedCount = gameState.removed_words.length;

        updateUI(gameState);
        wordInput.value = '';
        submitBtn.classList.remove('visible');
        wordInput.focus();

        // Feedback Messages
        if (removedCount === 0) {
            showError();
        }

        if (gameState.game_over) {
            handleGameOver(gameState);
        }

    } catch (error) {
        console.error('Error submitting word:', error);
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

    roundScoreEl.textContent = state.round_score > 0 ? `+${state.round_score}` : '';
    totalScoreEl.textContent = state.total_score;

    if (state.time_remaining !== undefined) {
        currentTimeRemaining = Math.floor(state.time_remaining);
        if (timeRemainingEl) timeRemainingEl.textContent = formatTime(currentTimeRemaining);
        startTimer();
    }

    if (livesHeart && livesCount) {
        const currentLives = state.lives !== undefined ? state.lives : 5;
        const totalLives = 5; // Assuming 5 is max lives
        const percentage = Math.max(0, (currentLives / totalLives) * 100);

        livesHeart.style.setProperty('--fill-percent', `${percentage}%`);
        livesCount.textContent = `x${currentLives}`;
    }

    if (shuffleBtn) {
        shuffleBtn.disabled = state.total_score < 200;
    }
}

function handleGameOver(state) {
    stopTimer();
    showScreen(gameOverScreen);
    finalScoreEl.textContent = state.total_score;

    const gameOverTitle = gameOverScreen.querySelector('h2');

    if (state.lives <= 0) {
        if (gameOverTitle) gameOverTitle.textContent = getText('outOfLivesMsg', selectedLang);
    } else if (state.time_remaining !== undefined && state.time_remaining <= 0) {
        if (gameOverTitle) gameOverTitle.textContent = getText('scoreMsg', selectedLang).replace('{score}', state.total_score);
    } else {
        if (gameOverTitle) gameOverTitle.textContent = getText('wonMsg', selectedLang);
    }
}

function shareScore(score) {
    const msg = getText('featureTelegramOnly', selectedLang) || 'Available only in Telegram';
    console.log("shareScore called with score:", score, "platform:", window.Telegram?.WebApp?.platform);

    if (window.Telegram && window.Telegram.WebApp && window.Telegram.WebApp.initData) {
        const platform = window.Telegram.WebApp.platform || 'unknown';
        const isWebPlatform = ['web', 'weba', 'webk'].includes(platform);

        // If it's a web platform, we already know it probably won't support switchInlineQuery reliably
        if (isWebPlatform) {
            console.log("Prevented switchInlineQuery on web platform:", platform);
            showToast(msg, 'warning');
            return;
        }

        // Check if isSupported exists (added in later versions)
        if (window.Telegram.WebApp.isSupported) {
            if (!window.Telegram.WebApp.isSupported('switchInlineQuery')) {
                console.log("switchInlineQuery not supported according to isSupported()");
                showToast(msg, 'warning');
                return;
            }
        }

        try {
            const params = new URLSearchParams(window.location.search);
            const seed = params.get('seed') || 'random';

            // Format: score <score> <seed>
            const query = `score ${score} ${seed}`;

            console.log("Calling switchInlineQuery with:", query);
            window.Telegram.WebApp.switchInlineQuery(query, ['users', 'groups', 'channels']);
        } catch (e) {
            // We catch EVERYTHING here to ensure no library error leaks to the user
            console.warn("Caught Telegram WebApp error during share:", e);
            showToast(msg, 'warning');
        }
    } else {
        console.log("No Telegram initData found, showing fallback message.");
        showToast(msg, "warning");
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

function isValidInput(text) {
    if (!text) return false;

    // Split by non-letters (works for English, Russian, German)
    const words = text.match(/\p{L}+/gu) || [];
    if (words.length === 0) return false;

    // Rule: At least one word must have length > 2 and unique letters >= 2
    let hasValidWord = false;
    for (const word of words) {
        if (word.length > 2) {
            const uniqueLetters = new Set(word.toLowerCase());
            if (uniqueLetters.size >= 2) {
                hasValidWord = true;
                break;
            }
        }
    }
    return hasValidWord;
}
