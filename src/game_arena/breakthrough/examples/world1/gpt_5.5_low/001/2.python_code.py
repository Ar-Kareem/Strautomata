
import time
import math


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Breakthrough policy for 8x8 board.

    color == 'b': our pieces move toward row 0
    color == 'w': our pieces move toward row 7
    """

    BOARD = 8
    INF = 10**9
    TIME_LIMIT = 0.92
    start_time = time.perf_counter()

    my_color = color
    op_color = 'w' if color == 'b' else 'b'

    def direction(c):
        return -1 if c == 'b' else 1

    def goal_row(c):
        return 0 if c == 'b' else 7

    my_dir = direction(my_color)
    op_dir = direction(op_color)
    my_goal = goal_row(my_color)
    op_goal = goal_row(op_color)

    def in_bounds(r, c):
        return 0 <= r < BOARD and 0 <= c < BOARD

    def progress_of(piece, c):
        r, _ = piece
        return 7 - r if c == 'b' else r

    def dist_to_goal(piece, c):
        r, _ = piece
        return r if c == 'b' else 7 - r

    def gen_moves(side, enemy, c):
        """Generate all legal moves for side with color c."""
        d = direction(c)
        side_set = set(side)
        enemy_set = set(enemy)
        occ = side_set | enemy_set
        moves = []

        for r, col in side:
            nr = r + d
            if not 0 <= nr < BOARD:
                continue

            # Straight forward: only if empty.
            to = (nr, col)
            if to not in occ:
                moves.append(((r, col), to))

            # Diagonal forward: legal if not occupied by own piece.
            for dc in (-1, 1):
                nc = col + dc
                if 0 <= nc < BOARD:
                    to = (nr, nc)
                    if to not in side_set:
                        moves.append(((r, col), to))

        return moves

    def move_order(moves, side, enemy, c):
        """Order promising moves first for alpha-beta efficiency."""
        enemy_set = set(enemy)
        g = goal_row(c)
        d = direction(c)

        def score(mv):
            fr, to = mv
            tr, tc = to
            s = 0

            # Immediate promotion.
            if tr == g:
                s += 100000

            # Captures.
            if to in enemy_set:
                s += 20000

            # Advancement.
            s += 1000 * progress_of(to, c)

            # Central columns are usually safer/flexible.
            s += 20 * (3.5 - abs(tc - 3.5))

            # Prefer diagonal moves that dodge straight blocks.
            if fr[1] != tc:
                s += 15

            # Prefer moves closer to goal.
            s -= 10 * dist_to_goal(to, c)

            # Slightly favor edge only near promotion.
            if tc in (0, 7):
                s -= 10
                if dist_to_goal(to, c) <= 2:
                    s += 35

            # Blocking/capturing near enemy goal is urgent.
            if to in enemy_set and dist_to_goal(to, c) <= 2:
                s += 1000

            return -s

        return sorted(moves, key=score)

    def terminal_score(my_pieces, op_pieces):
        if not op_pieces:
            return INF - 1
        if not my_pieces:
            return -INF + 1

        for p in my_pieces:
            if p[0] == my_goal:
                return INF - 1
        for p in op_pieces:
            if p[0] == op_goal:
                return -INF + 1

        return None

    def attacked_by(pieces, c):
        """Squares attacked/capturable by pieces of color c."""
        d = direction(c)
        attacks = set()
        for r, col in pieces:
            nr = r + d
            if 0 <= nr < BOARD:
                for dc in (-1, 1):
                    nc = col + dc
                    if 0 <= nc < BOARD:
                        attacks.add((nr, nc))
        return attacks

    def is_passed(p, enemies, c):
        """A pawn is passed if no enemy is ahead in same/adjacent files."""
        r, col = p
        d = direction(c)
        for er, ec in enemies:
            if abs(ec - col) <= 1:
                if c == 'b':
                    if er < r:
                        return False
                else:
                    if er > r:
                        return False
        return True

    def evaluate(my_pieces, op_pieces):
        """Static evaluation from our perspective."""
        t = terminal_score(my_pieces, op_pieces)
        if t is not None:
            return t

        my_set = set(my_pieces)
        op_set = set(op_pieces)

        score = 0

        # Material.
        score += 1200 * (len(my_pieces) - len(op_pieces))

        # Advancement, promotion distance, centralization.
        my_best_dist = 7
        op_best_dist = 7

        for p in my_pieces:
            r, c = p
            prog = progress_of(p, my_color)
            dist = dist_to_goal(p, my_color)
            my_best_dist = min(my_best_dist, dist)

            score += 95 * prog
            score -= 35 * dist
            score += int(18 * (3.5 - abs(c - 3.5)))

            # Advanced pawns become very dangerous.
            score += 12 * prog * prog

            if is_passed(p, op_pieces, my_color):
                score += 450 + 120 * prog
                if dist <= 2:
                    score += 900

        for p in op_pieces:
            r, c = p
            prog = progress_of(p, op_color)
            dist = dist_to_goal(p, op_color)
            op_best_dist = min(op_best_dist, dist)

            score -= 95 * prog
            score += 35 * dist
            score -= int(18 * (3.5 - abs(c - 3.5)))
            score -= 12 * prog * prog

            if is_passed(p, my_pieces, op_color):
                score -= 450 + 120 * prog
                if dist <= 2:
                    score -= 1200

        # Race urgency.
        score += 220 * (op_best_dist - my_best_dist)

        # Attack / vulnerability.
        my_attacks = attacked_by(my_pieces, my_color)
        op_attacks = attacked_by(op_pieces, op_color)

        score += 180 * len(my_attacks & op_set)
        score -= 210 * len(op_attacks & my_set)

        # Defended pieces.
        score += 45 * len(my_attacks & my_set)
        score -= 45 * len(op_attacks & op_set)

        # Mobility.
        my_mob = len(gen_moves(my_pieces, op_pieces, my_color))
        op_mob = len(gen_moves(op_pieces, my_pieces, op_color))
        score += 12 * (my_mob - op_mob)

        return score

    class Timeout(Exception):
        pass

    def check_time():
        if time.perf_counter() - start_time > TIME_LIMIT:
            raise Timeout()

    # Initial legal moves and mandatory fallback.
    my_pieces0 = tuple(me)
    op_pieces0 = tuple(opp)
    legal = gen_moves(my_pieces0, op_pieces0, my_color)

    if not legal:
        # Should not occur in normal Breakthrough arena positions.
        # Return a syntactically valid fallback.
        return ((0, 0), (0, 0))

    legal = move_order(legal, my_pieces0, op_pieces0, my_color)
    best_move = legal[0]

    # Immediate winning move.
    for mv in legal:
        if mv[1][0] == my_goal:
            return mv

    # If opponent has an immediate promotion threat, captures/blocks will be found by search,
    # but shallow ordering helps.
    memo = {}

    def apply_move(my_pieces, op_pieces, mv, turn):
        """turn == 1 means our move, turn == -1 means opponent move."""
        fr, to = mv
        if turn == 1:
            new_my = set(my_pieces)
            new_op = set(op_pieces)
            new_my.remove(fr)
            new_my.add(to)
            if to in new_op:
                new_op.remove(to)
            return tuple(new_my), tuple(new_op)
        else:
            new_my = set(my_pieces)
            new_op = set(op_pieces)
            new_op.remove(fr)
            new_op.add(to)
            if to in new_my:
                new_my.remove(to)
            return tuple(new_my), tuple(new_op)

    def alphabeta(my_pieces, op_pieces, depth, alpha, beta, turn):
        check_time()

        t = terminal_score(my_pieces, op_pieces)
        if t is not None:
            return t

        if depth <= 0:
            return evaluate(my_pieces, op_pieces)

        key = (
            depth,
            turn,
            tuple(sorted(my_pieces)),
            tuple(sorted(op_pieces)),
            alpha // 50,
            beta // 50,
        )
        if key in memo:
            return memo[key]

        if turn == 1:
            moves = gen_moves(my_pieces, op_pieces, my_color)
            if not moves:
                val = evaluate(my_pieces, op_pieces) - 500
                memo[key] = val
                return val

            moves = move_order(moves, my_pieces, op_pieces, my_color)
            value = -INF
            for mv in moves:
                nmy, nop = apply_move(my_pieces, op_pieces, mv, 1)
                value = max(value, alphabeta(nmy, nop, depth - 1, alpha, beta, -1))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            memo[key] = value
            return value

        else:
            moves = gen_moves(op_pieces, my_pieces, op_color)
            if not moves:
                val = evaluate(my_pieces, op_pieces) + 500
                memo[key] = val
                return val

            moves = move_order(moves, op_pieces, my_pieces, op_color)
            value = INF
            for mv in moves:
                nmy, nop = apply_move(my_pieces, op_pieces, mv, -1)
                value = min(value, alphabeta(nmy, nop, depth - 1, alpha, beta, 1))
                beta = min(beta, value)
                if alpha >= beta:
                    break
            memo[key] = value
            return value

    # Adaptive maximum depth.
    total_pieces = len(me) + len(opp)
    if total_pieces <= 10:
        max_depth = 7
    elif total_pieces <= 18:
        max_depth = 6
    else:
        max_depth = 5

    try:
        for depth in range(1, max_depth + 1):
            current_best = best_move
            current_val = -INF

            # Reorder root moves each iteration; previous best searched first.
            root_moves = legal[:]
            if best_move in root_moves:
                root_moves.remove(best_move)
                root_moves.insert(0, best_move)

            alpha = -INF
            beta = INF

            for mv in root_moves:
                check_time()
                nmy, nop = apply_move(my_pieces0, op_pieces0, mv, 1)

                # Prefer actual terminal wins instantly.
                tt = terminal_score(nmy, nop)
                if tt is not None and tt > INF // 2:
                    return mv

                val = alphabeta(nmy, nop, depth - 1, alpha, beta, -1)

                # Small deterministic tie-breaker for advancement/captures.
                if mv[1] in set(op_pieces0):
                    val += 8
                val += progress_of(mv[1], my_color)

                if val > current_val:
                    current_val = val
                    current_best = mv

                alpha = max(alpha, current_val)

            best_move = current_best

    except Timeout:
        pass

    # Final safety check: ensure returned move is legal.
    legal_set = set(legal)
    if best_move in legal_set:
        return best_move

    return legal[0]
