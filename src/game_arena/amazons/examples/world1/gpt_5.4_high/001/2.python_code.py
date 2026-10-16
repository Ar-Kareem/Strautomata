
import time
from collections import deque
import numpy as np

SIZE = 6
DIRS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)

CENTER = tuple(
    tuple(int(round(10 - 2 * ((r - 2.5) ** 2 + (c - 2.5) ** 2))) for c in range(SIZE))
    for r in range(SIZE)
)

WIN_SCORE = 1_000_000
INF_SCORE = 10_000_000
DIST_INF = 99


class _TimeoutSearch(Exception):
    pass


def _ray_squares(board, r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr, nc] == 0:
            yield nr, nc
            nr += dr
            nc += dc


def _count_reachable(board, r, c):
    cnt = 0
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        while 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr, nc] == 0:
            cnt += 1
            nr += dr
            nc += dc
    return cnt


def _apply_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    board[fr, fc] = 0
    board[tr, tc] = player
    board[ar, ac] = -1


def _undo_move(board, move, player):
    fr, fc, tr, tc, ar, ac = move
    board[ar, ac] = 0
    board[tr, tc] = 0
    board[fr, fc] = player


def _queen_distances(board, positions):
    dist = np.full((SIZE, SIZE), DIST_INF, dtype=np.int16)
    q = deque()

    for p in positions:
        r = int(p[0])
        c = int(p[1])
        dist[r, c] = 0
        q.append((r, c))

    while q:
        r, c = q.popleft()
        nd = int(dist[r, c]) + 1
        for dr, dc in DIRS:
            nr, nc = r + dr, c + dc
            while 0 <= nr < SIZE and 0 <= nc < SIZE and board[nr, nc] == 0:
                if nd < dist[nr, nc]:
                    dist[nr, nc] = nd
                    q.append((nr, nc))
                nr += dr
                nc += dc

    return dist


def _format_move(move):
    fr, fc, tr, tc, ar, ac = move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"


