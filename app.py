# ===================================================================
# INSTRUCȚIUNI DE INSTALARE ȘI RULARE
# ===================================================================
# 
# 1. Creează structura de foldere:
#    mkdir -p smartest/generators smartest/utils smartest/static/css smartest/static/js smartest/templates
# 
# 2. Salvează fișierele în locațiile corespunzătoare
# 
# 3. Instalează Flask:
#    pip install flask flask-cors
# 
# 4. Rulează aplicația:
#    python app.py
# 
# 5. Deschide în browser:
#    http://localhost:5000
# 
# ===================================================================

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from generators.question_generator import QuestionGenerator
from utils.evaluator import QuestionEvaluator

app = Flask(__name__)
CORS(app)

# Inițializare componente
generator = QuestionGenerator()
evaluator = QuestionEvaluator()

# Baza de date în memorie
questions_db = []


# ============= RUTE API =============

@app.route('/')
def home():
    """Pagina principală"""
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generează întrebare"""
    data = request.json
    q_type = data.get('type', 'random')
    
    question = generator.generate_question(q_type)
    questions_db.append(question)
    
    return jsonify(question)


@app.route('/api/questions', methods=['GET'])
def api_questions():
    """Lista întrebări"""
    return jsonify(questions_db)


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """Evaluează răspuns"""
    data = request.json
    q_id = data.get('questionId')
    user_answer = data.get('userAnswer', '')
    
    question = next((q for q in questions_db if q['id'] == q_id), None)
    
    if not question:
        return jsonify({'error': 'Întrebare negăsită'}), 404
    
    result = evaluator.evaluate_answer(question, user_answer)
    
    return jsonify({
        'score': result['score'],
        'feedback': result['feedback'],
        'correctAnswer': question['correctAnswer'],
        'explanation': question['explanation']
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)