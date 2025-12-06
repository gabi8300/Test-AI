"""
Evaluator pentru răspunsurile utilizatorilor
ACTUALIZAT cu suport pentru Nash Equilibrium
"""
import re
import json

class QuestionEvaluator:
    """Clasă responsabilă pentru evaluarea răspunsurilor"""
    
    def __init__(self):
        # Lista de termeni de negație
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
            ],
            'nash': [
                'nash', 'echilibru', 'equilibrium', 'equilibria',
                'pur', 'pure', 'mixt', 'mixed',
                'strategie', 'strategy', 'strategies',
                'plata', 'plată', 'payoff', 'payoffs',
                'jucator', 'jucător', 'player'
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
            dict: Dicționar cu score, feedback
        """
        # Gestionăm cazul în care user_answer este None sau gol
        if not user_answer or not user_answer.strip():
            return {
                'score': 0,
                'feedback': '❌ Niciun răspuns furnizat.'
            }
        
        # Verificăm dacă e Nash - folosim evaluator specializat
        if q_type == 'nash':
            return self._evaluate_nash(user_answer, correct_answer)
        
        # Evaluare standard pentru celelalte tipuri
        user_lower = user_answer.lower()
        correct_lower = correct_answer.lower()
        
        score = 0
        
        # Verificare exact match
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
                score = 85
                keyword_score = self._check_keywords(user_lower, q_type)
                if keyword_score > 20:
                    score = 100
            else:
                algo_score = self._check_main_algorithm(user_lower, correct_lower)
                score += algo_score
                keyword_score = self._check_keywords(user_lower, q_type)
                score += keyword_score
        
        score = min(100, score)
        feedback = self._get_feedback(score)
        
        return {
            'score': score,
            'feedback': feedback
        }
    
    # ==================== EVALUARE NASH ====================
    def _evaluate_nash(self, user_answer, correct_answer):
        """Evaluare specializată pentru Nash Equilibrium"""
        user_lower = user_answer.lower()
        correct_lower = correct_answer.lower()
        
        score = 0
        
        # 1. Verifică dacă utilizatorul identifică corect existența/absența Nash
        has_nash_correct = 'nu există' in correct_lower or 'nu exista' in correct_lower
        user_says_no_nash = any(phrase in user_lower for phrase in [
            'nu există', 'nu exista', 'fără', 'fara', 'niciun', 'no nash', 'no pure nash'
        ])
        user_says_yes_nash = any(phrase in user_lower for phrase in [
            'există', 'exista', 'da', 'yes', 'există un', 'există echilibru'
        ])
        
        # Verificare răspuns la existență
        if has_nash_correct and user_says_no_nash:
            score += 50  # Identificare corectă că NU există
        elif not has_nash_correct and user_says_yes_nash:
            score += 30  # Identificare corectă că există
        elif not has_nash_correct and not user_says_no_nash:
            score += 10  # Nu spune explicit "nu", dar nici nu neagă
        
        # 2. Dacă există Nash, verifică strategiile menționate
        if 'da,' in correct_lower or 'da.' in correct_lower:
            # Extragem perechile de strategii din răspunsul corect
            correct_pairs = self._extract_strategy_pairs(correct_answer)
            user_pairs = self._extract_strategy_pairs(user_answer)
            
            if len(correct_pairs) > 0:
                # Calculăm câte perechi corecte a identificat
                matching_pairs = 0
                for cp in correct_pairs:
                    for up in user_pairs:
                        if self._pairs_match(cp, up):
                            matching_pairs += 1
                            break
                
                if matching_pairs == len(correct_pairs):
                    score += 50  # Toate perechile corecte
                elif matching_pairs > 0:
                    score += int(50 * matching_pairs / len(correct_pairs))
        
        # 3. Verificăm termeni cheie Nash
        nash_terms = ['nash', 'echilibru', 'strategie', 'plata', 'plată', 'jucator', 'jucător']
        found_terms = sum(1 for term in nash_terms if term in user_lower)
        score += min(20, found_terms * 5)
        
        score = min(100, score)
        feedback = self._get_feedback(score)
        
        return {
            'score': score,
            'feedback': feedback
        }
    
    def _extract_strategy_pairs(self, text):
        """Extrage perechile de strategii din text, ex: (A1, B2)"""
        # Pattern pentru perechi de forma (A1, B2) sau A1,B2 sau (A1,B2)
        pattern = r'\(?\s*([A-Z]\d+)\s*,\s*([A-Z]\d+)\s*\)?'
        matches = re.findall(pattern, text, re.IGNORECASE)
        return [(m[0].upper(), m[1].upper()) for m in matches]
    
    def _pairs_match(self, pair1, pair2):
        """Verifică dacă două perechi de strategii sunt identice"""
        return pair1[0] == pair2[0] and pair1[1] == pair2[1]
    
    # ==================== METODE EXISTENTE (NESCHIMBATE) ====================
    def _extract_required_terms(self, correct_answer):
        """Extrage termenii obligatorii din răspunsul corect"""
        required = []
        for algo_name, variants in self.main_algorithms.items():
            for variant in variants:
                if variant in correct_answer:
                    required.append(variants[0])
                    break
        
        seen = set()
        unique_required = []
        for term in required:
            if term not in seen:
                seen.add(term)
                unique_required.append(term)
        
        return unique_required

    def _has_positive_mention(self, text, keywords):
        """Verifică dacă vreunul din cuvintele cheie apare în text FĂRĂ să fie negat"""
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
        """Verifică dacă răspunsul utilizatorului este echivalent cu cel corect"""
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
        """Verifică dacă algoritmul principal este menționat"""
        correct_algorithms = []
        for algo_name, variants in self.main_algorithms.items():
            if any(variant in correct_answer for variant in variants):
                correct_algorithms.append(algo_name)
        
        if not correct_algorithms:
            return 0
        
        matched_count = 0
        for algo_name in correct_algorithms:
            variants = self.main_algorithms[algo_name]
            if self._has_positive_mention(user_answer, variants):
                matched_count += 1
        
        if len(correct_algorithms) == 0:
            return 0
        
        proportion = matched_count / len(correct_algorithms)
        return int(50 * proportion)
    
    def _check_keywords(self, user_answer, q_type):
        """Verifică cuvintele cheie relevante"""
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