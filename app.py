from flask import Flask, jsonify, request, render_template
from flask_cors import CORS
from generators.question_generator import QuestionGenerator
from utils.evaluator import QuestionEvaluator
from utils.question_db_manager import QuestionDBManager
import random

app = Flask(__name__)
CORS(app)

# ============= CONFIGURARE =============
DB_CONFIG = {
    'host': 'localhost',
    'database': 'smartestDB',
    'user': 'postgres',
    'password': '12345',
    'port': 5433  # <--- Asigură-te că acesta e portul pe care rulează Postgres acum
}

generator = QuestionGenerator()
evaluator = QuestionEvaluator()
db_manager = QuestionDBManager(DB_CONFIG)

# ============= RUTE PRINCIPALE =============

@app.route('/')
def home():
    """Pagina principală"""
    return render_template('index.html')

@app.route('/api/batch-generate', methods=['POST'])
def api_batch_generate():
    """Generează întrebări unice alegând din lista celor disponibile"""
    try:
        data = request.json
        q_type = data.get('type', 'random')
        count = data.get('count', 1)
        
        # 1. Obține toate întrebările posibile (Universul)
        all_possible = generator.get_all_questions()
        
        # Filtrează după tip dacă e cerut
        if q_type != 'random':
            all_possible = [q for q in all_possible if q['type'] == q_type]

        # 2. Obține ce avem deja în baza de date
        existing_titles = db_manager.get_existing_titles()
        
        # 3. Calculează DISPONIBILE (Posibile - Existente)
        available_questions = [
            q for q in all_possible 
            if q['title'] not in existing_titles
        ]
        
        if not available_questions:
            return jsonify({'error': f'Nu mai există întrebări unice de tipul "{q_type}" de generat!'}), 400
            
        # 4. Alege aleatoriu din cele disponibile
        # Dacă userul cere mai multe decât avem, luăm tot ce a rămas
        num_to_generate = min(count, len(available_questions))
        
        selected_questions = random.sample(available_questions, num_to_generate)
        
        saved_questions = []
        for question in selected_questions:
            # Salvăm direct (știm sigur că e unic)
            db_id = db_manager.save_question(question)
            if db_id:
                question['dbId'] = db_id
                saved_questions.append(question)

        return jsonify(saved_questions)

    except Exception as e:
        app.logger.error(f"Eroare la generare batch: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/generate', methods=['POST'])
def api_generate():
    """Generează o singură întrebare unică"""
    try:
        data = request.json
        q_type = data.get('type', 'random')

        all_possible = generator.get_all_questions()
        if q_type != 'random':
            all_possible = [q for q in all_possible if q['type'] == q_type]

        existing_titles = db_manager.get_existing_titles()
        available = [q for q in all_possible if q['title'] not in existing_titles]

        if not available:
            return jsonify({'error': 'Toate întrebările posibile au fost deja generate!'}), 400

        question = random.choice(available)
        db_id = db_manager.save_question(question)
        question['dbId'] = db_id

        return jsonify(question)

    except Exception as e:
        app.logger.error(f"Eroare la generare: {e}")
        return jsonify({'error': str(e)}), 500

# ============= RUTE AUXILIARE (GET, EVALUATE, ETC) =============

@app.route('/api/questions', methods=['GET'])
def api_questions():
    """Lista întrebări din baza de date"""
    try:
        limit = request.args.get('limit', 50, type=int)
        questions = db_manager.get_all_questions(limit)

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
        db_id = data.get('dbId')  # ID din baza de date (opțional)
        user_answer = data.get('userAnswer', '')

        question = None
        if db_id:
            question = db_manager.get_question_by_db_id(db_id)

        if not question:
            return jsonify({'error': 'Întrebare negăsită'}), 404

        question_data = {
            'id': question['question_id'],
            'type': question['type'],
            'title': question['title'],
            'question': question['question'],
            'correctAnswer': question['correct_answer'],
            'explanation': question['explanation']
        }

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

@app.route('/api/question/<int:db_id>', methods=['DELETE'])
def api_delete_question(db_id):
    """Șterge o întrebare după ID"""
    try:
        success = db_manager.delete_question(db_id)
        if success:
            return jsonify({'message': 'Întrebare ștearsă cu succes'})
        else:
            return jsonify({'error': 'Întrebarea nu a fost găsită'}), 404
    except Exception as e:
        app.logger.error(f"Eroare la ștergere: {e}")
        return jsonify({'error': str(e)}), 500
    



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