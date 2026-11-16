
def policy(state: list[list[object]], role: str) -> str:
    board = {}
    for fact in state:
        if fact[0] == "cell":
            col, row, color = int(fact[1]), int(fact[2]), fact[3]
            board[(col, row)] = color

    opponent = "black" if role == "white" else "white"
    direction = 1 if role == "white" else -1
    promotion_row = 8 if role == "white" else 1

    def get_legal_moves():
        moves = []
        for (col, row), color in board.items():
            if color == role:
                # Forward
                target_f = (col, row + direction)
                if 1 <= target_f[1] <= 8 and target_f not in board:
                    moves.append((col, row, col, row + direction, False))
                
                # Diagonals
                for dc in [-1, 1]:
                    target_d = (col + dc, row + direction)
                    if 1 <= target_d[0] <= 8 and 1 <= target_d[1] <= 8:
                        if target_d in board and board[target_d] == opponent:
                            moves.append((col, row, col + dc, row + direction, True))
        return moves

    legal_moves = get_legal_moves()
    
    # Heuristic: 
    # 1. Prefer captures (True)
    # 2. Prefer moves to higher/lower numbered rows based on role
    best_move = None
    best_score = -999
    
    for m in legal_moves:
        c1, r1, c2, r2, is_capture = m
        score = (2 if is_capture else 0) + (r2 if role == "white" else (9 - r2))
        if score > best_score:
            best_score = score
            best_move = m
            
    if best_move:
        return f"move({best_move[0]},{best_move[1]},{best_move[2]},{best_move[3]})"
    
    return ""
