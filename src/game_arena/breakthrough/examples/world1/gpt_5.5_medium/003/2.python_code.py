
import time

BOARD_SIZE = 8
WIN_SCORE = 1_000_000
INF = 10**9
TIME_LIMIT = 0.86

ROW0_MASK = sum(1 << c for c in range(8))
ROW7_MASK = sum(1 << (7 * 8 + c) for c in range(8))

EXACT, LOWER, UPPER = 0, 1, 2


class SearchTimeout(Exception):
    pass


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    root = color
    enemy = "w" if root == "b" else "b"

    def encode(pieces):
        bits = 0
        for r, c in pieces:
            bits |= 1 << (r * 8 + c)
        return bits

    if color == "b":
        black = encode(me)
        white = encode(opp)
    else:
        black = encode(opp)
        white = encode(me)

    def bit_iter(bits):
        while bits:
            lsb = bits & -bits
            idx = lsb.bit_length() - 1
            yield idx
            bits ^= lsb

    def rc(idx):
        return idx // 8, idx & 7

    def decode_move(mv):
        f, t = mv
        return ((f // 8, f & 7), (t // 8, t & 7))

    def opponent(side):
        return "w" if side == "b" else "b"

    def winner(b, w):
        if b == 0:
            return "w"
        if w == 0:
            return "b"
        if b & ROW0_MASK:
            return "b"
        if w & ROW7_MASK:
            return "w"
        return None

    def generate_moves(side, b, w):
        own = b if side == "b" else w
        occ = b | w
        d = -1 if side == "b" else 1
        moves = []

        for f in bit_iter(own):
            r, c = rc(f)
            nr = r + d
            if nr < 0 or nr >= 8:
                continue

            # Straight forward: only if empty.
            t = nr * 8 + c
            tb = 1 << t
            if not (occ & tb):
                moves.append((f, t))

            # Diagonal forward: allowed if target is not occupied by own piece.
            if c > 0:
                t = nr * 8 + (c - 1)
                tb = 1 << t
                if not (own & tb):
                    moves.append((f, t))

            if c < 7:
                t = nr * 8 + (c + 1)
                tb = 1 << t
                if not (own & tb):
                    moves.append((f, t))

        return moves

    def apply_move(side, b, w, mv):
        f, t = mv
        fb = 1 << f
        tb = 1 << t

        if side == "b":
            b = (b & ~fb) | tb
            w = w & ~tb
        else:
            w = (w & ~fb) | tb
            b = b & ~tb

        return b, w

    def is_goal_move(side, mv):
        _, t = mv
        tr = t // 8
        return (side == "b" and tr == 0) or (side == "w" and tr == 7)

    def progress_of(side, idx):
        r = idx // 8
        return 7 - r if side == "b" else r

    def move_order_score(side, b, w, mv):
        f, t = mv
        tr, tc = rc(t)
        opp_bits = w if side == "b" else b
        score = 0

        if is_goal_move(side, mv):
            score += 100_000

        if opp_bits & (1 << t):
            captured_side = opponent(side)
            score += 1500 + 45 * progress_of(captured_side, t)

        score += 35 * progress_of(side, t)
        score += 12 - abs(2 * tc - 7)

        # Prefer diagonal moves slightly because they create threats and avoid blocks.
        if (f & 7) != tc:
            score += 8

        return score

    def order_moves(side, b, w, moves):
        return sorted(moves, key=lambda m: move_order_score(side, b, w, m), reverse=True)

    def has_piece(bits, r, c):
        if 0 <= r < 8 and 0 <= c < 8:
            return bool(bits & (1 << (r * 8 + c)))
        return False

    def immediate_goal_count(side, b, w):
        own = b if side == "b" else w
        occ = b | w
        d = -1 if side == "b" else 1
        goal_row = 0 if side == "b" else 7
        count = 0

        for f in bit_iter(own):
            r, c = rc(f)
            nr = r + d
            if nr != goal_row:
                continue

            # Forward promotion if empty.
            t = nr * 8 + c
            if not (occ & (1 << t)):
                count += 1

            # Diagonal promotions if not occupied by own piece.
            if c > 0:
                t = nr * 8 + c - 1
                if not (own & (1 << t)):
                    count += 1
            if c < 7:
                t = nr * 8 + c + 1
                if not (own & (1 << t)):
                    count += 1

        return count

    def passed_pawn(side, idx, own_bits, opp_bits):
        r, c = rc(idx)
        for o in bit_iter(opp_bits):
            orow, ocol = rc(o)
            if abs(ocol - c) > 1:
                continue
            if side == "b" and orow < r:
                return False
            if side == "w" and orow > r:
                return False
        return True

    def color_score(side, b, w):
        own = b if side == "b" else w
        oppb = w if side == "b" else b
        score = own.bit_count() * 120

        for idx in bit_iter(own):
            r, c = rc(idx)
            progress = progress_of(side, idx)
            dist = 7 - progress

            # Advancement is non-linear: advanced pawns become race threats.
            score += progress * progress * 8 + progress * 5

            # Central files are slightly more flexible.
            score += 5 - abs(2 * c - 7)

            # Passed pawns are very dangerous in Breakthrough.
            if passed_pawn(side, idx, own, oppb):
                score += 55 + 18 * progress
                if dist <= 2:
                    score += 90

            # Protection / vulnerability.
            if side == "b":
                protected = (
                    has_piece(own, r + 1, c - 1) or
                    has_piece(own, r + 1, c + 1)
                )
                attacked = (
                    has_piece(oppb, r - 1, c - 1) or
                    has_piece(oppb, r - 1, c + 1)
                )
                nr = r - 1
            else:
                protected = (
                    has_piece(own, r - 1, c - 1) or
                    has_piece(own, r - 1, c + 1)
                )
                attacked = (
                    has_piece(oppb, r + 1, c - 1) or
                    has_piece(oppb, r + 1, c + 1)
                )
                nr = r + 1

            if protected:
                score += 12
            if attacked and not protected:
                score -= 28
            elif attacked:
                score -= 7

            # Immediate capture opportunities.
            if 0 <= nr < 8:
                if c > 0 and has_piece(oppb, nr, c - 1):
                    score += 10
                if c < 7 and has_piece(oppb, nr, c + 1):
                    score += 10

        return score

    def min_dist(side, bits):
        if bits == 0:
            return 99
        best = 99
        for idx in bit_iter(bits):
            r = idx // 8
            d = r if side == "b" else 7 - r
            if d < best:
                best = d
        return best

    def evaluate(b, w):
        win = winner(b, w)
        if win is not None:
            return WIN_SCORE if win == root else -WIN_SCORE

        root_score = color_score(root, b, w)
        enemy_score = color_score(enemy, b, w)
        val = root_score - enemy_score

        root_bits = b if root == "b" else w
        enemy_bits = w if root == "b" else b

        # Race term: the side closer to promotion often controls the game.
        val += 55 * (min_dist(enemy, enemy_bits) - min_dist(root, root_bits))

        # One-move promotion threats are urgent.
        val += 520 * immediate_goal_count(root, b, w)
        val -= 680 * immediate_goal_count(enemy, b, w)

        return val

    legal = generate_moves(root, black, white)

    # In a valid Breakthrough game this should not happen, but keep a fallback.
    if not legal:
        if me:
            r, c = me[0]
            d = -1 if color == "b" else 1
            nr = max(0, min(7, r + d))
            return ((r, c), (nr, c))
        return ((0, 0), (0, 0))

    legal = order_moves(root, black, white, legal)

    # Immediate win: never miss it.
    for mv in legal:
        nb, nw = apply_move(root, black, white, mv)
        if winner(nb, nw) == root:
            return decode_move(mv)

    # Greedy fallback, guaranteed legal.
    best_move = legal[0]
    best_val = -INF
    for mv in legal:
        nb, nw = apply_move(root, black, white, mv)
        val = evaluate(nb, nw)
        if val > best_val:
            best_val = val
            best_move = mv

    deadline = time.perf_counter() + TIME_LIMIT
    tt = {}
    nodes = 0

    def check_time():
        if time.perf_counter() >= deadline:
            raise SearchTimeout()

    def alphabeta(b, w, side, depth, alpha, beta, ply):
        nonlocal nodes
        nodes += 1
        if (nodes & 2047) == 0:
            check_time()

        win = winner(b, w)
        if win is not None:
            if win == root:
                return WIN_SCORE - ply
            return -WIN_SCORE + ply

        if depth <= 0:
            return evaluate(b, w)

        key = (b, w, side, depth)
        entry = tt.get(key)
        if entry is not None:
            e_depth, flag, e_val = entry
            if e_depth >= depth:
                if flag == EXACT:
                    return e_val
                if flag == LOWER:
                    alpha = max(alpha, e_val)
                elif flag == UPPER:
                    beta = min(beta, e_val)
                if alpha >= beta:
                    return e_val

        orig_alpha, orig_beta = alpha, beta
        moves = generate_moves(side, b, w)

        if not moves:
            return evaluate(b, w)

        moves = order_moves(side, b, w, moves)

        if side == root:
            value = -INF
            next_side = opponent(side)
            for mv in moves:
                nb, nw = apply_move(side, b, w, mv)
                value = max(value, alphabeta(nb, nw, next_side, depth - 1, alpha, beta, ply + 1))
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = INF
            next_side = opponent(side)
            for mv in moves:
                nb, nw = apply_move(side, b, w, mv)
                value = min(value, alphabeta(nb, nw, next_side, depth - 1, alpha, beta, ply + 1))
                beta = min(beta, value)
                if alpha >= beta:
                    break

        if value <= orig_alpha:
            flag = UPPER
        elif value >= orig_beta:
            flag = LOWER
        else:
            flag = EXACT

        tt[key] = (depth, flag, value)
        return value

    root_moves = legal[:]

    # Iterative deepening: keep the best completed result.
    for depth in range(1, 8):
        try:
            check_time()
            depth_best_move = root_moves[0]
            depth_best_val = -INF
            scored = []

            alpha, beta = -INF, INF
            for mv in root_moves:
                check_time()
                nb, nw = apply_move(root, black, white, mv)
                val = alphabeta(nb, nw, opponent(root), depth - 1, alpha, beta, 1)
                scored.append((val, mv))

                if val > depth_best_val:
                    depth_best_val = val
                    depth_best_move = mv

                alpha = max(alpha, depth_best_val)

            best_move = depth_best_move
            best_val = depth_best_val
            root_moves = [m for _, m in sorted(scored, key=lambda x: x[0], reverse=True)]

            # If a forced win is found inside the completed horizon, take it.
            if best_val > WIN_SCORE // 2:
                break

        except SearchTimeout:
            break

    return decode_move(best_move)
