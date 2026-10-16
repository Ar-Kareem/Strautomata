
# Kalah policy for a standard 6-house board.
# API:
#   policy(you: list[int], opponent: list[int]) -> int

import time
import math

HOUSES = 6
STORE = 6
INF = 10**12


def _legal(side):
    return [i for i in range(HOUSES) if side[i] > 0]


def _terminal(you, opp):
    return all(x == 0 for x in you[:HOUSES]) or all(x == 0 for x in opp[:HOUSES])


def _final_score(you, opp):
    ys = you[STORE] + sum(you[:HOUSES])
    os = opp[STORE] + sum(opp[:HOUSES])
    return ys - os


def _simulate_cur_move(cur, other, move):
    """
    Simulate a move by the current player.
    Returns: new_cur, new_other, extra_turn
    If game ends, remaining house seeds are swept into stores.
    """
    cur = cur[:]
    other = other[:]

    seeds = cur[move]
    cur[move] = 0

    # 13 sowing positions, skipping opponent store:
    # cur houses move+1..5, cur store, other houses 0..5, cur houses 0..5 ...
    pos_side = 0  # 0=current side, 1=other side
    idx = move
    last_side = 0
    last_idx = move

    while seeds:
        if pos_side == 0:
            idx += 1
            if idx == STORE:
                cur[STORE] += 1
                seeds -= 1
                last_side = 0
                last_idx = STORE
                if seeds == 0:
                    break
                pos_side = 1
                idx = -1
            elif idx < HOUSES:
                cur[idx] += 1
                seeds -= 1
                last_side = 0
                last_idx = idx
            else:
                pos_side = 1
                idx = -1
        else:
            idx += 1
            if idx < HOUSES:
                other[idx] += 1
                seeds -= 1
                last_side = 1
                last_idx = idx
            else:
                pos_side = 0
                idx = -1

    extra = (last_side == 0 and last_idx == STORE)

    # Capture: last seed lands in an own empty house and opposite has seeds.
    if last_side == 0 and 0 <= last_idx < HOUSES and cur[last_idx] == 1:
        opp_idx = HOUSES - 1 - last_idx
        if other[opp_idx] > 0:
            cur[STORE] += other[opp_idx] + 1
            other[opp_idx] = 0
            cur[last_idx] = 0

    # Endgame sweep.
    if all(x == 0 for x in cur[:HOUSES]) or all(x == 0 for x in other[:HOUSES]):
        cur[STORE] += sum(cur[:HOUSES])
        other[STORE] += sum(other[:HOUSES])
        for i in range(HOUSES):
            cur[i] = 0
            other[i] = 0

    return cur, other, extra


def _simulate_root(you, opp, move):
    return _simulate_cur_move(you, opp, move)


def _extra_turn_moves(side):
    # Last seed in store iff seeds == 6 - i mod 13.
    out = 0
    for i in range(HOUSES):
        if side[i] > 0 and side[i] % 13 == (STORE - i):
            out += 1
    return out


def _capture_potential(side, other):
    score = 0
    for i in range(HOUSES):
        s = side[i]
        if s <= 0:
            continue
        # Check exact landing on own house j after sowing.
        # For typical Kalah counts this simple simulation-like test is cheap.
        c, o, extra = _simulate_cur_move(side, other, i)
        gain = c[STORE] - side[STORE]
        # Store seed(s) may be normal sowing; value high captures especially.
        if not extra and gain > 1:
            score += gain
    return score


def _evaluate_root_perspective(root, other):
    """
    root is the original 'you' side, other is original opponent.
    Positive is good for root.
    """
    if _terminal(root, other):
        return 1000000 * _final_score(root, other)

    store_diff = root[STORE] - other[STORE]
    my_seeds = sum(root[:HOUSES])
    op_seeds = sum(other[:HOUSES])
    total_houses = my_seeds + op_seeds

    # Positional factors.
    my_extra = _extra_turn_moves(root)
    op_extra = _extra_turn_moves(other)
    my_cap = _capture_potential(root, other)
    op_cap = _capture_potential(other, root)

    # Seeds closer to store are slightly better for the player.
    my_advance = sum((i + 1) * root[i] for i in range(HOUSES))
    op_advance = sum((i + 1) * other[i] for i in range(HOUSES))

    # Early/mid: keep seeds and tempo; late: store score dominates.
    phase = max(0.0, min(1.0, total_houses / 72.0))

    val = 0
    val += 120.0 * store_diff
    val += (4.0 + 6.0 * (1.0 - phase)) * (my_seeds - op_seeds)
    val += 10.0 * (my_extra - op_extra)
    val += 7.0 * (my_cap - op_cap)
    val += 0.45 * (my_advance - op_advance)

    # Starvation/endgame awareness.
    my_nonempty = sum(1 for x in root[:HOUSES] if x)
    op_nonempty = sum(1 for x in other[:HOUSES] if x)
    val += 2.5 * (my_nonempty - op_nonempty)

    return val


