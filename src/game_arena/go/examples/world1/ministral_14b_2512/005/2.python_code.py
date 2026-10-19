
import numpy as np
from collections import defaultdict

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Convert to numpy arrays for easier manipulation
    board_size = 19
    my_stones = np.array(me)
    opp_stones = np.array(opponent)

    # --- Opening Moves (First 10 Moves) ---
    if len(me) < 10:
        # Standard 19x19 opening sequence (simplified)
        opening_moves = [
            (10, 10), (10, 10),  # First move (center)
            (10, 10), (10, 10),  # Second move (opponent plays elsewhere)
            (4, 4), (13, 13), (4, 13), (13, 4),  # Standard 4-4 point
            (10, 10), (10, 10)   # Fill center if needed
        ]
        # Rotate moves based on opponent's first move (simplified)
        if len(opponent) > 0:
            opp_first = opponent[0]
            if opp_first == (10, 10):
                return (4, 4)  # Standard response to center
            elif opp_first == (4, 4):
                return (13, 13)
            elif opp_first == (13, 13):
                return (4, 13)
            elif opp_first == (4, 13):
                return (13, 4)
        return opening_moves[len(me) % len(opening_moves)]

    # --- Mid-Game Strategy ---
    # 1. Check for immediate captures (opponent stones with 0 liberties)
    opp_captures = find_captures(opp_stones, my_stones)
    if opp_captures:
        return opp_captures[0]  # Prioritize first capture

    # 2. Check for suicide moves (our stones would die)
    my_captures = find_captures(my_stones, opp_stones)
    if my_captures:
        return (0, 0)  # Pass if we can't move safely

    # 3. Influence-based move (distance to opponent stones)
    influence_map = compute_influence(opp_stones, board_size)
    best_move = find_best_influence_move(influence_map, my_stones, opp_stones)

    # 4. Fallback: Random edge/corner move if no clear influence
    if best_move is None:
        best_move = random_edge_move(my_stones, opp_stones)

    return best_move

def find_captures(stones, opponent_stones):
    """Find stones that can be captured (liberties = 0)."""
    liberties = defaultdict(int)
    for stone in stones:
        row, col = stone
        # Check 4 neighbors
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if (nr, nc) not in stones and (nr, nc) not in opponent_stones:
                    liberties[(row, col)] += 1
    # Return stones with 0 liberties
    return [stone for stone in stones if liberties.get(stone, 4) == 0]

def compute_influence(opponent_stones, board_size):
    """Compute influence map (distance to opponent stones)."""
    influence = np.zeros((board_size + 2, board_size + 2), dtype=float)
    for stone in opponent_stones:
        row, col = stone
        # Euclidean distance (simplified)
        for r in range(1, board_size + 1):
            for c in range(1, board_size + 1):
                influence[r, c] += 1 / (1 + np.sqrt((r - row)**2 + (c - col)**2))
    return influence

def find_best_influence_move(influence_map, my_stones, opp_stones):
    """Find move with highest influence (avoiding my stones)."""
    best_score = -1
    best_move = None
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in my_stones and (r, c) not in opp_stones:
                score = influence_map[r, c]
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    return best_move

def random_edge_move(my_stones, opp_stones):
    """Fallback: Random edge/corner move."""
    edges = [
        (1, 1), (1, 19), (19, 1), (19, 19),  # Corners
        (1, 2), (1, 18), (19, 2), (19, 18),  # Edge-adjacent
        (2, 1), (2, 19), (18, 1), (18, 19)   # Edge-adjacent
    ]
    # Filter out occupied moves
    available = [move for move in edges if move not in my_stones and move not in opp_stones]
    return available[0] if available else (0, 0)  # Pass if no edges available