def policy(board) -> str:
    board = np.array(board, dtype=np.int8, copy=True)
    deadline = time.perf_counter() + 0.92

    eval_cache = {}
    best_move_hint = {}
    node_counter = 0

    def time_check():
        if time.perf_counter() >= deadline:
            raise _TimeoutSearch

    def count_legal_moves(state, player):
        time_check()
        total = 0
        pieces = np.argwhere(state == player)
        for idx, p in enumerate(pieces):
            if idx & 1 == 0:
                time_check()
            fr = int(p[0])
            fc = int(p[1])
            for tr, tc in _ray_squares(state, fr, fc):
                state[fr, fc] = 0
                state[tr, tc] = player
                total += _count_reachable(state, tr, tc)
                state[tr, tc] = 0
                state[fr, fc] = player
        return total

    def generate_moves_scored(state, player, hint=None):
        time_check()
        opp = 2 if player == 1 else 1
        opp_positions = [tuple(map(int, p)) for p in np.argwhere(state == opp)]
        pieces = np.argwhere(state == player)
        moves = []

        for idx, p in enumerate(pieces):
            if idx & 1 == 0:
                time_check()

            fr = int(p[0])
            fc = int(p[1])

            for tr, tc in _ray_squares(state, fr, fc):
                state[fr, fc] = 0
                state[tr, tc] = player

                to_freedom = _count_reachable(state, tr, tc)
                base = 14 * to_freedom + 3 * CENTER[tr][tc]

                for ar, ac in _ray_squares(state, tr, tc):
                    press = 0
                    for orow, ocol in opp_positions:
                        d = max(abs(ar - orow), abs(ac - ocol))
                        if d < 4:
                            press += 4 - d

                    score = base + 2 * CENTER[ar][ac] + 5 * press
                    if ar == fr and ac == fc:
                        score += 2

                    mv = (fr, fc, int(tr), int(tc), int(ar), int(ac))
                    moves.append((mv, score))

                state[tr, tc] = 0
                state[fr, fc] = player

        if not moves:
            return moves

        moves.sort(key=lambda x: x[1], reverse=True)

        if hint is not None:
            for i, (mv, sc) in enumerate(moves):
                if mv == hint:
                    if i != 0:
                        moves[0], moves[i] = moves[i], moves[0]
                    break

        return moves

    def static_eval(state):
        key = state.tobytes()
        cached = eval_cache.get(key)
        if cached is not None:
            return cached

        my_positions = np.argwhere(state == 1)
        opp_positions = np.argwhere(state == 2)

        m1 = 0
        m2 = 0
        p1 = 0
        p2 = 0

        for p in my_positions:
            r = int(p[0])
            c = int(p[1])
            x = _count_reachable(state, r, c)
            m1 += x
            p1 += x * x

        for p in opp_positions:
            r = int(p[0])
            c = int(p[1])
            x = _count_reachable(state, r, c)
            m2 += x
            p2 += x * x

        d1 = _queen_distances(state, my_positions)
        d2 = _queen_distances(state, opp_positions)

        owner = 0
        influence = 0.0
        reach_diff = 0
        empties = np.argwhere(state == 0)

        for p in empties:
            r = int(p[0])
            c = int(p[1])
            a = int(d1[r, c])
            b = int(d2[r, c])

            if a < DIST_INF:
                reach_diff += 1
            if b < DIST_INF:
                reach_diff -= 1

            if a < b:
                owner += 1
            elif b < a:
                owner -= 1

            if a < DIST_INF or b < DIST_INF:
                va = (1.0 / (a + 1)) if a < DIST_INF else 0.0
                vb = (1.0 / (b + 1)) if b < DIST_INF else 0.0
                influence += va - vb

        center_score = 0
        for p in my_positions:
            center_score += CENTER[int(p[0])][int(p[1])]
        for p in opp_positions:
            center_score -= CENTER[int(p[0])][int(p[1])]

        empty_count = int(np.count_nonzero(state == 0))

        if empty_count > 14:
            val = (
                6.0 * owner +
                10.0 * influence +
                1.1 * (m1 - m2) +
                0.05 * (p1 - p2) +
                0.25 * center_score +
                0.5 * reach_diff
            )
        else:
            val = (
                5.0 * owner +
                8.0 * influence +
                1.7 * (m1 - m2) +
                0.08 * (p1 - p2) +
                0.15 * center_score +
                0.8 * reach_diff
            )

        if empty_count <= 10:
            lm1 = count_legal_moves(state, 1)
            lm2 = count_legal_moves(state, 2)
            val += 0.25 * (lm1 - lm2)

        result = (val, m1, m2)
        eval_cache[key] = result
        return result

    def evaluate(state, player_to_move):
        val, m1, m2 = static_eval(state)
        if player_to_move == 1 and m1 == 0:
            return -WIN_SCORE
        if player_to_move == 2 and m2 == 0:
            return WIN_SCORE
        return val

    def internal_cap(depth, num_moves, empty_count):
        if num_moves <= 20:
            return num_moves
        if depth >= 4:
            return min(num_moves, 10 if empty_count > 14 else 14)
        if depth == 3:
            return min(num_moves, 14 if empty_count > 14 else 20)
        if depth == 2:
            return min(num_moves, 24 if empty_count > 14 else 32)
        return num_moves

    def root_cap(depth, num_moves, empty_count):
        if depth == 1:
            return num_moves
        if depth == 2:
            return min(num_moves, 60 if empty_count > 14 else 80)
        if depth == 3:
            return min(num_moves, 28 if empty_count > 14 else 40)
        return min(num_moves, 16 if empty_count > 14 else 24)

    def alphabeta(state, depth, alpha, beta, player, ply):
        nonlocal node_counter
        node_counter += 1
        if (node_counter & 63) == 0:
            time_check()

        if depth == 0:
            return evaluate(state, player)

        key = (state.tobytes(), player)
        hint = best_move_hint.get(key)
        moves = generate_moves_scored(state, player, hint=hint)

        if not moves:
            return (-WIN_SCORE + ply) if player == 1 else (WIN_SCORE - ply)

        empty_count = int(np.count_nonzero(state == 0))
        cap = internal_cap(depth, len(moves), empty_count)

        if player == 1:
            best_val = -INF_SCORE
            best_mv = moves[0][0]
            for mv, _ in moves[:cap]:
                _apply_move(state, mv, 1)
                score = alphabeta(state, depth - 1, alpha, beta, 2, ply + 1)
                _undo_move(state, mv, 1)

                if score > best_val:
                    best_val = score
                    best_mv = mv
                if best_val > alpha:
                    alpha = best_val
                if alpha >= beta:
                    break

            best_move_hint[key] = best_mv
            return best_val

        else:
            best_val = INF_SCORE
            best_mv = moves[0][0]
            for mv, _ in moves[:cap]:
                _apply_move(state, mv, 2)
                score = alphabeta(state, depth - 1, alpha, beta, 1, ply + 1)
                _undo_move(state, mv, 2)

                if score < best_val:
                    best_val = score
                    best_mv = mv
                if best_val < beta:
                    beta = best_val
                if alpha >= beta:
                    break

            best_move_hint[key] = best_mv
            return best_val

    try:
        root_scored = generate_moves_scored(board, 1, hint=None)
    except _TimeoutSearch:
        root_scored = []

    if not root_scored:
        return "0,0:0,0:0,0"

    root_moves = [mv for mv, _ in root_scored]
    best_move = root_moves[0]
    empty_count = int(np.count_nonzero(board == 0))

    try:
        for depth in range(1, 7):
            time_check()

            cap = root_cap(depth, len(root_moves), empty_count)

            if best_move == root_moves[0]:
                ordered_root = root_moves
            else:
                ordered_root = [best_move] + [mv for mv in root_moves if mv != best_move]

            local_best_move = best_move
            local_best_score = -INF_SCORE
            exact_scores = []

            for mv in ordered_root[:cap]:
                time_check()
                _apply_move(board, mv, 1)
                score = alphabeta(board, depth - 1, -INF_SCORE, INF_SCORE, 2, 1)
                _undo_move(board, mv, 1)

                exact_scores.append((mv, score))
                if score > local_best_score:
                    local_best_score = score
                    local_best_move = mv

            best_move = local_best_move

            exact_scores.sort(key=lambda x: x[1], reverse=True)
            seen = {mv for mv, _ in exact_scores}
            root_moves = [mv for mv, _ in exact_scores] + [mv for mv in root_moves if mv not in seen]

    except _TimeoutSearch:
        pass

    return _format_move(best_move)
