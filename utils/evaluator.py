"""
Evaluator pentru răspunsurile utilizatorilor
"""
import re

class QuestionEvaluator:
    """Clasă responsabilă pentru evaluarea răspunsurilor"""
    
    def __init__(self):
        # Lista de termeni de negație pentru a evita false-positives
        self.negations = [
            'nu', 'not', 'fara', 'fără', 'without', 'nici', 'niciun', 'nicio', 
            'never', 'avoid', 'exclude', 'bad', 'gresit', 'greșit', 'wrong'
        ]

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
            # Acum folosim verificarea de context (fără negații)
            algo_score = self._check_main_algorithm(user_lower, correct_lower)
            score += algo_score
            
            # 2. Verifică cuvinte cheie relevante (40 puncte)
            # Și aici verificăm contextul
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

    def _has_positive_mention(self, text, keywords):
        """
        Verifică dacă vreunul din cuvintele cheie apare în text FĂRĂ să fie negat.
        Ex: "nu BFS" -> False, "BFS este bun" -> True
        """
        for kw in keywords:
            # Găsim cuvântul cheie ca un cuvânt întreg (\b)
            # re.escape e necesar pentru caractere speciale (gen + sau .)
            pattern = r'\b' + re.escape(kw) + r'\b'
            
            # Căutăm toate aparițiile
            matches = list(re.finditer(pattern, text))
            
            if not matches:
                continue
                
            for match in matches:
                start, end = match.span()
                
                # Definim o fereastră de context (ex: 25 caractere înainte și după)
                # "Nu BFS" (negare înainte) sau "BFS nu e bun" (negare după)
                ctx_start = max(0, start - 25)
                ctx_end = min(len(text), end + 25)
                
                context_before = text[ctx_start:start]
                context_after = text[end:ctx_end]
                
                # 1. Verificăm negații ÎNAINTE (ex: "fara bfs", "nu bfs")
                # Căutăm negația ca un cuvânt întreg
                is_negated_before = any(re.search(r'\b' + n + r'\b', context_before) for n in self.negations)
                
                # 2. Verificăm negații DUPĂ (ex: "bfs nu este...")
                # Verificăm doar primele 2-3 cuvinte de după, pentru a prinde "nu"-ul legat de subiect
                first_words_after = context_after.split()[:3]
                is_negated_after = any(n in first_words_after for n in ['nu', 'not', 'isnt', "isn't"])
                
                # Dacă găsim MĂCAR O apariție care NU e negată, considerăm că e o mențiune pozitivă
                if not is_negated_before and not is_negated_after:
                    return True
                    
        return False
    
    def _is_equivalent_answer(self, user_answer, correct_answer):
        """
        Verifică dacă răspunsul utilizatorului este echivalent cu cel corect
        """
        if user_answer == correct_answer:
            return True
        
        for algo_name, variants in self.main_algorithms.items():
            # Verifică dacă userul menționează pozitiv algoritmul corect
            user_has = self._has_positive_mention(user_answer, variants)
            correct_has = any(variant in correct_answer for variant in variants)
            
            if user_has and correct_has:
                # Verificăm contradicțiile
                other_algos = [v for name, vs in self.main_algorithms.items() 
                            if name != algo_name for v in vs]
                
                # Dacă menționează și alți algoritmi, ne asigurăm că îi neagă sau nu îi menționează pozitiv
                # (Simplificare: verificăm doar dacă menționează pozitiv algoritmul greșit)
                has_contradiction = self._has_positive_mention(user_answer, other_algos)
                
                if not has_contradiction:
                    return True
        
        return False

    def _check_main_algorithm(self, user_answer, correct_answer):
        """Verifică dacă algoritmul principal este menționat (și nu e negat)"""
        for algo_name, variants in self.main_algorithms.items():
            correct_has_algo = any(variant in correct_answer for variant in variants)
            
            # Aici folosim noua verificare de context
            user_has_algo = self._has_positive_mention(user_answer, variants)
            
            if correct_has_algo and user_has_algo:
                return 60
        
        return 0
    
    def _check_keywords(self, user_answer, q_type):
        """Verifică cuvintele cheie relevante (contextual)"""
        q_keywords = self.keywords.get(q_type, [])
        found_groups = set()
        
        for kw in q_keywords:
            # Verificăm dacă keyword-ul apare într-un context pozitiv
            if self._has_positive_mention(user_answer, [kw]):
                base_concept = kw.split()[0]
                found_groups.add(base_concept)
        
        # 15 puncte per concept găsit (max 40)
        keyword_score = min(40, len(found_groups) * 15)
        return keyword_score
    
    def _get_feedback(self, score):
        """Returnează feedback-ul corespunzător scorului"""
        for threshold, feedback in self.feedback_levels:
            if score >= threshold:
                return feedback
        return self.feedback_levels[-1][1]