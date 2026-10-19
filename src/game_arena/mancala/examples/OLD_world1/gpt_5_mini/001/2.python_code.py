
import math
from functools import lru_cache

# Kalah policy: returns an index 0..5 of a non-empty house to sow from.
# Implements alpha-beta minimax with captures and extra-move handling.

def policy(you: list[int], opponent: list[int]) -> int:
    # Defensive copy
    you = list(you)
    opponent = list(opponent)

    # Quick fallback: choose first non-empty if anything goes wrong
    legal = [i for i in range(6) if you[i] > 0]
    if not legal:
        # Should not happen per problem statement
        return 0

    # Apply a move for the side "you" (the player to move).
    # Returns (you_after, opponent_after, extra_move_flag)
    def apply_move(you_arr, opp_arr, i):
        you2 = you_arr.copy()
        opp2 = opp_arr.copy()
        original_you = you_arr.copy()
        seeds = you2[i]
        you2[i] = 0
        pos = i  # using 0..13 indexing map:
                 # 0..5 -> you houses
                 # 6    -> you store
                 # 7..12 -> opponent houses 0..5
                 # 13 -> opponent store (skipped)
        last_pos = None
        while seeds > 0:
            pos = (pos + 1) % 14
            if pos == 13:
                # skip opponent store
                continue
            if 0 <= pos <= 5:
                you2[pos] += 1
            elif pos == 6:
                you2[6] += 1
            elif 7 <= pos <= 12:
                opp2[pos - 7] += 1
            seeds -= 1
            last_pos = pos

        extra = (last_pos == 6)

        # Capture?
        if 0 <= last_pos <= 5:
            # last_pos house in your side
            # capture only if that house was empty before the drop
            if original_you[last_pos] == 0:
                opp_index = 5 - last_pos
                if opp2[opp_index] > 0:
                    captured = you2[last_pos] + opp2[opp_index]
                    you2[6] += captured
                    you2[last_pos] = 0
                    opp2[opp_index] = 0

        # Check for game end: if one side has no seeds in houses, collect remaining seeds
        if sum(you2[0:6]) == 0 or sum(opp2[0:6]) == 0:
            you2[6] += sum(you2[0:6])
            opp2[6] += sum(opp2[0:6])
            for k in range(6):
                you2[k] = 0
                opp2[k] = 0

        return you2, opp2, extra

    # Heuristic evaluation from the perspective of the root player.
    # root_is_first indicates whether the "you" array corresponds to the root player.
    def evaluate_state(you_arr, opp_arr, root_is_first):
        if root_is_first:
            root_store = you_arr[6]
            other_store = opp_arr[6]
            root_houses = sum(you_arr[0:6])
            other_houses = sum(opp_arr[0:6])
        else:
            root_store = opp_arr[6]
            other_store = you_arr[6]
            root_houses = sum(opp_arr[0:6])
            other_houses = sum(you_arr[0:6])

        # Basic heuristic: store difference primary, house difference secondary.
        # We weight houses less than stores.
        return (root_store - other_store) + 0.5 * (root_houses - other_houses)

    # Terminal check: returns (is_terminal, final_score_relative_to_root)
    def terminal_score(you_arr, opp_arr, root_is_first):
        # Terminal if either side has no seeds in houses
        if sum(you_arr[0:6]) == 0 or sum(opp_arr[0:6]) == 0:
            # final stores already should have been collected by apply_move
            if root_is_first:
                return True, you_arr[6] - opp_arr[6]
            else:
                return True, opp_arr[6] - you_arr[6]
        return False, 0

    # Transposition/memoization cache
    from functools import lru_cache

    # We'll limit depth. Choose depth based on total seeds to keep performance reasonable.
    total_seeds = sum(you[0:6]) + sum(opponent[0:6]) + you[6] + opponent[6]
    # Deeper search when fewer seeds remain.
    if total_seeds <= 20:
        MAX_DEPTH = 12
    elif total_seeds <= 36:
        MAX_DEPTH = 10
    else:
        MAX_DEPTH = 8

    # Cap depth to avoid excessive recursion in worst-case environments
    MAX_DEPTH = min(MAX_DEPTH, 12)

    INF = 10**9

    # Use memoization keyed by tuple states and depth and root orientation and maximizing flag
    @lru_cache(maxsize=200000)
    def minimax(you_t, opp_t, depth, alpha, beta, maximizing, root_is_first):
        you_arr = list(you_t)
        opp_arr = list(opp_t)

        term, term_score = terminal_score(you_arr, opp_arr, root_is_first)
        if term:
            return term_score

        if depth == 0:
            return evaluate_state(you_arr, opp_arr, root_is_first)

        moves = [i for i in range(6) if you_arr[i] > 0]
        if not moves:
            # No legal move for current player (should be terminal normally)
            term, term_score = terminal_score(you_arr, opp_arr, root_is_first)
            if term:
                return term_score
            # Fallback:
            return evaluate_state(you_arr, opp_arr, root_is_first)

        # Move ordering: sort by heuristic of resulting state (descending for maximizing)
        children = []
        for m in moves:
            child_you, child_opp, extra = apply_move(you_arr, opp_arr, m)
            # determine orientation for root: if we switch player (no extra), root_is_first flips
            if extra:
                child_root_is_first = root_is_first
            else:
                child_root_is_first = not root_is_first
            h = evaluate_state(child_you, child_opp, child_root_is_first)
            children.append((m, child_you, child_opp, extra, h))
        children.sort(key=lambda x: x[4], reverse=maximizing)

        if maximizing:
            value = -INF
            for m, child_you, child_opp, extra, _h in children:
                if extra:
                    val = minimax(tuple(child_you), tuple(child_opp), depth - 1, alpha, beta, True, root_is_first)
                else:
                    # switch perspective: next player is opponent; pass swapped arrays
                    val = minimax(tuple(child_opp), tuple(child_you), depth - 1, alpha, beta, False, not root_is_first)
                if val > value:
                    value = val
                if value > alpha:
                    alpha = value
                if alpha >= beta:
                    break
            return value
        else:
            value = INF
            for m, child_you, child_opp, extra, _h in children:
                if extra:
                    val = minimax(tuple(child_you), tuple(child_opp), depth - 1, alpha, beta, False, root_is_first)
                else:
                    val = minimax(tuple(child_opp), tuple(child_you), depth - 1, alpha, beta, True, not root_is_first)
                if val < value:
                    value = val
                if value < beta:
                    beta = value
                if alpha >= beta:
                    break
            return value

    # Top-level search: try increasing depth until MAX_DEPTH (iterative deepening)
    best_move = legal[0]
    best_score = -INF
    # initial alpha-beta window
    alpha = -INF
    beta = INF

    # For safety, restrict number of iterations; iterative deepening from 1 to MAX_DEPTH
    for depth in range(1, MAX_DEPTH + 1):
        local_best = None
        local_best_score = -INF
        # generate and order moves by quick heuristic to improve alpha-beta
        cand = []
        for m in legal:
            c_you, c_opp, extra = apply_move(you, opponent, m)
            if extra:
                child_root_is_first = True
            else:
                child_root_is_first = False
            h = evaluate_state(c_you, c_opp, child_root_is_first)
            cand.append((m, c_you, c_opp, extra, h))
        cand.sort(key=lambda x: x[4], reverse=True)

        # search each move
        for m, c_you, c_opp, extra, _h in cand:
            if extra:
                val = minimax(tuple(c_you), tuple(c_opp), depth - 1, alpha, beta, True, True)
            else:
                val = minimax(tuple(c_opp), tuple(c_you), depth - 1, alpha, beta, False, False)
            if val > local_best_score or (val == local_best_score and (local_best is None or m < local_best)):
                local_best_score = val
                local_best = m

        if local_best is not None:
            best_move = local_best
            best_score = local_best_score
        # continue deepening to try to improve; no time management available here

    return int(best_move)
