
import numpy as np
from math import sqrt, log


def policy(you: list[int], opponent: list[int]) -> int:
    # Convert to numpy arrays for easier manipulation
    you = np.array(you, dtype=int)
    opp = np.array(opponent, dtype=int)

    # Return immediate winning move if possible
    for i in range(6):
        if you[i] == 0:
            continue
        new_you, new_opp = _apply_move(you, opp, i)
        if new_you[6] > new_opp[6] and _is_end(new_you, new_opp):
            return i

    # Return move that gives an extra turn if it increases our score
    best_extra = -1
    for i in range(6):
        if you[i] == 0:
            continue
        new_you, new_opp = _apply_move(you, opp, i)
        if new_you[6] > you[6] and new_you[6] >= opp[6]:
            return i
        if new_you[6] > you[6]:
            best_extra = i

    if best_extra != -1:
        return best_extra

    # Minimax with depth-limited search
    # Evaluate all legal moves with a 6-ply lookahead (3 moves each)
    best_score = -1e9
    best_move = -1

    for i in range(6):
        if you[i] == 0:
            continue

        score = _alphabeta(you, opp, 6, -1e9, 1e9, True)
        if score > best_score:
            best_score = score
            best_move = i

    if best_move != -1:
        return best_move

    # Fallback: choose a move with some seeds
    for i in range(5, -1, -1):
        if you[i] > 0:
            return i

    # This should never happen as policy is not called when no legal moves exist
    return 0


def _apply_move(you, opp, move):
    # Apply a single move and return new states (you, opp)
    # move is index 0-5

    # Make copies to avoid mutating originals
    you = you.copy()
    opp = opp.copy()

    seeds = you[move]
    you[move] = 0

    # Distribute seeds
    idx = move + 1
    is_you_side = True
    last_house = None

    for _ in range(seeds):
        if is_you_side:
            if idx <= 6:
                you[idx] += 1
                last_house = ('you', idx)
                if idx == 6:
                    # landed in store
                    idx = 0  # next will start from house 0 on opponent
                    is_you_side = False
                else:
                    idx += 1
            else:
                # move to opponent's houses
                is_you_side = False
                idx = 0
                opp[idx] += 1
                last_house = ('opp', idx)
                idx += 1
        else:
            if idx <= 5:
                opp[idx] += 1
                last_house = ('opp', idx)
                idx += 1
            else:
                # move back to your houses
                is_you_side = True
                idx = 0
                you[idx] += 1
                last_house = ('you', idx)
                idx += 1

    # Capture if last seed landed in empty house on your side
    if last_house and last_house[0] == 'you' and 0 <= last_house[1] <= 5:
        house_idx = last_house[1]
        if you[house_idx] == 1:  # exactly one seed (our last seed)
            opp_idx = 5 - house_idx
            if opp[opp_idx] > 0:
                # Capture
                you[6] += you[house_idx] + opp[opp_idx]
                you[house_idx] = 0
                opp[opp_idx] = 0

    return you, opp


def _is_end(you, opp):
    return np.sum(you[:6]) == 0 or np.sum(opp[:6]) == 0


def _evaluate(you, opp):
    # Simple evaluation function
    if _is_end(you, opp):
        if you[6] > opp[6]:
            return 1000
        elif you[6] < opp[6]:
            return -1000
        else:
            return 0

    # Heuristic: score difference + house pressure
    score_diff = you[6] - opp[6]

    # Encourage having seeds in houses near the store (more likely to get extra moves)
    house_value = 0
    for i in range(6):
        if you[i] > 0:
            # Distance to store: 6-i (i=5 is closest)
            dist = 6 - i
            if you[i] == dist:
                house_value += 2  # potential extra move
            elif you[i] > dist and (you[i] - dist) % 13 == 0:
                house_value += 1.5  # could land in store with extra lap

    opp_value = 0
    for i in range(6):
        if opp[i] > 0:
            dist = 6 - i
            if opp[i] == dist:
                opp_value -= 2

    return score_diff + house_value + opp_value


def _alphabeta(you, opp, depth, alpha, beta, is_max):
    if depth == 0 or _is_end(you, opp):
        return _evaluate(you, opp)

    if is_max:
        max_eval = -1e9
        has_move = False
        for i in range(6):
            if you[i] == 0:
                continue
            has_move = True
            new_you, new_opp = _apply_move(you, opp, i)

            # Extra move if last seed in store
            if new_you[6] > you[6] and new_you[6] == you[6] + 1:
                # Extra move
                eval_val = _alphabeta(new_you, new_opp, depth, alpha, beta, True)
            else:
                eval_val = _alphabeta(new_you, new_opp, depth - 1, alpha, beta, False)

            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        if not has_move:
            # No moves, game ends
            return _evaluate(you, opp)
        return max_eval
    else:
        min_eval = 1e9
        has_move = False
        for i in range(6):
            if opp[i] == 0:
                continue
            has_move = True
            new_opp, new_you = _apply_move(opp, you, i)

            # Extra move if last seed in store
            if new_opp[6] > opp[6] and new_opp[6] == opp[6] + 1:
                eval_val = _alphabeta(new_you, new_opp, depth, alpha, beta, False)
            else:
                eval_val = _alphabeta(new_you, new_opp, depth - 1, alpha, beta, True)

            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        if not has_move:
            return _evaluate(you, opp)
        return min_eval

