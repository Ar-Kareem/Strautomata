
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    import numpy as np
    
    # Constants
    BOARD_SIZE = 19
    
    # Create board representation
    board = np.zeros((BOARD_SIZE + 1, BOARD_SIZE + 1), dtype=int)  # +1 for 1-indexed
    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = -1
    
    def is_occupied(r, c):
        return board[r][c] != 0

    # Generate possible moves
    possible_moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if not is_occupied(r, c):
                possible_moves.append((r, c))
    
    # Simple scoring function for moves
    def score_move(r, c):
        score = 0
        # Check surrounding positions
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if (dr == 0 and dc == 0):
                    continue
                rr, cc = r + dr, c + dc
                if 1 <= rr <= BOARD_SIZE and 1 <= cc <= BOARD_SIZE:
                    if board[rr][cc] == 1:  # My stone
                        score += 1
                    elif board[rr][cc] == -1:  # Opponent's stone
                        score -= 1
                    else:  # Empty
                        score += 0.5  # Can potentially place here
        return score
    
    # Evaluate all possible moves and get the best one
    best_move = (0, 0)  # default to passing
    best_score = -float('inf')
    for move in possible_moves:
        move_score = score_move(move[0], move[1])
        if move_score > best_score:
            best_score = move_score
            best_move = move
    
    return best_move, memory
