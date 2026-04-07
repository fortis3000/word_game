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
    infoBtn.addEventListener('click', showInfo);

    wordInput.addEventListener('input', () => {
        if (wordInput.value.trim().length > 0) {
            submitBtn.classList.add('visible');
        } else {
            submitBtn.classList.remove('visible');
        }
    });

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
        howToPlayBtn: "How to Play",
        howToPlayTitle: "How to Play",
        howToPlayIntro: "Welcome to the Word Similarity Game! Your goal is to clear the board by finding hidden connections between words.",
        howToPlayRulesHeader: "The Rules:",
        howToPlayRule1: "<strong>Match Words:</strong> Type a word or a short sentence that relates to one or more words currently on the screen. The closer the meaning, the better the match!",
        howToPlayRule2: "<strong>Score Points:</strong> You earn points for every successful match. Matching several words at once with a clever phrase gives you a big combo bonus!",
        howToPlayRule3: "<strong>Beat the Clock:</strong> Keep an eye on the timer. Every matched word adds +2 seconds to your clock! Clear as many words as you can before time runs out to secure a high score.",
        howToPlayRule4: "<strong>Use Shuffle 🔄:</strong> Stuck? Use the Shuffle button to rearrange the words and spot new associations.",
        howToPlayRule5: "<strong>Info ℹ️:</strong> Tap the Info button to review these rules again at any time during the game.",
        howToPlayOutro: "Ready to test your vocabulary and associative thinking? <strong>Play now and see how high you can score!</strong>",
        tutorialTitle: "Guess a word that has a similar meaning",
        tutorialImg: "/img/tutorial_analogy.png",
        placeholder: "Type a word close to one or several on the screen...",
        contextHeader: "Current Context",
        mainTitle: "Word Similarity Game",
        gameTitle: "Word Similarity Game",
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
        sessionEnded: "Good Effort!",
        totalScore: "Total Score",
        wordsFound: "Words Found",
        backToMenu: "Back to Menu",
        shuffleCost: "Not enough points! Need 200.",
        shuffleSuccess: "Words shuffled! -200 pts",
        gameStarted: "Game Started! Good Luck!",
        hintToast: "Type words that are semantically similar to the displayed words!",
        shuffleTooltip: "Shuffle Words (Cost: 200)",
        infoTooltip: "Info",
        featureTelegramOnly: "Available only in Telegram",
        typeWordWarning: "Please type a word!",
        wordOnScreenWarning: "Word is already on screen!",
        invalidMoveWarning: "Invalid Move",
        submitError: "Error submitting word. Please try again.",
        startError: "Could not start game. Please try again.",
        selectLangWarning: "Please select a language first!",
        stopError: "Error stopping game session.",
        countdownLabel: "Game starts in"
    },
    'de': {
        startBtn: "Spiel Starten",
        howToPlayBtn: "Spielanleitung",
        howToPlayTitle: "Spielanleitung",
        howToPlayIntro: "Willkommen bei Word Similarity Game! Dein Ziel ist es, das Spielfeld zu leeren, indem du versteckte Verbindungen zwischen Wörtern findest.",
        howToPlayRulesHeader: "Die Regeln:",
        howToPlayRule1: "<strong>Wörter kombinieren:</strong> Tippe ein Wort oder einen kurzen Satz ein, der sich auf eines oder mehrere Wörter auf dem Bildschirm bezieht. Je enger die Bedeutung, desto besser der Treffer!",
        howToPlayRule2: "<strong>Punkte sammeln:</strong> Du erhältst Punkte für jeden erfolgreichen Treffer. Wenn du mehrere Wörter gleichzeitig mit einem geschickten Begriff kombinierst, erhältst du einen großen Combo-Bonus!",
        howToPlayRule3: "<strong>Gegen die Zeit:</strong> Behalte den Timer im Auge. Jedes gefundene Wort fügt deiner Zeit +2 Sekunden hinzu! Leere so viele Wörter wie möglich, bevor die Zeit abläuft.",
        howToPlayRule4: "<strong>Mischen 🔄 benutzen:</strong> Kommst du nicht weiter? Nutze die Mischen-Taste, um die Wörter neu anzuordnen und neue Assoziationen zu entdecken.",
        howToPlayRule5: "<strong>Info ℹ️:</strong> Tippe auf die Info-Taste, um diese Regeln jederzeit während des Spiels erneut zu lesen.",
        howToPlayOutro: "Bereit, deinen Wortschatz und dein assoziatives Denken zu testen? <strong>Spiele jetzt und knacke den Highscore!</strong>",
        tutorialTitle: "Errate ein Wort, das eine ähnliche Bedeutung hat",
        tutorialImg: "/img/tutorial_analogy_de.png",
        placeholder: "Tippe ein Wort ein, das einem oder mehreren auf dem Schirm ähnelt...",
        contextHeader: "Aktueller Kontext",
        mainTitle: "Word Similarity Game",
        gameTitle: "Word Similarity Game",
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
        sessionEnded: "Guter Versuch",
        totalScore: "Gesamtpunktzahl",
        wordsFound: "Gefundene Wörter",
        backToMenu: "Zurück zum Menü",
        shuffleCost: "Nicht genug Punkte! Benötigt werden 200.",
        shuffleSuccess: "Wörter gemischt! -200 Pkt",
        gameStarted: "Spiel gestartet! Viel Erfolg!",
        hintToast: "Tippe Wörter ein, die den angezeigten Wörtern inhaltlich ähnlich sind!",
        shuffleTooltip: "Wörter mischen (Kosten: 200)",
        infoTooltip: "Info",
        featureTelegramOnly: "Nur in Telegram verfügbar",
        typeWordWarning: "Bitte tippe ein Wort ein!",
        wordOnScreenWarning: "Wort ist bereits auf dem Bildschirm!",
        invalidMoveWarning: "Ungültiger Zug",
        submitError: "Fehler beim Senden des Wortes. Bitte versuche es erneut.",
        startError: "Spiel konnte nicht gestartet werden. Bitte versuche es erneut.",
        selectLangWarning: "Bitte wähle zuerst eine Sprache!",
        stopError: "Fehler beim Beenden der Spielsitzung.",
        countdownLabel: "Spiel beginnt in"
    },
    'ru': {
        startBtn: "Начать игру",
        howToPlayBtn: "Как играть",
        howToPlayTitle: "Как играть",
        howToPlayIntro: "Добро пожаловать в Word Similarity Game! Ваша цель — очистить поле, находя скрытые связи между словами.",
        howToPlayRulesHeader: "Правила:",
        howToPlayRule1: "<strong>Ищите ассоциации:</strong> Введите слово или короткую фразу, которая относится к одному или нескольким словам на экране. Чем ближе смысл, тем лучше результат!",
        howToPlayRule2: "<strong>Набирайте очки:</strong> Вы получаете очки за каждое угаданное слово. Объединяя сразу несколько слов одной фразой, вы получите большой комбо-бонус!",
        howToPlayRule3: "<strong>Следите за временем:</strong> Каждое угаданное слово добавляет +2 секунды к вашему времени! Постарайтесь убрать как можно больше слов, пока время не вышло.",
        howToPlayRule4: "<strong>Перемешивание 🔄:</strong> Застряли? Используйте кнопку перемешивания, чтобы взглянуть на слова под другим углом и найти новые связи.",
        howToPlayRule5: "<strong>Инфо ℹ️:</strong> Нажмите на кнопку Инфо, чтобы просмотреть эти правила в любое время во время игры.",
        howToPlayOutro: "Готовы проверить свой словарный запас и ассоциативное мышление? <strong>Начните игру и узнайте, сколько очков вы сможете набрать!</strong>",
        tutorialTitle: "Угадайте слово, которое имеет похожее значение",
        tutorialImg: "/img/tutorial_analogy_ru.png",
        placeholder: "Введите слово, близкое к одному или нескольким на экране...",
        contextHeader: "Текущий контекст",
        mainTitle: "Word Similarity Game",
        gameTitle: "Word Similarity Game",
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
        sessionEnded: "Хорошая попытка",
        totalScore: "Общий счет",
        wordsFound: "Найденные слова",
        backToMenu: "Назад в меню",
        shuffleCost: "Недостаточно очков! Нужно 200.",
        shuffleSuccess: "Слова перемешаны! -200 очков",
        gameStarted: "Игра началась! Удачи!",
        hintToast: "Вводите слова, которые по смыслу похожи на отображаемые!",
        shuffleTooltip: "Перемешать слова (Цена: 200)",
        infoTooltip: "Инфо",
        featureTelegramOnly: "Доступно только в Telegram",
        typeWordWarning: "Пожалуйста, введите слово!",
        wordOnScreenWarning: "Слово уже на экране!",
        invalidMoveWarning: "Неверный ход",
        submitError: "Ошибка отправки слова. Попробуйте еще раз.",
        startError: "Не удалось начать игру. Попробуйте еще раз.",
        selectLangWarning: "Пожалуйста, выберите язык!",
        stopError: "Ошибка завершения сессии.",
        countdownLabel: "Игра начнется через"
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
    howToPlayBtn.classList.remove('hidden');

    updateStaticText(selectedLang);
}

