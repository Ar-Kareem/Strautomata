
from __future__ import annotations

import time
from functools import lru_cache
from typing import List, Tuple

Move = Tuple[Tuple[int, int], Tuple[int, int]]

BOARD = 8
INF = 10**9
TIME_LIMIT = 0.88


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.perf_counter()

    me_t = tuple(sorted(me))
    opp_t = tuple(sorted(opp))

    moves = _legal_moves(me_t, opp_t, color)
    if not moves:
        # Should not occur in normal Breakthrough play unless the game is already over.
        # Return a syntactically valid fallback from an existing piece if possible.
        if me:
            r, c = me[0]
            dr = -1 if color == "b" else 1
            nr = max(0, min(7, r + dr))
            return ((r, c), (nr, c))
        return ((0, 0), (0, 0))

    # Immediate win if available.
    goal = 0 if color == "b" else 7
    for mv in moves:
        if mv[1][0] == goal:
            return mv

    best_move = moves[0]
    nodes = 0

    def time_up() -> bool:
        return time.perf_counter() - start_time > TIME_LIMIT

    @lru_cache(maxsize=200000)
    def search(cur: tuple[tuple[int, int], ...],
               enemy: tuple[tuple[int, int], ...],
               side: str,
               depth: int,
               alpha: int,
               beta: int) -> int:
        nonlocal nodes
        nodes += 1
        if nodes & 2047 == 0 and time_up():
            raise TimeoutError

        term = _terminal_value(cur, enemy, side)
        if term is not None:
            return term

        if depth <= 0:
            return _evaluate(cur, enemy, side)

        legal = _legal_moves(cur, enemy, side)
        if not legal:
            return -INF + 10

        legal.sort(key=lambda m: _move_order_score(m, cur, enemy, side), reverse=True)

        best = -INF
        next_side = "w" if side == "b" else "b"

        for mv in legal:
            new_cur, new_enemy = _apply_move(cur, enemy, mv)
            val = -search(new_enemy, new_cur, next_side, depth - 1, -beta, -alpha)
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
        return best

    pieces = len(me) + len(opp)
    max_depth = 4
    if pieces <= 24:
        max_depth = 5
    if pieces <= 14:
        max_depth = 6
    if pieces <= 8:
        max_depth = 7

    try:
        for depth in range(1, max_depth + 1):
            if time_up():
                break

            ordered = list(moves)
            ordered.sort(key=lambda m: _move_order_score(m, me_t, opp_t, color), reverse=True)

            alpha = -INF
            beta = INF
            local_best = best_move
            local_score = -INF
            next_color = "w" if color == "b" else "b"

            for mv in ordered:
                if time_up():
                    raise TimeoutError
                new_me, new_opp = _apply_move(me_t, opp_t, mv)
                score = -search(new_opp, new_me, next_color, depth - 1, -beta, -alpha)
                if score > local_score:
                    local_score = score
                    local_best = mv
                if score > alpha:
                    alpha = score

            best_move = local_best

            # Forced win found.
            if local_score > INF // 2:
                break

    except TimeoutError:
        pass

    # Final safety check.
    if best_move in moves:
        return best_move
    return moves[0]


def _dir(color: str) -> int:
    return -1 if color == "b" else 1


def _goal(color: str) -> int:
    return 0 if color == "b" else 7


def _opp_color(color: str) -> str:
    return "w" if color == "b" else "b"


def _legal_moves(me: tuple[tuple[int, int], ...],
                 opp: tuple[tuple[int, int], ...],
                 color: str) -> list[Move]:
    me_set = set(me)
    opp_set = set(opp)
    occupied = me_set | opp_set
    dr = _dir(color)
    moves: list[Move] = []

    # More advanced pieces first.
    pieces = sorted(me, key=lambda p: p[0], reverse=(color == "w"))

    for r, c in pieces:
        nr = r + dr
        if nr < 0 or nr >= BOARD:
            continue

        # Straight forward only if empty.
        if (nr, c) not in occupied:
            moves.append(((r, c), (nr, c)))

        # Diagonal left/right: may move to empty or capture opponent, but not own piece.
        for dc in (-1, 1):
            nc = c + dc
            if 0 <= nc < BOARD and (nr, nc) not in me_set:
                moves.append(((r, c), (nr, nc)))

    return moves


def _apply_move(me: tuple[tuple[int, int], ...],
                opp: tuple[tuple[int, int], ...],
                mv: Move) -> tuple[tuple[tuple[int, int], ...], tuple[tuple[int, int], ...]]:
    src, dst = mv
    new_me_list = []
    for p in me:
        if p == src:
            new_me_list.append(dst)
        else:
            new_me_list.append(p)

    new_opp_list = [p for p in opp if p != dst]
    return tuple(sorted(new_me_list)), tuple(sorted(new_opp_list))


