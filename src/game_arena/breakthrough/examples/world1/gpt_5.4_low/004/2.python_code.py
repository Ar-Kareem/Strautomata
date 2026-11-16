
import time
from typing import List, Tuple

Move = Tuple[Tuple[int, int], Tuple[int, int]]

INF = 10**9


def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Move:
    start = time.perf_counter()
    deadline = start + 0.92

    me = tuple(sorted(me))
    opp = tuple(sorted(opp))

    legal = generate_moves(me, opp, color)
    if not legal:
        return ((0, 0), (0, 0))

    fallback = legal[0]

    for mv in legal:
        me2, opp2 = apply_move(me, opp, mv)
        if is_win(me2, opp2, color):
            return mv

    opp_color = other(color)
    opp_wins = set()
    for omv in generate_moves(opp, me, opp_color):
        opp2, me2 = apply_move(opp, me, omv)
        if is_win(opp2, me2, opp_color):
            opp_wins.add(omv[1])

    if opp_wins:
        blockers = []
        for mv in legal:
            if mv[1] in opp_wins:
                blockers.append(mv)
            else:
                me2, opp2 = apply_move(me, opp, mv)
                bad = False
                for omv in generate_moves(opp2, me2, opp_color):
                    opp3, me3 = apply_move(opp2, me2, omv)
                    if is_win(opp3, me3, opp_color):
                        bad = True
                        break
                if not bad:
                    blockers.append(mv)
        if blockers:
            legal = blockers
            fallback = legal[0]

    best_move = fallback
    best_score = -INF
    tt = {}

    class Timeout(Exception):
        pass

    def check_time():
        if time.perf_counter() >= deadline:
            raise Timeout()

    def negamax(cur_me, cur_opp, cur_color, depth, alpha, beta):
        check_time()

        key = (cur_me, cur_opp, cur_color, depth)
        if key in tt:
            return tt[key]

        if is_win(cur_opp, cur_me, other(cur_color)):
            return -1000000 - depth
        if is_win(cur_me, cur_opp, cur_color):
            return 1000000 + depth

        moves = generate_moves(cur_me, cur_opp, cur_color)
        if not moves:
            return -1000000 - depth

        if depth == 0:
            val = evaluate(cur_me, cur_opp, cur_color)
            tt[key] = val
            return val

        ordered = order_moves(cur_me, cur_opp, cur_color, moves)

        best = -INF
        for mv in ordered:
            me2, opp2 = apply_move(cur_me, cur_opp, mv)
            if is_win(me2, opp2, cur_color):
                val = 1000000 + depth
            else:
                val = -negamax(opp2, me2, other(cur_color), depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[key] = best
        return best

    try:
        for depth in range(1, 6):
            check_time()
            current_best_move = best_move
            current_best_score = -INF

            ordered_root = order_moves(me, opp, color, legal)
            alpha = -INF
            beta = INF

            for mv in ordered_root:
                check_time()
                me2, opp2 = apply_move(me, opp, mv)
                if is_win(me2, opp2, color):
                    current_best_move = mv
                    current_best_score = 1000000 + depth
                    break
                score = -negamax(opp2, me2, other(color), depth - 1, -beta, -alpha)
                if score > current_best_score:
                    current_best_score = score
                    current_best_move = mv
                if score > alpha:
                    alpha = score

            best_move = current_best_move
            best_score = current_best_score

    except Exception:
        pass

    if best_move in legal:
        return best_move
    return fallback


def other(color: str) -> str:
    return 'b' if color == 'w' else 'w'


def goal_row(color: str) -> int:
    return 7 if color == 'w' else 0


def forward_dir(color: str) -> int:
    return 1 if color == 'w' else -1


def is_win(me, opp, color: str) -> bool:
    if not opp:
        return True
    g = goal_row(color)
    for r, c in me:
        if r == g:
            return True
    return False


def generate_moves(me, opp, color: str) -> List[Move]:
    me_set = set(me)
    opp_set = set(opp)
    dr = forward_dir(color)
    moves = []

    pieces = sorted(me, key=lambda p: progress_of_piece(p, color), reverse=True)

    for r, c in pieces:
        nr = r + dr
        if not (0 <= nr < 8):
            continue

        if (nr, c) not in me_set and (nr, c) not in opp_set:
            moves.append(((r, c), (nr, c)))

        nc = c - 1
        if 0 <= nc < 8 and (nr, nc) not in me_set:
            moves.append(((r, c), (nr, nc)))

        nc = c + 1
        if 0 <= nc < 8 and (nr, nc) not in me_set:
            moves.append(((r, c), (nr, nc)))

    return moves


def apply_move(me, opp, mv: Move):
    src, dst = mv
    me_list = list(me)
    me_list.remove(src)
    me_list.append(dst)
    opp_list = list(opp)
    if dst in opp_list:
        opp_list.remove(dst)
    return tuple(sorted(me_list)), tuple(sorted(opp_list))


def progress_of_piece(p, color: str) -> int:
    r, c = p
    return r if color == 'w' else 7 - r


def order_moves(me, opp, color: str, moves: List[Move]) -> List[Move]:
    opp_set = set(opp)
    g = goal_row(color)
    dr = forward_dir(color)

    def score(mv: Move):
        (r, c), (nr, nc) = mv
        s = 0

        if nr == g:
            s += 100000

        if (nr, nc) in opp_set:
            s += 5000

        s += 60 * progress_of_piece((nr, nc), color)
        s += 8 * (3 - abs(3.5 - nc))

        if c != nc:
            s += 10

        if threatens_from((nr, nc), color, opp_set):
            s += 120

        if is_passed_runner((nr, nc), opp, color):
            s += 200

        if near_goal((nr, nc), color):
            s += 150

        if vulnerable_after((nr, nc), me, opp, color, src=(r, c)):
            s -= 180

        if nr == r + dr and nc == c:
            s += 5

        return s

    return sorted(moves, key=score, reverse=True)


def near_goal(p, color: str) -> bool:
    r, c = p
    return r >= 5 if color == 'w' else r <= 2


def threatens_from(p, color: str, opp_set) -> bool:
    r, c = p
    nr = r + forward_dir(color)
    if not (0 <= nr < 8):
        return False
    for dc in (-1, 1):
        nc = c + dc
        if 0 <= nc < 8 and (nr, nc) in opp_set:
            return True
    return False


def vulnerable_after(p, me, opp, color: str, src=None) -> bool:
    me_set = set(me)
    opp_set = set(opp)
    if src is not None and src in me_set:
        me_set.remove(src)
    me_set.add(p)
    if p in opp_set:
        opp_set.remove(p)

    r, c = p
    enemy = other(color)
    edr = forward_dir(enemy)

    er = r - edr
    if not (0 <= er < 8):
        return False

    for ec in (c - 1, c + 1):
        if 0 <= ec < 8 and (er, ec) in opp_set:
            return True
    return False


def is_passed_runner(p, opp, color: str) -> bool:
    r, c = p
    if color == 'w':
        for orow, ocol in opp:
            if orow > r and abs(ocol - c) <= 1:
                return False
        return True
    else:
        for orow, ocol in opp:
            if orow < r and abs(ocol - c) <= 1:
                return False
        return True


def evaluate(me, opp, color: str) -> int:
    if is_win(me, opp, color):
        return 1000000
    if is_win(opp, me, other(color)):
        return -1000000

    my_set = set(me)
    op_set = set(opp)

    score = 0

    score += 900 * (len(me) - len(opp))

    my_prog = sum(progress_of_piece(p, color) for p in me)
    op_prog = sum(progress_of_piece(p, other(color)) for p in opp)
    score += 70 * (my_prog - op_prog)

    my_max = max((progress_of_piece(p, color) for p in me), default=0)
    op_max = max((progress_of_piece(p, other(color)) for p in opp), default=0)
    score += 160 * (my_max - op_max)

    my_moves = generate_moves(me, opp, color)
    op_moves = generate_moves(opp, me, other(color))
    score += 12 * (len(my_moves) - len(op_moves))

    for p in me:
        r, c = p
        score += int(18 * (3.5 - abs(3.5 - c)))
        if threatens_from(p, color, op_set):
            score += 90
        if is_passed_runner(p, opp, color):
            score += 140 + 35 * progress_of_piece(p, color)
        if near_goal(p, color):
            score += 60
        if vulnerable_after(p, me, opp, color):
            score -= 70

    for p in opp:
        r, c = p
        score -= int(18 * (3.5 - abs(3.5 - c)))
        if threatens_from(p, other(color), my_set):
            score -= 90
        if is_passed_runner(p, me, other(color)):
            score -= 140 + 35 * progress_of_piece(p, other(color))
        if near_goal(p, other(color)):
            score -= 60
        if vulnerable_after(p, opp, me, other(color)):
            score += 70

    my_goal_threats = count_goal_threats(me, opp, color)
    op_goal_threats = count_goal_threats(opp, me, other(color))
    score += 500 * (my_goal_threats - op_goal_threats)

    return score


def count_goal_threats(me, opp, color: str) -> int:
    me_set = set(me)
    occ = me_set | set(opp)
    g = goal_row(color)
    dr = forward_dir(color)
    count = 0

    for r, c in me:
        nr = r + dr
        if nr != g:
            continue
        if 0 <= nr < 8:
            if (nr, c) not in occ:
                count += 1
            for nc in (c - 1, c + 1):
                if 0 <= nc < 8 and (nr, nc) not in me_set:
                    count += 1
    return count
