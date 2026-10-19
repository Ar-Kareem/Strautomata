
#!/usr/bin/env python3
# Kalah policy: choose a legal move index (0..5) for the given board state.
# The state is given as:
#   you = [h0, h1, h2, h3, h4, h5, store]
#   opponent = [h0, h1, h2, h3, h4, h5, store]
# Returns an integer i (0..5) where you[i] > 0.

from typing import List, Tuple, Dict
import math
import time

# Prebuilt cycle for sowing (excluding opponent store)
# Order: you[0..5], you[6] (store), opp[0..5]
_CYCLE = [('you', i) for i in range(0, 6)] + [('you', 6)] + [('opp', i) for i in range(0, 6)]
_CYCLE_LEN = len(_CYCLE)  # 13

def _apply_move(you: List[int], opp: List[int], house: int) -> Tuple[List[int], List[int], bool]:
    """
    Apply move from your house index `house`.
    Returns (new_you, new_opp, extra_move_flag).
    This function does not modify the input lists.
    """
    # Copy boards
    you = list(you)
    opp = list(opp)
    seeds = you[house]
    you[house] = 0

    # Find start index in cycle: next pit after (you,house)
    if house < 5:
        start_idx = house + 1  # corresponds to ('you', house+1) in cycle because cycle begins at you[0]
    else:
        start_idx = 6  # ('you',6) store

    pos = start_idx
    last = None
    # Place seeds one by one
    for _ in range(seeds):
        side, idx = _CYCLE[pos % _CYCLE_LEN]
        if side == 'you':
            if idx == 6:
                you[6] += 1
            else:
                you[idx] += 1
        else:  # 'opp'
            opp[idx] += 1
        last = (side, idx)
        pos += 1

    extra = (last == ('you', 6))

    # Capture rule
    if (not extra) and last is not None:
        side, idx = last
        if side == 'you' and 0 <= idx <= 5:
            # It is a capture only if the house was empty before the final sow (i.e., now equals 1)
            if you[idx] == 1:
                opp_idx = 5 - idx
                if opp[opp_idx] > 0:
                    captured = opp[opp_idx] + you[idx]
                    you[idx] = 0
                    opp[opp_idx] = 0
                    you[6] += captured

    # End-of-game check: if one side has no seeds in houses, move remaining seeds to other store
    if all(x == 0 for x in you[:6]) or all(x == 0 for x in opp[:6]):
        # Move remaining to each player's store
        you_remaining = sum(you[:6])
        opp_remaining = sum(opp[:6])
        you = you[:]  # already copied
        opp = opp[:]  # already copied
        you[:6] = [0]*6
        opp[:6] = [0]*6
        you[6] += you_remaining
        opp[6] += opp_remaining

    return you, opp, extra

def _is_terminal(you: Tuple[int, ...], opp: Tuple[int, ...]) -> bool:
    return all(x == 0 for x in you[:6]) or all(x == 0 for x in opp[:6])

def _evaluate(you: Tuple[int, ...], opp: Tuple[int, ...]) -> float:
    """
    Heuristic evaluation from 'you' perspective.
    Primary factor: store difference.
    Secondary: weighted seeds in houses (closer houses to store are more valuable).
    """
    store_diff = you[6] - opp[6]
    # Weigh your houses by proximity to store (index 0..5 -> weight 1..6)
    your_weighted = sum(you[i] * (i + 1) for i in range(6))
    # Opponent houses weighted similarly from their perspective (closer to their store are high index => weight 1..6)
    opp_weighted = sum(opp[i] * (i + 1) for i in range(6))
    # Combine with smaller weight for house seeds
    return float(store_diff) + 0.08 * (your_weighted - opp_weighted)

# Transposition table: key = (tuple(you), tuple(opp), depth) -> value
_tt: Dict[Tuple[Tuple[int, ...], Tuple[int, ...], int], float] = {}

# Search parameters
_MAX_DEPTH = 8
_TIME_LIMIT = 0.95  # seconds; safe cutoff for iterative contexts (not used per-node here)

