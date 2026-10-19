
import math
from typing import List, Tuple, Dict

def policy(you: List[int], opponent: List[int]) -> int:
    # Depth selection based on remaining seeds
    total = sum(you[:6]) + sum(opponent[:6])
    if total <= 12:
        max_depth = 10
    elif total <= 24:
        max_depth = 9
    elif total <= 36:
        max_depth = 8
    else:
        max_depth = 7

    # Transposition table
    TT: Dict[Tuple[Tuple[int, ...], Tuple[int, ...], int], int] = {}

    def is_game_over(a: List[int], b: List[int]) -> bool:
        return sum(a[:6]) == 0 or sum(b[:6]) == 0

    def terminal_score(a: List[int], b: List[int]) -> int:
        # Returns final difference * 100 (strong terminal value)
        if sum(a[:6]) == 0:
            a_store = a[6]
            b_store = b[6] + sum(b[:6])
        else:
            a_store = a[6] + sum(a[:6])
            b_store = b[6]
        return (a_store - b_store) * 100

    def heuristic(a: List[int], b: List[int]) -> int:
        store_diff = a[6] - b[6]
        side_diff = sum(a[:6]) - sum(b[:6])

        extra_a = 0
        extra_b = 0
        for i in range(6):
            if a[i] > 0 and (i + a[i]) % 13 == 6:
                extra_a += 1
            if b[i] > 0 and (i + b[i]) % 13 == 6:
                extra_b += 1

        cap_a = 0
        cap_b = 0
        for i in range(6):
            seeds = a[i]
            if seeds > 0 and seeds < 13:
                landing = (i + seeds) % 13
                if landing < 6 and a[landing] == 0 and b[5 - landing] > 0:
                    cap_a += 1
            seeds = b[i]
            if seeds > 0 and seeds < 13:
                landing = (i + seeds) % 13
                if landing < 6 and b[landing] == 0 and a[5 - landing] > 0:
                    cap_b += 1

        return int(store_diff * 4 + side_diff + (extra_a - extra_b) * 2 + (cap_a - cap_b))

    def apply_move(a: List[int], b: List[int], move: int) -> Tuple[List[int], List[int], bool, int]:
        pits = a[:6] + [a[6]] + b[:6]  # 13 pits, opponent store excluded
        seeds = pits[move]
        pits[move] = 0
        idx = move

        for _ in range(seeds):
            idx = (idx + 1) % 13
            pits[idx] += 1

        extra = (idx == 6)
        captured = 0
        if idx < 6 and pits[idx] == 1:
            opp_idx = 12 - idx
            if pits[opp_idx] > 0:
                captured = pits[opp_idx] + pits[idx]
                pits[6] += captured
                pits[opp_idx] = 0
                pits[idx] = 0

        new_a = pits[0:6] + [pits[6]]
        new_b = pits[7:13] + [b[6]]
        return new_a, new_b, extra, captured

    def negamax(a: List[int], b: List[int], depth: int, alpha: int, beta: int) -> int:
        if is_game_over(a, b):
            return terminal_score(a, b)
        if depth == 0:
            return heuristic(a, b)

        key = (tuple(a), tuple(b), depth)
        if key in TT:
            return TT[key]

        moves = [i for i in range(6) if a[i] > 0]
        move_data = []
        for m in moves:
            a2, b2, extra, cap = apply_move(a, b, m)
            score = (2 if extra else 0) + (1 if cap > 0 else 0)
            move_data.append((-score, m, a2, b2, extra))
        move_data.sort()

        best = -math.inf
        for _, m, a2, b2, extra in move_data:
            if extra:
                val = negamax(a2, b2, depth - 1, alpha, beta)
            else:
                val = -negamax(b2, a2, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        TT[key] = best
        return best

    # Root search
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        return 0  # should not happen by problem statement

    best_move = legal[0]
    best_val = -math.inf

    # Root move ordering
    root_data = []
    for m in legal:
        y2, o2, extra, cap = apply_move(you, opponent, m)
        score = (2 if extra else 0) + (1 if cap > 0 else 0)
        root_data.append((-score, m, y2, o2, extra))
    root_data.sort()

    for _, m, y2, o2, extra in root_data:
        if extra:
            val = negamax(y2, o2, max_depth - 1, -math.inf, math.inf)
        else:
            val = -negamax(o2, y2, max_depth - 1, -math.inf, math.inf)
        if val > best_val:
            best_val = val
            best_move = m

    return best_move
