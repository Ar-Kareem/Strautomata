
def policy(state: list[list[object]], role: str) -> str:
    """AI policy for Trifecta using minimax with alpha-beta pruning."""
    
    # Parse state into cell dictionary
    cells = {}
    for prop in state:
        if prop[0] == "cell" and len(prop) >= 4:
            cells[(prop[1], prop[2])] = prop[3]
    
    # Find empty cells
    empty_cells = [(r, c) for r in "123" for c in "123" if cells.get((r, c)) == "b"]
    
    if not empty_cells:
        return "mark(1,1)"
    
    # All 12 winning lines: rows, columns, suits, values
    lines = [
        [("1","1"),("1","2"),("1","3")], [("2","1"),("2","2"),("2","3")], [("3","1"),("3","2"),("3","3")],
        [("1","1"),("2","1"),("3","1")], [("1","2"),("2","2"),("3","2")], [("1","3"),("2","3"),("3","3")],
        [("1","1"),("2","3"),("3","2")], [("1","2"),("2","1"),("3","3")], [("1","3"),("2","2"),("3","1")],
        [("1","1"),("2","2"),("3","3")], [("1","2"),("2","3"),("3","1")], [("1","3"),("2","1"),("3","2")],
    ]
    
    opp = "o" if role == "x" else "x"
    
    def count(line, player):
        return sum(1 for c in line if cells.get(c) == player)
    
    def get_winner():
        for player in ["x", "o"]:
            for line in lines:
                if count(line, player) == 3:
                    return player
        return None
    
    def evaluate_cell(cell, player):
        """Heuristic for move ordering."""
        score = 0
        for line in lines:
            if cell in line:
                my = count(line, player)
                opp_c = count(line, "o" if player == "x" else "x")
                if opp_c == 0:
                    score += (my + 1) ** 2
        return score
    
    def minimax(depth, is_maximizing, alpha, beta):
        winner = get_winner()
        if winner == role:
            return 10 - depth
        if winner == opp:
            return depth - 10
        
        empties = [(r, c) for r in "123" for c in "123" if cells.get((r, c)) == "b"]
        if not empties:
            return 0
        
        current_player = role if is_maximizing else opp
        empties.sort(key=lambda c: -evaluate_cell(c, current_player))
        
        if is_maximizing:
            max_eval = -float('inf')
            for cell in empties:
                cells[cell] = role
                eval_score = minimax(depth + 1, False, alpha, beta)
                cells[cell] = "b"
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for cell in empties:
                cells[cell] = opp
                eval_score = minimax(depth + 1, True, alpha, beta)
                cells[cell] = "b"
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    # Order initial moves by heuristic
    empty_cells.sort(key=lambda c: -evaluate_cell(c, role))
    
    best_cell = empty_cells[0]
    best_score = -float('inf')
    
    for cell in empty_cells:
        cells[cell] = role
        score = minimax(0, False, -float('inf'), float('inf'))
        cells[cell] = "b"
        
        if score > best_score:
            best_score = score
            best_cell = cell
    
    return f"mark({best_cell[0]},{best_cell[1]})"