function updateStaticText(lang) {
    // Main Screen
    startBtn.textContent = getText('startBtn', lang);
    howToPlayBtn.textContent = getText('howToPlayBtn', lang);

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

function showInfo() {
    openHowToPlay();
}

async function shuffleWords() {
    console.log("shuffleWords called. SessionId:", sessionId);
    if (!sessionId || shuffleBtn.disabled) {
        console.warn("Cannot shuffle: No session or disabled.");
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

async function startGame() {
    if (!selectedLang) {
        showToast(getText('selectLangWarning', selectedLang), 'warning');
        return;
    }

    countdownOverlay.classList.remove('hidden');
    let count = 3;
    countdownText.textContent = count;

    const countInterval = setInterval(async () => {
        count--;
        if (count > 0) {
            countdownText.textContent = count;
        } else {
            clearInterval(countInterval);
            countdownOverlay.classList.add('hidden');

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
                submitBtn.classList.remove('visible');

                updateUI(data.game_state);

                showGameArea();
                wordInput.focus();
            } catch (error) {
                console.error('Error starting game:', error);
                showToast(getText('startError', selectedLang), 'warning');
            }
        }
    }, 1000);
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

function showError() {
    wordInput.classList.add('input-error', 'shake');
    setTimeout(() => {
        wordInput.classList.remove('input-error', 'shake');
    }, 500);
}

async function submitWord() {
    const word = wordInput.value.trim();

    if (!word) {
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

    if (shuffleBtn) {
        shuffleBtn.disabled = state.total_score < 200;
    }
}

function handleGameOver(state) {
    stopTimer();
    gameArea.classList.add('hidden');
    gameOverScreen.classList.remove('hidden');
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
