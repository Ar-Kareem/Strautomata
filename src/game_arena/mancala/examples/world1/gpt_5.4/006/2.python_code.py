
import time
from math import inf

# Kalah policy for standard 6-house board.
# API:
#   def policy(you: list[int], opponent: list[int]) -> int

HOUSES = 6
STORE = 6

# Tuned to stay comfortably within a 1s arena budget.
TIME_LIMIT = 0.92


def legal_moves(you):
    return [i for i in range(HOUSES) if you[i] > 0]


def game_over(you, opp):
    return all(x == 0 for x in you[:HOUSES]) or all(x == 0 for x in opp[:HOUSES])


def finalize_if_terminal(you, opp):
    """Sweep remaining seeds to stores if game ended."""
    if all(x == 0 for x in you[:HOUSES]):
        rem = sum(opp[:HOUSES])
        if rem:
            opp = opp[:]
            opp[STORE] += rem
            for i in range(HOUSES):
                opp[i] = 0
        return you, opp, True
    if all(x == 0 for x in opp[:HOUSES]):
        rem = sum(you[:HOUSES])
        if rem:
            you = you[:]
            you[STORE] += rem
            for i in range(HOUSES):
                you[i] = 0
        return you, opp, True
    return you, opp, False


def apply_move(you, opp, move):
    """
    Returns (new_you, new_opp, extra_turn, terminal)
    Perspective remains with current mover in returned arrays only if extra_turn is True.
    If extra_turn is False, the caller should swap perspective for the next player.
    """
    you = you[:]
    opp = opp[:]
    seeds = you[move]
    you[move] = 0

    side = 0  # 0 = you, 1 = opp
    pos = move + 1
    last_side = None
    last_pos = None
    landed_in_own_house_empty_before = False

    while seeds > 0:
        if side == 0:
            while pos <= STORE and seeds > 0:
                if pos == STORE:
                    you[STORE] += 1
                    seeds -= 1
                    last_side, last_pos = 0, STORE
                    if seeds == 0:
                        break
                    side = 1
                    pos = 0
                    break
                else:
                    was_empty = (you[pos] == 0)
                    you[pos] += 1
                    seeds -= 1
                    last_side, last_pos = 0, pos
                    landed_in_own_house_empty_before = was_empty
                    pos += 1
            else:
                if seeds > 0:
                    side = 1
                    pos = 0
        else:
            while pos < HOUSES and seeds > 0:
                opp[pos] += 1
                seeds -= 1
                last_side, last_pos = 1, pos
                pos += 1
            if seeds > 0:
                side = 0
                pos = 0

    extra_turn = (last_side == 0 and last_pos == STORE)

    # Capture
    if (last_side == 0 and last_pos is not None and 0 <= last_pos < HOUSES
            and landed_in_own_house_empty_before and you[last_pos] == 1):
        opp_idx = HOUSES - 1 - last_pos
        if opp[opp_idx] > 0:
            you[STORE] += you[last_pos] + opp[opp_idx]
            you[last_pos] = 0
            opp[opp_idx] = 0

    you, opp, terminal = finalize_if_terminal(you, opp)
    return you, opp, extra_turn, terminal


def immediate_tactical_score(you, opp, m):
    """Cheap move ordering heuristic."""
    seeds = you[m]
    score = 0

    # Extra turn if exact landing in store modulo lap length 13 (skip opp store).
    if seeds > 0 and ((m + seeds) % 13) == STORE:
        score += 120

    # Prefer captures if cheaply detectable by direct sim.
    ny, no, extra, terminal = apply_move(you, opp, m)
    gain = (ny[STORE] - you[STORE]) - (no[STORE] - opp[STORE])
    score += 8 * gain

    if extra:
        score += 60
    if terminal:
        score += 40 * ((ny[STORE] - no[STORE]) > 0)

    # Mild preference for larger houses in opening/midgame for distribution.
    score += min(seeds, 12)
    return score


def count_extra_turn_moves(you):
    c = 0
    for i in range(HOUSES):
        s = you[i]
        if s > 0 and ((i + s) % 13) == STORE:
            c += 1
    return c


def count_potential_captures(you, opp):
    c = 0
    for m in range(HOUSES):
        if you[m] == 0:
            continue
        ny, no, extra, terminal = apply_move(you, opp, m)
        if ny[STORE] - you[STORE] >= 2:
            c += 1
    return c


