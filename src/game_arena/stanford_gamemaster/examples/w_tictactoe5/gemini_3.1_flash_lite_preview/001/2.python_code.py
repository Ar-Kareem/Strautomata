
def policy(state: list[list[object]], role: str) -> str:
    # Build board representation
    board = {}
    empty_cells = []
    for fact in state:
        if fact[0] == "cell":
            r, c, val = fact[1], fact[2], fact[3]
            board[(r, c)] = val
            if val == "b":
                empty_cells.append((r, c))

    opponent = "o" if role == "x" else "x"

    def check_win(b, p):
        # Rows, cols, diagonals
        lines = [
            [(str(i), str(j)) for j in ["1", "2", "3"]] for i in ["1", "2", "3"]
        ] + [
            [(str(i), str(j)) for i in ["1", "2", "3"]] for j in ["1", "2", "3"]
        ] + [
            [("1", "1"), ("2", "2"), ("3", "3")],
            [("1", "3"), ("2", "2"), ("3", "1")]
        ]
        for line in lines:
            if all(b.get(pos) == p for pos in line):
                return True
        return False

    def terminal(b):
        if check_win(b, "x") or check_win(b, "o"): return True
        if not any(b[pos] == "b" for pos in b): return True
        return False

    def utility(b):
        if check_win(b, role): return 1
        if check_win(b, opponent): return -1
        return 0

    def minimax(b, depth, is_maximizing):
        if terminal(b): return utility(b)
        
        scores = []
        for pos in [p for p in b if b[p] == "b"]:
            b[pos] = role if is_maximizing else opponent
            scores.append(minimax(b, depth + 1, not is_maximizing))
            b[pos] = "b"
        
        return max(scores) if is_maximizing else min(scores)

    best_score = -float('inf')
    best_move = None
    
    # Try all empty actions
    for pos in empty_cells:
        board[pos] = role
        score = minimax(board, 0, False)
        board[pos] = "b"
        if score > best_score:
            best_score = score
            best_move = pos
            
    if best_move is None:
        best_move = empty_cells[0]
        
    return f"mark({best_move[0]},{best_move[1]})"
