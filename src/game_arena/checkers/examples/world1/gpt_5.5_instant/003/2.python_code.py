
from functools import lru_cache
import time
import math

# Checkers policy for 8x8 American-style draughts.
# Coordinates: row 0 bottom, row 7 top.
# Black men move toward lower rows; white men move toward higher rows.
# Return format: ((from_row, from_col), (to_row, to_col))


INF = 10**9


def policy(my_men, my_kings, opp_men, opp_kings, color) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.perf_counter()
    TIME_LIMIT = 0.86

    me = color
    opp = 'w' if me == 'b' else 'b'

    root = (
        frozenset(tuple(x) for x in my_men),
        frozenset(tuple(x) for x in my_kings),
        frozenset(tuple(x) for x in opp_men),
        frozenset(tuple(x) for x in opp_kings),
        me
    )

    def inb(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def promote_row(side):
        return 0 if side == 'b' else 7

    def man_dirs(side):
        return [(-1, -1), (-1, 1)] if side == 'b' else [(1, -1), (1, 1)]

    KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]

    @lru_cache(maxsize=200000)
    def legal_moves(state):
        mm, mk, om, ok, side = state
        own_men, own_kings, enemy_men, enemy_kings = mm, mk, om, ok
        occ = own_men | own_kings | enemy_men | enemy_kings
        enemy = enemy_men | enemy_kings

        caps = []
        # Men captures: American checkers men capture only forward.
        for r, c in own_men:
            for dr, dc in man_dirs(side):
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if inb(tr, tc) and (mr, mc) in enemy and (tr, tc) not in occ:
                    caps.append(((r, c), (tr, tc)))

        for r, c in own_kings:
            for dr, dc in KING_DIRS:
                mr, mc = r + dr, c + dc
                tr, tc = r + 2 * dr, c + 2 * dc
                if inb(tr, tc) and (mr, mc) in enemy and (tr, tc) not in occ:
                    caps.append(((r, c), (tr, tc)))

        if caps:
            return tuple(caps)

        moves = []
        for r, c in own_men:
            for dr, dc in man_dirs(side):
                tr, tc = r + dr, c + dc
                if inb(tr, tc) and (tr, tc) not in occ:
                    moves.append(((r, c), (tr, tc)))

        for r, c in own_kings:
            for dr, dc in KING_DIRS:
                tr, tc = r + dr, c + dc
                if inb(tr, tc) and (tr, tc) not in occ:
                    moves.append(((r, c), (tr, tc)))

        return tuple(moves)

    def apply_move(state, move):
        mm, mk, om, ok, side = state
        mm, mk, om, ok = set(mm), set(mk), set(om), set(ok)
        fr, to = move
        r1, c1 = fr
        r2, c2 = to
        is_king = fr in mk

        if fr in mm:
            mm.remove(fr)
        else:
            mk.remove(fr)

        # capture
        if abs(r2 - r1) == 2:
            cap = ((r1 + r2) // 2, (c1 + c2) // 2)
            if cap in om:
                om.remove(cap)
            elif cap in ok:
                ok.remove(cap)

        if is_king:
            mk.add(to)
        else:
            if r2 == promote_row(side):
                mk.add(to)
            else:
                mm.add(to)

        # Swap perspective for next side to move.
        next_side = 'w' if side == 'b' else 'b'
        return (frozenset(om), frozenset(ok), frozenset(mm), frozenset(mk), next_side)

    def square_weight_for(side, r, c, king=False):
        # Encourage centralization, advancement, promotion, and stable edge squares.
        center = 3.5 - (abs(c - 3.5) + abs(r - 3.5)) * 0.35
        edge = 0.18 if c == 0 or c == 7 else 0.0
        if king:
            return center * 0.35 + edge
        if side == 'w':
            advancement = r * 0.18
            promo = 0.75 if r == 6 else 0.0
            back = 0.25 if r == 0 else 0.0
        else:
            advancement = (7 - r) * 0.18
            promo = 0.75 if r == 1 else 0.0
            back = 0.25 if r == 7 else 0.0
        return center * 0.25 + advancement + promo + back + edge

    def count_threats(own_men, own_kings, enemy_men, enemy_kings, side):
        # Number of own pieces currently capturable by the opponent.
        occ = own_men | own_kings | enemy_men | enemy_kings
        own = own_men | own_kings
        threats = 0
        for r, c in enemy_men:
            for dr, dc in man_dirs('w' if side == 'b' else 'b'):
                mr, mc = r + dr, c + dc
                lr, lc = r + 2 * dr, c + 2 * dc
                if inb(lr, lc) and (mr, mc) in own and (lr, lc) not in occ:
                    threats += 1
        for r, c in enemy_kings:
            for dr, dc in KING_DIRS:
                mr, mc = r + dr, c + dc
                lr, lc = r + 2 * dr, c + 2 * dc
                if inb(lr, lc) and (mr, mc) in own and (lr, lc) not in occ:
                    threats += 1
        return threats

    @lru_cache(maxsize=200000)
    def evaluate(state):
        mm, mk, om, ok, side = state

        # Evaluation is from player-to-move perspective in this state.
        my_side = side
        enemy_side = 'w' if side == 'b' else 'b'

        val = 0.0
        val += 100.0 * (len(mm) - len(om))
        val += 175.0 * (len(mk) - len(ok))

        for r, c in mm:
            val += square_weight_for(my_side, r, c, False) * 8.0
        for r, c in mk:
            val += square_weight_for(my_side, r, c, True) * 8.0
        for r, c in om:
            val -= square_weight_for(enemy_side, r, c, False) * 8.0
        for r, c in ok:
            val -= square_weight_for(enemy_side, r, c, True) * 8.0

        # Mobility and mandatory capture opportunities.
        moves = legal_moves(state)
        val += min(len(moves), 12) * 2.0
        if moves and abs(moves[0][1][0] - moves[0][0][0]) == 2:
            val += 18.0

        opp_state = (om, ok, mm, mk, enemy_side)
        opp_moves = legal_moves(opp_state)
        val -= min(len(opp_moves), 12) * 2.0
        if opp_moves and abs(opp_moves[0][1][0] - opp_moves[0][0][0]) == 2:
            val -= 22.0

        val -= 10.0 * count_threats(mm, mk, om, ok, side)
        val += 6.0 * count_threats(om, ok, mm, mk, enemy_side)

        return val

    def terminal_value(state, ply):
        moves = legal_moves(state)
        if not moves:
            return -500000 + ply
        return None

    def move_score(state, move):
        mm, mk, om, ok, side = state
        fr, to = move
        score = 0
        if abs(to[0] - fr[0]) == 2:
            cap = ((to[0] + fr[0]) // 2, (to[1] + fr[1]) // 2)
            score += 1000
            if cap in ok:
                score += 300
            else:
                score += 150
        if fr in mm and to[0] == promote_row(side):
            score += 500
        # Prefer central destinations and forward progress.
        score += int((4 - abs(to[1] - 3.5)) * 8)
        if side == 'w':
            score += to[0] - fr[0]
        else:
            score += fr[0] - to[0]
        return score

    nodes = 0

    def negamax(state, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1

        if nodes & 2047 == 0:
            if time.perf_counter() - start_time > TIME_LIMIT:
                raise TimeoutError

        term = terminal_value(state, ply)
        if term is not None:
            return term
        if depth <= 0:
            return evaluate(state)

        moves = list(legal_moves(state))
        moves.sort(key=lambda m: move_score(state, m), reverse=True)

        best = -INF
        for mv in moves:
            child = apply_move(state, mv)
            val = -negamax(child, depth - 1, -beta, -alpha, ply + 1)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    root_moves = list(legal_moves(root))

    # Absolute safety fallback: if no move is listed, return a syntactically plausible move
    # from any own piece. In valid arena positions this should never be reached.
    if not root_moves:
        pieces = list(root[0] | root[1])
        if pieces:
            fr = pieces[0]
            dirs = KING_DIRS if fr in root[1] else man_dirs(me)
            occ = root[0] | root[1] | root[2] | root[3]
            for dr, dc in dirs:
                to = (fr[0] + dr, fr[1] + dc)
                if inb(*to) and to not in occ:
                    return (fr, to)
            return (fr, fr)
        return ((0, 0), (0, 0))

    # Greedy fallback, already legal.
    root_moves.sort(key=lambda m: move_score(root, m), reverse=True)
    best_move = root_moves[0]

    total_pieces = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    max_depth = 7 if total_pieces <= 8 else 6 if total_pieces <= 14 else 5

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() - start_time > TIME_LIMIT:
                break
            current_best = best_move
            current_val = -INF

            ordered = list(root_moves)
            ordered.sort(key=lambda m: (m == best_move, move_score(root, m)), reverse=True)

            alpha = -INF
            beta = INF
            for mv in ordered:
                child = apply_move(root, mv)
                val = -negamax(child, depth - 1, -beta, -alpha, 1)
                # Small deterministic tie-breaker using move score.
                if val > current_val or (val == current_val and move_score(root, mv) > move_score(root, current_best)):
                    current_val = val
                    current_best = mv
                if val > alpha:
                    alpha = val
                if time.perf_counter() - start_time > TIME_LIMIT:
                    raise TimeoutError

            best_move = current_best
    except TimeoutError:
        pass
    except Exception:
        # Never risk disqualification because of an unexpected edge case.
        return root_moves[0]

    return best_move