def _move_order(cur, other, maximizing):
    moves = _legal(cur)
    scored = []
    for m in moves:
        nc, no, extra = _simulate_cur_move(cur, other, m)
        gain = nc[STORE] - cur[STORE]
        # Prefer extra turns, captures/store gain, and moves from right side.
        score = 1000 * int(extra) + 40 * gain + m
        # Prefer ending positions that are good for current mover.
        if _terminal(nc, no):
            score += 100000 + 1000 * _final_score(nc, no)
        scored.append((score, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]


def policy(you: list[int], opponent: list[int]) -> int:
    legal = _legal(you)
    if not legal:
        return 0
    fallback = legal[0]

    try:
        start = time.perf_counter()
        # Conservative budget for arena safety.
        budget = 0.82

        best_move = fallback
        best_val = -INF

        # Transposition cache local to this move.
        tt = {}

        def timed_out():
            return (time.perf_counter() - start) > budget

        def key(cur, other, root_turn, depth):
            return (tuple(cur), tuple(other), root_turn, depth)

        def search(cur, other, depth, alpha, beta, root_turn):
            """
            cur/other are sides in original orientation:
              root_turn=True  -> root player to move, moves on cur=root side.
              root_turn=False -> opponent to move, moves on other side.
            """
            if timed_out():
                raise TimeoutError

            root = cur
            opp = other

            if depth <= 0 or _terminal(root, opp):
                return _evaluate_root_perspective(root, opp)

            k = key(root, opp, root_turn, depth)
            if k in tt:
                return tt[k]

            if root_turn:
                moves = _move_order(root, opp, True)
                if not moves:
                    return _evaluate_root_perspective(root, opp)
                val = -INF
                for m in moves:
                    nr, no, extra = _simulate_cur_move(root, opp, m)
                    if extra and not _terminal(nr, no):
                        child = search(nr, no, depth - 1, alpha, beta, True)
                    else:
                        child = search(nr, no, depth - 1, alpha, beta, False)
                    if child > val:
                        val = child
                    if val > alpha:
                        alpha = val
                    if alpha >= beta:
                        break
            else:
                # Opponent moves; simulate with opponent as current, then map back.
                moves = _move_order(opp, root, False)
                if not moves:
                    return _evaluate_root_perspective(root, opp)
                val = INF
                for m in moves:
                    no_cur, nr_other, extra = _simulate_cur_move(opp, root, m)
                    # no_cur is new opponent side, nr_other is new root side.
                    nr = nr_other
                    no = no_cur
                    if extra and not _terminal(nr, no):
                        child = search(nr, no, depth - 1, alpha, beta, False)
                    else:
                        child = search(nr, no, depth - 1, alpha, beta, True)
                    if child < val:
                        val = child
                    if val < beta:
                        beta = val
                    if alpha >= beta:
                        break

            tt[k] = val
            return val

        # Immediate tactical ordering at root.
        root_moves = _move_order(you, opponent, True)
        if root_moves:
            best_move = root_moves[0]

        # Iterative deepening. Extra turns are handled inside the tree.
        # Depth here counts plies, including repeated turns.
        max_depth = 10
        for depth in range(1, max_depth + 1):
            if timed_out():
                break
            current_best = best_move
            current_val = -INF
            alpha = -INF
            beta = INF

            for m in root_moves:
                if timed_out():
                    raise TimeoutError
                ny, no, extra = _simulate_root(you, opponent, m)
                if _terminal(ny, no):
                    val = _evaluate_root_perspective(ny, no)
                elif extra:
                    val = search(ny, no, depth - 1, alpha, beta, True)
                else:
                    val = search(ny, no, depth - 1, alpha, beta, False)

                # Small deterministic tie-breaker favoring extra turn/store gain.
                gain = ny[STORE] - you[STORE]
                val += 0.001 * gain + 0.0001 * m

                if val > current_val:
                    current_val = val
                    current_best = m
                if val > alpha:
                    alpha = val

            best_move = current_best
            best_val = current_val

        if best_move in legal:
            return int(best_move)
        return int(fallback)

    except Exception:
        # Absolute safety: never return an illegal move.
        return int(fallback)
