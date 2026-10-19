
from math import inf
import time

BOARD_SIZE = 8


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    start_time = time.perf_counter()
    time_limit = 0.92

    my_goal = 0 if color == 'b' else 7
    opp_color = 'w' if color == 'b' else 'b'
    my_dir = -1 if color == 'b' else 1
    opp_dir = -my_dir

    me_set = set(me)
    opp_set = set(opp)

    def inb(r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def gen_moves(side_set, enemy_set, side_color):
        d = -1 if side_color == 'b' else 1
        all_occ = side_set | enemy_set
        moves = []
        for r, c in side_set:
            nr = r + d
            if not (0 <= nr < BOARD_SIZE):
                continue

            # diagonal moves, including captures or empty diagonals
            for dc in (-1, 1):
                nc = c + dc
                if 0 <= nc < BOARD_SIZE and (nr, nc) not in side_set:
                    # diagonal may move to empty or opponent, never own piece
                    moves.append(((r, c), (nr, nc)))

            # straight move only to empty
            if (nr, c) not in all_occ:
                moves.append(((r, c), (nr, c)))
        return moves

    def apply_move(side_set, enemy_set, mv):
        a, b = mv
        ns = set(side_set)
        ne = set(enemy_set)
        ns.remove(a)
        ns.add(b)
        if b in ne:
            ne.remove(b)
        return ns, ne

    def is_win_after(side_set, enemy_set, side_color):
        goal = 0 if side_color == 'b' else 7
        return not enemy_set or any(r == goal for r, _ in side_set)

    def attackers_of(square, side_set, side_color):
        # side_color pieces attack one row forward diagonally
        r, c = square
        d = -1 if side_color == 'b' else 1
        # A side piece at (r-d, c+-1) attacks square.
        cnt = 0
        pr = r - d
        for pc in (c - 1, c + 1):
            if (pr, pc) in side_set:
                cnt += 1
        return cnt

    def protected(square, side_set, side_color):
        return attackers_of(square, side_set, side_color) > 0

    def passed_pawn_score(r, c, enemy_set, side_color):
        d = -1 if side_color == 'b' else 1
        score = 0
        rr = r + d
        blocked = False
        while 0 <= rr < BOARD_SIZE:
            for cc in (c - 1, c, c + 1):
                if 0 <= cc < BOARD_SIZE and (rr, cc) in enemy_set:
                    blocked = True
            rr += d
        if not blocked:
            score += 45
        return score

    def evaluate(my_set, en_set):
        if not en_set:
            return 100000
        if not my_set:
            return -100000
        if any(r == my_goal for r, _ in my_set):
            return 100000
        if any(r == (7 if color == 'b' else 0) for r, _ in en_set):
            return -100000

        score = 0

        # Material.
        score += 115 * (len(my_set) - len(en_set))

        # Advancement and promotion pressure.
        for r, c in my_set:
            adv = (7 - r) if color == 'b' else r
            dist = abs(my_goal - r)
            score += 9 * adv
            score += (7 - dist) * (7 - dist) * 3

            if dist <= 2:
                score += 35 * (3 - dist)

            # central files are more flexible
            score += 4 * (3.5 - abs(c - 3.5))

            # protection and exposure
            if protected((r, c), my_set, color):
                score += 16
            if attackers_of((r, c), en_set, opp_color):
                score -= 24
                if not protected((r, c), my_set, color):
                    score -= 26

            # connected neighbors
            for dc in (-1, 1):
                if (r, c + dc) in my_set:
                    score += 4
                if (r - my_dir, c + dc) in my_set:
                    score += 5
                if (r + my_dir, c + dc) in my_set:
                    score += 5

            score += passed_pawn_score(r, c, en_set, color)

        opp_goal = 7 if color == 'b' else 0
        for r, c in en_set:
            adv = r if color == 'b' else (7 - r)
            dist = abs(opp_goal - r)
            score -= 9 * adv
            score -= (7 - dist) * (7 - dist) * 3

            if dist <= 2:
                score -= 40 * (3 - dist)

            score -= 4 * (3.5 - abs(c - 3.5))

            if protected((r, c), en_set, opp_color):
                score -= 12
            if attackers_of((r, c), my_set, color):
                score += 22
                if not protected((r, c), en_set, opp_color):
                    score += 22

            score -= passed_pawn_score(r, c, my_set, opp_color)

        # Strong bonus for immediate threats next turn.
        for mv in gen_moves(my_set, en_set, color):
            _, to = mv
            if to[0] == my_goal:
                score += 220
        for mv in gen_moves(en_set, my_set, opp_color):
            _, to = mv
            if to[0] == (7 if color == 'b' else 0):
                score -= 260

        return score

    def move_score(mv, side_set, enemy_set, side_color):
        frm, to = mv
        d = -1 if side_color == 'b' else 1
        goal = 0 if side_color == 'b' else 7
        enemy_color = 'w' if side_color == 'b' else 'b'
        s = 0
        if to[0] == goal:
            s += 100000
        if to in enemy_set:
            s += 650
        # Prefer advancement.
        s += 20 * ((frm[0] - to[0]) if d == -1 else (to[0] - frm[0]))
        # Prefer central flexible squares.
        s += int(8 * (3.5 - abs(to[1] - 3.5)))
        # Prefer safe/protected destinations.
        temp_side = set(side_set)
        temp_enemy = set(enemy_set)
        temp_side.remove(frm)
        temp_side.add(to)
        if to in temp_enemy:
            temp_enemy.remove(to)
        if attackers_of(to, temp_enemy, enemy_color):
            s -= 160
            if protected(to, temp_side, side_color):
                s += 70
        if protected(to, temp_side, side_color):
            s += 45
        # Advance passed pawns.
        s += passed_pawn_score(to[0], to[1], temp_enemy, side_color)
        return s

    root_moves = gen_moves(me_set, opp_set, color)
    if not root_moves:
        return ((0, 0), (0, 0))  # Should never happen in legal Breakthrough positions.

    # Immediate win.
    for mv in root_moves:
        ns, ne = apply_move(me_set, opp_set, mv)
        if is_win_after(ns, ne, color):
            return mv

    root_moves.sort(key=lambda m: move_score(m, me_set, opp_set, color), reverse=True)
    best_move = root_moves[0]

    # If opponent has an immediate winning move, prefer moves that prevent it if possible.
    def opponent_immediate_win_exists(my_s, en_s):
        for mv in gen_moves(en_s, my_s, opp_color):
            ns, ne = apply_move(en_s, my_s, mv)
            if is_win_after(ns, ne, opp_color):
                return True
        return False

    safe_root = []
    for mv in root_moves:
        ns, ne = apply_move(me_set, opp_set, mv)
        if not opponent_immediate_win_exists(ns, ne):
            safe_root.append(mv)
    if safe_root:
        best_move = safe_root[0]
        root_moves = safe_root

    trans = {}

    def alphabeta(my_s, en_s, depth, alpha, beta, maximizing):
        if time.perf_counter() - start_time > time_limit:
            raise TimeoutError

        key = (frozenset(my_s), frozenset(en_s), depth, maximizing)
        if key in trans:
            return trans[key]

        if not en_s:
            return 100000 + depth
        if not my_s:
            return -100000 - depth
        if any(r == my_goal for r, _ in my_s):
            return 100000 + depth
        if any(r == (7 if color == 'b' else 0) for r, _ in en_s):
            return -100000 - depth
        if depth == 0:
            return evaluate(my_s, en_s)

        if maximizing:
            moves = gen_moves(my_s, en_s, color)
            if not moves:
                return -99999
            moves.sort(key=lambda m: move_score(m, my_s, en_s, color), reverse=True)
            val = -inf
            for mv in moves:
                ns, ne = apply_move(my_s, en_s, mv)
                score = alphabeta(ns, ne, depth - 1, alpha, beta, False)
                if score > val:
                    val = score
                alpha = max(alpha, val)
                if alpha >= beta:
                    break
            trans[key] = val
            return val
        else:
            moves = gen_moves(en_s, my_s, opp_color)
            if not moves:
                return 99999
            moves.sort(key=lambda m: move_score(m, en_s, my_s, opp_color), reverse=True)
            val = inf
            for mv in moves:
                ns_opp, ne_my = apply_move(en_s, my_s, mv)
                # From our perspective: our pieces are ne_my, enemy pieces are ns_opp.
                score = alphabeta(ne_my, ns_opp, depth - 1, alpha, beta, True)
                if score < val:
                    val = score
                beta = min(beta, val)
                if alpha >= beta:
                    break
            trans[key] = val
            return val

    # Iterative deepening. In typical positions this reaches 4-5 plies within 1s.
    max_depth = 5
    try:
        for depth in range(1, max_depth + 1):
            if time.perf_counter() - start_time > time_limit:
                break
            current_best = best_move
            current_score = -inf
            ordered = list(root_moves)
            ordered.sort(key=lambda m: (m == best_move, move_score(m, me_set, opp_set, color)), reverse=True)

            for mv in ordered:
                if time.perf_counter() - start_time > time_limit:
                    raise TimeoutError
                ns, ne = apply_move(me_set, opp_set, mv)
                score = alphabeta(ns, ne, depth - 1, -inf, inf, False)
                if score > current_score:
                    current_score = score
                    current_best = mv

            best_move = current_best
    except Exception:
        pass

    # Final legality guard.
    legal = set(root_moves if root_moves else gen_moves(me_set, opp_set, color))
    if best_move in legal:
        return best_move

    all_legal = gen_moves(me_set, opp_set, color)
    if all_legal:
        all_legal.sort(key=lambda m: move_score(m, me_set, opp_set, color), reverse=True)
        return all_legal[0]

    # Impossible in non-terminal legal play, but keeps API total.
    return ((0, 0), (0, 0))
