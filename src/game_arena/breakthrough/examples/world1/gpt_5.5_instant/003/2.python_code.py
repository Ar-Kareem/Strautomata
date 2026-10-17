
from functools import lru_cache
import time
import math

BOARD_N = 8
INF = 10**9

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start = time.perf_counter()
    deadline = start + 0.92

    my_dir = -1 if color == 'b' else 1
    op_dir = -my_dir
    my_goal = 0 if color == 'b' else 7
    op_goal = 7 if color == 'b' else 0

    me_t = tuple(sorted(me))
    opp_t = tuple(sorted(opp))

    def inb(r, c):
        return 0 <= r < 8 and 0 <= c < 8

    def legal_moves(side, other, d):
        sset = set(side)
        oset = set(other)
        occ = sset | oset
        moves = []
        for r, c in side:
            nr = r + d
            if 0 <= nr < 8:
                # diagonal moves, including capture or quiet diagonal
                for dc in (-1, 1):
                    nc = c + dc
                    if 0 <= nc < 8 and (nr, nc) not in sset:
                        moves.append(((r, c), (nr, nc)))
                # straight quiet only
                if (nr, c) not in occ:
                    moves.append(((r, c), (nr, c)))
        return moves

    def apply_move(side, other, mv):
        fr, to = mv
        side_l = list(side)
        other_l = list(other)
        try:
            side_l.remove(fr)
        except ValueError:
            pass
        side_l.append(to)
        if to in other_l:
            other_l.remove(to)
        return tuple(sorted(side_l)), tuple(sorted(other_l))

    def is_win(side, other, goal):
        return (not other) or any(r == goal for r, c in side)

    root_moves = legal_moves(me_t, opp_t, my_dir)
    if not root_moves:
        # Should not happen in normal Breakthrough, but return a harmless fallback if possible.
        return (me[0], me[0]) if me else ((0, 0), (0, 0))

    # Immediate winning move.
    for mv in root_moves:
        ns, no = apply_move(me_t, opp_t, mv)
        if is_win(ns, no, my_goal):
            return mv

    def dist_to_goal(r, goal):
        return abs(goal - r)

    def attackers_of(square, enemy, enemy_dir):
        r, c = square
        # Enemy attacks square from one row behind relative to its movement.
        er = r - enemy_dir
        if not (0 <= er < 8):
            return 0
        return ((er, c - 1) in enemy) + ((er, c + 1) in enemy)

    def defenders_of(square, side, d):
        r, c = square
        br = r - d
        if not (0 <= br < 8):
            return 0
        return ((br, c - 1) in side) + ((br, c + 1) in side)

    def passed_bonus(piece, enemies, d):
        r, c = piece
        # Passed if no enemy in same/adjacent files ahead.
        rr = r + d
        while 0 <= rr < 8:
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < 8 and (rr, cc) in enemies:
                    return 0
            rr += d
        return 90

    @lru_cache(maxsize=200000)
    def evaluate(my_side, op_side):
        my_side = tuple(my_side)
        op_side = tuple(op_side)
        my_set = set(my_side)
        op_set = set(op_side)

        if is_win(my_side, op_side, my_goal):
            return INF - 1000
        if is_win(op_side, my_side, op_goal):
            return -INF + 1000

        score = 0
        score += (len(my_side) - len(op_side)) * 130

        my_min_dist = 99
        op_min_dist = 99

        for p in my_side:
            r, c = p
            dgoal = dist_to_goal(r, my_goal)
            my_min_dist = min(my_min_dist, dgoal)
            adv = 7 - dgoal
            score += adv * adv * 8 + adv * 9
            score += passed_bonus(p, op_set, my_dir)
            defs = defenders_of(p, my_set, my_dir)
            atks = attackers_of(p, op_set, op_dir)
            score += defs * 18
            if atks and not defs:
                score -= 35
            elif atks:
                score -= 10
            # Central files are slightly better.
            score += 6 - abs(3.5 - c) * 2

        for p in op_side:
            r, c = p
            dgoal = dist_to_goal(r, op_goal)
            op_min_dist = min(op_min_dist, dgoal)
            adv = 7 - dgoal
            score -= adv * adv * 8 + adv * 9
            score -= passed_bonus(p, my_set, op_dir)
            defs = defenders_of(p, op_set, op_dir)
            atks = attackers_of(p, my_set, my_dir)
            score -= defs * 18
            if atks and not defs:
                score += 35
            elif atks:
                score += 10
            score -= 6 - abs(3.5 - c) * 2

        # Race term: being closer to promotion is extremely important.
        score += (op_min_dist - my_min_dist) * 85

        return int(score)

    def move_priority(mv, side, other, d, goal):
        fr, to = mv
        tr, tc = to
        val = 0
        if tr == goal:
            val += 100000
        if to in other:
            val += 5000
        val += (7 - dist_to_goal(tr, goal)) * 200
        val += int(30 - abs(3.5 - tc) * 6)
        ns, no = apply_move(side, other, mv)
        val += evaluate(ns, no) // 20
        return val

    def ordered_moves(side, other, d, goal):
        ms = legal_moves(side, other, d)
        return sorted(ms, key=lambda m: move_priority(m, set(side), set(other), d, goal), reverse=True)

    nodes = 0

    def alphabeta(my_side, op_side, depth, alpha, beta, maximizing):
        nonlocal nodes
        nodes += 1
        if nodes & 255 == 0 and time.perf_counter() > deadline:
            raise TimeoutError

        if is_win(my_side, op_side, my_goal):
            return INF - (20 - depth)
        if is_win(op_side, my_side, op_goal):
            return -INF + (20 - depth)
        if depth == 0:
            return evaluate(my_side, op_side)

        if maximizing:
            best = -INF
            ms = ordered_moves(my_side, op_side, my_dir, my_goal)
            if not ms:
                return -INF // 2
            for mv in ms:
                ns, no = apply_move(my_side, op_side, mv)
                val = alphabeta(ns, no, depth - 1, alpha, beta, False)
                if val > best:
                    best = val
                alpha = max(alpha, best)
                if alpha >= beta:
                    break
            return best
        else:
            best = INF
            ms = ordered_moves(op_side, my_side, op_dir, op_goal)
            if not ms:
                return INF // 2
            for mv in ms:
                no, ns = apply_move(op_side, my_side, mv)
                val = alphabeta(ns, no, depth - 1, alpha, beta, True)
                if val < best:
                    best = val
                beta = min(beta, best)
                if alpha >= beta:
                    break
            return best

    # Tactical safety: if opponent has a one-move win, prefer moves that stop it.
    best_move = max(root_moves, key=lambda m: move_priority(m, set(me_t), set(opp_t), my_dir, my_goal))

    max_depth = 5
    if len(me_t) + len(opp_t) <= 16:
        max_depth = 7
    elif len(me_t) + len(opp_t) <= 24:
        max_depth = 6

    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() > deadline:
                break
            current_best = best_move
            current_score = -INF
            moves = ordered_moves(me_t, opp_t, my_dir, my_goal)
            # Search previous best first.
            if best_move in moves:
                moves.remove(best_move)
                moves.insert(0, best_move)

            alpha = -INF
            beta = INF
            for mv in moves:
                ns, no = apply_move(me_t, opp_t, mv)

                # Avoid moves allowing immediate enemy promotion/capture win when alternatives exist.
                if is_win(ns, no, my_goal):
                    val = INF
                else:
                    val = alphabeta(ns, no, depth - 1, alpha, beta, False)

                if val > current_score:
                    current_score = val
                    current_best = mv
                alpha = max(alpha, current_score)

            best_move = current_best
    except TimeoutError:
        pass
    except Exception:
        # Absolute safety: never fail to return legal move.
        pass

    # Final legality guard.
    if best_move in root_moves:
        return best_move
    return root_moves[0]
