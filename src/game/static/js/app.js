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
const livesHeart = document.getElementById('lives-heart');
const livesCount = document.getElementById('lives-count');
const roundScoreEl = document.getElementById('round-score');
const totalScoreEl = document.getElementById('total-score');
const finalScoreEl = document.getElementById('final-score');
let timeRemainingEl = document.getElementById('time-remaining');
const toastContainer = document.getElementById('toast-container');
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
});

// Translations
const TRANSLATIONS = {
    'en': {
        startBtn: "Start Game",
        tutorialTitle: "Guess a word that has a similar meaning",
        tutorialImg: "/img/tutorial_analogy.png",
        placeholder: "Type a word close to one or several on the screen...",
        submitBtn: "Submit",
        contextHeader: "Current Context",
        mainTitle: "Word Context Game",
        gameTitle: "Word Context Game",
        lives: "Lives",
        time: "Time",
        score: "Score",
        quit: "Quit",
        gameOverTitle: "Game Over!",
        wonTitle: "You Won!",
        timeUpTitle: "Time's Up!",
        outOfLivesMsg: "You ran out of lives!",
        wonMsg: "You found all the words!",
        scoreMsg: "You scored {score} points!",
        finalScore: "Final Score",
        playAgain: "Play Again",
        shareScore: "Share Score 🏆",
        mainMenu: "Main Menu",
        sessionEnded: "Session Ended",
        summaryMsg: "Good effort! Here is how you did:",
        totalScore: "Total Score",
        wordsFound: "Words Found",
        backToMenu: "Back to Menu",
        shuffleCost: "Not enough points! Need 200.",
        shuffleSuccess: "Words shuffled! -200 pts",
        gameStarted: "Game Started! Good Luck!",
        hintToast: "Type words that are semantically similar to the displayed words!",
        shuffleTooltip: "Shuffle Words (Cost: 200)",
        hintTooltip: "Hint",
        featureTelegramOnly: "Feature only available in Telegram!",
        typeWordWarning: "Please type a word!",
        wordOnScreenWarning: "Word is already on screen!",
        invalidMoveWarning: "Invalid Move",
        submitError: "Error submitting word. Please try again.",
        startError: "Could not start game. Please try again.",
        selectLangWarning: "Please select a language first!",
        stopError: "Error stopping game session."
    },
    'de': {
        startBtn: "Spiel Starten",
        tutorialTitle: "Errate ein Wort, das eine ähnliche Bedeutung hat",
        tutorialImg: "/img/tutorial_analogy_de.png",
        placeholder: "Tippe ein Wort ein, das einem oder mehreren auf dem Schirm ähnelt...",
        submitBtn: "Senden",
        contextHeader: "Aktueller Kontext",
        mainTitle: "Word Context Game",
        gameTitle: "Word Context Game",
        lives: "Leben",
        time: "Zeit",
        score: "Punkte",
        quit: "Beenden",
        gameOverTitle: "Spiel vorbei!",
        wonTitle: "Gewonnen!",
        timeUpTitle: "Die Zeit ist um!",
        outOfLivesMsg: "Du hast keine Leben mehr!",
        wonMsg: "Du hast alle Wörter gefunden!",
        scoreMsg: "Du hast {score} Punkte erzielt!",
        finalScore: "Endstand",
        playAgain: "Nochmal spielen",
        shareScore: "Ergebnis teilen 🏆",
        mainMenu: "Hauptmenü",
        sessionEnded: "Sitzung beendet",
        summaryMsg: "Guter Versuch! Hier ist dein Ergebnis:",
        totalScore: "Gesamtpunktzahl",
        wordsFound: "Gefundene Wörter",
        backToMenu: "Zurück zum Menü",
        shuffleCost: "Nicht genug Punkte! Benötigt werden 200.",
        shuffleSuccess: "Wörter gemischt! -200 Pkt",
        gameStarted: "Spiel gestartet! Viel Erfolg!",
        hintToast: "Tippe Wörter ein, die den angezeigten Wörtern inhaltlich ähnlich sind!",
        shuffleTooltip: "Wörter mischen (Kosten: 200)",
        hintTooltip: "Hinweis",
        featureTelegramOnly: "Funktion nur in Telegram verfügbar!",
        typeWordWarning: "Bitte tippe ein Wort ein!",
        wordOnScreenWarning: "Wort ist bereits auf dem Bildschirm!",
        invalidMoveWarning: "Ungültiger Zug",
        submitError: "Fehler beim Senden des Wortes. Bitte versuche es erneut.",
        startError: "Spiel konnte nicht gestartet werden. Bitte versuche es erneut.",
        selectLangWarning: "Bitte wähle zuerst eine Sprache!",
        stopError: "Fehler beim Beenden der Spielsitzung."
    },
    'ru': {
        startBtn: "Начать игру",
        tutorialTitle: "Угадайте слово, которое имеет похожее значение",
        tutorialImg: "/img/tutorial_analogy_ru.png",
        placeholder: "Введите слово, близкое к одному или нескольким на экране...",
        submitBtn: "Отправить",
        contextHeader: "Текущий контекст",
        mainTitle: "Word Context Game",
        gameTitle: "Word Context Game",
        lives: "Жизни",
        time: "Время",
        score: "Очки",
        quit: "Выйти",
        gameOverTitle: "Игра окончена!",
        wonTitle: "Победа!",
        timeUpTitle: "Время вышло!",
        outOfLivesMsg: "Жизни закончились!",
        wonMsg: "Вы нашли все слова!",
        scoreMsg: "Вы набрали {score} очков!",
        finalScore: "Итоговый счет",
        playAgain: "Играть снова",
        shareScore: "Поделиться 🏆",
        mainMenu: "Главное меню",
        sessionEnded: "Сессия завершена",
        summaryMsg: "Хорошая попытка! Вот ваши результаты:",
        totalScore: "Общий счет",
        wordsFound: "Найденные слова",
        backToMenu: "Назад в меню",
        shuffleCost: "Недостаточно очков! Нужно 200.",
        shuffleSuccess: "Слова перемешаны! -200 очков",
        gameStarted: "Игра началась! Удачи!",
        hintToast: "Вводите слова, которые по смыслу похожи на отображаемые!",
        shuffleTooltip: "Перемешать слова (Цена: 200)",
        hintTooltip: "Подсказка",
        featureTelegramOnly: "Функция доступна только в Telegram!",
        typeWordWarning: "Пожалуйста, введите слово!",
        wordOnScreenWarning: "Слово уже на экране!",
        invalidMoveWarning: "Неверный ход",
        submitError: "Ошибка отправки слова. Попробуйте еще раз.",
        startError: "Не удалось начать игру. Попробуйте еще раз.",
        selectLangWarning: "Пожалуйста, выберите язык!",
        stopError: "Ошибка завершения сессии."
    }
};

