
// State Management
let questions = [];
let currentQuestion = null;

/**
 * Încarcă întrebările de pe server
 */
async function loadQuestions() {
  try {
    const res = await fetch("/api/questions");
    questions = await res.json();
    updateQuestionCount();
  } catch (error) {
    console.error("Eroare la încărcarea întrebărilor:", error);
  }
}

/**
 * Actualizează contorul de întrebări
 */
function updateQuestionCount() {
  document.getElementById("count").textContent = questions.length;
  document.getElementById("total").textContent = questions.length;
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
}

/**
 * Afișează ecranul de generare
 */
function showGenerate() {
  hideAll();
  document.getElementById("screen-generate").classList.remove("hidden");
}

/**
 * Afișează lista de întrebări
 */
function showQuestions() {
  hideAll();
  loadQuestions();
  displayQuestions();
  document.getElementById("screen-questions").classList.remove("hidden");
}

/**
 * Afișează ecranul de răspuns
 */
function showAnswer() {
  if (questions.length === 0) {
    alert("Nu există întrebări! Generează întâi.");
    return;
  }
  hideAll();

  // Pick a random question from the list
  const randomIndex = Math.floor(Math.random() * questions.length);
  currentQuestion = questions[randomIndex];

  document.getElementById("answer-title").textContent = currentQuestion.title;
  document.getElementById("answer-question").textContent =
    currentQuestion.question;
  document.getElementById("screen-answer").classList.remove("hidden");
}

/**
 * Generează o nouă întrebare (sau mai multe)
 * @param {string} type - Tipul întrebării
 */
async function generate(type) {
  // 1. Ask user for the number of questions
  const countInput = prompt("How many questions do you want to generate? (max 10)" , "1");
  const count = parseInt(countInput, 10);

  // 2. Stop if user cancels or enters an invalid number
  if (isNaN(count) || count <= 0) {
    return;
  }
    // 3. Limit to maximum 10 questions
  if (count > 10) {
    alert("Maximum 10 questions can be generated at once!");
    return;
  }

  try {
    if (count === 1) {
      // 3a. Handle single generation (original logic)
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: type }),
      });

      const question = await res.json();
      if (res.status !== 200 || question.error) {
        throw new Error(question.error || "Server error");
      }

      questions.push(question);
      currentQuestion = question;

      // View the single generated question
      viewQuestion(question);
    } else {
      // 3b. Handle batch generation (new logic)
      const res = await fetch("/api/batch-generate", {
        // Use the new endpoint
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ type: type, count: count }), // Send type and count
      });

      const generatedQuestions = await res.json();
      if (res.status !== 200 || generatedQuestions.error) {
        throw new Error(generatedQuestions.error || "Server error");
      }

      // 4. Add all new questions to the local state
      questions.push(...generatedQuestions);

      alert(`${count} questions of type '${type}' generated successfully!`);

      // Go to the questions list to see the new questions
      showQuestions();
    }
  } catch (error) {
    console.error("Eroare la generarea întrebării:", error);
    alert("Eroare la generarea întrebării: " + error.message);
  }
}

/**
 * Afișează o întrebare specifică
 * @param {Object} q - Obiectul întrebare
 */
function viewQuestion(q) {
  hideAll();
  document.getElementById("view-title").textContent = q.title;
  document.getElementById("view-question").textContent = q.question;
  currentQuestion = q;
  document.getElementById("screen-view").classList.remove("hidden");
}

/**
 * Afișează lista de întrebări
 */
function displayQuestions() {
  const list = document.getElementById("questions-list");

  if (questions.length === 0) {
    list.innerHTML =
      '<p style="text-align: center; color: #999; padding: 40px;">Nu există întrebări generate încă.</p>';
    return;
  }

  list.innerHTML = questions
    .map(
      (q) => `
        <div class="question-item" onclick='viewQuestion(${JSON.stringify(
          q
        ).replace(/'/g, "&#39;")})'>
            <strong>#${q.id} - ${q.title}</strong>
            <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                ${escapeHtml(q.question.substring(0, 100))}...
            </div>
        </div>
    `
    )
    .join("");
}

/**
 * Escape HTML pentru securitate
 * @param {string} text - Text de escape
 * @returns {string}
 */
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}

/**
 * Inițiază procesul de răspuns
 */
function startAnswer() {
  hideAll();
  document.getElementById("answer-title").textContent = currentQuestion.title;
  document.getElementById("answer-question").textContent =
    currentQuestion.question;
  document.getElementById("user-answer").value = "";
  document.getElementById("screen-answer").classList.remove("hidden");
}

/**
 * Afișează răspunsul corect direct
 */
function showCorrect() {
  hideAll();
  
  // Ascunde score-display complet
  document.getElementById("score-display").style.display = 'none';
  
  // Afișează răspunsul corect și explicația
  document.getElementById("eval-correct").textContent = currentQuestion.correctAnswer;
  document.getElementById("eval-explanation").textContent = currentQuestion.explanation;
  
  document.getElementById("screen-eval").classList.remove("hidden");
}

/**
 * Trimite răspunsul pentru evaluare
 */
async function submitAnswer() {
  const userAnswer = document.getElementById("user-answer").value;

  if (!userAnswer.trim()) {
    alert("Te rog scrie un răspuns!");
    return;
  }
  console.log("Submitting evaluation for dbId:", currentQuestion.dbId);
  try {
    const res = await fetch("/api/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        questionId: currentQuestion.id,
        dbId: currentQuestion.dbId,
        userAnswer: userAnswer,
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

  // Afișează score-display pentru evaluări normale
  const scoreDisplay = document.getElementById("score-display");
  scoreDisplay.style.display = 'block';
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

// Încarcă întrebările când pagina este gata
document.addEventListener("DOMContentLoaded", () => {
  loadQuestions();
  console.log("✅ SmarTest aplicație încărcată cu succes!");
});
