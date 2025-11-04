"""
Evaluator pentru răspunsurile utilizatorilor
"""


class QuestionEvaluator:
    """Clasă responsabilă pentru evaluarea răspunsurilor"""
    
    def __init__(self):
        self.keywords = {
            'n-queens': ['backtracking', 'dfs', 'forward checking', 'mrv', 'csp', 'constraint'],
            'hanoi': ['recursiv', 'bfs', 'optimal', 'ids', 'iterative'],
            'coloring': ['greedy', 'backtracking', 'welsh-powell', 'dsatur', 'forward checking'],
            'knight': ['warnsdorff', 'backtracking', 'heuristic', 'degree']
        }
        
        self.main_algorithms = [
            'backtracking', 'bfs', 'greedy', 'warnsdorff', 'recursiv', 'dfs'
        ]
        
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
        
        # 1. Verifică algoritmul principal (40 puncte)
        score += self._check_main_algorithm(user_lower, correct_lower)
        
        # 2. Verifică cuvinte cheie relevante (40 puncte)
        score += self._check_keywords(user_lower, q_type)
        
        if user_lower == correct_lower: 
            score = 100

        # Limitează scorul la 100
        score = min(100, score)
        
        # Determină feedback-ul
        feedback = self._get_feedback(score)
        
        return {
            'score': score,
            'feedback': feedback
        }
    
    def _check_main_algorithm(self, user_answer, correct_answer):
        """Verifică dacă algoritmul principal este menționat"""
        for algo in self.main_algorithms:
            if algo in user_answer and algo in correct_answer:
                return 50
        return 0
    
    def _check_keywords(self, user_answer, q_type):
        """Verifică cuvintele cheie relevante pentru tipul întrebării"""
        q_keywords = self.keywords.get(q_type, [])
        keyword_count = sum(1 for kw in q_keywords if kw in user_answer)
        return min(50, keyword_count * 10)
    
    def _get_feedback(self, score):
        """Returnează feedback-ul corespunzător scorului"""
        for threshold, feedback in self.feedback_levels:
            if score >= threshold:
                return feedback
        return self.feedback_levels[-1][1]