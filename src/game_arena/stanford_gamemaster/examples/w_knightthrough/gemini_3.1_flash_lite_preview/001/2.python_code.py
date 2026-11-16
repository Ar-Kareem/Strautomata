
def policy(state: list[list[object]], role: str) -> str:
    # Build current board state
    board = {}
    for fact in state:
        if fact[0] == "cell":
            board[(fact[1], int(fact[2]))] = fact[3]

    my_pieces = [pos for pos, color in board.items() if color == role]
    
    # Knight move deltas: (col_change, row_change)
    # Knight moves: (±1, ±2) or (±2, ±1)
    # For white, forward means increasing row index. For black, decreasing row index.
    direction = 1 if role == "white" else -1
    possible_deltas = [
        (1, 2 * direction), (-1, 2 * direction),
        (2, 1 * direction), (-2, 1 * direction)
    ]
    
    legal_moves = []
    cols = "abcdefgh"
    
    for (col, row) in my_pieces:
        col_idx = cols.find(col)
        for dc, dr in possible_deltas:
            new_c_idx = col_idx + dc
            new_r = row + dr
            
            if 0 <= new_c_idx < 8 and 1 <= new_r <= 8:
                new_col = cols[new_c_idx]
                if (new_col, new_r) not in board:
                    # Score move: maximize vertical progress
                    # White: new_r, Black: -new_r
                    score = new_r if role == "white" else (9 - new_r)
                    legal_moves.append((score, new_col, new_r, col, row))
    
    if not legal_moves:
        return ""
    
    # Pick the move with the highest rank progress
    legal_moves.sort(key=lambda x: x[0], reverse=True)
    best = legal_moves[0]
    
    return f"move({best[3]},{best[4]},{best[1]},{best[2]})"