def _negamax(you: Tuple[int, ...], opp: Tuple[int, ...], depth: int, alpha: float, beta: float, start_time: float) -> float:
    # Check time (rudimentary)
    if time.monotonic() - start_time > _TIME_LIMIT:
        # Time cutoff: return heuristic
        return _evaluate(you, opp)

    if _is_terminal(you, opp):
        # Terminal: final stores already included in state if applied; evaluate directly
        return float(you[6] - opp[6])

    if depth == 0:
        return _evaluate(you, opp)

    key = (you, opp, depth)
    if key in _tt:
        return _tt[key]

    best = -math.inf

    # Generate legal moves
    moves = [i for i in range(6) if you[i] > 0]
    # Move ordering heuristic: try moves that end in store first (likely extra moves)
    def _move_score(i):
        s = you[i]
        if s == 0:
            return -999
        # compute final position on cycle
        if i < 5:
            start_idx = i + 1
        else:
            start_idx = 6
        final_idx = (start_idx + (s - 1)) % _CYCLE_LEN
        side, idx = _CYCLE[final_idx]
        score = 0
        if side == 'you' and idx == 6:
            score += 1000
        if side == 'you' and 0 <= idx <= 5 and you[idx] == 0 and opp[5 - idx] > 0:
            score += 500
        # prefer larger s slightly
        score += s / 10.0
        return score

    moves.sort(key=_move_score, reverse=True)

    for i in moves:
        new_you, new_opp, extra = _apply_move(list(you), list(opp), i)
        new_you_t = tuple(new_you)
        new_opp_t = tuple(new_opp)
        if extra:
            val = _negamax(new_you_t, new_opp_t, depth - 1, alpha, beta, start_time)
        else:
            # turn passes: swap roles and negate
            val = -_negamax(new_opp_t, new_you_t, depth - 1, -beta, -alpha, start_time)
        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    # If no moves (shouldn't happen since policy not called in that case), best remains -inf; fallback to evaluation
    if best == -math.inf:
        best = _evaluate(you, opp)

    _tt[key] = best
    return best

def policy(you: List[int], opponent: List[int]) -> int:
    """
    Choose and return a legal move index for current player.
    """
    start_time = time.monotonic()

    you_t = tuple(you)
    opp_t = tuple(opponent)
    legal_moves = [i for i in range(6) if you[i] > 0]
    if not legal_moves:
        raise ValueError("policy called with no legal moves")

    best_move = legal_moves[0]
    best_val = -math.inf

    # Clear transposition table for fresh search (keeps memory bounded)
    _tt.clear()

    # Try fixed depth search (could be iteratively deepened; single depth chosen for performance)
    depth = _MAX_DEPTH

    # Order initial moves with heuristic like in search
    def _init_score(i):
        s = you[i]
        if i < 5:
            start_idx = i + 1
        else:
            start_idx = 6
        final_idx = (start_idx + (s - 1)) % _CYCLE_LEN
        side, idx = _CYCLE[final_idx]
        score = 0
        if side == 'you' and idx == 6:
            score += 1000
        if side == 'you' and 0 <= idx <= 5 and you[idx] == 0 and opponent[5 - idx] > 0:
            score += 500
        score += s / 10.0
        return score

    legal_moves.sort(key=_init_score, reverse=True)

    alpha = -math.inf
    beta = math.inf

    for i in legal_moves:
        # Time check
        if time.monotonic() - start_time > _TIME_LIMIT:
            break
        new_you, new_opp, extra = _apply_move(list(you), list(opponent), i)
        new_you_t = tuple(new_you)
        new_opp_t = tuple(new_opp)
        if extra:
            val = _negamax(new_you_t, new_opp_t, depth - 1, alpha, beta, start_time)
        else:
            val = -_negamax(new_opp_t, new_you_t, depth - 1, -beta, -alpha, start_time)

        if val > best_val or (val == best_val and i < best_move):
            best_val = val
            best_move = i
        if best_val > alpha:
            alpha = best_val

    # Ensure returned move is legal
    if you[best_move] == 0:
        # fallback: pick first legal
        for m in range(6):
            if you[m] > 0:
                return m
        # Should not reach here as caller guarantees a legal move exists
        raise RuntimeError("No legal moves found")

    return int(best_move)


# If run as a script, do a tiny self-test
if __name__ == "__main__":
    # Example starting position: 4 seeds each house, stores zero
    you = [4, 4, 4, 4, 4, 4, 0]
    opp = [4, 4, 4, 4, 4, 4, 0]
    print("Chosen move:", policy(you, opp))
