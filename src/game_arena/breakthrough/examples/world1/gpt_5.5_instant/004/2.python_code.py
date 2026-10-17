
import math
import time
from functools import lru_cache

BOARD_N = 8
INF = 10**9


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.time()
    time_limit = 0.92

    my_dir = -1 if color == "b" else 1
    opp_color = "w" if color == "b" else "b"
    opp_dir = -my_dir
    my_goal = 0 if color == "b" else 7
    opp_goal = 7 if color == "b" else 0

    me_t = tuple(sorted(me))
    opp_t = tuple(sorted(opp))

    def inb(r, c):
        return 0 <= r < BOARD_N and 0 <= c < BOARD_N

    def gen_moves(side, enemy, side_color):
        d = -1 if side_color == "b" else 1
        side_set = set(side)
        enemy_set = set(enemy)
        occ = side_set | enemy_set
        moves = []
        for r, c in side:
            nr = r + d
            if not (0 <= nr < BOARD_N):
                continue
            # straight, only if empty
            if (nr, c) not in occ:
                moves.append(((r, c), (nr, c)))
            # diagonals, empty or capture
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < BOARD_N and (nr, nc) not in side_set:
                    moves.append(((r, c), (nr, nc)))
        return moves

    def apply_move(side, enemy, mv):
        fr, to = mv
        side_l = list(side)
        enemy_l = list(enemy)
        try:
            idx = side_l.index(fr)
            side_l[idx] = to
        except ValueError:
            return tuple(side), tuple(enemy)
        if to in enemy_l:
            enemy_l.remove(to)
        return tuple(sorted(side_l)), tuple(sorted(enemy_l))

    legal = gen_moves(me_t, opp_t, color)
    if not legal:
        return ((0, 0), (0, 0))
    fallback = legal[0]

    # Immediate win
    for mv in legal:
        if mv[1][0] == my_goal:
            return mv
        nm, no = apply_move(me_t, opp_t, mv)
        if not no:
            return mv

    # Immediate defense: capture/block opponent pieces that can win next turn when possible.
    opp_winners = []
    for omv in gen_moves(opp_t, me_t, opp_color):
        if omv[1][0] == opp_goal:
            opp_winners.append(omv)
    if opp_winners:
        danger_from = {m[0] for m in opp_winners}
        danger_to = {m[1] for m in opp_winners}
        candidates = []
        for mv in legal:
            score = 0
            if mv[1] in danger_from:
                score += 10000
            if mv[1] in danger_to:
                score += 5000
            if mv[1] in opp_t:
                score += 1000
            if score:
                candidates.append((score, mv))
        if candidates:
            candidates.sort(reverse=True)
            return candidates[0][1]

    def terminal_score(my_side, enemy_side, side_to_eval_color):
        # score from root player's perspective; my_side is root pieces, enemy_side opp pieces
        if not enemy_side:
            return INF - 1000
        if not my_side:
            return -INF + 1000
        if any(r == my_goal for r, c in my_side):
            return INF - 1000
        if any(r == opp_goal for r, c in enemy_side):
            return -INF + 1000
        return None

    def dist_to_goal(r, col):
        return r if color == "b" else 7 - r

    def opp_dist_to_goal(r, col):
        return 7 - r if color == "b" else r

    def evaluate(my_side, enemy_side):
        term = terminal_score(my_side, enemy_side, color)
        if term is not None:
            return term

        my_set = set(my_side)
        en_set = set(enemy_side)
        score = 0

        # Material
        score += 115 * (len(my_side) - len(enemy_side))

        # Advancement, nonlinear bonus for nearing goal
        for r, c in my_side:
            adv = 7 - dist_to_goal(r, c)
            score += 12 * adv + 3 * adv * adv
            if c in (2, 3, 4, 5):
                score += 6
            if c in (0, 7):
                score -= 4

            nr = r + my_dir
            # promotion threat
            if nr == my_goal:
                score += 170
            # passed pawn-ish: no enemy in forward cone
            blocked = False
            rr = r + my_dir
            while 0 <= rr < BOARD_N:
                for cc in (c - 1, c, c + 1):
                    if 0 <= cc < BOARD_N and (rr, cc) in en_set:
                        blocked = True
                        break
                if blocked:
                    break
                rr += my_dir
            if not blocked:
                score += 65 + 10 * adv

            # support behind diagonals
            br = r - my_dir
            if (br, c - 1) in my_set or (br, c + 1) in my_set:
                score += 18
            # can be captured next
            ar = r - my_dir
            attackers = 0
            if (ar, c - 1) in en_set:
                attackers += 1
            if (ar, c + 1) in en_set:
                attackers += 1
            defenders = 0
            if (br, c - 1) in my_set:
                defenders += 1
            if (br, c + 1) in my_set:
                defenders += 1
            if attackers and defenders == 0:
                score -= 35 * attackers
            elif attackers:
                score -= 10 * attackers

        for r, c in enemy_side:
            adv = 7 - opp_dist_to_goal(r, c)
            score -= 12 * adv + 3 * adv * adv
            if c in (2, 3, 4, 5):
                score -= 6
            if c in (0, 7):
                score += 4
            nr = r + opp_dir
            if nr == opp_goal:
                score -= 190

            blocked = False
            rr = r + opp_dir
            while 0 <= rr < BOARD_N:
                for cc in (c - 1, c, c + 1):
                    if 0 <= cc < BOARD_N and (rr, cc) in my_set:
                        blocked = True
                        break
                if blocked:
                    break
                rr += opp_dir
            if not blocked:
                score -= 70 + 10 * adv

            br = r - opp_dir
            if (br, c - 1) in en_set or (br, c + 1) in en_set:
                score -= 18

        # Mobility
        score += 2 * len(gen_moves(tuple(my_side), tuple(enemy_side), color))
        score -= 2 * len(gen_moves(tuple(enemy_side), tuple(my_side), opp_color))
        return score

    def move_order(moves, side, enemy, side_color, maximizing):
        d = -1 if side_color == "b" else 1
        goal = 0 if side_color == "b" else 7
        enemy_set = set(enemy)
        ordered = []
        for mv in moves:
            fr, to = mv
            val = 0
            if to[0] == goal:
                val += 100000
            if to in enemy_set:
                val += 5000
            # advancement
            val += (fr[0] - to[0]) * 20 if side_color == "b" else (to[0] - fr[0]) * 20
            # central
            val += 5 * (4 - abs(3.5 - to[1]))
            # prefer near-goal threats
            if to[0] + d == goal:
                val += 1000
            ordered.append((val, mv))
        ordered.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in ordered]

    @lru_cache(maxsize=200000)
    def search(my_side, enemy_side, turn_color, depth, alpha, beta):
        if time.time() - start_time > time_limit:
            raise TimeoutError

        term = terminal_score(my_side, enemy_side, color)
        if term is not None:
            return term
        if depth <= 0:
            return evaluate(my_side, enemy_side)

        if turn_color == color:
            moves = gen_moves(my_side, enemy_side, color)
            if not moves:
                return -INF + 10
            best = -INF
            for mv in move_order(moves, my_side, enemy_side, color, True):
                nm, ne = apply_move(my_side, enemy_side, mv)
                val = search(nm, ne, opp_color, depth - 1, alpha, beta)
                if val > best:
                    best = val
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
            return best
        else:
            moves = gen_moves(enemy_side, my_side, opp_color)
            if not moves:
                return INF - 10
            best = INF
            for mv in move_order(moves, enemy_side, my_side, opp_color, False):
                ne, nm = apply_move(enemy_side, my_side, mv)
                val = search(nm, ne, color, depth - 1, alpha, beta)
                if val < best:
                    best = val
                beta = min(beta, best)
                if alpha >= beta:
                    break
            return best

    best_move = fallback
    best_score = -INF

    # Adaptive iterative deepening. Depth 4 is usually feasible; depth 5 in reduced positions.
    piece_count = len(me_t) + len(opp_t)
    max_depth = 4
    if piece_count <= 18:
        max_depth = 5
    if piece_count <= 10:
        max_depth = 6

    try:
        for depth in range(1, max_depth + 1):
            current_best = best_move
            current_score = -INF
            ordered = move_order(legal, me_t, opp_t, color, True)
            for mv in ordered:
                if time.time() - start_time > time_limit:
                    raise TimeoutError
                nm, no = apply_move(me_t, opp_t, mv)
                val = search(nm, no, opp_color, depth - 1, -INF, INF)
                # Small deterministic tie-breaker toward advancement/captures
                if mv[1] in opp_t:
                    val += 2
                val += (mv[0][0] - mv[1][0]) if color == "b" else (mv[1][0] - mv[0][0])
                if val > current_score:
                    current_score = val
                    current_best = mv
            best_move, best_score = current_best, current_score
    except TimeoutError:
        pass
    except Exception:
        return fallback

    # Final legality guard
    if best_move in legal:
        return best_move
    return fallback
