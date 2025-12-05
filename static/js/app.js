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


/**
 * Afișează ecranul de răspuns (individual)
 */
async function showAnswer() {
  hideAll();
  document.getElementById("screen-answer").classList.remove("hidden");

  // Alege o întrebare aleatorie din cele salvate
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
    currentQuestion.id = q_id; // Păstrăm ID-ul pentru trimiterea răspunsului
    document.getElementById("answer-title").textContent = `Răspunde: ${currentQuestion.title}`;
    document.getElementById("answer-question").textContent = currentQuestion.question;
    document.getElementById("user-answer").value = ""; // Curățăm câmpul de răspuns
  } catch (error) {
    console.error("Eroare la încărcarea întrebării de răspuns:", error);
    showHome();
  }
}

/**
 * Trimiterea răspunsului (individual) pentru evaluare
 */
async function submitAnswer() {
  const user_answer = document.getElementById("user-answer").value.trim();
  if (!user_answer) {
    alert("Te rog, scrie un răspuns.");
    return;
  }

  try {
    const res = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question_id: currentQuestion.id,
        user_answer: user_answer,
      }),
    });

    const result = await res.json();
    displayEvaluation(result);
  } catch (error) {
    console.error("Eroare la evaluarea răspunsului:", error);
    alert("Eroare la evaluarea răspunsului!");
  }
}

function displayEvaluation(result) {
  hideAll();

  const scoreClass = getScoreClass(result.score);

  document.getElementById("eval-question-text").textContent =
    currentQuestion.question;

  // Afișează score-display pentru evaluări normale
  const scoreDisplay = document.getElementById("score-display");
  scoreDisplay.style.display = "block";
  scoreDisplay.innerHTML = `
        <div class="score-box ${scoreClass}">
            <div style="font-size: 3em; font-weight: bold;">${result.score}%</div>
            <div style="font-size: 1.5em;">${result.feedback}</div>
        </div>
    `;

  document.getElementById("eval-correct").textContent = result.correctAnswer;
  document.getElementById("eval-explanation").textContent = result.explanation;
  document.getElementById("screen-eval").classList.remove("hidden");
}

/**
 * Determină clasa CSS pentru scor
 * @param {number} score - Scorul obținut
 * @returns {string}
 */
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
    document.getElementById("screen-test-quiz").classList.remove("hidden");
    loadQuestion(currentTestIndex);
}

/**
 * Încarcă o întrebare specifică din test
 * @param {number} index - Indexul întrebării în `testQuestions`
 */
function loadQuestion(index) {
    // 1. Salvăm răspunsul curent înainte de a naviga (dacă nu e prima întrebare)
    if (currentTestIndex >= 0 && currentTestIndex < testQuestions.length) {
        saveCurrentAnswer();
    }

    currentTestIndex = index;
    const currentQ = testQuestions[index];

    // 2. Actualizăm UI
    document.getElementById("current-q-index").textContent = index + 1;
    document.getElementById("total-q-test").textContent = testQuestions.length;
    document.getElementById("test-quiz-title").textContent = `Test în derulare (${index + 1}/${testQuestions.length})`;

    document.getElementById("test-q-title").textContent = `[${currentQ.type.toUpperCase()}] ${currentQ.title}`;
    document.getElementById("test-q-text").textContent = currentQ.question;

    // 3. Reîncărcăm răspunsul salvat (dacă există)
    document.getElementById("test-user-answer").value = testAnswers[currentQ.id] || '';

    // 4. Gestionăm butoanele de navigare și finalizare
    document.getElementById("prev-q-btn").disabled = index === 0;
    // Butonul "Următoarea" se ascunde la ultima întrebare
    document.getElementById("next-q-btn").classList.toggle("hidden", index === testQuestions.length - 1);
    // Butonul "Finalizează Test" apare doar la ultima întrebare
    document.getElementById("finish-test-btn").classList.toggle("hidden", index !== testQuestions.length - 1);
}

/**
 * Salvează răspunsul din textarea în `testAnswers`
 */
function saveCurrentAnswer() {
    if (testQuestions.length === 0) return;

    const currentQ = testQuestions[currentTestIndex];
    const answerTextarea = document.getElementById("test-user-answer");

    // Salvăm răspunsul (trimming spațiile goale)
    testAnswers[currentQ.id] = answerTextarea.value.trim();
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