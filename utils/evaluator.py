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
    
    def evaluate(self, user_answer, correct_answer, q_type):
        """
        Evaluează răspunsul utilizatorului
        
        Args:
            user_answer (str): Răspunsul utilizatorului
            correct_answer (str): Răspunsul corect
            q_type (str): Tipul întrebării
            
        Returns:
            dict: Dicționar cu score, feedback și explanation
        """
        # Gestionăm cazul în care user_answer este None sau gol
        if not user_answer or not user_answer.strip():
            return {
                'score': 0,
                'feedback': '❌ Niciun răspuns furnizat.'
            }
        
        user_lower = user_answer.lower()
        correct_lower = correct_answer.lower()
        
        score = 0
        
        # Verificare exact match (considerând și variante)
        if self._is_equivalent_answer(user_lower, correct_lower):
            score = 100
        else:
            # Verificăm dacă răspunsul conține TOȚI termenii obligatorii
            required_terms = self._extract_required_terms(correct_lower)
            user_has_all_required = all(
                self._has_positive_mention(user_lower, [term]) 
                for term in required_terms
            )
            
            if user_has_all_required and len(required_terms) > 0:
                # Dacă are toți termenii obligatorii, scor mare
                score = 85
                
                # Verifică cuvinte cheie suplimentare pentru punctaj maxim
                keyword_score = self._check_keywords(user_lower, q_type)
                if keyword_score > 20:
                    score = 100
            else:
                # Evaluare parțială standard
                # 1. Verifică algoritmul principal (50 puncte)
                algo_score = self._check_main_algorithm(user_lower, correct_lower)
                score += algo_score
                
                # 2. Verifică cuvinte cheie relevante (50 puncte)
                keyword_score = self._check_keywords(user_lower, q_type)
                score += keyword_score
        
        # Limitează scorul la 100
        score = min(100, score)
        
        # Determină feedback-ul
        feedback = self._get_feedback(score)
        
        return {
            'score': score,
            'feedback': feedback
        }

    def _extract_required_terms(self, correct_answer):
        """
        Extrage termenii obligatorii din răspunsul corect.
        De exemplu: "Backtracking cu DFS" -> ['backtracking', 'dfs']
        """
        required = []
        
        # Verificăm pentru fiecare algoritm dacă apare în răspunsul corect
        for algo_name, variants in self.main_algorithms.items():
            for variant in variants:
                if variant in correct_answer:
                    # Adăugăm forma de bază (prima variantă)
                    required.append(variants[0])
                    break
        
        # Eliminăm duplicatele păstrând ordinea
        seen = set()
        unique_required = []
        for term in required:
            if term not in seen:
                seen.add(term)
                unique_required.append(term)
        
        return unique_required

    def _has_positive_mention(self, text, keywords):
        """
        Verifică dacă vreunul din cuvintele cheie apare în text FĂRĂ să fie negat.
        """
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            matches = list(re.finditer(pattern, text))
            
            if not matches:
                continue
                
            for match in matches:
                start, end = match.span()
                
                ctx_start = max(0, start - 25)
                ctx_end = min(len(text), end + 25)
                
                context_before = text[ctx_start:start]
                context_after = text[end:ctx_end]
                
                is_negated_before = any(re.search(r'\b' + n + r'\b', context_before) for n in self.negations)
                
                first_words_after = context_after.split()[:3]
                is_negated_after = any(n in first_words_after for n in ['nu', 'not', 'isnt', "isn't"])
                
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
            user_has = self._has_positive_mention(user_answer, variants)
            correct_has = any(variant in correct_answer for variant in variants)
            
            if user_has and correct_has:
                other_algos = [v for name, vs in self.main_algorithms.items() 
                            if name != algo_name for v in vs]
                
                has_contradiction = self._has_positive_mention(user_answer, other_algos)
                
                if not has_contradiction:
                    return True
        
        return False

    def _check_main_algorithm(self, user_answer, correct_answer):
        """
        Verifică dacă algoritmul principal este menționat (și nu e negat).
        Returnează scor bazat pe câți algoritmi corecți sunt menționați.
        """
        # Extragem toți algoritmii din răspunsul corect
        correct_algorithms = []
        for algo_name, variants in self.main_algorithms.items():
            if any(variant in correct_answer for variant in variants):
                correct_algorithms.append(algo_name)
        
        if not correct_algorithms:
            return 0
        
        # Verificăm câți algoritmi corecți sunt menționați de user
        matched_count = 0
        for algo_name in correct_algorithms:
            variants = self.main_algorithms[algo_name]
            if self._has_positive_mention(user_answer, variants):
                matched_count += 1
        
        # Calculăm scorul proporțional
        if len(correct_algorithms) == 0:
            return 0
        
        # Dacă are toți algoritmii corecți -> 50 puncte
        # Dacă are doar unul din mai mulți -> scor proporțional
        proportion = matched_count / len(correct_algorithms)
        return int(50 * proportion)
    
    def _check_keywords(self, user_answer, q_type):
        """Verifică cuvintele cheie relevante (contextual)"""
        q_keywords = self.keywords.get(q_type, [])
        found_groups = set()
        
        for kw in q_keywords:
            if self._has_positive_mention(user_answer, [kw]):
                base_concept = kw.split()[0]
                found_groups.add(base_concept)
        
        keyword_score = min(40, len(found_groups) * 15)
        return keyword_score
    
    def _get_feedback(self, score):
        """Returnează feedback-ul corespunzător scorului"""
        for threshold, feedback in self.feedback_levels:
            if score >= threshold:
                return feedback
        return self.feedback_levels[-1][1]