def evaluate(you, opp):
    """
    Heuristic from side-to-move perspective.
    Large positive is good for current player.
    """
    # Terminal-aware exact scoring
    if game_over(you, opp):
        y, o, _ = finalize_if_terminal(you[:], opp[:])
        diff = y[STORE] - o[STORE]
        return 100000 + diff if diff > 0 else (-100000 + diff if diff < 0 else 0)

    store_diff = you[STORE] - opp[STORE]
    house_sum_diff = sum(you[:HOUSES]) - sum(opp[:HOUSES])

    your_moves = len(legal_moves(you))
    opp_moves = len(legal_moves(opp))

    your_extra = count_extra_turn_moves(you)
    opp_extra = count_extra_turn_moves(opp)

    your_caps = count_potential_captures(you, opp)
    opp_caps = count_potential_captures(opp, you)

    # Endgame scaling
    seeds_left = sum(you[:HOUSES]) + sum(opp[:HOUSES])
    endgame_weight = 1.0 + (48 - min(seeds_left, 48)) / 24.0

    score = 0.0
    score += 24.0 * store_diff * endgame_weight
    score += 2.2 * house_sum_diff
    score += 4.0 * (your_moves - opp_moves)
    score += 10.0 * (your_extra - opp_extra)
    score += 8.0 * (your_caps - opp_caps)

    # Starvation / sweep threats
    if sum(opp[:HOUSES]) == 0:
        score += 500
    if sum(you[:HOUSES]) == 0:
        score -= 500

    # Encourage keeping seeds on our side in late game if ahead in store,
    # discourage if behind and need tactical chances.
    if store_diff > 0:
        score += 0.8 * sum(you[:HOUSES])
    else:
        score -= 0.4 * sum(opp[:HOUSES])

    return score


def ordered_moves(you, opp):
    moves = legal_moves(you)
    moves.sort(key=lambda m: immediate_tactical_score(you, opp, m), reverse=True)
    return moves


def negamax(you, opp, depth, alpha, beta, end_time):
    if time.perf_counter() >= end_time:
        raise TimeoutError

    if depth <= 0 or game_over(you, opp):
        return evaluate(you, opp)

    best = -inf
    moves = ordered_moves(you, opp)

    if not moves:
        return evaluate(you, opp)

    for m in moves:
        ny, no, extra, terminal = apply_move(you, opp, m)

        if terminal:
            val = evaluate(ny, no)
        elif extra:
            # Same player moves again; no sign flip.
            val = negamax(ny, no, depth - 1, alpha, beta, end_time)
        else:
            # Opponent to move; swap perspective and negate.
            val = -negamax(no, ny, depth - 1, -beta, -alpha, end_time)

        if val > best:
            best = val
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def choose_safe_legal_move(you, opp):
    moves = legal_moves(you)
    if len(moves) == 1:
        return moves[0]

    # Prefer immediate extra turn, then best tactical move, else first legal.
    best = moves[0]
    best_score = -inf
    for m in moves:
        s = immediate_tactical_score(you, opp, m)
        if s > best_score:
            best_score = s
            best = m
    return best


def policy(you: list[int], opponent: list[int]) -> int:
    # Absolute legality fallback
    legal = [i for i in range(HOUSES) if you[i] > 0]
    if not legal:
        return 0  # should never happen per prompt
    if len(legal) == 1:
        return legal[0]

    start = time.perf_counter()
    end_time = start + TIME_LIMIT

    # Opening shortcut: prioritize extra turns/captures with tiny search.
    best_move = choose_safe_legal_move(you, opponent)

    # Iterative deepening
    depth = 1
    try:
        while True:
            if time.perf_counter() >= end_time:
                break

            moves = ordered_moves(you, opponent)
            current_best_move = moves[0]
            current_best_val = -inf

            alpha = -inf
            beta = inf

            for m in moves:
                if time.perf_counter() >= end_time:
                    raise TimeoutError

                ny, no, extra, terminal = apply_move(you, opponent, m)

                if terminal:
                    val = evaluate(ny, no)
                elif extra:
                    val = negamax(ny, no, depth - 1, alpha, beta, end_time)
                else:
                    val = -negamax(no, ny, depth - 1, -beta, -alpha, end_time)

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = m

                if val > alpha:
                    alpha = val

            best_move = current_best_move
            depth += 1

            # Practical cap to avoid diminishing returns in very branchy positions
            if depth > 10:
                break

    except TimeoutError:
        pass
    except Exception:
        # Never risk disqualification from an unexpected issue.
        return choose_safe_legal_move(you, opponent)

    # Ensure legality
    if 0 <= best_move < HOUSES and you[best_move] > 0:
        return best_move
    return legal[0]
