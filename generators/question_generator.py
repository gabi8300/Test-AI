"""
Generator de întrebări - generează universul complet de întrebări posibile
"""
import random

class QuestionGenerator:
    """Clasă care generează toate combinațiile posibile de întrebări"""
    
    def __init__(self):
        self.question_counter = 0

    def get_all_questions(self):
        """Returnează lista completă a tuturor întrebărilor posibile"""
        questions = []
        self.question_counter = 0  # Resetăm contorul
        
        questions.extend(self._get_all_nqueens())
        questions.extend(self._get_all_hanoi())
        questions.extend(self._get_all_coloring())
        questions.extend(self._get_all_knight())
        
        return questions

    def generate_question(self, q_type='random'):
        """Păstrăm metoda pentru compatibilitate, dar alege din lista completă"""
        all_q = self.get_all_questions()
        if q_type != 'random':
            all_q = [q for q in all_q if q['type'] == q_type]
        return random.choice(all_q)
    
    def _get_all_nqueens(self):
        """Generează toate variantele N-Queens (n=4..15)"""
        qs = []
        # N de la 4 la 15
        for n in range(4, 16):
            self.question_counter += 1
            qs.append({
                'id': self.question_counter,
                'type': 'n-queens',
                'title': f'N-Queens (n={n})',
                'question': f'''Pentru problema N-Queens cu n={n}:

Trebuie să plasați {n} regine pe o tablă de șah {n}x{n} astfel încât nicio regină să nu se atace reciproc.

Care este cea mai potrivită strategie de rezolvare? Justificați alegerea.''',
                'correct_answer': 'Backtracking cu DFS' if n <= 8 else 'Backtracking cu Forward Checking și MRV',
                'explanation': f'''Răspuns: {"Backtracking cu DFS" if n <= 8 else "Backtracking cu Forward Checking și MRV"}

Justificare:
- Spațiu de stări: {n}^{n} = {n**n} posibilități
- Problema CSP (Constraint Satisfaction Problem)
- {"DFS eficient pentru table mici" if n <= 8 else "Forward Checking + MRV pentru table mari"}
- Complexitate: O({n}!) fără optimizări
- Backtracking permite abandon rapid (pruning)

Alternative: {"Forward Checking, MRV" if n <= 8 else "AC-3, Minimum Conflicts"}'''
            })
        return qs
    
    def _get_all_hanoi(self):
        """Generează toate variantele Hanoi (discuri 3-8, tije 3-6)"""
        qs = []
        for n_disks in range(3, 9):
            for n_pegs in range(3, 7):
                self.question_counter += 1
                qs.append({
                    'id': self.question_counter,
                    'type': 'hanoi',
                    'title': f'Hanoi ({n_disks} discuri, {n_pegs} tije)',
                    'question': f'''Pentru problema Hanoi Generalizată:

- {n_disks} discuri de dimensiuni diferite
- {n_pegs} tije disponibile
- Mutați toate discurile de pe prima tijă pe ultima
- Un disc mai mare nu poate fi peste unul mai mic

Care este cea mai potrivită strategie?''',
                    'correct_answer': 'Algoritm recursiv (DFS)' if n_pegs == 3 else 'BFS',
                    'explanation': f'''Răspuns: {"Algoritm recursiv (DFS)" if n_pegs == 3 else "BFS"}

Justificare:
- {"Hanoi clasic (3 tije) are formulă optimă: 2^n - 1" if n_pegs == 3 else f"Hanoi cu {n_pegs} tije NU are formulă optimă"}
- {"Recursivitate garantează soluția optimă" if n_pegs == 3 else "BFS garantează număr minim de mutări"}
- Număr mutări: {2**n_disks - 1 if n_pegs == 3 else "necunoscut"}
- {"Complexitate: O(2^n)" if n_pegs == 3 else "Complexitate: O(k^n)"}

Alternative: {"IDS pentru memorie limitată" if n_pegs == 3 else "IDS (Iterative Deepening Search)"}'''
                })
        return qs
    
    def _get_all_coloring(self):
        """Generează toate variantele Graph Coloring"""
        qs = []
        # Combinăm toți parametrii
        nodes_opts = [5, 6, 7, 8, 10]
        colors_opts = [3, 4, 5]
        density_opts = ['sparse', 'dense', 'moderate']

        for n_nodes in nodes_opts:
            for density in density_opts:
                for n_colors in colors_opts:
                    self.question_counter += 1
                    
                    edges = {
                        'sparse': n_nodes + 2,
                        'moderate': n_nodes * 2,
                        'dense': n_nodes * (n_nodes - 1) // 3
                    }[density]
                    
                    is_easy = density == 'sparse' or n_colors >= 4
                    
                    qs.append({
                        'id': self.question_counter,
                        'type': 'coloring',
                        # Actualizat titlul pentru unicitate
                        'title': f'Graph Coloring ({n_nodes} noduri, {density}, {n_colors} culori)',
                        'question': f'''Pentru problema Graph Coloring:

- Graf cu {n_nodes} noduri și {edges} muchii ({density})
- Maximum {n_colors} culori disponibile
- Noduri adiacente trebuie să aibă culori diferite

Care este cea mai potrivită strategie?''',
                        'correct_answer': 'Greedy (Largest Degree First)' if is_easy else 'Backtracking cu Forward Checking',
                        'explanation': f'''Răspuns: {"Greedy cu ordonare (Largest Degree First)" if is_easy else "Backtracking cu Forward Checking"}

Justificare:
- Graf {density}: {n_nodes} noduri, {edges} muchii
- {n_colors} culori {"probabil suficiente" if n_colors >= 4 else "puține - problemă dificilă"}
- {"Greedy: O(V+E), rapid și eficient" if is_easy else "Backtracking necesar pentru explorare sistematică"}
- {"Welsh-Powell garantează Δ+1 culori" if is_easy else "Forward Checking reduce ramificarea"}

Alternative: {"DSatur, Backtracking la eșec" if is_easy else "MRV, Degree Heuristic"}'''
                    })
        return qs
    
    def _get_all_knight(self):
        """Generează toate variantele Knight's Tour"""
        qs = []
        sizes = [5, 6, 8]
        types = ['open', 'closed']
        
        for board_size in sizes:
            for tour_type in types:
                # Iterăm prin TOATE pozițiile posibile de start
                for r in range(board_size):
                    for c in range(board_size):
                        self.question_counter += 1
                        start = [r, c]
                        
                        qs.append({
                            'id': self.question_counter,
                            'type': 'knight',
                            # Actualizat titlul pentru unicitate
                            'title': f"Knight's Tour ({board_size}x{board_size}, {tour_type}, start {r},{c})",
                            'question': f'''Pentru problema Knight's Tour:

- Tablă de șah {board_size}x{board_size}
- Poziție start: ({start[0]}, {start[1]})
- Tur {tour_type} ({"revine la start" if tour_type == "closed" else "orice final"})
- Vizitează fiecare pătrat exact o dată

Care este cea mai potrivită strategie?''',
                            'correct_answer': 'Backtracking cu Warnsdorff' if board_size <= 6 else 'Warnsdorff cu backtracking limitat',
                            'explanation': f'''Răspuns: {"Backtracking cu heuristica Warnsdorff" if board_size <= 6 else "Warnsdorff cu backtracking limitat"}

Justificare:
- Tablă {board_size}x{board_size} = {board_size*board_size} pătrate
- Heuristica Warnsdorff: alege pătratul cu mai puține mutări viitoare
- {"Reduce dramatic ramificarea" if board_size <= 6 else "Esențială pentru table mari"}
- Evită blocarea timpurie
- {"Rezolvare în timp liniar practic" if board_size <= 6 else "Succes ~99% pentru 8x8"}

Alternative: {"Divide & Conquer pentru table mari" if board_size > 6 else "Random backtracking"}'''
                        })
        return qs