function getText(key, lang) {
    const l = lang || 'en';
    return (TRANSLATIONS[l] && TRANSLATIONS[l][key]) || TRANSLATIONS['en'][key];
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

    updateStaticText(selectedLang);
}

function updateStaticText(lang) {
    // Main Screen
    startBtn.textContent = getText('startBtn', lang);

    // Tutorial
    updateTextContent('tutorial-title', getText('tutorialTitle', lang));
    const tutorialImg = document.getElementById('tutorial-img');
    if (tutorialImg) {
        tutorialImg.src = getText('tutorialImg', lang);
    }

    if (document.getElementById('main-title')) {
        document.getElementById('main-title').textContent = getText('mainTitle', lang);
    }

    // Game Area
    if (document.getElementById('game-title')) {
        document.getElementById('game-title').textContent = getText('gameTitle', lang);
    }
    if (contextHeader) contextHeader.textContent = getText('contextHeader', lang);

    // Labels
    updateTextContent('lives-label', getText('lives', lang));
    updateTextContent('time-label', getText('time', lang));
    updateTextContent('score-label', getText('score', lang));

    // buttons
    wordInput.placeholder = getText('placeholder', lang);
    submitBtn.textContent = getText('submitBtn', lang);
    quitBtn.textContent = getText('quit', lang);

    // Game Over / Summary Static
    updateTextContent('final-score-label', getText('finalScore', lang));
    updateTextContent('summary-score-label', getText('totalScore', lang));
    updateTextContent('words-found-label', getText('wordsFound', lang));
    updateTextContent('summary-title', getText('sessionEnded', lang));
    updateTextContent('summary-msg', getText('summaryMsg', lang));

    // Action Buttons
    restartBtn.textContent = getText('playAgain', lang);
    backToMenuBtn.textContent = getText('mainMenu', lang);
    summaryBackBtn.textContent = getText('backToMenu', lang);

    if (shareScoreBtnGameover) shareScoreBtnGameover.textContent = getText('shareScore', lang);
    if (shareScoreBtnSummary) shareScoreBtnSummary.textContent = getText('shareScore', lang);

    // Tooltips
    if (shuffleBtn) shuffleBtn.title = getText('shuffleTooltip', lang);
    if (hintBtn) hintBtn.title = getText('hintTooltip', lang);

    // Document Title
    document.title = getText('gameTitle', lang);
}

