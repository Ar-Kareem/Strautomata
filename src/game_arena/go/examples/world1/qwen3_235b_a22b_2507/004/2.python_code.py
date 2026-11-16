
import random
from typing import List, Tuple, Set, Dict

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    board_size = 19
    # Convert lists to sets for fast lookup
    my_stones = set(me)
    opp_stones = set(opponent)
    all_stones = my_stones | opp_stones

    # Helper: get neighboring points (up, down, left, right)
    def neighbors(row: int, col: int) -> List[Tuple[int, int]]:
        n = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if 1 <= nr <= board_size and 1 <= nc <= board_size:
                n.append((nr, nc))
        return n

    # Helper: get connected group and its liberties
    def get_group_and_liberties(start: Tuple[int, int], colorset: Set[Tuple[int, int]]) -> Tuple[Set[Tuple[int, int]], Set[Tuple[int, int]]]:
        stack = [start]
        group = {start}
        visited = {start}
        liberties = set()
        while stack:
            r, c = stack.pop()
            for nr, nc in neighbors(r, c):
                if (nr, nc) in colorset and (nr, nc) not in visited:
                    stack.append((nr, nc))
                    visited.add((nr, nc))
                    group.add((nr, nc))
                if (nr, nc) not in all_stones:
                    liberties.add((nr, nc))
        return group, liberties

    # Fast liberty count for a stone group
    def liberty_count(pos: Tuple[int, int], colorset: Set[Tuple[int, int]]) -> int:
        group, liberties = get_group_and_liberties(pos, colorset)
        return len(liberties)

    # Simulate placing a stone and return (new_my_stones, new_opp_stones, captures)
    def simulate_move(row: int, col: int, my_stones: Set[Tuple[int, int]], opp_stones: Set[Tuple[int, int]]):
        new_my = my_stones.copy()
        new_opp = opp_stones.copy()
        pos = (row, col)
        if pos in new_my or pos in new_opp:
            return None, None, 0  # invalid move
        new_my.add(pos)
        new_all = new_my | new_opp
        captured = 0
        # Check opponent captures
        for npos in neighbors(row, col):
            if npos in new_opp:
                group, liberties = get_group_and_liberties(npos, new_opp)
                if len(liberties) == 0:  # captured
                    for s in group:
                        new_opp.remove(s)
                    captured += len(group)
        # Now check if my own group is fully surrounded (self-atari)
        my_group, my_liberties = get_group_and_liberties(pos, new_my)
        if len(my_liberties) == 0:
            return None, None, 0  # suicide move
        return new_my, new_opp, captured

    # Check if move is legal (will be played without capture of own group)
    def is_legal(row: int, col: int):
        return simulate_move(row, col, my_stones, opp_stones)[0] is not None

    # Score move based on heuristics
    def score_move(row: int, col: int) -> float:
        pos = (row, col)
        score = 0.0

        # Immediate capture bonus
        _, _, captures = simulate_move(row, col, my_stones, opp_stones)
        score += captures * 10.0

        # Self-atari: if move has no liberties after play (but simulate already checks suicide)
        # So if we're here, it's legal. But if only one liberty, be cautious unless it captures
        new_my, new_opp, _ = simulate_move(row, col, my_stones, opp_stones)
        if new_my is None:
            return -float('inf')
        my_group, my_liberties = get_group_and_liberties(pos, new_my)
        if len(my_liberties) == 1 and captures == 0:
            score -= 20.0  # avoid self-atari unless capturing
        elif len(my_liberties) >= 2:
            score += 1.0

        # Proximity to own stones
        friendly_neighbors = 0
        for nr, nc in neighbors(row, col):
            if (nr, nc) in my_stones:
                friendly_neighbors += 1
                # Extra bonus if connecting to a weak group
                if liberty_count((nr, nc), my_stones) <= 2:
                    score += 2.0
        score += friendly_neighbors * 1.5

        # Proximity to opponent stones
        enemy_neighbors = 0
        for nr, nc in neighbors(row, col):
            if (nr, nc) in opp_stones:
                enemy_neighbors += 1
                # Bonus if threatening an enemy group with only 2 liberties
                if liberty_count((nr, nc), opp_stones) == 2:
                    score += 1.0
        # Playing next to opponent can be good (attack) or bad (build their strength)
        # But if it reduces their liberties, it's good

        # Center preference (for opening/midgame)
        center_dist = abs(row - 10) + abs(col - 10)
        score += max(0, (10 - center_dist) * 0.05)

        # Avoid edge in early game, but edges matter in endgame
        # But without game stage detection, be neutral

        return score

    # Candidate moves: empty positions adjacent to existing stones or center if board is empty
    candidates = []
    if not all_stones:
        # Opening move: play in center or near
        return (10, 10)

    # Collect candidate positions: empty, adjacent to any stone, or potential extensions
    considered = set()
    for r, c in all_stones:
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in all_stones and (nr, nc) not in considered:
                considered.add((nr, nc))
                candidates.append((nr, nc))
    # Also add diagonal neighbors as secondary candidates
    for r, c in all_stones:
        for dr, dc in [(-1,-1), (-1,1), (1,-1), (1,1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19 and (nr, nc) not in all_stones and (nr, nc) not in considered:
                considered.add((nr, nc))
                candidates.append((nr, nc))

    # Remove duplicates and invalid
    candidates = list(set(candidates))
    # Filter legal moves
    legal_candidates = [pos for pos in candidates if is_legal(pos[0], pos[1])]
    
    # Always consider passing as last resort
    if not legal_candidates:
        return (0, 0)

    # Score all legal candidates
    scored_moves = [(pos, score_move(pos[0], pos[1])) for pos in legal_candidates]
    # Sort by score descending
    scored_moves.sort(key=lambda x: x[1], reverse=True)

    # Choose the best move
    best_move = scored_moves[0][0]

    # Emergency: if no move improves position, consider passing
    if scored_moves[0][1] < -100:
        return (0, 0)

    return best_move
