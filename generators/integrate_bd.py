"""
Exemplu complet de utilizare - Generator + Database
"""
from question_generator import QuestionGenerator
from question_db_manager import QuestionDBManager


def main():
    # Configurare bază de date
    db_config = {
        'host': 'localhost',
        'database': 'smartestDB',
        'user': 'postgres',
        'password': '12345',
        'port': 5433
    }

    # Inițializare
    generator = QuestionGenerator()
    db_manager = QuestionDBManager(db_config)

    print("=== Generator și Salvare Întrebări AI ===\n")

    # Exemplu 1: Generează și salvează o întrebare random
    print("1. Generare întrebare random...")
    question = generator.generate_question('random')
    db_id = db_manager.save_question(question)
    print(f"✓ Întrebarea #{question['id']} salvată cu ID {db_id}")
    print(f"  Tip: {question['type']}")
    print(f"  Titlu: {question['title']}\n")

    # Exemplu 2: Generează mai multe întrebări de tipuri specifice
    print("2. Generare întrebări multiple...")
    types_to_generate = ['n-queens', 'hanoi', 'coloring', 'knight']

    for q_type in types_to_generate:
        question = generator.generate_question(q_type)
        db_id = db_manager.save_question(question)
        print(f"✓ {q_type}: {question['title']} (ID: {db_id})")

    print()

    # Exemplu 3: Generează 10 întrebări random
    print("3. Generare 10 întrebări random...")
    for i in range(10):
        question = generator.generate_question('random')
        db_id = db_manager.save_question(question)
        print(f"✓ Întrebare {i + 1}/10 salvată (ID: {db_id}, Tip: {question['type']})")

    print()

    # Exemplu 4: Afișează statistici
    print("4. Statistici întrebări:")
    stats = db_manager.get_statistics()
    for stat in stats:
        print(f"  {stat['question_type']}: {stat['total_generated']} întrebări")

    print()

    # Exemplu 5: Recuperează întrebări după tip
    print("5. Ultimele 3 întrebări N-Queens:")
    nqueens_questions = db_manager.get_questions_by_type('n-queens', limit=3)
    for q in nqueens_questions:
        print(f"  - {q['title']} (creat: {q['created_at']})")

    print()

    # Exemplu 6: Caută întrebări
    print("6. Căutare întrebări cu 'hanoi':")
    search_results = db_manager.search_questions('hanoi', limit=5)
    for q in search_results:
        print(f"  - {q['title']}")

    print()

    # Exemplu 7: Afișează o întrebare completă
    if search_results:
        print("7. Detalii întrebare:")
        question = search_results[0]
        print(f"  ID: {question['id']}")
        print(f"  Titlu: {question['title']}")
        print(f"  Tip: {question['type']}")
        print(f"  Întrebare:\n{question['question']}")
        print(f"\n  Răspuns corect: {question['correct_answer']}")
        print(f"\n  Explicație:\n{question['explanation']}")


def generate_batch(n=100, q_type='random'):
    """
    Funcție utilă pentru generarea în batch

    Args:
        n: număr de întrebări de generat
        q_type: tipul de întrebare sau 'random'
    """
    db_config = {
        'host': 'localhost',
        'database': 'smartestDB',
        'user': 'postgres',
        'password': '12345',
        'port': 5433
    }

    generator = QuestionGenerator()
    db_manager = QuestionDBManager(db_config)

    print(f"Generare {n} întrebări de tip '{q_type}'...")

    saved_count = 0
    for i in range(n):
        try:
            question = generator.generate_question(q_type)
            db_id = db_manager.save_question(question)
            saved_count += 1

            if (i + 1) % 10 == 0:
                print(f"  Progres: {i + 1}/{n} întrebări salvate")

        except Exception as e:
            print(f"  Eroare la întrebarea {i + 1}: {e}")

    print(f"\n✓ Total salvate: {saved_count}/{n} întrebări")

    # Afișează statistici finale
    stats = db_manager.get_count_by_type()
    print("\nDistribuție întrebări:")
    for stat in stats:
        print(f"  {stat['type']}: {stat['count']} întrebări")


if __name__ == '__main__':
    # Rulează exemplul principal
    main()

    # Sau generează un batch mare:
    # generate_batch(n=100, q_type='random')