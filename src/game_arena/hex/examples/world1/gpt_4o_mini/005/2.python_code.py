
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    size = 11
    board = [['.' for _ in range(size)] for _ in range(size)]
    
    for r, c in me:
        board[r][c] = 'b' if color == 'b' else 'w'
    
    for r, c in opp:
        board[r][c] = 'w' if color == 'b' else 'b'

    def is_valid_move(r, c):
        return 0 <= r < size and 0 <= c < size and board[r][c] == '.'

    def get_neighbors(r, c):
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if abs(dr) + abs(dc) == 1:  # Ensures we only take the right neighbors in hex
                    nr, nc = r + dr, c + dc
                    if is_valid_move(nr, nc):
                        neighbors.append((nr, nc))
        return neighbors

    def score_move(r, c):
        score = 0
        neighbors = get_neighbors(r, c)
        for nr, nc in neighbors:
            if board[nr][nc] == ('b' if color == 'b' else 'w'):
                score += 1
            elif board[nr][nc] == ('w' if color == 'b' else 'b'):
                score -= 1
        return score

    best_move = None
    best_score = -float('inf')

    for r in range(size):
        for c in range(size):
            if is_valid_move(r, c):
                move_score = score_move(r, c)
                if move_score > best_score:
                    best_score = move_score
                    best_move = (r, c)

    return best_move if best_move else (0, 0)
