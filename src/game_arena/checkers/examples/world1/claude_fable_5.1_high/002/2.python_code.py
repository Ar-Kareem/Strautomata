
import time

ALL_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
TIME_BUDGET = 0.6
_LAST = {'exp': None}


class TimeUp(Exception):
    pass


def _dfs(board, side, r, c, path, captured, is_king, dirs, promo_row, out):
    found = False
    for dr, dc in dirs:
        lr = r + 2 * dr
        lc = c + 2 * dc
        if 0 <= lr < 8 and 0 <= lc < 8:
            mid = (r + dr) * 8 + (c + dc)
            m = board[mid]
            if m * side < 0 and mid not in captured and board[lr * 8 + lc] == 0:
                found = True
                land = lr * 8 + lc
                np_ = path + (land,)
                nc = captured + (mid,)
                if (not is_king) and lr == promo_row:
                    out.append((np_, nc))
                else:
                    _dfs(board, side, lr, lc, np_, nc, is_king, dirs, promo_row, out)
    if not found and captured:
        out.append((path, captured))


def _gen_moves(board, side, my_dir):
    fwd = my_dir * side
    promo_row = 0 if fwd == -1 else 7
    caps = []
    for sq in range(64):
        p = board[sq]
        if p * side <= 0:
            continue
        r = sq >> 3
        c = sq & 7
        is_king = (p == 2 * side)
        dirs = ALL_DIRS if is_king else ((fwd, -1), (fwd, 1))
        board[sq] = 0
        _dfs(board, side, r, c, (sq,), (), is_king, dirs, promo_row, caps)
        board[sq] = p
    if caps:
        caps.sort(key=lambda m: -len(m[1]))
        return caps
    moves = []
    for sq in range(64):
        p = board[sq]
        if p * side <= 0:
            continue
        r = sq >> 3
        c = sq & 7
        is_king = (p == 2 * side)
        dirs = ALL_DIRS if is_king else ((fwd, -1), (fwd, 1))
        for dr, dc in dirs:
            nr = r + dr
            nc = c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr * 8 + nc] == 0:
                moves.append(((sq, nr * 8 + nc), ()))
    return moves


def _apply(board, move, side, my_dir):
    nb = board[:]
    path, captured = move
    p = nb[path[0]]
    nb[path[0]] = 0
    for cp in captured:
        nb[cp] = 0
    dest = path[-1]
    fwd = my_dir * side
    promo_row = 0 if fwd == -1 else 7
    if p == side and (dest >> 3) == promo_row:
        p = 2 * side
    nb[dest] = p
    return nb


def _evaluate(board, my_dir):
    my_home = 7 if my_dir == -1 else 0
    opp_home = 7 - my_home
    score = 0
    my_mat = 0
    opp_mat = 0
    opp_men = 0
    my_men = 0
    total = 0
    my_pieces = []
    opp_pieces = []
    my_kings = []
    opp_kings = []
    for sq in range(64):
        p = board[sq]
        if p == 0:
            continue
        total += 1
        r = sq >> 3
        c = sq & 7
        central = 1 if (2 <= r <= 5 and 2 <= c <= 5) else 0
        if p == 1:
            my_mat += 100
            my_men += 1
            adv = (r - my_home) * my_dir
            s = 100 + 3 * adv + 4 * central
            if r == my_home:
                s += 7
            score += s
            my_pieces.append((r, c))
        elif p == 2:
            my_mat += 170
            score += 170 + 5 * central
            my_pieces.append((r, c))
            my_kings.append((r, c))
        elif p == -1:
            opp_mat += 100
            opp_men += 1
            adv = (r - opp_home) * (-my_dir)
            s = 100 + 3 * adv + 4 * central
            if r == opp_home:
                s += 7
            score -= s
            opp_pieces.append((r, c))
        else:
            opp_mat += 170
            score -= 170 + 5 * central
            opp_pieces.append((r, c))
            opp_kings.append((r, c))
    # Back-rank bonus only matters while the opponent has men to stop.
    if opp_men == 0:
        for (r, c) in my_pieces:
            if r == my_home and board[r * 8 + c] == 1:
                score -= 7
    if my_men == 0:
        for (r, c) in opp_pieces:
            if r == opp_home and board[r * 8 + c] == -1:
                score += 7
    diff = my_mat - opp_mat
    # Encourage trades when ahead, avoid when behind.
    score += (diff * (24 - total)) // 24
    # Endgame: leader's kings hunt the opponent.
    if total <= 10 and diff != 0:
        if diff > 0 and my_kings and opp_pieces:
            for (kr, kc) in my_kings:
                d = min(max(abs(kr - r), abs(kc - c)) for (r, c) in opp_pieces)
                score -= 3 * d
        elif diff < 0 and opp_kings and my_pieces:
            for (kr, kc) in opp_kings:
                d = min(max(abs(kr - r), abs(kc - c)) for (r, c) in my_pieces)
                score += 3 * d
    return score


