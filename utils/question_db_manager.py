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
        Salvează o întrebare în baza de date
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                query = """
                    INSERT INTO questions 
                    (question_id, type, title, question, correct_answer, explanation)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id;
                """

                cursor.execute(query, (
                    question_data['id'],
                    question_data['type'],
                    question_data['title'],
                    question_data['question'],
                    question_data['correctAnswer'],
                    question_data['explanation']
                ))

                db_id = cursor.fetchone()[0]

                # Actualizează statisticile
                self._update_stats(cursor, question_data['type'])

                return db_id

    def _update_stats(self, cursor, question_type):
        """
        Actualizează statisticile pentru tipul de întrebare
        """
        query = """
            INSERT INTO question_stats (question_type, total_generated, last_generated)
            VALUES (%s, 1, CURRENT_TIMESTAMP)
            ON CONFLICT (question_type) 
            DO UPDATE SET 
                total_generated = question_stats.total_generated + 1,
                last_generated = CURRENT_TIMESTAMP;
        """
        cursor.execute(query, (question_type,))

    def get_question_by_db_id(self, db_id):
        """
        Recuperează o întrebare după ID-ul din baza de date
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM questions WHERE id = %s;"
                cursor.execute(query, (db_id,))
                return cursor.fetchone()

    def get_questions_by_type(self, question_type, limit=10):
        """
        Recuperează întrebările după tip
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM questions 
                    WHERE type = %s 
                    ORDER BY created_at DESC 
                    LIMIT %s;
                """
                cursor.execute(query, (question_type, limit))
                return cursor.fetchall()

    def get_all_questions(self, limit=50, offset=0):
        """
        Recuperează toate întrebările cu paginare
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM questions 
                    ORDER BY created_at DESC 
                    LIMIT %s OFFSET %s;
                """
                cursor.execute(query, (limit, offset))
                return cursor.fetchall()

    def get_statistics(self):
        """
        Recuperează statisticile despre întrebări
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = "SELECT * FROM question_stats ORDER BY question_type;"
                cursor.execute(query)
                return cursor.fetchall()

    def search_questions(self, search_term, limit=20):
        """
        Caută întrebări după termen (în titlu sau conținut)
        """
        with self.get_connection() as conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                query = """
                    SELECT * FROM questions 
                    WHERE title ILIKE %s OR question ILIKE %s
                    ORDER BY created_at DESC 
                    LIMIT %s;
                """
                search_pattern = f'%{search_term}%'
                cursor.execute(query, (search_pattern, search_pattern, limit))
                return cursor.fetchall()

    def delete_question(self, db_id):
        """
        Șterge o întrebare din baza de date
        """
        with self.get_connection() as conn:
            with conn.cursor() as cursor:
                # Obține tipul întrebării înainte de ștergere
                cursor.execute("SELECT type FROM questions WHERE id = %s;", (db_id,))
                result = cursor.fetchone()

                if result:
                    question_type = result[0]

                    # Șterge întrebarea
                    cursor.execute("DELETE FROM questions WHERE id = %s;", (db_id,))

                    # Actualizează statisticile
                    cursor.execute("""
                        UPDATE question_stats 
                        SET total_generated = total_generated - 1
                        WHERE question_type = %s AND total_generated > 0;
                    """, (question_type,))

                    return True
                return False

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