"""
Generator pentru jocuri în forma normală (Nash Equilibrium)
Fișier: generators/nash_generator.py
"""
import random
import json

class NashGameGenerator:
    """Generează jocuri în forma normală și calculează echilibrele Nash pure"""
    
    def __init__(self):
        self.game_counter = 0
    
    def find_pure_nash_equilibria(self, payoff_matrix):
        """
        Găsește toate echilibrele Nash pure pentru o matrice de plată
        
        Args:
            payoff_matrix: dict cu structura:
                {
                    'rows': ['A1', 'A2', ...],
                    'cols': ['B1', 'B2', ...],
                    'payoffs': [
                        [(p1_row0_col0, p2_row0_col0), (p1_row0_col1, p2_row0_col1), ...],
                        [(p1_row1_col0, p2_row1_col0), (p1_row1_col1, p2_row1_col1), ...],
                        ...
                    ]
                }
        
        Returns:
            list: Lista de echilibre Nash pure [(row_idx, col_idx), ...]
        """
        rows = payoff_matrix['rows']
        cols = payoff_matrix['cols']
        payoffs = payoff_matrix['payoffs']
        
        n_rows = len(rows)
        n_cols = len(cols)
        
        nash_equilibria = []
        
        # Pentru fiecare celulă din matrice
        for i in range(n_rows):
            for j in range(n_cols):
                is_nash = True
                
                # Verifică dacă jucătorul 1 (rânduri) poate îmbunătăți
                current_p1_payoff = payoffs[i][j][0]
                for alt_i in range(n_rows):
                    if alt_i != i and payoffs[alt_i][j][0] > current_p1_payoff:
                        is_nash = False
                        break
                
                if not is_nash:
                    continue
                
                # Verifică dacă jucătorul 2 (coloane) poate îmbunătăți
                current_p2_payoff = payoffs[i][j][1]
                for alt_j in range(n_cols):
                    if alt_j != j and payoffs[i][alt_j][1] > current_p2_payoff:
                        is_nash = False
                        break
                
                if is_nash:
                    nash_equilibria.append((i, j))
        
        return nash_equilibria
    
    def generate_game_with_nash(self, n_rows=3, n_cols=3, ensure_nash=True, num_nash=1):
        """
        Generează un joc cu sau fără echilibru Nash
        
        Args:
            n_rows: număr de strategii pentru jucătorul 1
            n_cols: număr de strategii pentru jucătorul 2
            ensure_nash: dacă True, garantează existența echilibrului Nash
            num_nash: numărul dorit de echilibre Nash (dacă ensure_nash=True)
        """
        max_attempts = 100
        
        for attempt in range(max_attempts):
            # Generăm matrice random
            rows = [f'A{i+1}' for i in range(n_rows)]
            cols = [f'B{i+1}' for i in range(n_cols)]
            
            # Generăm plăți random între -5 și 10
            payoffs = []
            for i in range(n_rows):
                row = []
                for j in range(n_cols):
                    p1 = random.randint(-5, 10)
                    p2 = random.randint(-5, 10)
                    row.append((p1, p2))
                payoffs.append(row)
            
            game = {
                'rows': rows,
                'cols': cols,
                'payoffs': payoffs
            }
            
            # Găsim echilibrele Nash
            nash_eq = self.find_pure_nash_equilibria(game)
            
            # Verificăm dacă satisface cerințele
            if ensure_nash and len(nash_eq) == num_nash:
                return game, nash_eq
            elif not ensure_nash and len(nash_eq) == 0:
                return game, nash_eq
        
        # Dacă nu reușim random, generăm un joc garantat
        if ensure_nash:
            return self._generate_guaranteed_nash(n_rows, n_cols, num_nash)
        else:
            return self._generate_guaranteed_no_nash(n_rows, n_cols)
    
    def _generate_guaranteed_nash(self, n_rows, n_cols, num_nash):
        """Generează un joc cu echilibru Nash garantat"""
        rows = [f'A{i+1}' for i in range(n_rows)]
        cols = [f'B{i+1}' for i in range(n_cols)]
        
        # Inițializăm cu valori mici
        payoffs = [[(random.randint(0, 3), random.randint(0, 3)) 
                    for _ in range(n_cols)] for _ in range(n_rows)]
        
        # Alegem celule random pentru echilibrele Nash
        nash_positions = []
        available_positions = [(i, j) for i in range(n_rows) for j in range(n_cols)]
        random.shuffle(available_positions)
        
        for _ in range(min(num_nash, len(available_positions))):
            nash_i, nash_j = available_positions.pop()
            nash_positions.append((nash_i, nash_j))
            
            # Facem această celulă să fie echilibru Nash
            # Setăm plăți mari pentru ambii jucători
            payoffs[nash_i][nash_j] = (10, 10)
            
            # Asigurăm că nicio altă strategie nu e mai bună
            for i in range(n_rows):
                if i != nash_i:
                    payoffs[i][nash_j] = (random.randint(0, 8), payoffs[i][nash_j][1])
            
            for j in range(n_cols):
                if j != nash_j:
                    payoffs[nash_i][j] = (payoffs[nash_i][j][0], random.randint(0, 8))
        
        game = {'rows': rows, 'cols': cols, 'payoffs': payoffs}
        return game, nash_positions
    
    def _generate_guaranteed_no_nash(self, n_rows, n_cols):
        """Generează un joc fără echilibru Nash pur (matching pennies style)"""
        rows = [f'A{i+1}' for i in range(n_rows)]
        cols = [f'B{i+1}' for i in range(n_cols)]
        
        # Generăm un pattern "matching pennies" extins
        payoffs = []
        for i in range(n_rows):
            row = []
            for j in range(n_cols):
                # Pattern care asigură că nu există Nash pur
                if (i + j) % 2 == 0:
                    p1, p2 = 5, -5
                else:
                    p1, p2 = -5, 5
                row.append((p1, p2))
            payoffs.append(row)
        
        game = {'rows': rows, 'cols': cols, 'payoffs': payoffs}
        return game, []
    
    def format_game_as_text(self, game):
        """Formatează jocul ca text pentru întrebare"""
        rows = game['rows']
        cols = game['cols']
        payoffs = game['payoffs']
        
        # Header
        text = "Matricea de plată:\n\n"
        text += "        " + "  ".join([f"{col:>8}" for col in cols]) + "\n"
        text += "        " + "-" * (10 * len(cols)) + "\n"
        
        # Rânduri
        for i, row_name in enumerate(rows):
            text += f"{row_name:>6} |"
            for j in range(len(cols)):
                p1, p2 = payoffs[i][j]
                text += f" ({p1:>2},{p2:>2}) "
            text += "\n"
        
        text += "\nNotație: (Plata Jucător 1, Plata Jucător 2)"
        return text
    
    def format_nash_answer(self, game, nash_equilibria):
        """Formatează răspunsul corect"""
        if len(nash_equilibria) == 0:
            return "Nu există echilibru Nash pur."
        
        rows = game['rows']
        cols = game['cols']
        
        answer_parts = []
        for i, j in nash_equilibria:
            strategy_pair = f"({rows[i]}, {cols[j]})"
            payoffs = game['payoffs'][i][j]
            answer_parts.append(f"{strategy_pair} cu plățile ({payoffs[0]}, {payoffs[1]})")
        
        if len(nash_equilibria) == 1:
            return f"Da, există un echilibru Nash pur: {answer_parts[0]}"
        else:
            return f"Da, există {len(nash_equilibria)} echilibre Nash pure: " + "; ".join(answer_parts)
    
    def generate_explanation(self, game, nash_equilibria):
        """Generează explicație detaliată"""
        rows = game['rows']
        cols = game['cols']
        payoffs = game['payoffs']
        
        explanation = "Verificare echilibru Nash:\n\n"
        explanation += "Un echilibru Nash pur există când niciun jucător nu poate îmbunătăți plata sa schimbând unilateral strategia.\n\n"
        
        if len(nash_equilibria) == 0:
            explanation += "Verificăm fiecare celulă:\n"
            # Arătăm câteva exemple de celule care NU sunt Nash
            for i in range(min(2, len(rows))):
                for j in range(min(2, len(cols))):
                    p1, p2 = payoffs[i][j]
                    explanation += f"\n({rows[i]}, {cols[j]}): "
                    
                    # Verificăm dacă jucătorul 1 poate îmbunătăți
                    can_improve_p1 = False
                    for alt_i in range(len(rows)):
                        if alt_i != i and payoffs[alt_i][j][0] > p1:
                            explanation += f"J1 poate alege {rows[alt_i]} pentru plată {payoffs[alt_i][j][0]} > {p1}. "
                            can_improve_p1 = True
                            break
                    
                    # Verificăm dacă jucătorul 2 poate îmbunătăți
                    if not can_improve_p1:
                        for alt_j in range(len(cols)):
                            if alt_j != j and payoffs[i][alt_j][1] > p2:
                                explanation += f"J2 poate alege {cols[alt_j]} pentru plată {payoffs[i][alt_j][1]} > {p2}. "
                                break
            
            explanation += "\n\nConcluzie: Nu există nicio celulă unde ambii jucători sunt simultan la optimul lor."
        
        else:
            for idx, (i, j) in enumerate(nash_equilibria):
                explanation += f"\nEchilibru Nash {idx + 1}: ({rows[i]}, {cols[j]})\n"
                p1, p2 = payoffs[i][j]
                
                explanation += f"- Jucătorul 1 primește {p1}. "
                explanation += "Strategii alternative: "
                alt_strats = []
                for alt_i in range(len(rows)):
                    if alt_i != i:
                        alt_strats.append(f"{rows[alt_i]}→{payoffs[alt_i][j][0]}")
                explanation += ", ".join(alt_strats) + f". Nicio îmbunătățire posibilă.\n"
                
                explanation += f"- Jucătorul 2 primește {p2}. "
                explanation += "Strategii alternative: "
                alt_strats = []
                for alt_j in range(len(cols)):
                    if alt_j != j:
                        alt_strats.append(f"{cols[alt_j]}→{payoffs[i][alt_j][1]}")
                explanation += ", ".join(alt_strats) + ". Nicio îmbunătățire posibilă.\n"
        
        return explanation
    
    def get_all_nash_questions(self):
        """Generează toate variantele de întrebări Nash"""
        questions = []
        self.game_counter = 0
        
        # Configurații diferite de jocuri
        configs = [
            # (rows, cols, has_nash, num_nash, description)
            (2, 2, True, 1, "2x2 cu 1 Nash"),
            (2, 2, False, 0, "2x2 fără Nash"),
            (2, 3, True, 1, "2x3 cu 1 Nash"),
            (2, 3, False, 0, "2x3 fără Nash"),
            (3, 2, True, 1, "3x2 cu 1 Nash"),
            (3, 3, True, 1, "3x3 cu 1 Nash"),
            (3, 3, True, 2, "3x3 cu 2 Nash"),
            (3, 3, False, 0, "3x3 fără Nash"),
            (3, 4, True, 1, "3x4 cu 1 Nash"),
            (4, 3, True, 1, "4x3 cu 1 Nash"),
        ]
        
        # Generăm multiple variante pentru fiecare configurație
        for rows, cols, has_nash, num_nash, desc in configs:
            # Generăm 3-5 variante pentru fiecare configurație
            num_variants = 4 if has_nash else 3
            
            for variant in range(num_variants):
                self.game_counter += 1
                
                game, nash_eq = self.generate_game_with_nash(
                    n_rows=rows, 
                    n_cols=cols, 
                    ensure_nash=has_nash,
                    num_nash=num_nash
                )
                
                game_text = self.format_game_as_text(game)
                correct_answer = self.format_nash_answer(game, nash_eq)
                explanation = self.generate_explanation(game, nash_eq)
                
                # Serializăm jocul pentru stocare
                game_data_json = json.dumps(game)
                nash_eq_json = json.dumps(nash_eq)
                
                questions.append({
                    'type': 'nash',
                    'title': f'Nash Equilibrium - {desc} (V{variant + 1})',
                    'question': f'''Pentru următorul joc în forma normală:

{game_text}

Întrebări:
1. Există echilibru Nash pur?
2. Dacă da, care este/sunt acesta/acestea?

Notă: Un echilibru Nash pur este o pereche de strategii (s₁*, s₂*) astfel încât:
- Jucătorul 1 nu poate obține o plată mai mare schimbând doar s₁* (păstrând s₂* fix)
- Jucătorul 2 nu poate obține o plată mai mare schimbând doar s₂* (păstrând s₁* fix)''',
                    'correct_answer': correct_answer,
                    'explanation': explanation,
                    'game_data': game_data_json,
                    'nash_equilibria': nash_eq_json
                })
        
        return questions