class _Searcher:
    def __init__(self, my_dir, deadline):
        self.my_dir = my_dir
        self.deadline = deadline
        self.nodes = 0
        self.tt = {}

    def negamax(self, board, side, depth, alpha, beta, ply):
        self.nodes += 1
        if (self.nodes & 255) == 0 and time.perf_counter() > self.deadline:
            raise TimeUp()
        moves = _gen_moves(board, side, self.my_dir)
        if not moves:
            return -100000 + ply
        if depth <= 0 and not moves[0][1]:
            return side * _evaluate(board, self.my_dir)
        key = (tuple(board), side)
        entry = self.tt.get(key)
        tt_move = None
        if entry is not None:
            e_depth, e_flag, e_val, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_val
                elif e_flag == 1:
                    if e_val > alpha:
                        alpha = e_val
                elif e_flag == 2:
                    if e_val < beta:
                        beta = e_val
                if alpha >= beta:
                    return e_val
        if tt_move is not None and len(moves) > 1:
            for i, m in enumerate(moves):
                if m == tt_move:
                    if i != 0:
                        moves[0], moves[i] = moves[i], moves[0]
                    break
        orig_alpha = alpha
        best = -10 ** 9
        best_move = None
        for m in moves:
            nb = _apply(board, m, side, self.my_dir)
            v = -self.negamax(nb, -side, depth - 1, -beta, -alpha, ply + 1)
            if v > best:
                best = v
                best_move = m
            if v > alpha:
                alpha = v
            if alpha >= beta:
                break
        if best <= orig_alpha:
            flag = 2
        elif best >= beta:
            flag = 1
        else:
            flag = 0
        self.tt[key] = (depth, flag, best, best_move)
        return best


def _to_move(m):
    a = m[0][0]
    b = m[0][1]
    return ((a >> 3, a & 7), (b >> 3, b & 7))


def _policy(my_men, my_kings, opp_men, opp_kings, color, start):
    my_dir = -1 if color == 'b' else 1
    board = [0] * 64
    for (r, c) in my_men:
        board[r * 8 + c] = 1
    for (r, c) in my_kings:
        board[r * 8 + c] = 2
    for (r, c) in opp_men:
        board[r * 8 + c] = -1
    for (r, c) in opp_kings:
        board[r * 8 + c] = -2

    moves = _gen_moves(board, 1, my_dir)
    if not moves:
        # No legal move by our rules; return something plausible.
        pieces = list(my_men) + list(my_kings)
        if pieces:
            r, c = pieces[0]
            return ((r, c), (max(0, min(7, r + my_dir)), max(0, min(7, c + 1))))
        return ((0, 0), (1, 1))

    # Multi-jump continuation detection.
    exp = _LAST['exp']
    if exp is not None and exp[0] == color:
        cur_my = frozenset(tuple(x) for x in list(my_men) + list(my_kings))
        cur_opp = frozenset(tuple(x) for x in list(opp_men) + list(opp_kings))
        if cur_my == exp[1] and cur_opp == exp[2] and moves[0][1]:
            land = exp[3]
            cont = [m for m in moves if m[0][0] == land]
            if cont:
                moves = cont

    fallback = moves[0]
    if len(moves) == 1:
        best_move = fallback
    else:
        deadline = start + TIME_BUDGET
        searcher = _Searcher(my_dir, deadline)
        best_move = fallback
        root_moves = list(moves)
        try:
            for depth in range(1, 40):
                alpha = -10 ** 9
                beta = 10 ** 9
                cur_best = None
                cur_val = -10 ** 9
                for m in root_moves:
                    nb = _apply(board, m, 1, my_dir)
                    v = -searcher.negamax(nb, -1, depth - 1, -beta, -alpha, 1)
                    if v > cur_val:
                        cur_val = v
                        cur_best = m
                    if v > alpha:
                        alpha = v
                if cur_best is not None:
                    best_move = cur_best
                    root_moves.remove(cur_best)
                    root_moves.insert(0, cur_best)
                if cur_val > 90000 or cur_val < -90000:
                    break
                if time.perf_counter() > deadline:
                    break
        except TimeUp:
            pass

    # Record expected state after the first jump for continuation detection.
    path, captured = best_move
    if captured:
        first = ((path[0], path[1]), (captured[0],))
        nb = _apply(board, first, 1, my_dir)
        exp_my = frozenset((sq >> 3, sq & 7) for sq in range(64) if nb[sq] > 0)
        exp_opp = frozenset((sq >> 3, sq & 7) for sq in range(64) if nb[sq] < 0)
        _LAST['exp'] = (color, exp_my, exp_opp, path[1])
    else:
        _LAST['exp'] = None

    return _to_move(best_move)


def policy(my_men, my_kings, opp_men, opp_kings, color):
    start = time.perf_counter()
    try:
        return _policy(my_men, my_kings, opp_men, opp_kings, color, start)
    except Exception:
        try:
            my_dir = -1 if color == 'b' else 1
            board = [0] * 64
            for (r, c) in my_men:
                board[r * 8 + c] = 1
            for (r, c) in my_kings:
                board[r * 8 + c] = 2
            for (r, c) in opp_men:
                board[r * 8 + c] = -1
            for (r, c) in opp_kings:
                board[r * 8 + c] = -2
            moves = _gen_moves(board, 1, my_dir)
            if moves:
                return _to_move(moves[0])
        except Exception:
            pass
        pieces = list(my_men) + list(my_kings)
        if pieces:
            r, c = pieces[0]
            d = -1 if color == 'b' else 1
            return ((r, c), (max(0, min(7, r + d)), max(0, min(7, c + 1))))
        return ((0, 0), (1, 1))
