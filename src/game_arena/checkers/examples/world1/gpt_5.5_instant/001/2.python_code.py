
import time
import math
from functools import lru_cache

# Checkers policy for 8x8 American/English-style draughts.
# Coordinates: row 0 bottom, row 7 top.
# Black men move down: row -1. White men move up: row +1.
# Return a single legal move ((fr,fc),(tr,tc)); captures are mandatory.


INF = 10**9
TIME_LIMIT = 0.88


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start = time.time()
    my_men = tuple(sorted(tuple(x) for x in my_men))
    my_kings = tuple(sorted(tuple(x) for x in my_kings))
    opp_men = tuple(sorted(tuple(x) for x in opp_men))
    opp_kings = tuple(sorted(tuple(x) for x in opp_kings))
    side = 1 if color == 'w' else -1

    root = (frozenset(my_men), frozenset(my_kings), frozenset(opp_men), frozenset(opp_kings), side)

    moves = legal_moves(*root)
    if not moves:
        # Should not happen in a legal game state, but return some owned piece move-like tuple if possible.
        allmine = list(my_men) + list(my_kings)
        if allmine:
            p = allmine[0]
            return (p, p)
        return ((0, 0), (0, 0))

    # If only one legal move, return it immediately.
    if len(moves) == 1:
        return moves[0][0]

    # Order root moves tactically.
    moves = order_moves(root, moves, side)

    best_move = moves[0][0]
    best_score = -INF

    # Iterative deepening. Full ply includes side changes; multi-jumps are represented internally.
    max_depth = 7
    for depth in range(1, max_depth + 1):
        if time.time() - start > TIME_LIMIT:
            break
        current_best = best_move
        current_score = -INF
        alpha = -INF
        completed = True

        for mv, child in moves:
            if time.time() - start > TIME_LIMIT:
                completed = False
                break
            score = -negamax(child, depth - 1, -INF, -alpha, -side, start)
            if score > current_score:
                current_score = score
                current_best = mv
            if score > alpha:
                alpha = score

        if completed:
            best_move = current_best
            best_score = current_score
            # Reorder for next iteration.
            moves = sorted(moves, key=lambda mc: (0 if mc[0] != best_move else 1, quick_move_score(root, mc, side)), reverse=True)
        else:
            break

    return best_move


def inside(r, c):
    return 0 <= r < 8 and 0 <= c < 8


def man_dirs(side):
    return ((side, -1), (side, 1))


def king_dirs():
    return ((1, -1), (1, 1), (-1, -1), (-1, 1))


def legal_moves(my_men, my_kings, opp_men, opp_kings, side):
    """Return list of (first_step_move, resulting_state_after_complete_turn)."""
    my_men = frozenset(my_men)
    my_kings = frozenset(my_kings)
    opp_men = frozenset(opp_men)
    opp_kings = frozenset(opp_kings)

    caps = []
    occupied = my_men | my_kings | opp_men | opp_kings

    for p in my_men:
        caps.extend(capture_sequences(p, False, my_men, my_kings, opp_men, opp_kings, side, p, None))
    for p in my_kings:
        caps.extend(capture_sequences(p, True, my_men, my_kings, opp_men, opp_kings, side, p, None))

    if caps:
        return caps

    moves = []
    for r, c in my_men:
        for dr, dc in man_dirs(side):
            nr, nc = r + dr, c + dc
            if inside(nr, nc) and (nr, nc) not in occupied:
                nmen = set(my_men)
                nkings = set(my_kings)
                nmen.remove((r, c))
                if (side == 1 and nr == 7) or (side == -1 and nr == 0):
                    nkings.add((nr, nc))
                else:
                    nmen.add((nr, nc))
                child = canonical_state(opp_men, opp_kings, nmen, nkings, -side)
                moves.append((((r, c), (nr, nc)), child))

    for r, c in my_kings:
        for dr, dc in king_dirs():
            nr, nc = r + dr, c + dc
            if inside(nr, nc) and (nr, nc) not in occupied:
                nkings = set(my_kings)
                nkings.remove((r, c))
                nkings.add((nr, nc))
                child = canonical_state(opp_men, opp_kings, my_men, nkings, -side)
                moves.append((((r, c), (nr, nc)), child))

    return moves