function updateTextContent(id, text) {
    const el = document.getElementById(id);
    if (el) el.textContent = text;
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
    langBtns.forEach(b => {
        b.style.border = 'none';
        b.style.opacity = '1';
    });
}

function showHint() {
    showToast(getText('hintToast', selectedLang), 'info');
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
            showToast(getText('shuffleCost', selectedLang), 'warning');
            return;
        }

        if (!response.ok) throw new Error('Failed to shuffle');

        const gameState = await response.json();
        updateUI(gameState);

        showToast(getText('shuffleSuccess', selectedLang), 'success');

    } catch (error) {
        console.error('Error shuffling words:', error);
        showToast('Error shuffling words.', 'error');
    }
}

async function startGame() {
    if (!selectedLang) {
        showToast(getText('selectLangWarning', selectedLang), 'warning');
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

        showToast(getText('gameStarted', selectedLang), 'info');
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
        showToast(getText('typeWordWarning', selectedLang), 'warning');
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
                showToast(getText('wordOnScreenWarning', selectedLang), 'warning');
            } else {
                showToast(errData.detail || getText('invalidMoveWarning', selectedLang), 'warning');
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
        showToast(getText('submitError', selectedLang), 'warning');
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
}

function handleGameOver(state) {
    stopTimer();
    gameArea.classList.add('hidden');
    gameOverScreen.classList.remove('hidden');
    finalScoreEl.textContent = state.total_score;

    const gameOverTitle = gameOverScreen.querySelector('h2');
    const gameOverMsg = gameOverScreen.querySelector('p');

    if (state.lives <= 0) {
        if (gameOverTitle) gameOverTitle.textContent = getText('gameOverTitle', selectedLang);
        if (gameOverMsg) gameOverMsg.textContent = getText('outOfLivesMsg', selectedLang);
    } else if (state.time_remaining !== undefined && state.time_remaining <= 0) {
        if (gameOverTitle) gameOverTitle.textContent = getText('timeUpTitle', selectedLang);
        if (gameOverMsg) gameOverMsg.textContent = getText('scoreMsg', selectedLang).replace('{score}', state.total_score);
    } else {
        if (gameOverTitle) gameOverTitle.textContent = getText('wonTitle', selectedLang);
        if (gameOverMsg) gameOverMsg.textContent = getText('wonMsg', selectedLang);
    }
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
        const msg = getText('featureTelegramOnly', selectedLang);
        showToast(msg, "warning");
        alert(msg);
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
