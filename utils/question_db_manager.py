"""
Manager pentru baza de date PostgreSQL - Întrebări AI
Versiune modularizată pentru integrare cu Flask
"""
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from datetime import datetime


class QuestionDBManager:
    """Clasă pentru gestionarea întrebărilor în PostgreSQL"""

    def __init__(self, db_config):
        """
        Inițializare cu configurația bazei de date
        """
        self.db_config = db_config

    @contextmanager
    def get_connection(self):
        """Context manager pentru conexiuni sigure la baza de date"""
        conn = None
        try:
            conn = psycopg2.connect(**self.db_config)
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()

    def get_existing_titles(self):
        """
        Returnează un SET cu toate titlurile întrebărilor existente în baza de date.
        Folosit pentru a filtra rapid duplicatele.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT title FROM questions;")
                # Returnăm un set pentru căutare O(1)
                return {row[0] for row in cursor.fetchall()}

    def save_question(self, question_data):
        """
        Salvează o nouă întrebare în baza de date.
        question_data trebuie să conțină: title, question, correct_answer, explanation, type
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Inserare în tabela questions
                query = """
                    INSERT INTO questions 
                    (title, question, correct_answer, explanation, type, created_at)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """
                cursor.execute(query, (
                    question_data['title'],
                    question_data['question'],
                    question_data['correct_answer'],
                    question_data['explanation'],
                    question_data['type'],
                    datetime.now()
                ))
                new_id = cursor.fetchone()[0]

                # 2. Actualizare/Creare în tabela question_stats
                # Verificăm dacă tipul există deja
                cursor.execute("SELECT total_generated FROM question_stats WHERE question_type = %s;", (question_data['type'],))
                if cursor.fetchone():
                    # Dacă există, actualizăm
                    cursor.execute("""
                        UPDATE question_stats SET total_generated = total_generated + 1
                        WHERE question_type = %s;
                    """, (question_data['type'],))
                else:
                    # Dacă nu există, inserăm
                    cursor.execute("""
                        INSERT INTO question_stats (question_type, total_generated)
                        VALUES (%s, 1);
                    """, (question_data['type'],))

                return new_id

    def get_all_questions(self):
        """
        Returnează toate întrebările. (Doar meta-date: id, title, type, created_at)
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT id, title, type, created_at
                    FROM questions 
                    ORDER BY created_at DESC;
                """
                cursor.execute(query)
                return cursor.fetchall()

    def get_question_by_id(self, q_id, include_answer=True):
        """
        Returnează o întrebare după ID.
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                if include_answer:
                    query = """
                        SELECT id, title, question, correct_answer, explanation, type
                        FROM questions 
                        WHERE id = %s;
                    """
                else:
                    query = """
                        SELECT id, title, question, type
                        FROM questions 
                        WHERE id = %s;
                    """
                cursor.execute(query, (q_id,))
                return cursor.fetchone()

    def delete_question_by_id(self, q_id):
        """
        Șterge o întrebare după ID și actualizează statisticile.
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # 1. Obținem tipul întrebării înainte de a o șterge
                cursor.execute("SELECT type FROM questions WHERE id = %s;", (q_id,))
                result = cursor.fetchone()
                if not result:
                    return False

                q_type = result[0]

                # 2. Ștergem întrebarea
                cursor.execute("DELETE FROM questions WHERE id = %s;", (q_id,))

                # 3. Decrementăm contorul de statistici
                cursor.execute("""
                    UPDATE question_stats SET total_generated = total_generated - 1
                    WHERE question_type = %s AND total_generated > 0;
                    """, (q_type,))

                return True


    def get_count_by_type(self):
        """
        Returnează numărul de întrebări per tip
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT type, COUNT(*) as count 
                    FROM questions 
                    GROUP BY type 
                    ORDER BY count DESC;
                """
                cursor.execute(query)
                return cursor.fetchall()

    def get_total_count(self):
        """
        Returnează numărul total de întrebări
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM questions;")
                return cursor.fetchone()[0]

    def clear_all_questions(self):
        """
        Șterge toate întrebările (ATENȚIE: operație periculoasă!)
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM questions;")
                count = cursor.fetchone()[0]

                cursor.execute("DELETE FROM questions;")
                cursor.execute("UPDATE question_stats SET total_generated = 0;")

                return count

    # ======================= METODE PENTRU TEST =======================

    def get_random_questions_by_type(self, q_type, count):
        """
        Returnează un număr specificat de întrebări (random) dintr-un anumit tip.
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT id, title, question, correct_answer, explanation, type
                    FROM questions 
                    WHERE type = %s
                    ORDER BY RANDOM()
                    LIMIT %s;
                """
                cursor.execute(query, (q_type, count))
                return cursor.fetchall()

    def get_questions_by_ids(self, ids):
        """
        Returnează întrebările pentru o listă de ID-uri.
        Returnează un dicționar {id: question_data}.
        """
        if not ids:
            return {}

        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT id, title, question, correct_answer, explanation, type
                    FROM questions 
                    WHERE id IN %s;
                """
                cursor.execute(query, (tuple(ids),))

                return {q['id']: q for q in cursor.fetchall()}

    # ======================= METODĂ NOUĂ PENTRU EXPORT PDF =======================

    def get_all_questions_full(self):
        """
        Returnează TOATE întrebările, inclusiv răspunsul și explicația.
        Folosit pentru exportul PDF.
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT id, title, question, correct_answer, explanation, type, created_at
                    FROM questions 
                    ORDER BY created_at DESC;
                """
                cursor.execute(query)
                return cursor.fetchall()