def capture_sequences(pos, is_king, my_men, my_kings, opp_men, opp_kings, side, start_pos, first_move):
    """Generate all completed capture-turn states. Men capture forward only; kings all directions."""
    r, c = pos
    dirs = king_dirs() if is_king else man_dirs(side)
    found = False
    results = []

    occupied = my_men | my_kings | opp_men | opp_kings

    for dr, dc in dirs:
        mr, mc = r + dr, c + dc
        lr, lc = r + 2 * dr, c + 2 * dc
        if not inside(lr, lc):
            continue
        mid = (mr, mc)
        land = (lr, lc)
        if mid not in (opp_men | opp_kings) or land in occupied:
            continue

        found = True
        n_my_men = set(my_men)
        n_my_kings = set(my_kings)
        n_opp_men = set(opp_men)
        n_opp_kings = set(opp_kings)

        if is_king:
            n_my_kings.remove(pos)
        else:
            n_my_men.remove(pos)

        if mid in n_opp_men:
            n_opp_men.remove(mid)
        else:
            n_opp_kings.remove(mid)

        promoted = False
        next_is_king = is_king
        if (not is_king) and ((side == 1 and lr == 7) or (side == -1 and lr == 0)):
            # In American checkers, a man reaching king row by jump stops and crowns.
            n_my_kings.add(land)
            promoted = True
            next_is_king = True
        else:
            if is_king:
                n_my_kings.add(land)
            else:
                n_my_men.add(land)

        fm = first_move if first_move is not None else (start_pos, land)

        if promoted:
            child = canonical_state(frozenset(n_opp_men), frozenset(n_opp_kings),
                                    frozenset(n_my_men), frozenset(n_my_kings), -side)
            results.append((fm, child))
        else:
            more = capture_sequences(land, next_is_king,
                                     frozenset(n_my_men), frozenset(n_my_kings),
                                     frozenset(n_opp_men), frozenset(n_opp_kings),
                                     side, start_pos, fm)
            results.extend(more)

    if not found and first_move is not None:
        child = canonical_state(opp_men, opp_kings, my_men, my_kings, -side)
        results.append((first_move, child))

    return results


def canonical_state(my_men, my_kings, opp_men, opp_kings, side):
    return (frozenset(my_men), frozenset(my_kings), frozenset(opp_men), frozenset(opp_kings), side)


def order_moves(state, moves, side):
    return sorted(moves, key=lambda mc: quick_move_score(state, mc, side), reverse=True)


def quick_move_score(state, move_child, side):
    mv, child = move_child
    (fr, fc), (tr, tc) = mv
    my_men, my_kings, opp_men, opp_kings, s = state
    c_my_men, c_my_kings, c_opp_men, c_opp_kings, cs = child

    # child is opponent-to-move perspective, so captured opponent pieces are reductions in child opp sets
    captured = (len(opp_men) + len(opp_kings)) - (len(c_my_men) + len(c_my_kings))
    promo = 0
    if (fr, fc) in my_men and ((side == 1 and tr == 7) or (side == -1 and tr == 0)):
        promo = 1

    center = 4 - abs(3.5 - tr) - abs(3.5 - tc)
    edge_penalty = 1 if tc in (0, 7) else 0

    return captured * 1000 + promo * 500 + center * 10 + edge_penalty * 6


def negamax(state, depth, alpha, beta, side, start):
    if time.time() - start > TIME_LIMIT:
        return evaluate(state, side)

    moves = legal_moves(*state)
    if not moves:
        return -50000 - depth

    if depth <= 0:
        return quiesce(state, alpha, beta, side, start, 2)

    moves = order_moves(state, moves, side)
    best = -INF

    for mv, child in moves:
        val = -negamax(child, depth - 1, -beta, -alpha, -side, start)
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
        if time.time() - start > TIME_LIMIT:
            break

    return best


def quiesce(state, alpha, beta, side, start, qdepth):
    stand = evaluate(state, side)
    if stand >= beta:
        return beta
    if stand > alpha:
        alpha = stand
    if qdepth <= 0 or time.time() - start > TIME_LIMIT:
        return alpha

    moves = legal_moves(*state)
    # Only extend if captures are available.
    capture_moves = []
    my_men, my_kings, opp_men, opp_kings, s = state
    for mc in moves:
        mv, child = mc
        if abs(mv[0][0] - mv[1][0]) == 2:
            capture_moves.append(mc)

    if not capture_moves:
        return alpha

    capture_moves = order_moves(state, capture_moves, side)
    for mv, child in capture_moves:
        val = -quiesce(child, -beta, -alpha, -side, start, qdepth - 1)
        if val >= beta:
            return beta
        if val > alpha:
            alpha = val
    return alpha


