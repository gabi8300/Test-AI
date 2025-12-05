from flask import Flask, jsonify, request, render_template, make_response
from flask_cors import CORS
from generators.question_generator import QuestionGenerator
from utils.evaluator import QuestionEvaluator
from utils.question_db_manager import QuestionDBManager
import random
from datetime import datetime
from io import BytesIO

# Importuri Reportlab pentru PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT

app = Flask(__name__)
CORS(app)

# ============= CONFIGURARE =============
DB_CONFIG = {
    'host': 'localhost',
    'database': 'smartestDB',
    'user': 'postgres',
    'password': '12345',
    'port': 5433
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

        # 2. Obține titlurile întrebărilor existente din DB
        existing_titles = db_manager.get_existing_titles()

        # 3. Filtrează întrebările deja existente și pe tip
        possible_new_questions = [
            q for q in all_possible
            if q['title'] not in existing_titles and (q_type == 'random' or q['type'] == q_type)
        ]

        # 4. Alege un subset de dimensiunea 'count'
        if len(possible_new_questions) > count:
            questions_to_save = random.sample(possible_new_questions, count)
        else:
            questions_to_save = possible_new_questions

        # 5. Salvează în DB
        saved_count = 0
        for q in questions_to_save:
            db_manager.save_question(q)
            saved_count += 1

        return jsonify({
            'success': True,
            'message': f'Am generat și salvat {saved_count} întrebări noi. {len(possible_new_questions) - saved_count} întrebări posibile rămase din tipul {q_type}.',
            'saved_count': saved_count
        })
    except Exception as e:
        app.logger.error(f"Eroare la generarea batch: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/questions', methods=['GET'])
def api_get_questions():
    """Returnează lista scurtă de întrebări și contorul total"""
    try:
        questions = db_manager.get_all_questions()
        total_count = db_manager.get_total_count()
        return jsonify({'questions': questions, 'total': total_count})
    except Exception as e:
        app.logger.error(f"Eroare la obținerea listei de întrebări: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/question/<int:q_id>', methods=['GET'])
def api_get_question(q_id):
    """Returnează o întrebare după ID, fără răspuns (doar pentru vizualizare)"""
    try:
        question = db_manager.get_question_by_id(q_id, include_answer=False)
        if question:
            return jsonify(question)
        return jsonify({'error': 'Întrebarea nu a fost găsită'}), 404
    except Exception as e:
        app.logger.error(f"Eroare la obținerea întrebării: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluate', methods=['POST'])
def api_evaluate_answer():
    """Evaluează răspunsul utilizatorului la o întrebare specifică"""
    try:
        data = request.json
        q_id = data.get('question_id')
        user_answer = data.get('user_answer', '')

        question_data = db_manager.get_question_by_id(q_id, include_answer=True)

        if not question_data:
            return jsonify({'error': 'Întrebarea nu a fost găsită'}), 404

        # Extrage datele necesare
        correct_answer = question_data['correct_answer']
        q_type = question_data['type']

        # Evaluează răspunsul folosind QuestionEvaluator
        evaluation_result = evaluator.evaluate(user_answer, correct_answer, q_type)

        # Întoarce rezultatul
        return jsonify({
            'questionId': q_id,
            'score': evaluation_result['score'],
            'feedback': evaluation_result['feedback'],
            'correctAnswer': correct_answer,
            'explanation': evaluation_result['explanation']
        })

    except Exception as e:
        app.logger.error(f"Eroare la evaluare: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/delete/<int:q_id>', methods=['DELETE'])
def api_delete_question(q_id):
    """Șterge o întrebare după ID"""
    try:
        if db_manager.delete_question_by_id(q_id):
            return jsonify({'success': True, 'message': f'Întrebarea cu ID-ul {q_id} a fost ștearsă.'})
        else:
            return jsonify({'error': 'Întrebarea nu a fost găsită'}), 404
    except Exception as e:
        app.logger.error(f"Eroare la ștergere: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/clear-all', methods=['DELETE'])
def api_clear_all():
    """Șterge TOATE întrebările din baza de date"""
    try:
        count = db_manager.clear_all_questions()
        return jsonify({
            'success': True,
            'message': f'Au fost șterse {count} întrebări din baza de date.'
        })
    except Exception as e:
        app.logger.error(f"Eroare la ștergerea tuturor întrebărilor: {e}")
        return jsonify({'error': str(e)}), 500


# ============= RUTE PENTRU TESTE =============

@app.route('/api/question-types', methods=['GET'])
def api_get_question_types():
    """
    Returnează lista de tipuri de întrebări și numărul lor disponibil.
    """
    try:
        counts = db_manager.get_count_by_type()
        return jsonify(counts)
    except Exception as e:
        app.logger.error(f"Eroare la obținerea tipurilor de întrebări: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/generate-test', methods=['POST'])
def api_generate_test():
    """
    Generează un test cu întrebări bazate pe configurația utilizatorului.
    """
    try:
        config = request.json
        test_questions = []

        for q_type, count in config.items():
            count = int(count)
            if count > 0:
                questions_of_type = db_manager.get_random_questions_by_type(q_type, count)
                test_questions.extend(questions_of_type)

        random.shuffle(test_questions)

        # Păstrăm doar câmpurile necesare pentru frontend: id, title, question, type
        sanitized_questions = [
            {'id': q['id'], 'title': q['title'], 'question': q['question'], 'type': q['type']}
            for q in test_questions
        ]

        return jsonify(sanitized_questions)
    except Exception as e:
        app.logger.error(f"Eroare la generarea testului: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/evaluate-test', methods=['POST'])
def api_evaluate_test():
    """
    Evaluează toate răspunsurile trimise pentru un test.
    """
    try:
        answers = request.json
        results = []

        question_ids = [a['question_id'] for a in answers]

        questions_map = db_manager.get_questions_by_ids(question_ids)

        for answer_data in answers:
            q_id = answer_data['question_id']
            user_answer = answer_data['user_answer']
            question_data = questions_map.get(q_id)

            if question_data:
                evaluation_result = evaluator.evaluate(
                    user_answer,
                    question_data['correct_answer'],
                    question_data['type']
                )

                results.append({
                    'question_id': q_id,
                    'type': question_data['type'],
                    'title': question_data['title'],
                    'question': question_data['question'],
                    'user_answer': user_answer,
                    'correct_answer': question_data['correct_answer'],
                    'explanation': evaluation_result['explanation'],
                    'score': evaluation_result['score'],
                    'feedback': evaluation_result['feedback']
                })

        return jsonify(results)
    except Exception as e:
        app.logger.error(f"Eroare la evaluarea testului: {e}")
        return jsonify({'error': str(e)}), 500


# ============= RUTĂ PENTRU EXPORT PDF =============

@app.route('/api/export-pdf', methods=['GET'])
def api_export_pdf():
    """
    Generează un PDF care conține toate întrebările din baza de date,
    inclusiv răspunsurile și explicațiile.
    """
    try:
        # Obținem toate întrebările din DB (cu conținut complet)
        all_questions = db_manager.get_all_questions_full()

        if not all_questions:
            return jsonify({'error': 'Nu există întrebări de exportat'}), 404

        # Buffer pentru a scrie PDF-ul
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=40, leftMargin=40,
                                topMargin=40, bottomMargin=40)

        styles = getSampleStyleSheet()

        # Creăm un stil bold personalizat pentru etichete
        bold_style = ParagraphStyle(
            'CustomBold',
            parent=styles['Normal'],
            fontName='Helvetica-Bold',
            fontSize=10,
            textColor=colors.HexColor('#006400')
        )

        story = []

        # Funcție helper pentru a escapa caractere speciale XML
        def escape_xml(text):
            if text is None:
                return ""
            text = str(text)
            text = text.replace('&', '&amp;')
            text = text.replace('<', '&lt;')
            text = text.replace('>', '&gt;')
            return text

        # Titlu
        story.append(Paragraph("Catalog Complet Intrebari SmartTest AI", styles['Title']))
        story.append(Spacer(1, 12))
        story.append(Paragraph(f"Data Export: {datetime.now().strftime('%Y-%m-%d %H:%M')}", styles['Italic']))
        story.append(Spacer(1, 24))

        for i, q in enumerate(all_questions):
            try:
                # Header Întrebare
                q_header = f"<b>{i + 1}. [{escape_xml(q['type']).upper()}] {escape_xml(q['title'])}</b>"
                story.append(Paragraph(q_header, styles['Heading2']))
                story.append(Spacer(1, 6))

                # Întrebarea
                q_text = f"<b>Intrebare:</b> {escape_xml(q['question'])}"
                story.append(Paragraph(q_text, styles['Normal']))
                story.append(Spacer(1, 6))

                # Răspuns Corect - folosim bold_style în loc de 'Strong'
                data_answer = [
                    [Paragraph("Raspuns Corect:", bold_style),
                     Paragraph(escape_xml(q['correct_answer']), styles['Normal'])]
                ]
                t_answer = Table(data_answer, colWidths=[120, 380])
                t_answer.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, -1), colors.lightgreen),
                    ('BOX', (0, 0), (-1, -1), 1, colors.green),
                    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                    ('LEFTPADDING', (0, 0), (-1, -1), 8),
                    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                    ('TOPPADDING', (0, 0), (-1, -1), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ]))
                story.append(t_answer)
                story.append(Spacer(1, 6))

                # Explicație
                q_explanation = f"<b>Explicatie:</b> {escape_xml(q['explanation'])}"
                story.append(Paragraph(q_explanation, styles['Normal']))
                story.append(Spacer(1, 24))

            except Exception as q_error:
                app.logger.error(f"Eroare la procesarea întrebării {i + 1}: {q_error}")
                # Continuăm cu următoarea întrebare
                continue

        doc.build(story)

        pdf_content = buffer.getvalue()
        buffer.close()

        # Creare răspuns Flask
        response = make_response(pdf_content)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=SmartTest_Questions.pdf'

        return response

    except Exception as e:
        app.logger.error(f"Eroare la generarea PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Eroare la generarea PDF: {str(e)}'}), 500


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
    print("=" * 70)
    print("\n⏳ Testare conexiune la baza de date...")

    try:
        # Cod de inițializare DB (verificare tabele)
        with db_manager.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS questions (
                        id SERIAL PRIMARY KEY,
                        title VARCHAR(255) UNIQUE NOT NULL,
                        question TEXT NOT NULL,
                        correct_answer TEXT NOT NULL,
                        explanation TEXT,
                        type VARCHAR(50) NOT NULL,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS question_stats (
                        question_type VARCHAR(50) PRIMARY KEY,
                        total_generated INTEGER DEFAULT 0
                    );
                """)
        print("✅ Conexiune reușită și tabele verificate/create.")
    except Exception as e:
        print(f"❌ EROARE CRITICĂ la conexiunea DB: {e}")
        print("Asigură-te că PostgreSQL rulează și configurația în `app.py` este corectă.")
        import sys

        sys.exit(1)

    app.run(debug=True, port=5000)