def _terminal_value(me: tuple[tuple[int, int], ...],
                    opp: tuple[tuple[int, int], ...],
                    color: str) -> int | None:
    if not opp:
        return INF
    if not me:
        return -INF

    my_goal = _goal(color)
    enemy_goal = _goal(_opp_color(color))

    for r, _ in me:
        if r == my_goal:
            return INF
    for r, _ in opp:
        if r == enemy_goal:
            return -INF
    return None


def _progress(row: int, color: str) -> int:
    # Higher is better.
    return 7 - row if color == "b" else row


def _dist_to_goal(row: int, color: str) -> int:
    return row if color == "b" else 7 - row


def _evaluate(me: tuple[tuple[int, int], ...],
              opp: tuple[tuple[int, int], ...],
              color: str) -> int:
    term = _terminal_value(me, opp, color)
    if term is not None:
        return term

    enemy_color = _opp_color(color)
    me_set = set(me)
    opp_set = set(opp)

    score = 0

    # Material is important, but race-to-goal is often decisive.
    score += 125 * (len(me) - len(opp))

    my_dists = [_dist_to_goal(r, color) for r, _ in me]
    op_dists = [_dist_to_goal(r, enemy_color) for r, _ in opp]

    score += 85 * (min(op_dists) - min(my_dists))

    for r, c in me:
        prog = _progress(r, color)
        dist = _dist_to_goal(r, color)

        score += 18 * prog * prog
        score += 4 * (3 - abs(c - 3.5))

        if _is_passed((r, c), opp, color):
            score += 170 + 45 * (7 - dist)

        if _is_protected((r, c), me_set, color):
            score += 28

        if _has_immediate_threat((r, c), opp_set, color):
            score += 35

        # A pawn one move from winning is extremely valuable if not trivially blocked.
        if dist == 1:
            score += 500

    for r, c in opp:
        prog = _progress(r, enemy_color)
        dist = _dist_to_goal(r, enemy_color)

        score -= 18 * prog * prog
        score -= 4 * (3 - abs(c - 3.5))

        if _is_passed((r, c), me, enemy_color):
            score -= 170 + 45 * (7 - dist)

        if _is_protected((r, c), opp_set, enemy_color):
            score -= 28

        if _has_immediate_threat((r, c), me_set, enemy_color):
            score -= 35

        if dist == 1:
            score -= 500

    return int(score)


def _is_passed(piece: tuple[int, int],
               enemies,
               color: str) -> bool:
    r, c = piece
    dr = _dir(color)

    for er, ec in enemies:
        if abs(ec - c) > 1:
            continue
        if color == "b":
            if er < r:
                return False
        else:
            if er > r:
                return False
    return True


def _is_protected(piece: tuple[int, int],
                  own_set: set[tuple[int, int]],
                  color: str) -> bool:
    r, c = piece
    # A protecting friendly pawn is one row behind and one column sideways.
    back = r - _dir(color)
    return (back, c - 1) in own_set or (back, c + 1) in own_set


def _has_immediate_threat(piece: tuple[int, int],
                          enemy_set: set[tuple[int, int]],
                          color: str) -> bool:
    r, c = piece
    nr = r + _dir(color)
    return (nr, c - 1) in enemy_set or (nr, c + 1) in enemy_set


def _move_order_score(mv: Move,
                      me: tuple[tuple[int, int], ...],
                      opp: tuple[tuple[int, int], ...],
                      color: str) -> int:
    src, dst = mv
    opp_set = set(opp)
    score = 0

    if dst[0] == _goal(color):
        score += 100000

    if dst in opp_set:
        score += 10000

    score += 100 * _progress(dst[0], color)

    # Prefer central files slightly.
    score += int(10 * (3.5 - abs(dst[1] - 3.5)))

    # Passed-pawn advances are high priority.
    if _is_passed(dst, opp, color):
        score += 600

    # Prefer moves that keep or create protection.
    me_after = set(me)
    if src in me_after:
        me_after.remove(src)
    me_after.add(dst)
    if _is_protected(dst, me_after, color):
        score += 80

    # Avoid moving into an immediate recapture unless it is a win/capture.
    enemy_color = _opp_color(color)
    enemy_attackers = 0
    for er, ec in opp:
        if er + _dir(enemy_color) == dst[0] and abs(ec - dst[1]) == 1:
            enemy_attackers += 1
    if enemy_attackers:
        score -= 90 * enemy_attackers
        if dst in opp_set:
            score += 55

    return score