def evaluate(state, side):
    """Evaluate from player-to-move perspective in state."""
    my_men, my_kings, opp_men, opp_kings, s = state

    score = 0

    # Material.
    score += 100 * (len(my_men) - len(opp_men))
    score += 175 * (len(my_kings) - len(opp_kings))

    # Advancement and promotion pressure.
    for r, c in my_men:
        adv = r if s == 1 else 7 - r
        score += adv * 6
        if (s == 1 and r == 6) or (s == -1 and r == 1):
            score += 22
        if c in (0, 7):
            score += 5
        score += int((3.5 - abs(c - 3.5)) * 3)
        score += int((3.5 - abs(r - 3.5)) * 2)

    for r, c in opp_men:
        adv = r if s == -1 else 7 - r
        score -= adv * 6
        if (s == -1 and r == 6) or (s == 1 and r == 1):
            score -= 22
        if c in (0, 7):
            score -= 5
        score -= int((3.5 - abs(c - 3.5)) * 3)
        score -= int((3.5 - abs(r - 3.5)) * 2)

    # Kings: center and mobility-like placement.
    for r, c in my_kings:
        score += int((3.5 - abs(c - 3.5)) * 5 + (3.5 - abs(r - 3.5)) * 5)
        if c in (0, 7):
            score -= 4
    for r, c in opp_kings:
        score -= int((3.5 - abs(c - 3.5)) * 5 + (3.5 - abs(r - 3.5)) * 5)
        if c in (0, 7):
            score += 4

    # Back row guard: useful early/midgame.
    if len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings) > 10:
        back = 0 if s == 1 else 7
        oback = 7 if s == 1 else 0
        score += 8 * sum(1 for p in my_men if p[0] == back)
        score -= 8 * sum(1 for p in opp_men if p[0] == oback)

    # Mobility.
    my_mob = pseudo_mobility(my_men, my_kings, opp_men, opp_kings, s)
    opp_mob = pseudo_mobility(opp_men, opp_kings, my_men, my_kings, -s)
    score += 4 * (my_mob - opp_mob)

    # Tactical vulnerability: pieces capturable immediately.
    score -= 28 * vulnerable_count(my_men, my_kings, opp_men, opp_kings, s)
    score += 24 * vulnerable_count(opp_men, opp_kings, my_men, my_kings, -s)

    return score


def pseudo_mobility(my_men, my_kings, opp_men, opp_kings, side):
    occ = my_men | my_kings | opp_men | opp_kings
    m = 0
    for r, c in my_men:
        for dr, dc in man_dirs(side):
            if inside(r + dr, c + dc) and (r + dr, c + dc) not in occ:
                m += 1
    for r, c in my_kings:
        for dr, dc in king_dirs():
            if inside(r + dr, c + dc) and (r + dr, c + dc) not in occ:
                m += 1
    return m


def vulnerable_count(my_men, my_kings, opp_men, opp_kings, side):
    """Count our pieces that opponent can jump next, approximate but legal-direction aware."""
    occ = my_men | my_kings | opp_men | opp_kings
    mine = my_men | my_kings
    count = 0
    for pr, pc in mine:
        vulnerable = False

        # Opp men capture in direction -side.
        for dr, dc in man_dirs(-side):
            ar, ac = pr - dr, pc - dc     # opponent piece square
            lr, lc = pr + dr, pc + dc     # landing beyond us
            if inside(ar, ac) and inside(lr, lc) and (lr, lc) not in occ and (ar, ac) in opp_men:
                vulnerable = True
                break

        if not vulnerable:
            for dr, dc in king_dirs():
                ar, ac = pr - dr, pc - dc
                lr, lc = pr + dr, pc + dc
                if inside(ar, ac) and inside(lr, lc) and (lr, lc) not in occ and (ar, ac) in opp_kings:
                    vulnerable = True
                    break

        if vulnerable:
            count += 1
    return count
