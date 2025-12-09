// State Management
let questions = [];
let currentQuestion = null;

// New State for Test Mode
let testQuestions = []; // Array of questions for the current test
let currentTestIndex = 0; // Index of the question the user is viewing
let testAnswers = {}; // {question_id: user_answer_text, ...}
let testResults = []; // Array of evaluation results
let availableQuestionTypes = []; // List of types and counts


/**
 * Încarcă întrebările de pe server
 */
async function loadQuestions() {
  try {
    const res = await fetch("/api/questions");
    const data = await res.json();
    questions = data.questions;
    updateQuestionCount(data.total);
  } catch (error) {
    console.error("Eroare la încărcarea întrebărilor:", error);
  }
}

/**
 * Actualizează contorul de întrebări
 */
function updateQuestionCount(total) {
  document.getElementById("count").textContent = total;
  document.getElementById("total").textContent = total;
}

/**
 * Ascunde toate ecranele
 */
function hideAll() {
  document.querySelectorAll('[id^="screen-"]').forEach((el) => {
    el.classList.add("hidden");
  });
}

/**
 * Afișează ecranul Home
 */
function showHome() {
  hideAll();
  document.getElementById("screen-home").classList.remove("hidden");
  loadQuestions(); // Reîncarcă contorul de întrebări la revenirea acasă
}

/**
 * Afișează ecranul de generare
 */
function showGenerate() {
  hideAll();
  document.getElementById("screen-generate").classList.remove("hidden");
}

/**
 * Generează întrebări noi
 */
async function generateBatch() {
  const type = document.getElementById("question-type").value;
  const count = parseInt(document.getElementById("question-count").value);
  const statusEl = document.getElementById("generation-status");
  statusEl.innerHTML = "⏳ Se generează... Așteaptă câteva secunde.";
  statusEl.innerHTML = "<div style='color: #667eea;'><span class='loading'></span> Se generează... Așteaptă câteva secunde.</div>";

  try {
    const res = await fetch("/api/batch-generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, count }),
    });

    const data = await res.json();
    if (data.success) {
      statusEl.innerHTML = `<div style="color: green; font-weight: bold;">✅ Succes: ${data.message}</div>`;
    } else {
      statusEl.innerHTML = `<div style="color: red; font-weight: bold;">❌ Eroare: ${data.error}</div>`;
    }
  } catch (error) {
    console.error("Eroare la generarea batch:", error);
    statusEl.innerHTML = `<div style="color: red; font-weight: bold;">❌ Eroare de rețea/server.</div>`;
  }
  loadQuestions(); // Actualizează lista și contorul
}


/**
 * Afișează lista de întrebări
 */
