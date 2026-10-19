
import random
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Predefined strong opening moves (first 10 moves)
    opening_moves = [
        (4, 4), (4, 16), (16, 4), (16, 16),  # 4-4 point opening
        (10, 10), (10, 10), (10, 10), (10, 10),  # Simplified for demo
        (7, 7), (7, 13), (13, 7), (13, 13),  # Additional openings
    ]

    # If it's the first 10 moves, use predefined openings
    if len(me) < 10:
        move = opening_moves[len(me)]
        return move

    # If board is mostly filled, pass
    if len(me) + len(opponent) > 300:  # Arbitrary threshold
        return (0, 0)

    # Get all possible moves (empty points)
    all_moves = set()
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me and (r, c) not in opponent:
                all_moves.add((r, c))

    # If no moves left, pass
    if not all_moves:
        return (0, 0)

    # Evaluate moves based on local patterns
    def evaluate_move(move):
        r, c = move
        score = 0

        # Prefer corners and sides
        if r in {1, 19} or c in {1, 19}:
            score += 2
        elif r in {2, 18} or c in {2, 18}:
            score += 1

        # Prefer moves near my stones
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in me:
                score += 1

        # Avoid moves near opponent's large groups
        for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
            nr, nc = r + dr, c + dc
            if (nr, nc) in opponent:
                score -= 1

        return score

    # Find the best move
    best_move = None
    best_score = -float('inf')
    for move in all_moves:
        score = evaluate_move(move)
        if score > best_score:
            best_score = score
            best_move = move

    # If no clear best move, pick randomly
    if best_move is None:
        best_move = random.choice(list(all_moves))

    return best_move
