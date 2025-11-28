"""
Evaluator pentru răspunsurile utilizatorilor
"""


class QuestionEvaluator:
    """Clasă responsabilă pentru evaluarea răspunsurilor"""
    
    def __init__(self):
        # Expansiune keywords cu variante și sinonime
        self.keywords = {
            'n-queens': [
                'backtracking', 'back tracking', 'back-tracking',
                'dfs', 'depth first', 'depth-first', 'depth first search',
                'forward checking', 'forward-checking',
                'mrv', 'minimum remaining value', 'minimum remaining values',
                'csp', 'constraint satisfaction', 'constraint satisfaction problem',
                'constraint', 'constrangere', 'pruning'
            ],
            'hanoi': [
                'recursiv', 'recursive', 'recursie', 'recursion',
                'bfs', 'breadth first', 'breadth-first', 'breadth first search',
                'optimal', 'optim',
                'ids', 'iterative deepening', 'iterative-deepening',
                'iterative', 'iterativ'
            ],
            'coloring': [
                'greedy', 'lacom', 'greedy algorithm',
                'backtracking', 'back tracking', 'back-tracking',
                'welsh-powell', 'welsh powell',
                'dsatur', 'd-satur', 'degree saturation',
                'forward checking', 'forward-checking',
                'largest degree first', 'largest-degree-first'
            ],
            'knight': [
                'warnsdorff', 'warnsdorff\'s', 'warnsdorff heuristic',
                'backtracking', 'back tracking', 'back-tracking',
                'heuristic', 'heuristica', 'euristic',
                'degree', 'grad', 'degree heuristic'
            ]
        }
        
        # Algoritmi principali cu variante
        self.main_algorithms = {
            'backtracking': ['backtracking', 'back tracking', 'back-tracking'],
            'bfs': ['bfs', 'breadth first', 'breadth-first', 'breadth first search'],
            'dfs': ['dfs', 'depth first', 'depth-first', 'depth first search'],
            'greedy': ['greedy', 'lacom', 'greedy algorithm'],
            'warnsdorff': ['warnsdorff', 'warnsdorff\'s', 'warnsdorff heuristic'],
            'recursiv': ['recursiv', 'recursive', 'recursie', 'recursion']
        }

        # Niveluri de feedback
        self.feedback_levels = [
            (90, '🎉 Excelent! Răspuns complet și corect!'),
            (70, '👍 Foarte bine! Acoperă punctele principale.'),
            (50, '👌 Bine! Parțial corect, dar lipsesc detalii.'),
            (30, '🤔 Satisfăcător. Identifică strategia, dar incomplet.'),
            (0, '❌ Nesatisfăcător. Nu acoperă cerințele.')
        ]
    
    def evaluate_answer(self, question, user_answer):
        """
        Evaluează răspunsul utilizatorului
        
        """
        user_lower = user_answer.lower()
        correct_lower = question['correctAnswer'].lower()
        q_type = question['type']
        
        score = 0
        
        # Verificare exact match (considerând și variante)
        if self._is_equivalent_answer(user_lower, correct_lower):
            score = 100
        else:
            # 1. Verifică algoritmul principal (60 puncte)
            algo_score = self._check_main_algorithm(user_lower, correct_lower)
            score += algo_score
            
            # 2. Verifică cuvinte cheie relevante (40 puncte)
            keyword_score = self._check_keywords(user_lower, q_type)
            score += keyword_score
            
            # Bonus: dacă are algoritmul principal corect, punctaj mai mare
            if algo_score >= 50:
                score = min(100, score + 10)  # Bonus 10 puncte
        
        # Limitează scorul la 100
        score = min(100, score)
        
        # Determină feedback-ul
        feedback = self._get_feedback(score)
        
        return {
            'score': score,
            'feedback': feedback
        }
    
    def _is_equivalent_answer(self, user_answer, correct_answer):
        """
        Verifică dacă răspunsul utilizatorului este echivalent cu cel corect
        (considerând variante: BFS = Breadth First Search)
        """
        # Verificare exactă
        if user_answer == correct_answer:
            return True
        
        # Verifică dacă ambele conțin același algoritm principal
        for algo_name, variants in self.main_algorithms.items():
            user_has = any(variant in user_answer for variant in variants)
            correct_has = any(variant in correct_answer for variant in variants)
            
            if user_has and correct_has:
                # Ambele menționează același algoritm principal
                # Verifică dacă user_answer nu conține algoritmi contradictorii
                other_algos = [v for name, variants in self.main_algorithms.items() 
                            if name != algo_name for v in variants]
                
                # Dacă user_answer conține doar algoritmul corect (sau cu termeni adiționali relevanți)
                has_contradiction = any(other in user_answer for other in other_algos)
                
                if not has_contradiction:
                    return True
        
        return False

    def _check_main_algorithm(self, user_answer, correct_answer):
        """Verifică dacă algoritmul principal este menționat (cu variante)"""
        # Verifică fiecare algoritm și variantele sale
        for algo_name, variants in self.main_algorithms.items():
            # Verifică dacă vreo variantă apare în răspunsul corect
            correct_has_algo = any(variant in correct_answer for variant in variants)
            
            # Verifică dacă vreo variantă apare în răspunsul utilizatorului
            user_has_algo = any(variant in user_answer for variant in variants)
            
            if correct_has_algo and user_has_algo:
                return 60  # Crescut de la 50 la 60
        
        return 0
    
    def _check_keywords(self, user_answer, q_type):
        """Verifică cuvintele cheie relevante pentru tipul întrebării"""
        q_keywords = self.keywords.get(q_type, [])
        
        # Contorizează grupuri unice de keywords găsite (nu conta de câte ori)
        found_groups = set()
        
        for kw in q_keywords:
            if kw in user_answer:
                # Grupează variantele (ex: 'bfs', 'breadth first' = același concept)
                base_concept = kw.split()[0]  # Primul cuvânt ca identificator
                found_groups.add(base_concept)
        
        # Punctaj mai generos: 15 puncte per concept găsit (max 50)
        keyword_score = min(50, len(found_groups) * 15)
        return keyword_score
    
    def _get_feedback(self, score):
        """Returnează feedback-ul corespunzător scorului"""
        for threshold, feedback in self.feedback_levels:
            if score >= threshold:
                return feedback
        return self.feedback_levels[-1][1]