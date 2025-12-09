"""
Evaluator SIMPLU pentru Nash Equilibrium cu checkboxuri
Logică clară: compară liste de celule bifate
"""
import re
import json

class QuestionEvaluator:
    """Clasă responsabilă pentru evaluarea răspunsurilor"""
    
    def __init__(self):
        self.negations = [
            'nu', 'not', 'fara', 'fără', 'without', 'nici', 'niciun', 'nicio', 
            'never', 'avoid', 'exclude', 'bad', 'gresit', 'greșit', 'wrong'
        ]

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
        
        self.main_algorithms = {
            'backtracking': ['backtracking', 'back tracking', 'back-tracking'],
            'bfs': ['bfs', 'breadth first', 'breadth-first', 'breadth first search'],
            'dfs': ['dfs', 'depth first', 'depth-first', 'depth first search'],
            'greedy': ['greedy', 'lacom', 'greedy algorithm'],
            'warnsdorff': ['warnsdorff', 'warnsdorff\'s', 'warnsdorff heuristic'],
            'recursiv': ['recursiv', 'recursive', 'recursie', 'recursion']
        }

        self.feedback_levels = [
            (90, '🎉 Excelent! Răspuns complet și corect!'),
            (70, '👍 Foarte bine! Acoperă punctele principale.'),
            (50, '👌 Bine! Parțial corect, dar lipsesc detalii.'),
            (30, '🤔 Satisfăcător. Identifică strategia, dar incomplet.'),
            (0, '❌ Nesatisfăcător. Nu acoperă cerințele.')
        ]
    
    def evaluate(self, user_answer, correct_answer, q_type, question_data=None):
        """Evaluează răspunsul utilizatorului"""
        if not user_answer or not user_answer.strip():
            return {
                'score': 0,
                'feedback': '❌ Niciun răspuns furnizat.'
            }
        
        if q_type == 'nash':
            return self._evaluate_nash_checkbox(user_answer, question_data)
        
        # Evaluare standard pentru celelalte tipuri
        user_lower = user_answer.lower()
        correct_lower = correct_answer.lower()
        
        score = 0
        
        if self._is_equivalent_answer(user_lower, correct_lower):
            score = 100
        else:
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
    
    # ==================== EVALUARE NASH CU CHECKBOXURI ====================
    def _evaluate_nash_checkbox(self, user_answer, question_data):
        """
        Evaluare SIMPLĂ cu checkboxuri
        
        user_answer: JSON string cu format:
        {
            "no_nash": true/false,
            "selected_cells": [{"i": 0, "j": 1}, {"i": 2, "j": 3}]
        }
        """
        try:
            user_data = json.loads(user_answer)
        except:
            return {'score': 0, 'feedback': '❌ Format răspuns invalid.'}
        
        # Extragem Nash-urile corecte
        correct_nash_indices = []
        if question_data and 'nash_equilibria' in question_data:
            try:
                correct_nash_indices = json.loads(question_data['nash_equilibria'])
            except:
                pass
        
        no_nash_correct = (len(correct_nash_indices) == 0)
        user_says_no_nash = user_data.get('no_nash', False)
        user_selected_cells = user_data.get('selected_cells', [])
        
        # Convertim celulele user la set de tuple pentru comparație
        user_cells_set = set()
        for cell in user_selected_cells:
            user_cells_set.add((cell['i'], cell['j']))
        
        # Convertim Nash-urile corecte la set
        correct_cells_set = set()
        for i, j in correct_nash_indices:
            correct_cells_set.add((i, j))
        
        # LOGICA SIMPLĂ:
        
        # CAZUL 1: NU EXISTĂ Nash
        if no_nash_correct:
            if user_says_no_nash and len(user_selected_cells) == 0:
                return {'score': 100, 'feedback': '🎉 Excelent! Răspuns corect!'}
            elif len(user_selected_cells) > 0:
                return {'score': 0, 'feedback': '❌ Greșit. Nu există echilibru Nash în acest joc.'}
            else:
                return {'score': 50, 'feedback': '🤔 Răspuns ambiguu.'}
        
        # CAZUL 2: EXISTĂ Nash
        if user_says_no_nash:
            return {'score': 0, 'feedback': '❌ Greșit. Există echilibru Nash în acest joc.'}
        
        if len(user_selected_cells) == 0:
            return {'score': 20, 'feedback': '❌ Nu ai selectat nicio celulă Nash.'}
        
        # Comparăm seturile
        correct_count = len(user_cells_set & correct_cells_set)  # Intersecție
        wrong_count = len(user_cells_set - correct_cells_set)    # Diferență
        total_nash = len(correct_cells_set)
        
        if correct_count == total_nash and wrong_count == 0:
            return {'score': 100, 'feedback': '🎉 Excelent! Toate echilibrele Nash identificate corect!'}
        elif correct_count == total_nash and wrong_count > 0:
            return {'score': 70, 'feedback': f'👍 Ai găsit toate Nash-urile corecte, dar ai selectat și {wrong_count} greșite.'}
        elif correct_count > 0 and wrong_count == 0:
            percentage = int((correct_count / total_nash) * 100)
            return {'score': percentage, 'feedback': f'👌 Parțial corect. Ai găsit {correct_count} din {total_nash} Nash-uri.'}
        elif correct_count > 0:
            percentage = max(30, int((correct_count / total_nash) * 60))
            return {'score': percentage, 'feedback': f'🤔 Ai găsit {correct_count} Nash-uri corecte, dar și {wrong_count} greșite.'}
        else:
            return {'score': 10, 'feedback': '❌ Celulele selectate sunt toate greșite.'}
    
    # ==================== METODE PENTRU CELELALTE TIPURI ====================
    def _extract_required_terms(self, correct_answer):
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
        q_keywords = self.keywords.get(q_type, [])
        found_groups = set()
        
        for kw in q_keywords:
            if self._has_positive_mention(user_answer, [kw]):
                base_concept = kw.split()[0]
                found_groups.add(base_concept)
        
        keyword_score = min(40, len(found_groups) * 15)
        return keyword_score
    
    def _get_feedback(self, score):
        for threshold, feedback in self.feedback_levels:
            if score >= threshold:
                return feedback
        return self.feedback_levels[-1][1]