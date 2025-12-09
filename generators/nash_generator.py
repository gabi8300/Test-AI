"""
Generator pentru jocuri în forma normală (Nash Equilibrium)
Cu tabel formatat simplu (fără Unicode)
"""
import random
import json

class NashGameGenerator:
    """Generează jocuri aleatorii și calculează echilibrele Nash pure"""
    
    def __init__(self):
        self.game_counter = 0
    
    def find_pure_nash_equilibria(self, payoff_matrix):
        """
        Găsește TOATE echilibrele Nash pure pentru o matrice de plată
        
        Returns:
            list: [(row_idx, col_idx), ...] - toate echilibrele Nash găsite
        """
        rows = payoff_matrix['rows']
        cols = payoff_matrix['cols']
        payoffs = payoff_matrix['payoffs']
        
        n_rows = len(rows)
        n_cols = len(cols)
        
        nash_equilibria = []
        
        for i in range(n_rows):
            for j in range(n_cols):
                is_nash = True
                
                # Verifică Jucătorul 1
                current_p1_payoff = payoffs[i][j][0]
                for alt_i in range(n_rows):
                    if alt_i != i and payoffs[alt_i][j][0] > current_p1_payoff:
                        is_nash = False
                        break
                
                if not is_nash:
                    continue
                
                # Verifică Jucătorul 2
                current_p2_payoff = payoffs[i][j][1]
                for alt_j in range(n_cols):
                    if alt_j != j and payoffs[i][alt_j][1] > current_p2_payoff:
                        is_nash = False
                        break
                
                if is_nash:
                    nash_equilibria.append((i, j))
        
        return nash_equilibria
    
    def generate_random_game(self, n_rows=3, n_cols=3, min_payoff=-5, max_payoff=10):
        """Generează un joc COMPLET ALEATORIU"""
        rows = [f'A{i+1}' for i in range(n_rows)]
        cols = [f'B{i+1}' for i in range(n_cols)]
        
        # Generăm plăți ALEATORII
        payoffs = []
        for i in range(n_rows):
            row = []
            for j in range(n_cols):
                p1 = random.randint(min_payoff, max_payoff)
                p2 = random.randint(min_payoff, max_payoff)
                row.append((p1, p2))
            payoffs.append(row)
        
        game = {
            'rows': rows,
            'cols': cols,
            'payoffs': payoffs
        }
        
        # CALCULĂM Nash cu funcția
        nash_eq = self.find_pure_nash_equilibria(game)
        
        return game, nash_eq
    
    def format_game_as_table(self, game):
        """Formatează jocul ca tabel SIMPLU (fără Unicode)"""
        rows = game['rows']
        cols = game['cols']
        payoffs = game['payoffs']
        
        text = "\nMatricea de plata:\n\n"
        
        # Header
        text += "      "
        for col in cols:
            text += f"  {col:^8}  "
        text += "\n"
        
        # Separator
        text += "    " + "-" * (12 * len(cols) + 4) + "\n"
        
        # Randuri
        for i, row_name in enumerate(rows):
            text += f" {row_name} | "
            for j in range(len(cols)):
                p1, p2 = payoffs[i][j]
                text += f" ({p1:>2},{p2:>2})  "
            text += "\n"
        
        text += "\nNotatie: (Plata Jucator 1, Plata Jucator 2)"
        return text
    
    def format_nash_answer(self, game, nash_equilibria):
        """Formatează răspunsul corect"""
        if len(nash_equilibria) == 0:
            return "Nu exista echilibru Nash pur"
        
        rows = game['rows']
        cols = game['cols']
        
        answer_parts = []
        for i, j in nash_equilibria:
            strategy_pair = f"({rows[i]}, {cols[j]})"
            payoffs = game['payoffs'][i][j]
            answer_parts.append(f"{strategy_pair} cu platile ({payoffs[0]}, {payoffs[1]})")
        
        if len(nash_equilibria) == 1:
            return f"Da, exista un echilibru Nash pur: {answer_parts[0]}"
        else:
            return f"Da, exista {len(nash_equilibria)} echilibre Nash pure: " + "; ".join(answer_parts)
    
    def generate_explanation(self, game, nash_equilibria):
        """Generează explicație detaliată"""
        rows = game['rows']
        cols = game['cols']
        payoffs = game['payoffs']
        
        explanation = "Verificare echilibru Nash:\n\n"
        explanation += "Pentru fiecare celula verificam daca ambii jucatori sunt la optimul lor.\n\n"
        
        if len(nash_equilibria) == 0:
            explanation += "Verificam cateva celule:\n"
            checked = 0
            for i in range(len(rows)):
                for j in range(len(cols)):
                    if checked >= 3:
                        break
                    p1, p2 = payoffs[i][j]
                    explanation += f"\n({rows[i]}, {cols[j]}): "
                    
                    can_improve_p1 = False
                    for alt_i in range(len(rows)):
                        if alt_i != i and payoffs[alt_i][j][0] > p1:
                            explanation += f"J1 poate imbunatati: {rows[alt_i]} -> {payoffs[alt_i][j][0]} > {p1}. "
                            can_improve_p1 = True
                            break
                    
                    if not can_improve_p1:
                        for alt_j in range(len(cols)):
                            if alt_j != j and payoffs[i][alt_j][1] > p2:
                                explanation += f"J2 poate imbunatati: {cols[alt_j]} -> {payoffs[i][alt_j][1]} > {p2}. "
                                break
                    checked += 1
                if checked >= 3:
                    break
            
            explanation += "\n\nConcluzie: Nu exista echilibru Nash pur."
        
        else:
            for idx, (i, j) in enumerate(nash_equilibria):
                explanation += f"\nEchilibru Nash {idx + 1}: ({rows[i]}, {cols[j]})\n"
                p1, p2 = payoffs[i][j]
                
                explanation += f"J1 primeste {p1}. Alternative: "
                alt_strats = []
                for alt_i in range(len(rows)):
                    if alt_i != i:
                        alt_strats.append(f"{rows[alt_i]}->{payoffs[alt_i][j][0]}")
                explanation += ", ".join(alt_strats) + f". Maximum la {rows[i]}.\n"
                
                explanation += f"J2 primeste {p2}. Alternative: "
                alt_strats = []
                for alt_j in range(len(cols)):
                    if alt_j != j:
                        alt_strats.append(f"{cols[alt_j]}->{payoffs[i][alt_j][1]}")
                explanation += ", ".join(alt_strats) + f". Maximum la {cols[j]}.\n"
            
            explanation += f"\nConcluzie: Echilibru Nash stabil."
        
        return explanation
    
    def get_all_nash_questions(self):
        """Generează întrebări Nash cu DIVERSITATE ALEATORIE"""
        questions = []
        self.game_counter = 0
        
        sizes = [
            (2, 2), (2, 3), (3, 2), (3, 3), (3, 4), (4, 3), (4, 4)
        ]
        
        for n_rows, n_cols in sizes:
            for variant in range(8):
                self.game_counter += 1
                
                game, nash_eq = self.generate_random_game(
                    n_rows=n_rows,
                    n_cols=n_cols,
                    min_payoff=-5,
                    max_payoff=10
                )
                
                game_text = self.format_game_as_table(game)
                correct_answer = self.format_nash_answer(game, nash_eq)
                explanation = self.generate_explanation(game, nash_eq)
                
                nash_count = len(nash_eq)
                if nash_count == 0:
                    desc = f"{n_rows}x{n_cols} fara Nash"
                elif nash_count == 1:
                    desc = f"{n_rows}x{n_cols} cu 1 Nash"
                else:
                    desc = f"{n_rows}x{n_cols} cu {nash_count} Nash"
                
                game_data_json = json.dumps(game)
                nash_eq_json = json.dumps(nash_eq)
                
                questions.append({
                    'type': 'nash',
                    'title': f'Nash Equilibrium - {desc} (V{variant + 1})',
                    'question': f'''Pentru urmatorul joc in forma normala:

{game_text}

Intrebari:
1. Exista echilibru Nash pur?
2. Daca da, care este/sunt acesta/acestea?

Nota: Un echilibru Nash pur este o pereche de strategii unde niciun jucator nu poate imbunatati unilateral plata sa.''',
                    'correct_answer': correct_answer,
                    'explanation': explanation,
                    'game_data': game_data_json,
                    'nash_equilibria': nash_eq_json
                })
        
        return questions


if __name__ == "__main__":
    gen = NashGameGenerator()
    
    print("=" * 70)
    print("TEST: Tabel Simplu (fara Unicode)")
    print("=" * 70)
    
    game, nash_eq = gen.generate_random_game(3, 3)
    print(gen.format_game_as_table(game))
    print(f"\nNash gasit: {len(nash_eq)} echilibre")
    if nash_eq:
        for idx, (i, j) in enumerate(nash_eq):
            print(f"  {idx+1}. ({game['rows'][i]}, {game['cols'][j]})")