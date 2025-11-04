# ===================================================================
# INSTRUCȚIUNI DE INSTALARE ȘI RULARE
# ===================================================================
#
# 1. Creează structura de foldere:
#    mkdir -p generators utils static/css static/js templates
#
# 2. Instalează dependențele:
#    pip install flask flask-cors psycopg2-binary
#
# 3. Configurează PostgreSQL:
#    - Rulează schema.sql pentru a crea baza de date
#    - Actualizează DB_CONFIG mai jos cu datele tale
#
# 4. Salvează toate fișierele în locațiile corespunzătoare:
#    - app.py (acesta)
#    - generators/question_generator.py
#    - generators/__init__.py
#    - utils/evaluator.py
#    - utils/__init__.py
#    - utils/db_manager.py (NOU!)
#    - templates/index.html
#    - static/css/style.css
#    - static/js/app.js
#
# 5. Rulează aplicația:
#    python app.py
#
# 6. Deschide în browser:
#    http://localhost:5000
#
# ===================================================================

from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from generators.question_generator import QuestionGenerator
from utils.evaluator import QuestionEvaluator
from utils.question_db_manager import QuestionDBManager

app = Flask(__name__)
CORS(app)

# ============= CONFIGURARE BAZĂ DE DATE =============
DB_CONFIG = {
    'host': 'localhost',
    'database': 'Proiect_AI',
    'user': 'postgres',
    'password': '1234',
    'port': 5432
}

# ============= INIȚIALIZARE COMPONENTE =============
generator = QuestionGenerator()
evaluator = QuestionEvaluator()
db_manager = QuestionDBManager(DB_CONFIG)


# ============= RUTE API =============

@app.route('/')
def home():
    """Pagina principală"""
    return render_template('index.html')
