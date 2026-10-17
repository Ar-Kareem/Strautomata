
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    ships = [5, 4, 3, 3, 2]
    scores = [[0 for _ in range(10)] for _ in range(10)]
    
    # Accumulate scores from all valid placements of all ships
    for L in ships:
        # Horizontal placements
        for r in range(10):
            for c in range(10 - L + 1):
                # Check if this placement is valid (contains no -1)
                valid = True
                for dc in range(L):
                    if board[r][c + dc] == -1:
                        valid = False
                        break
                if valid:
                    # Add to score for each unknown cell covered
                    for dc in range(L):
                        if board[r][c + dc] == 0:
                            scores[r][c + dc] += 1
                            
        # Vertical placements
        for c in range(10):
            for r in range(10 - L + 1):
                valid = True
                for dr in range(L):
                    if board[r + dr][c] == -1:
                        valid = False
                        break
                if valid:
                    for dr in range(L):
                        if board[r + dr][c] == 0:
                            scores[r + dr][c] += 1

    # Find the unknown cell(s) with the maximum score
    max_score = -1
    best_moves = []
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                if scores[r][c] > max_score:
                    max_score = scores[r][c]
                    best_moves = [(r, c)]
                elif scores[r][c] == max_score:
                    best_moves.append((r, c))

    # Tie-broken randomly to avoid predictable patterns
    return random.choice(best_moves)
