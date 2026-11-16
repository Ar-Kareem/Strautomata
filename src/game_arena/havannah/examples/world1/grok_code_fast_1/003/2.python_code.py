
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    occupied = set(me + opp)
    possible_moves = [
        (r, c) for r in range(15)
        for c in range(15)
        if valid_mask[r][c] and (r, c) not in occupied
    ]
    if not possible_moves:
        # Fallback, though unlikely
        return (0, 0)  # But ensure it's valid if possible

    # Hexagonal neighbor offsets
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1)]

    def get_neighbors(r: int, c: int):
        ns = []
        for dr, dc in dirs:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 15 and 0 <= nc < 15 and valid_mask[nr][nc]:
                ns.append((nr, nc))
        return ns

    best_score = float('-inf')
    best_move = possible_moves[0]  # Default
    for move in possible_moves:
        r, c = move
        own_count = 0
        opp_count = 0
        occupied_me = set(me)  # For faster lookup
        occupied_opp = set(opp)
        for nr, nc in get_neighbors(r, c):
            if (nr, nc) in occupied_me:
                own_count += 1
            elif (nr, nc) in occupied_opp:
                opp_count += 1
        score = own_count - opp_count
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score and np.random.random() < 0.5:  # Rare tiebreaker with randomness
            best_move = move

    return best_move