@app.route('/api/batch-generate', methods=['POST'])
def api_batch_generate():
    """Generează un lot de întrebări și salvează în baza de date"""
    try:
        data = request.json
        q_type = data.get('type', 'random')
        # Get 'count' from the request, default to 1 if not provided
        count = data.get('count', 1)
        
        generated_questions = []

        for _ in range(count):
            # Generează întrebare
            question = generator.generate_question(q_type)

            # Salvează în baza de date
            db_id = db_manager.save_question(question)

            # Adaugă ID-ul din baza de date la răspuns
            question['dbId'] = db_id
            generated_questions.append(question)

        # Return the list of newly created questions
        return jsonify(generated_questions)

    except Exception as e:
        app.logger.error(f"Eroare la generare batch: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generează întrebare și salvează în baza de date"""
    try:
        data = request.json
        q_type = data.get('type', 'random')

        # Generează întrebare
        question = generator.generate_question(q_type)

        # Salvează în baza de date
        db_id = db_manager.save_question(question)

        # Adaugă ID-ul din baza de date la răspuns
        question['dbId'] = db_id

        return jsonify(question)

    except Exception as e:
        app.logger.error(f"Eroare la generare: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions', methods=['GET'])
def api_questions():
    """Lista întrebări din baza de date"""
    try:
        limit = request.args.get('limit', 50, type=int)
        questions = db_manager.get_all_questions(limit)

        # Convertește din formatul DB în formatul frontend
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                'id': q['question_id'],
                'dbId': q['id'],
                'type': q['type'],
                'title': q['title'],
                'question': q['question'],
                'correctAnswer': q['correct_answer'],
                'explanation': q['explanation'],
                'created_at': q['created_at'].isoformat() if q.get('created_at') else None
            })

        return jsonify(formatted_questions)

    except Exception as e:
        app.logger.error(f"Eroare la încărcarea întrebărilor: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/question/<int:db_id>', methods=['GET'])
def api_question_detail(db_id):
    """Detalii întrebare după ID bază de date"""
    try:
        question = db_manager.get_question_by_db_id(db_id)

        if not question:
            return jsonify({'error': 'Întrebare negăsită'}), 404

        # Formatează răspunsul
        formatted = {
            'id': question['question_id'],
            'dbId': question['id'],
            'type': question['type'],
            'title': question['title'],
            'question': question['question'],
            'correctAnswer': question['correct_answer'],
            'explanation': question['explanation']
        }

        return jsonify(formatted)

    except Exception as e:
        app.logger.error(f"Eroare la detalii întrebare: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate():
    """Evaluează răspuns"""
    try:
        data = request.json
        question_id = data.get('questionId')  # ID din generator
        db_id = data.get('dbId')  # ID din baza de date (opțional)
        user_answer = data.get('userAnswer', '')

        # Încearcă să găsească întrebarea
        question = None

        if db_id:
            # Caută după ID-ul din baza de date
            question = db_manager.get_question_by_db_id(db_id)

        if not question:
            return jsonify({'error': 'Întrebare negăsită'}), 404

        # Convertește în formatul așteptat de evaluator
        question_data = {
            'id': question['question_id'],
            'type': question['type'],
            'title': question['title'],
            'question': question['question'],
            'correctAnswer': question['correct_answer'],
            'explanation': question['explanation']
        }

        # Evaluează răspunsul
        result = evaluator.evaluate_answer(question_data, user_answer)

        return jsonify({
            'score': result['score'],
            'feedback': result['feedback'],
            'correctAnswer': question['correct_answer'],
            'explanation': question['explanation']
        })

    except Exception as e:
        app.logger.error(f"Eroare la evaluare: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/stats', methods=['GET'])
def api_stats():
    """Statistici întrebări din baza de date"""
    try:
        stats = db_manager.get_statistics()
        return jsonify(stats)

    except Exception as e:
        app.logger.error(f"Eroare la statistici: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions/type/<q_type>', methods=['GET'])
def api_questions_by_type(q_type):
    """Întrebări după tip"""
    try:
        limit = request.args.get('limit', 10, type=int)
        questions = db_manager.get_questions_by_type(q_type, limit)

        # Formatează răspunsul
        formatted_questions = []
        for q in questions:
            formatted_questions.append({
                'id': q['question_id'],
                'dbId': q['id'],
                'type': q['type'],
                'title': q['title'],
                'question': q['question'],
                'correctAnswer': q['correct_answer'],
                'explanation': q['explanation']
            })

        return jsonify(formatted_questions)

    except Exception as e:
        app.logger.error(f"Eroare la căutare după tip: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/test-connection', methods=['GET'])
def test_connection():
    """Testează conexiunea la baza de date"""
    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT version();")
                version = cursor.fetchone()[0]

                # Verifică și tabela questions
                cursor.execute("SELECT COUNT(*) FROM questions;")
                count = cursor.fetchone()[0]

                return jsonify({
                    'status': 'success',
                    'message': 'Conexiune reușită!',
                    'postgres_version': version,
                    'questions_count': count,
                    'database': DB_CONFIG['database']
                })

    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e),
            'database': DB_CONFIG['database']
        }), 500


# ============= ERROR HANDLERS =============

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint negăsit'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Eroare internă server'}), 500


# ============= MAIN =============

if __name__ == '__main__':
    print("=" * 70)
    print("🎓 SmarTest - Generator Întrebări AI cu PostgreSQL")
    print("=" * 70)
    print(f"📊 Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print(f"🌐 Server: http://localhost:5000")
    print(f"🔧 Test conexiune: http://localhost:5000/api/test-connection")
    print("=" * 70)
    print("\n⏳ Testare conexiune la baza de date...")

    try:
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM questions;")
                count = cursor.fetchone()[0]
                print(f"✅ Conexiune reușită! Întrebări în DB: {count}")
    except Exception as e:
        print(f"⚠️  Avertisment conexiune DB: {e}")
        print("    Aplicația va porni, dar verifică configurația bazei de date!")

    print("\n🚀 Pornire server Flask...\n")
    app.run(debug=True, port=5000)