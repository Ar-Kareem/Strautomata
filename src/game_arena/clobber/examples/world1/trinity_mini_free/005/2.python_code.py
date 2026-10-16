
value_matrix = [
    [0, 0, 1, 1, 0, 0],
    [0, 2, 3, 3, 2, 0],
    [1, 3, 4, 4, 3, 1],
    [1, 3, 4, 4, 3, 1],
    [0, 2, 3, 3, 2, 0]
]

def policy(you, opponent):
    moves = []
    directions = [('U', -1, 0), ('R', 0, 1), ('D', 1, 0), ('L', 0, -1)]
    for r in range(5):
        for c in range(6):
            if you[r][c] == 1:
                for d, dr, dc in directions:
                    nr = r + dr
                    nc = c + dc
                    if 0 <= nr < 5 and 0 <= nc < 6:
                        if opponent[nr][nc] == 1:
                            moves.append((r, c, d, nr, nc))
    if not moves:
        return ""  # Should not occur as player must have moves
    best_move = None
    best_score = -1
    for move in moves:
        r, c, d, nr, nc = move
        score = 10 + value_matrix[nr][nc]
        if score > best_score:
            best_score = score
            best_move = (r, c, d)
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
