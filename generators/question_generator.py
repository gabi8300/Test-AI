"""
Generator de întrebări pentru diferite tipuri de probleme AI
"""
import random


class QuestionGenerator:
    """Clasă responsabilă pentru generarea întrebărilor"""
    
    def __init__(self):
        self.question_counter = 0
        self.generators = {
            'n-queens': self._generate_nqueens,
            'hanoi': self._generate_hanoi,
            'coloring': self._generate_coloring,
            'knight': self._generate_knight
        }
    
    def generate_question(self, q_type='random'):
        """Generează o întrebare de tipul specificat"""
        if q_type == 'random':
            q_type = random.choice(list(self.generators.keys()))
        
        if q_type not in self.generators:
            raise ValueError(f"Tip întrebare invalid: {q_type}")
        
        return self.generators[q_type]()
    
    def _generate_nqueens(self):
        """Generează întrebare N-Queens"""
        self.question_counter += 1
        n = random.randint(4, 15)
        
        return {
            'id': self.question_counter,
            'type': 'n-queens',
            'title': f'N-Queens (n={n})',
            'question': f'''Pentru problema N-Queens cu n={n}:

Trebuie să plasați {n} regine pe o tablă de șah {n}x{n} astfel încât nicio regină să nu se atace reciproc.

Care este cea mai potrivită strategie de rezolvare? Justificați alegerea.''',
            'correctAnswer': 'Backtracking cu DFS' if n <= 8 else 'Backtracking cu Forward Checking și MRV',
            'explanation': f'''Răspuns: {"Backtracking cu DFS" if n <= 8 else "Backtracking cu Forward Checking și MRV"}

Justificare:
- Spațiu de stări: {n}^{n} = {n**n} posibilități
- Problema CSP (Constraint Satisfaction Problem)
- {"DFS eficient pentru table mici" if n <= 8 else "Forward Checking + MRV pentru table mari"}
- Complexitate: O({n}!) fără optimizări
- Backtracking permite abandon rapid (pruning)

Alternative: {"Forward Checking, MRV" if n <= 8 else "AC-3, Minimum Conflicts"}'''
        }
    
    def _generate_hanoi(self):
        """Generează întrebare Hanoi"""
        self.question_counter += 1
        n_disks = random.randint(3, 8)
        n_pegs = random.randint(3, 6)
        
        return {
            'id': self.question_counter,
            'type': 'hanoi',
            'title': f'Hanoi ({n_disks} discuri, {n_pegs} tije)',
            'question': f'''Pentru problema Hanoi Generalizată:

- {n_disks} discuri de dimensiuni diferite
- {n_pegs} tije disponibile
- Mutați toate discurile de pe prima tijă pe ultima
- Un disc mai mare nu poate fi peste unul mai mic

Care este cea mai potrivită strategie?''',
            'correctAnswer': 'Algoritm recursiv (DFS)' if n_pegs == 3 else 'BFS',
            'explanation': f'''Răspuns: {"Algoritm recursiv (DFS)" if n_pegs == 3 else "BFS"}

Justificare:
- {"Hanoi clasic (3 tije) are formulă optimă: 2^n - 1" if n_pegs == 3 else f"Hanoi cu {n_pegs} tije NU are formulă optimă"}
- {"Recursivitate garantează soluția optimă" if n_pegs == 3 else "BFS garantează număr minim de mutări"}
- Număr mutări: {2**n_disks - 1 if n_pegs == 3 else "necunoscut"}
- {"Complexitate: O(2^n)" if n_pegs == 3 else "Complexitate: O(k^n)"}

Alternative: {"IDS pentru memorie limitată" if n_pegs == 3 else "IDS (Iterative Deepening Search)"}'''
        }
    
    def _generate_coloring(self):
        """Generează întrebare Graph Coloring"""
        self.question_counter += 1
        n_nodes = random.choice([5, 6, 7, 8, 10])
        n_colors = random.choice([3, 4, 5])
        density = random.choice(['sparse', 'dense', 'moderate'])
        
        edges = {
            'sparse': n_nodes + 2,
            'moderate': n_nodes * 2,
            'dense': n_nodes * (n_nodes - 1) // 3
        }[density]
        
        is_easy = density == 'sparse' or n_colors >= 4
        
        return {
            'id': self.question_counter,
            'type': 'coloring',
            'title': f'Graph Coloring ({n_nodes} noduri, {density})',
            'question': f'''Pentru problema Graph Coloring:

- Graf cu {n_nodes} noduri și {edges} muchii ({density})
- Maximum {n_colors} culori disponibile
- Noduri adiacente trebuie să aibă culori diferite

Care este cea mai potrivită strategie?''',
            'correctAnswer': 'Greedy (Largest Degree First)' if is_easy else 'Backtracking cu Forward Checking',
            'explanation': f'''Răspuns: {"Greedy cu ordonare (Largest Degree First)" if is_easy else "Backtracking cu Forward Checking"}

Justificare:
- Graf {density}: {n_nodes} noduri, {edges} muchii
- {n_colors} culori {"probabil suficiente" if n_colors >= 4 else "puține - problemă dificilă"}
- {"Greedy: O(V+E), rapid și eficient" if is_easy else "Backtracking necesar pentru explorare sistematică"}
- {"Welsh-Powell garantează Δ+1 culori" if is_easy else "Forward Checking reduce ramificarea"}

Alternative: {"DSatur, Backtracking la eșec" if is_easy else "MRV, Degree Heuristic"}'''
        }
    
    def _generate_knight(self):
        """Generează întrebare Knight's Tour"""
        self.question_counter += 1
        board_size = random.choice([5, 6, 8])
        start = [random.randint(0, board_size-1), random.randint(0, board_size-1)]
        tour_type = random.choice(['open', 'closed'])
        
        return {
            'id': self.question_counter,
            'type': 'knight',
            'title': f"Knight's Tour ({board_size}x{board_size}, {tour_type})",
            'question': f'''Pentru problema Knight's Tour:

- Tablă de șah {board_size}x{board_size}
- Poziție start: ({start[0]}, {start[1]})
- Tur {tour_type} ({"revine la start" if tour_type == "closed" else "orice final"})
- Vizitează fiecare pătrat exact o dată

Care este cea mai potrivită strategie?''',
            'correctAnswer': 'Backtracking cu Warnsdorff' if board_size <= 6 else 'Warnsdorff cu backtracking limitat',
            'explanation': f'''Răspuns: {"Backtracking cu heuristica Warnsdorff" if board_size <= 6 else "Warnsdorff cu backtracking limitat"}

Justificare:
- Tablă {board_size}x{board_size} = {board_size*board_size} pătrate
- Heuristica Warnsdorff: alege pătratul cu mai puține mutări viitoare
- {"Reduce dramatic ramificarea" if board_size <= 6 else "Esențială pentru table mari"}
- Evită blocarea timpurie
- {"Rezolvare în timp liniar practic" if board_size <= 6 else "Succes ~99% pentru 8x8"}

Alternative: {"Divide & Conquer pentru table mari" if board_size > 6 else "Random backtracking"}'''
        }