function showQuestions() {
  hideAll();
  loadQuestions().then(() => {
    const listEl = document.getElementById("questions-list");
    listEl.innerHTML = "";

    if (questions.length === 0) {
      listEl.innerHTML = "<p style='text-align: center; color: #555;'>Nu există întrebări salvate.</p>";
      document.getElementById("screen-questions").classList.remove("hidden");
      return;
    }

    questions.forEach((q) => {
      const item = document.createElement("div");
      item.className = "question-list-item menu-card";
      item.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        <strong>[${q.type.toUpperCase()}]</strong> ${q.title}
                    </div>
                    <div>
                        <button class="btn btn-info btn-sm" onclick="showDetail(${q.id})">Vizualizează</button>
                    </div>
                </div>
            `;
      listEl.appendChild(item);
    });
    document.getElementById("screen-questions").classList.remove("hidden");
  });
}

/**
 * Afișează detaliile unei întrebări
 * @param {number} q_id - ID-ul întrebării
 */
async function showDetail(q_id) {
  hideAll();
  document.getElementById("screen-detail").classList.remove("hidden");

  try {
    const res = await fetch(`/api/question/${q_id}`);
    currentQuestion = await res.json();
    if (currentQuestion.error) {
      alert(currentQuestion.error);
      showQuestions();
      return;
    }
    document.getElementById("detail-title").textContent = `Vizualizare: ${currentQuestion.title}`;
    document.getElementById("detail-question").textContent = currentQuestion.question;
    document.getElementById("delete-q-btn").dataset.id = q_id; // Salvăm ID-ul pe butonul de ștergere
  } catch (error) {
    console.error("Eroare la încărcarea detaliilor întrebării:", error);
    showQuestions();
  }
}

/**
 * Confirmă și șterge o întrebare
 */
async function confirmDeleteQuestion() {
  const q_id = document.getElementById("delete-q-btn").dataset.id;
  if (!confirm(`Ești sigur că vrei să ștergi întrebarea cu ID-ul ${q_id}?`)) {
    return;
  }
  try {
    const res = await fetch(`/api/delete/${q_id}`, { method: "DELETE" });
    const data = await res.json();
    if (data.success) {
      alert(data.message);
      showQuestions();
    } else {
      alert(data.error);
    }
  } catch (error) {
    console.error("Eroare la ștergere:", error);
    alert("Eroare la ștergerea întrebării!");
  }
}

let currentNashGame = null;

// ATENȚIE: AICI ERA PRIMA FUNCTIE showAnswer - AM MUTAT-O ȘI AM PĂSTRAT DOAR UNA CORECTĂ

function showStandardAnswer() {
    document.getElementById("screen-answer").classList.remove("hidden");
    document.getElementById("answer-title").textContent = `Răspunde: ${currentQuestion.title}`;
    document.getElementById("answer-question").textContent = currentQuestion.question;
    document.getElementById("user-answer").value = "";
}

function showNashAnswer() {
    try {
        currentNashGame = JSON.parse(currentQuestion.game_data);
    } catch {
        showStandardAnswer();
        return;
    }
    
    document.getElementById("screen-nash-answer").classList.remove("hidden");
    document.getElementById("nash-answer-title").textContent = `Răspunde: ${currentQuestion.title}`;
    document.getElementById("nash-answer-question").textContent = currentQuestion.question;
    
    // Resetăm checkboxurile
    document.getElementById("nash-no-equilibrium").checked = false;
    
    // Generăm checkboxurile pentru celule
    generateNashCellCheckboxes(currentNashGame);
}

function generateNashCellCheckboxes(game) {
    const container = document.getElementById("nash-cells-container");
    const rows = game.rows;
    const cols = game.cols;
    
    let html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">';
    
    for (let i = 0; i < rows.length; i++) {
        for (let j = 0; j < cols.length; j++) {
            const cellId = `nash-cell-${i}-${j}`;
            const [p1, p2] = game.payoffs[i][j];
            
            html += `
                <label style="display: flex; align-items: center; padding: 12px; background: white; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; transition: all 0.2s;" 
                    onmouseover="this.style.background='#e8f5e9'; this.style.borderColor='#28a745';"
                    onmouseout="this.style.background='white'; this.style.borderColor='#ddd';">
                    <input type="checkbox" id="${cellId}" value="${i},${j}" 
                        style="width: 20px; height: 20px; margin-right: 12px; cursor: pointer;"
                        onchange="handleCellCheckbox()">
                    <div>
                        <div style="font-weight: bold; color: #667eea; margin-bottom: 5px;">(${rows[i]}, ${cols[j]})</div>
                        <div style="font-size: 0.9em; color: #666;">Plăți: (${p1}, ${p2})</div>
                    </div>
                </label>
            `;
        }
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function handleNoNashCheckbox() {
    const noNashChecked = document.getElementById("nash-no-equilibrium").checked;
    
    if (noNashChecked) {
        // Debifează toate celulele
        const cellCheckboxes = document.querySelectorAll('[id^="nash-cell-"]');
        cellCheckboxes.forEach(cb => cb.checked = false);
    }
}

function handleCellCheckbox() {
    // Dacă o celulă e bifată, debifează "Nu există"
    const cellCheckboxes = document.querySelectorAll('[id^="nash-cell-"]:checked');
    if (cellCheckboxes.length > 0) {
        document.getElementById("nash-no-equilibrium").checked = false;
    }
}

// app.js (Adăugați această funcție dacă lipsește sau este incompletă)

/**
 * Evaluează răspunsul utilizatorului pentru întrebările standard (non-Nash).
 */


// app.js (Funcția submitAnswer)

async function submitAnswer() {
    // 1. Verificăm dacă suntem pe o întrebare standard
    if (currentQuestion.type === 'nash') {
        alert("Te rog, folosește butonul de Evaluare specific pentru jocul Nash.");
        return;
    }

    // Extragem răspunsul din DOM.
    const user_answer_text = document.getElementById("user-answer").value.trim();
    
    if (user_answer_text === "") {
        alert("Te rog, completează un răspuns înainte de a evalua.");
        return;
    }

    try {
        const res = await fetch("/api/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question_id: currentQuestion.id,
                user_answer: user_answer_text, // Trimitem ca string simplu
            }),
        });

        const result = await res.json();
        
        // **NOU:** Adăugăm răspunsul utilizatorului în obiectul rezultat pentru a-l folosi la afișare
        result.user_answer = user_answer_text; 

        displayEvaluation(result);
    } catch (error) {
        console.error("Eroare la evaluarea răspunsului:", error);
        alert("Eroare la evaluarea răspunsului!");
    }
}

// app.js (Funcția submitNashAnswer)

async function submitNashAnswer() {
    // ... (Logica de construire a user_answer_data și user_answer_string)
    // ...
    
    // Construim răspunsul (JSON string)
    let user_answer_string = JSON.stringify(user_answer_data); // Aici e stringul JSON

    // ... (Validare)
    
    try {
        const res = await fetch("/api/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question_id: currentQuestion.id,
                user_answer: user_answer_string, // Trimitem stringul JSON
            }),
        });

        const result = await res.json();
        
        // **NOU:** Adăugăm răspunsul utilizatorului în obiectul rezultat pentru a-l folosi la afișare
        result.user_answer = user_answer_string; 

        displayEvaluation(result);
    } catch (error) {
        console.error("Eroare la evaluarea răspunsului:", error);
        alert("Eroare la evaluarea răspunsului!");
    }
}


/**
 * Afișează ecranul de răspuns (individual)
 * ACEASTA ESTE SINGURA FUNCTIE showAnswer() VALIDA, AM ELIMINAT DUPLICATUL
 */
// ==================== ACTUALIZARE COMPLETĂ app.js ====================
// ADAUGĂ/ÎNLOCUIEȘTE aceste funcții în app.js

// Variabile globale (verifică că există)

// ==================== FUNCȚII NASH ====================

async function showAnswer() {
    hideAll();
    
    if (questions.length === 0) {
        await loadQuestions();
    }

    if (questions.length === 0) {
        alert("Nu există întrebări salvate pentru a răspunde!");
        showHome();
        return;
    }

    const randomQMeta = questions[Math.floor(Math.random() * questions.length)];
    const q_id = randomQMeta.id;

    try {
        const res = await fetch(`/api/question/${q_id}`);
        currentQuestion = await res.json();
        currentQuestion.id = q_id;
        
        console.log("Întrebare încărcată:", currentQuestion.type); // DEBUG
        
        // IMPORTANT: Verificăm dacă e Nash
        if (currentQuestion.type === 'nash') {
            console.log("Redirectare către Nash answer"); // DEBUG
            showNashAnswer();
        } else {
            console.log("Redirectare către Standard answer"); // DEBUG
            showStandardAnswer();
        }
    } catch (error) {
        console.error("Eroare la încărcarea întrebării:", error);
        showHome();
    }
}

function showStandardAnswer() {
    document.getElementById("screen-answer").classList.remove("hidden");
    document.getElementById("answer-title").textContent = `Răspunde: ${currentQuestion.title}`;
    document.getElementById("answer-question").textContent = currentQuestion.question;
    document.getElementById("user-answer").value = "";
}

function showNashAnswer() {
    console.log("showNashAnswer() apelată"); // DEBUG
    
    // Verificăm că avem game_data
    if (!currentQuestion.game_data) {
        console.error("Lipsește game_data! Folosim interfața standard");
        showStandardAnswer();
        return;
    }
    
    try {
        if (typeof currentQuestion.game_data === "string") {
            currentNashGame = JSON.parse(currentQuestion.game_data);
        } else {
            currentNashGame = currentQuestion.game_data;
        }
    } catch (e) {
        console.error("Eroare parsare game_data:", e);
        showStandardAnswer();
        return;
    }

    
    // Afișăm screen-ul Nash
    const nashScreen = document.getElementById("screen-nash-answer");
    if (!nashScreen) {
        console.error("EROARE: screen-nash-answer nu există în HTML!");
        alert("Interfața Nash lipsește! Verifică că ai adăugat screen-nash-answer în index.html");
        showStandardAnswer();
        return;
    }
    
    nashScreen.classList.remove("hidden");
    
    // Setăm titlul
    document.getElementById("nash-answer-title").textContent = `Răspunde: ${currentQuestion.title}`;
    
    // Setăm întrebarea
    document.getElementById("nash-answer-question").textContent = currentQuestion.question;
    
    // Resetăm checkboxul "Nu există"
    const noNashCheckbox = document.getElementById("nash-no-equilibrium");
    if (noNashCheckbox) {
        noNashCheckbox.checked = false;
    }
    
    // Generăm checkboxurile pentru celule
    console.log("Generare checkboxuri celule..."); // DEBUG
    generateNashCellCheckboxes(currentNashGame);
    
    console.log("Nash UI afișat cu succes!"); // DEBUG
}

function generateNashCellCheckboxes(game) {
    const container = document.getElementById("nash-cells-container");
    
    if (!container) {
        console.error("EROARE: nash-cells-container nu există!");
        return;
    }
    
    const rows = game.rows;
    const cols = game.cols;
    
    console.log(`Generare ${rows.length}x${cols.length} checkboxuri`); // DEBUG
    
    let html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">';
    
    for (let i = 0; i < rows.length; i++) {
        for (let j = 0; j < cols.length; j++) {
            const cellId = `nash-cell-${i}-${j}`;
            const [p1, p2] = game.payoffs[i][j];
            
            html += `
                <label style="display: flex; align-items: center; padding: 12px; background: white; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; transition: all 0.2s;" 
                       onmouseover="this.style.background='#e8f5e9'; this.style.borderColor='#28a745';"
                       onmouseout="this.style.background='white'; this.style.borderColor='#ddd';">
                    <input type="checkbox" id="${cellId}" value="${i},${j}" 
                           style="width: 20px; height: 20px; margin-right: 12px; cursor: pointer;"
                           onchange="handleCellCheckbox()">
                    <div>
                        <div style="font-weight: bold; color: #667eea; margin-bottom: 5px;">(${rows[i]}, ${cols[j]})</div>
                        <div style="font-size: 0.9em; color: #666;">Plăți: (${p1}, ${p2})</div>
                    </div>
                </label>
            `;
        }
    }
    
    html += '</div>';
    container.innerHTML = html;
    
    console.log(`Generat ${rows.length * cols.length} checkboxuri`); // DEBUG
}

function handleNoNashCheckbox() {
    const noNashChecked = document.getElementById("nash-no-equilibrium").checked;
    
    console.log("handleNoNashCheckbox:", noNashChecked); // DEBUG
    
    if (noNashChecked) {
        // Debifează toate celulele
        const cellCheckboxes = document.querySelectorAll('[id^="nash-cell-"]');
        cellCheckboxes.forEach(cb => cb.checked = false);
        console.log("Debifate toate celulele"); // DEBUG
    }
}

function handleCellCheckbox() {
    // Dacă o celulă e bifată, debifează "Nu există"
    const cellCheckboxes = document.querySelectorAll('[id^="nash-cell-"]:checked');
    
    console.log("handleCellCheckbox: celule bifate =", cellCheckboxes.length); // DEBUG
    
    if (cellCheckboxes.length > 0) {
        document.getElementById("nash-no-equilibrium").checked = false;
        console.log("Debifat 'Nu există'"); // DEBUG
    }
}

async function submitNashAnswer() {
    console.log("submitNashAnswer() apelată"); // DEBUG
    
    const noNashChecked = document.getElementById("nash-no-equilibrium").checked;
    const cellCheckboxes = document.querySelectorAll('[id^="nash-cell-"]:checked');
    
    let selectedCells = [];
    cellCheckboxes.forEach(cb => {
        const [i, j] = cb.value.split(',');
        selectedCells.push({i: parseInt(i), j: parseInt(j)});
    });
    
    console.log("No Nash:", noNashChecked); // DEBUG
    console.log("Selected cells:", selectedCells); // DEBUG
    
    // Validare
    if (!noNashChecked && selectedCells.length === 0) {
        alert("Te rog, bifează 'Nu există' SAU selectează celulele Nash!");
        return;
    }
    
    // Construim răspunsul
    let user_answer_data = {
        no_nash: noNashChecked,
        selected_cells: selectedCells
    };
    
    console.log("User answer data:", user_answer_data); // DEBUG
    
    try {
        const res = await fetch("/api/evaluate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                question_id: currentQuestion.id,
                user_answer: JSON.stringify(user_answer_data),
            }),
        });

        const result = await res.json();
        console.log("Evaluation result:", result); // DEBUG
        displayEvaluation(result);
    } catch (error) {
        console.error("Eroare la evaluarea răspunsului:", error);
        alert("Eroare la evaluarea răspunsului!");
    }
}

// ==================== FUNCȚII EXISTENTE (păstrează-le) ====================

// displayEvaluation, getScoreClass, etc. rămân neschimbate
// Asigură-te că există funcția displayEvaluation

// app.js (în jurul liniei 345)

// app.js (Funcția displayEvaluation)

function displayEvaluation(result) {
    hideAll();

    // Răspunsul utilizatorului vine acum direct din `result.user_answer` (text simplu sau string JSON)
    const rawUserAnswer = result.user_answer || "";
    const isNash = currentQuestion.type === 'nash';
    let userAnswerDisplay = "";
    
    // 2. Formatăm Răspunsul Utilizatorului
    if (isNash) {
        // Logica de parsare și formatare pentru Nash
        try {
            const answerObj = JSON.parse(rawUserAnswer);
            const game = currentNashGame; // Avem nevoie de asta pentru a obține numele strategiilor
            
            if (answerObj.no_nash) {
                userAnswerDisplay = "Nu există echilibru Nash pur";
            } else if (answerObj.selected_cells && answerObj.selected_cells.length > 0) {
                let cells = [];
                answerObj.selected_cells.forEach(cell => {
                    const i = cell.i;
                    const j = cell.j;
                    if (game && game.rows && game.cols) {
                        cells.push(`(${game.rows[i]}, ${game.cols[j]}) Plăți: (${game.payoffs[i][j].join(', ')})`);
                    } else {
                        cells.push(`Celulă [${i},${j}]`);
                    }
                });
                userAnswerDisplay = `Echilibru Nash selectat:\n - ${cells.join('\n - ')}`;
            } else {
                userAnswerDisplay = "Niciun răspuns furnizat.";
            }
        } catch (e) {
            // Dacă parsarea eșuează, afișăm stringul brut
            userAnswerDisplay = `Format nevalid: ${rawUserAnswer}`;
        }
    } else {
        // Răspuns standard (text)
        userAnswerDisplay = rawUserAnswer.trim() || "Niciun răspuns furnizat.";
    }


    const scoreClass = getScoreClass(result.score);

    document.getElementById("eval-question-text").textContent = currentQuestion.question;

    const scoreDisplay = document.getElementById("score-display");
    scoreDisplay.style.display = "block";
    scoreDisplay.innerHTML = `
        <div class="score-box ${scoreClass}">
            <div style="font-size: 3em; font-weight: bold;">${result.score}%</div>
            <div style="font-size: 1.5em;">${result.feedback}</div>
        </div>
    `;

    // Afișăm Răspunsul Utilizatorului
    const userDisplayEl = document.getElementById("eval-user-answer-display");
    if (userDisplayEl) {
        userDisplayEl.textContent = userAnswerDisplay;
    }
    
    document.getElementById("eval-correct").textContent = result.correctAnswer;
    document.getElementById("eval-explanation").textContent = result.explanation;
    document.getElementById("screen-eval").classList.remove("hidden");
}

function getScoreClass(score) {
    if (score >= 90) return "score-excellent";
    if (score >= 70) return "score-good";
    if (score >= 50) return "score-fair";
    return "score-poor";
}

// ======================= LOGICĂ NOUĂ PENTRU TEST =======================

/**
 * Determină feedback-ul text pentru scorul mediu
 * @param {number} score - Scorul obținut
 * @returns {string}
 */
function getFeedbackForScore(score) {
    if (score >= 90) return "Excelent! Ai o înțelegere solidă a materiei.";
    if (score >= 70) return "Foarte bine. Ai identificat conceptele cheie.";
    if (score >= 50) return "Mulțumitor. Sunt necesare îmbunătățiri.";
    return "Nevoie de studiu suplimentar. Revizuiește conceptele de bază.";
}

/**
 * Afișează ecranul de configurare a testului
 */
async function showTestConfig() {
    hideAll();
    document.getElementById("screen-test-config").classList.remove("hidden");
    await loadQuestionTypes();
}

/**
 * Încarcă tipurile de întrebări și numărul lor din backend
 */
async function loadQuestionTypes() {
    try {
        const res = await fetch("/api/question-types");
        const data = await res.json();

        if (data.error) throw new Error(data.error);

        availableQuestionTypes = data; // [{type: 'n-queens', count: 12}, ...]

        const totalCount = availableQuestionTypes.reduce((acc, q) => acc + q.count, 0);
        document.getElementById("total-q-config").textContent = totalCount;

        const form = document.getElementById("test-config-form");
        form.innerHTML = ""; // Curățăm formularul

        if (availableQuestionTypes.length === 0) {
            form.innerHTML = "<p style='text-align: center; color: #555;'>Nu există întrebări salvate pentru a crea un test.</p>";
            return;
        }

        availableQuestionTypes.forEach(qType => {
            // Formatăm tipul (ex: 'n-queens' -> 'N-Queens')
            const displayType = qType.type.split('-').map(s => s.charAt(0).toUpperCase() + s.slice(1)).join(' ');

            const card = document.createElement('div');
            // Folosim form-group și menu-card
            card.className = 'form-group menu-card';
            card.style.textAlign = 'left';
            card.innerHTML = `
                <label for="type-${qType.type}"><strong>${displayType}</strong></label>
                <p style="font-size: 0.9em; margin-bottom: 5px;">Disponibile: ${qType.count}</p>
                <input type="number" id="type-${qType.type}" name="${qType.type}" min="0" max="${qType.count}" value="0" class="form-control">
            `;
            form.appendChild(card);
        });

    } catch (error) {
        console.error("Eroare la încărcarea tipurilor de întrebări:", error);
        alert("Eroare la încărcarea tipurilor de întrebări: " + error.message);
    }
}

/**
 * Generează și pornește testul
 */
async function generateTest() {
    const config = {};
    let totalRequested = 0;

    // Colectează configurația de la utilizator
    availableQuestionTypes.forEach(qType => {
        const input = document.getElementById(`type-${qType.type}`);
        if (input) {
            const count = parseInt(input.value);
            if (count > 0) {
                config[qType.type] = count;
                totalRequested += count;
            }
        }
    });

    if (totalRequested === 0) {
        alert("Te rog, alege cel puțin o întrebare pentru a începe testul!");
        return;
    }

    try {
        // Apel API pentru a genera întrebările
        const res = await fetch("/api/generate-test", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(config),
        });

        const data = await res.json();

        if (data.error) {
            throw new Error(data.error);
        }

        testQuestions = data;

        if (testQuestions.length === 0) {
            alert("Nu s-au putut genera întrebările. Asigură-te că baza de date are întrebări și încearcă din nou.");
            return;
        }

        // Inițializare stare test
        currentTestIndex = 0;
        testAnswers = {};

        // Trecem la ecranul de test
        showTestQuiz();

    } catch (error) {
        console.error("Eroare la generarea testului:", error);
        alert("Eroare la generarea testului! " + error.message);
    }
}

/**
 * Afișează ecranul de test și încarcă întrebarea curentă
 */
function showTestQuiz() {
    hideAll();
    const testScreen = document.getElementById("screen-test-quiz");
    testScreen.classList.remove("hidden");
    
    // Forțează browser-ul să re-rendereze înainte de a accesa elementele
    testScreen.offsetHeight; // Trigger reflow
    
    // Acum încarcă întrebarea
    loadQuestion(currentTestIndex);
}

// app.js

/**
 * Încarcă o întrebare specifică din test
 * @param {number} index - Indexul întrebării în `testQuestions`
 */
function loadQuestion(index) {
    // Validare: verificăm dacă indexul este valid
    if (index < 0 || index >= testQuestions.length) {
        console.error('Index invalid:', index);
        return;
    }

    // 1. Salvăm răspunsul curent înainte de a naviga (dacă nu e prima încărcare)
    if (currentTestIndex >= 0 && currentTestIndex < testQuestions.length && currentTestIndex !== index) {
        saveCurrentAnswer();
    }

    currentTestIndex = index;
    const currentQ = testQuestions[index];

    // 2. Actualizăm UI - verificăm dacă elementele există
    const currentIndexEl = document.getElementById("current-q-index");
    const totalTestEl = document.getElementById("total-q-test");
    const titleEl = document.getElementById("test-quiz-title");
    const qTitleEl = document.getElementById("test-q-title");
    const qTextEl = document.getElementById("test-q-text");
    // Eliminăm 'answerEl' care era un simplu textarea
    const answerContainerEl = document.getElementById("test-answer-container"); // Noul container
    
    // ... (verificări de eroare UI)

    currentIndexEl.textContent = index + 1;
    totalTestEl.textContent = testQuestions.length;
    titleEl.textContent = `Test în derulare (${index + 1}/${testQuestions.length})`;
    qTitleEl.textContent = `[${currentQ.type.toUpperCase()}] ${currentQ.title}`;
    qTextEl.textContent = currentQ.question;
    
    // =========================================================
    // NOU: Afișează interfața corectă (Textarea SAU Nash Checkbox)
    // =========================================================
    
    const savedAnswer = testAnswers[currentQ.id];
    
    if (currentQ.type === 'nash') {
        // Asignăm currentQuestion (deși este doar meta-data) pentru a folosi logica Nash existentă
        currentQuestion = currentQ; 
        
        // **IMPORTANT:** Trebuie să obținem datele complete ale întrebării pentru Nash
        // Deoarece api/generate-test returnează doar meta-data, trebuie să apelăm 
        // /api/question/<id> pentru a obține `game_data`.
        // Asta înseamnă că `loadQuestion` ar trebui să fie async și să facă un fetch.
        // Totuși, pentru a evita complexitatea, vom folosi o soluție mai simplă
        // și vom trece peste partea async, presupunând că întrebările Nash au
        // `game_data` populat (chiar dacă este doar un string placeholder) 
        // SAU vom presupune că backend-ul a returnat `game_data` în `api/generate-test` (deși nu e așa).
        
        // Deoarece funcția generateTest din backend returnează DOAR ID, TITLE, QUESTION, TYPE,
        // NU avem game_data aici. Trebuie să adăugăm o metodă să obținem acele date.

        // SOLUTIA MAI COMPLEXA, DAR CORECTA:
        fetchAndRenderNashQuestion(currentQ.id, savedAnswer);
        
    } else {
        // Întrebare standard: afișăm Textarea
        answerContainerEl.innerHTML = `<textarea id="test-user-answer" placeholder="Scrie răspunsul tău aici..." style="width: 100%;"></textarea>`;
        const answerEl = document.getElementById("test-user-answer");
        if (answerEl) {
            answerEl.value = savedAnswer || '';
        }
    }

    // 4. Gestionăm butoanele de navigare și finalizare
    const prevBtn = document.getElementById("prev-q-btn");
    const nextBtn = document.getElementById("next-q-btn");
    const finishBtn = document.getElementById("finish-test-btn");
    
    if (prevBtn) prevBtn.disabled = index === 0;
    if (nextBtn) nextBtn.classList.toggle("hidden", index === testQuestions.length - 1);
    if (finishBtn) finishBtn.classList.toggle("hidden", index !== testQuestions.length - 1);
}

// FUNCȚIE NOUĂ PENTRU NASH ÎN MODUL TEST
async function fetchAndRenderNashQuestion(q_id, savedAnswer) {
    const answerContainerEl = document.getElementById("test-answer-container");
    answerContainerEl.innerHTML = '<div style="text-align: center; color: #667eea;"><span class="loading"></span> Se încarcă datele jocului...</div>';

    try {
        // Preluăm datele complete (inclusiv game_data) de la ruta api_get_question
        const res = await fetch(`/api/question/${q_id}`);
        const fullQuestionData = await res.json();
        
        if (fullQuestionData.error || fullQuestionData.type !== 'nash') {
            throw new Error("Datele jocului Nash nu au putut fi încărcate.");
        }
        
        // Preluăm game_data și parsam
        let gameData;
        if (typeof fullQuestionData.game_data === "string") {
            gameData = JSON.parse(fullQuestionData.game_data);
        } else {
            gameData = fullQuestionData.game_data;
        }

        // Construim interfața Nash
        answerContainerEl.innerHTML = `
            <div style="background: #fff3cd; padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #ffc107;">
                <label style="display: flex; align-items: center; cursor: pointer; font-size: 1.1em;">
                    <input type="checkbox" id="test-nash-no-equilibrium" style="width: 25px; height: 25px; margin-right: 15px; cursor: pointer;" onchange="handleTestNoNashCheckbox()">
                    <strong>Nu există echilibru Nash pur</strong>
                </label>
            </div>
            <div style="background: #d4edda; padding: 20px; border-radius: 10px; margin: 20px 0; border: 2px solid #28a745;">
                <h3 style="margin-bottom: 15px; color: #155724;">SAU selectează celulele Nash:</h3>
                <div id="test-nash-cells-container">
                    </div>
            </div>
        `;
        
        // Generăm checkboxurile folosind o funcție adaptată
        generateTestNashCellCheckboxes(gameData, q_id);
        
        // Reîncărcăm răspunsul salvat (dacă există)
        if (savedAnswer) {
            const answerObj = JSON.parse(savedAnswer);
            if (answerObj.no_nash) {
                document.getElementById("test-nash-no-equilibrium").checked = true;
            } else if (answerObj.selected_cells && answerObj.selected_cells.length > 0) {
                answerObj.selected_cells.forEach(cell => {
                    const cellId = `test-nash-cell-${q_id}-${cell.i}-${cell.j}`;
                    const cb = document.getElementById(cellId);
                    if (cb) cb.checked = true;
                });
            }
        }

    } catch (error) {
        console.error("Eroare la încărcarea datelor Nash în test:", error);
        answerContainerEl.innerHTML = '<p style="color: red;">❌ Eroare la încărcarea interfeței Nash. Te rog, treci la următoarea întrebare.</p>';
    }
}


// FUNCȚII NOI DE GESTIONARE NASH PENTRU MODUL TEST (Adaptare a celor existente)
function generateTestNashCellCheckboxes(game, q_id) {
    const container = document.getElementById("test-nash-cells-container");
    const rows = game.rows;
    const cols = game.cols;
    
    let html = '<div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 15px;">';
    
    for (let i = 0; i < rows.length; i++) {
        for (let j = 0; j < cols.length; j++) {
            // ID-ul trebuie să includă q_id pentru unicitate
            const cellId = `test-nash-cell-${q_id}-${i}-${j}`; 
            const [p1, p2] = game.payoffs[i][j];
            
            html += `
                <label style="display: flex; align-items: center; padding: 12px; background: white; border: 2px solid #ddd; border-radius: 8px; cursor: pointer; transition: all 0.2s;" 
                    onmouseover="this.style.background='#e8f5e9'; this.style.borderColor='#28a745';"
                    onmouseout="this.style.background='white'; this.style.borderColor='#ddd';">
                    <input type="checkbox" id="${cellId}" value="${i},${j}" 
                        style="width: 20px; height: 20px; margin-right: 12px; cursor: pointer;"
                        onchange="handleTestCellCheckbox()">
                    <div>
                        <div style="font-weight: bold; color: #667eea; margin-bottom: 5px;">(${rows[i]}, ${cols[j]})</div>
                        <div style="font-size: 0.9em; color: #666;">Plăți: (${p1}, ${p2})</div>
                    </div>
                </label>
            `;
        }
    }
    
    html += '</div>';
    container.innerHTML = html;
}

function handleTestNoNashCheckbox() {
    const noNashChecked = document.getElementById("test-nash-no-equilibrium").checked;
    
    if (noNashChecked) {
        // Debifează toate celulele
        const cellCheckboxes = document.querySelectorAll('[id^="test-nash-cell-"]');
        cellCheckboxes.forEach(cb => cb.checked = false);
    }
}

function handleTestCellCheckbox() {
    // Dacă o celulă e bifată, debifează "Nu există"
    const cellCheckboxes = document.querySelectorAll('[id^="test-nash-cell-"]:checked');
    if (cellCheckboxes.length > 0) {
        document.getElementById("test-nash-no-equilibrium").checked = false;
    }
}

// (Continuă cu restul funcției loadQuestion)
// ...
// ...

/**
 * Salvează răspunsul din textarea în `testAnswers`
 */
// app.js

/**
 * Salvează răspunsul din interfața curentă în `testAnswers`
 */
function saveCurrentAnswer() {
    if (testQuestions.length === 0) return;

    const currentQ = testQuestions[currentTestIndex];
    let answerToSave = "";

    if (currentQ.type === 'nash') {
        // Logica de salvare pentru Nash
        const noNashChecked = document.getElementById("test-nash-no-equilibrium")?.checked || false;
        
        // Selectăm doar checkboxurile din containerul de test-nash-cells
        const cellCheckboxes = document.querySelectorAll('#test-answer-container [id^="test-nash-cell-"]:checked');
        
        let selectedCells = [];
        cellCheckboxes.forEach(cb => {
            const [i, j] = cb.value.split(',');
            selectedCells.push({i: parseInt(i), j: parseInt(j)});
        });
        
        const user_answer_data = {
            no_nash: noNashChecked,
            selected_cells: selectedCells
        };
        
        // Dacă nu e bifat nimic și nu e bifat "Nu există", salvăm string gol.
        if (!noNashChecked && selectedCells.length === 0) {
            answerToSave = "";
        } else {
            // Salvăm ca JSON string, conform așteptărilor backend-ului
            answerToSave = JSON.stringify(user_answer_data);
        }

    } else {
        // Logica de salvare pentru Textarea standard
        const answerTextarea = document.getElementById("test-user-answer");
        if (answerTextarea) {
            // Salvăm răspunsul (trimming spațiile goale)
            answerToSave = answerTextarea.value.trim();
        } else {
            // Dacă textarea nu există (poate e un Nash care nu s-a încărcat corect)
            answerToSave = "";
        }
    }

    testAnswers[currentQ.id] = answerToSave;
}
/**
 * Navighează la întrebarea anterioară/următoare
 * @param {number} direction - -1 pentru înapoi, 1 pentru înainte
 */
function navigateTest(direction) {
    let newIndex = currentTestIndex + direction;

    if (newIndex >= 0 && newIndex < testQuestions.length) {
        loadQuestion(newIndex);
    }
}

/**
 * Finalizează testul și trimite răspunsurile pentru evaluare
 */
async function submitTest() {
    // 1. Salvăm răspunsul final
    saveCurrentAnswer();

    const answersPayload = [];

    // 2. Pregătim payload-ul pentru API (includem toate întrebările din test)
    testQuestions.forEach(q => {
        answersPayload.push({
            question_id: q.id,
            // Dacă răspunsul nu există în testAnswers (sau e gol), trimitem un string gol.
            user_answer: testAnswers[q.id] || ""
        });
    });

    if (answersPayload.length === 0) {
        alert("Testul este gol sau nu s-a putut pregăti pentru evaluare.");
        return;
    }

    try {
        // 3. Apel API pentru evaluare
        const res = await fetch("/api/evaluate-test", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(answersPayload),
        });

        const data = await res.json();

        if (data.error) {
            throw new Error(data.error);
        }

        testResults = data;

        displayTestResults(testResults);

    } catch (error) {
        console.error("Eroare la evaluarea testului:", error);
        alert("Eroare la evaluarea testului! " + error.message);
    }
}

/**
 * Afișează rezultatele complete ale testului
 * @param {Array} results - Lista de rezultate de evaluare
 */
function displayTestResults(results) {
    hideAll();

    const totalScore = results.reduce((sum, res) => sum + res.score, 0);
    const averageScore = results.length > 0 ? Math.round(totalScore / results.length) : 0;
    const scoreClass = getScoreClass(averageScore);

    // 1. Afișează scorul global
    const globalScoreEl = document.getElementById("test-global-score");
    globalScoreEl.className = `score-box ${scoreClass}`;
    globalScoreEl.innerHTML = `
        <h3>Scorul Mediu al Testului</h3>
        <div style="font-size: 4em; font-weight: bold;">${averageScore}%</div>
        <p style="font-size: 1.5em;">${getFeedbackForScore(averageScore)}</p>
        <p>Evaluare bazată pe ${results.length} întrebări.</p>
    `;

    // 2. Afișează lista detaliată
    const resultsListEl = document.getElementById("test-results-list");
    resultsListEl.innerHTML = ""; // Curățăm lista

    results.forEach((res, index) => {
        const itemClass = getScoreClass(res.score);
        const resultItem = document.createElement('div');
        resultItem.className = 'question-box';
        resultItem.style.marginBottom = '30px';

        // Formatare specială pentru răspunsul utilizatorului gol
        const userAnswerDisplay = res.user_answer ? res.user_answer : 'Niciun răspuns furnizat.';
        const userAnswerStyle = res.user_answer ? 'font-style: italic; color: #555;' : 'font-style: italic; color: #dc3545;';

        resultItem.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 2px solid #ddd; padding-bottom: 15px; margin-bottom: 15px;">
                <h4 style="color: #667eea;">${index + 1}. (${res.type.toUpperCase()}) ${res.title}</h4>
                <div class="score-box ${itemClass}" style="padding: 10px 15px; margin: 0; display: inline-block; font-size: 1.2em; font-weight: bold;">${res.score}%</div>
            </div>

            <p><strong>Întrebarea:</strong> ${res.question}</p>
            <p style="margin-top: 10px;"><strong>Răspunsul tău:</strong>
                <span style="${userAnswerStyle}">${userAnswerDisplay}</span>
            </p>

            <div style="background: #e7f3ff; padding: 15px; border-radius: 8px; margin-top: 15px; border: 1px solid #cce5ff;">
                <strong>Răspuns corect:</strong> <div style="margin-top: 5px; font-weight: 500;">${res.correct_answer}</div>
            </div>
            <div style="background: #f3e5f5; padding: 15px; border-radius: 8px; margin-top: 10px; border: 1px solid #e2d1e7;">
                <strong>Explicație:</strong> <div style="margin-top: 5px; font-weight: 500;">${res.explanation}</div>
            </div>
            <p style="margin-top: 15px; font-weight: bold;">Feedback Evaluator: ${res.feedback}</p>
        `;
        resultsListEl.appendChild(resultItem);
    });

    document.getElementById("screen-test-results").classList.remove("hidden");
}

/**
 * Declanșează descărcarea PDF-ului cu toate întrebările
 */
async function downloadPDF() {
    if (questions.length === 0) {
        alert("Nu există întrebări salvate pentru a genera un PDF!");
        return;
    }

    try {
        // Găsim butonul și îl dezactivăm temporar
        const btnDownload = document.querySelector('#screen-questions .btn-info');
        const originalText = btnDownload.textContent;
        btnDownload.textContent = '⏳ Generare PDF...';
        btnDownload.disabled = true;

        // Facem request către API
        const response = await fetch('/api/export-pdf');

        if (!response.ok) {
            throw new Error('Eroare la generarea PDF-ului');
        }

        // Obținem blob-ul PDF
        const blob = await response.blob();

        // Creăm un URL temporar pentru blob
        const url = window.URL.createObjectURL(blob);

        // Creăm un link temporar și simulăm click-ul
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'SmartTest_Questions.pdf';
        document.body.appendChild(a);
        a.click();

        // Curățăm
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        // Restaurăm butonul
        btnDownload.textContent = originalText;
        btnDownload.disabled = false;

        alert("PDF-ul a fost descărcat cu succes!");

    } catch (error) {
        console.error('Eroare la descărcarea PDF:', error);
        alert('Eroare la descărcarea PDF-ului: ' + error.message);

        // Restaurăm butonul în caz de eroare
        const btnDownload = document.querySelector('#screen-questions .btn-info');
        if (btnDownload) {
            btnDownload.textContent = '⬇️ Descarcă PDF';
            btnDownload.disabled = false;
        }
    }
}

/**
 * Confirmă și șterge toate întrebările
 */
async function confirmClearAll() {
    if (!confirm("ATENȚIE! Ești sigur că vrei să ștergi TOATE întrebările? Această acțiune nu poate fi anulată!")) {
        return;
    }

    // A doua confirmare pentru siguranță
    if (!confirm("Confirmă din nou: Ștergi DEFINITIV toate întrebările?")) {
        return;
    }

    try {
        const res = await fetch("/api/clear-all", { method: "DELETE" });
        const data = await res.json();

        if (data.success) {
            alert(data.message);
            showHome();
        } else {
            alert("Eroare: " + data.error);
        }
    } catch (error) {
        console.error("Eroare la ștergerea tuturor întrebărilor:", error);
        alert("Eroare la ștergerea întrebărilor!");
    }
}


// Apel la încărcarea paginii
document.addEventListener("DOMContentLoaded", loadQuestions);