
import time

MATE = 1_000_000
INF = 2_000_000
VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
PASSED = [0, 5, 12, 25, 45, 80, 140]
KNIGHT_OFFS = ((1, 2), (2, 1), (2, -1), (1, -2), (-1, -2), (-2, -1), (-2, 1), (-1, 2))
KING_OFFS = ((1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1))
DIAG_DIRS = ((1, 1), (1, -1), (-1, 1), (-1, -1))
STRAIGHT_DIRS = ((1, 0), (-1, 0), (0, 1), (0, -1))


class _Timeout(Exception):
    pass


def other(color):
    return 'b' if color == 'w' else 'w'


def sq_to_idx(s):
    return (int(s[1]) - 1) * 8 + (ord(s[0]) - 97)


def idx_to_sq(i):
    return chr(97 + (i % 8)) + str(i // 8 + 1)


def in_bounds(r, f):
    return 0 <= r < 8 and 0 <= f < 8


def find_king(board, color):
    target = color + 'K'
    for i, p in enumerate(board):
        if p == target:
            return i
    return None


def file_has_pawn(bits, file):
    return ((bits >> file) & 1) != 0


def is_endgame(board):
    queens = 0
    non_king_material = 0
    for p in board:
        if not p:
            continue
        t = p[1]
        if t == 'Q':
            queens += 1
        if t != 'P' and t != 'K':
            non_king_material += VALUES[t]
    return queens == 0 or non_king_material <= 2600


def is_attacked(board, idx, by_color):
    if idx is None:
        return False
    r = idx // 8
    f = idx % 8

    # Pawns
    sr = r - 1 if by_color == 'w' else r + 1
    if 0 <= sr < 8:
        pawn = by_color + 'P'
        for sf in (f - 1, f + 1):
            if 0 <= sf < 8 and board[sr * 8 + sf] == pawn:
                return True

    # Knights
    knight = by_color + 'N'
    for dr, df in KNIGHT_OFFS:
        nr, nf = r + dr, f + df
        if in_bounds(nr, nf) and board[nr * 8 + nf] == knight:
            return True

    # King adjacency
    king = by_color + 'K'
    for dr, df in KING_OFFS:
        nr, nf = r + dr, f + df
        if in_bounds(nr, nf) and board[nr * 8 + nf] == king:
            return True

    # Sliding pieces
    bishop_like = ('B', 'Q')
    rook_like = ('R', 'Q')
    for dr, df in DIAG_DIRS:
        nr, nf = r + dr, f + df
        while in_bounds(nr, nf):
            p = board[nr * 8 + nf]
            if p:
                if p[0] == by_color and p[1] in bishop_like:
                    return True
                break
            nr += dr
            nf += df

    for dr, df in STRAIGHT_DIRS:
        nr, nf = r + dr, f + df
        while in_bounds(nr, nf):
            p = board[nr * 8 + nf]
            if p:
                if p[0] == by_color and p[1] in rook_like:
                    return True
                break
            nr += dr
            nf += df

    return False


def apply_move(board, move):
    frm = sq_to_idx(move[:2])
    to = sq_to_idx(move[2:4])
    nb = board[:]  # small copy is fast and very safe
    piece = nb[frm]
    if piece is None:
        return nb

    nb[frm] = None
    color = piece[0]
    typ = piece[1]

    # castling: move rook as well as king
    if typ == 'K' and abs(to - frm) == 2:
        if color == 'w':
            if to == 6:      # e1g1
                nb[5] = nb[7]
                nb[7] = None
            elif to == 2:    # e1c1
                nb[3] = nb[0]
                nb[0] = None
        else:
            if to == 62:     # e8g8
                nb[61] = nb[63]
                nb[63] = None
            elif to == 58:   # e8c8
                nb[59] = nb[56]
                nb[56] = None

    if len(move) == 5:
        nb[to] = color + move[4].upper()
    else:
        nb[to] = piece
    return nb


def generate_pseudo(board, color, captures_only=False):
    opp = other(color)
    moves = []
    white = color == 'w'
    step = 8 if white else -8
    start_rank = 1 if white else 6
    promo_rank = 7 if white else 0

    for idx, piece in enumerate(board):
        if not piece or piece[0] != color:
            continue
        typ = piece[1]
        r = idx // 8
        f = idx % 8

        if typ == 'P':
            # captures and capture-promotions
            for df in (-1, 1):
                nf = f + df
                if 0 <= nf < 8:
                    to = idx + step + df
                    if 0 <= to < 64:
                        target = board[to]
                        if target and target[0] == opp and target[1] != 'K':
                            base = idx_to_sq(idx) + idx_to_sq(to)
                            if to // 8 == promo_rank:
                                for pr in 'qrbn':
                                    moves.append(base + pr)
                            else:
                                moves.append(base)

            # pushes; quiet promotion is tactical, so keep it even in capture-only mode
            one = idx + step
            if 0 <= one < 64 and board[one] is None:
                base = idx_to_sq(idx) + idx_to_sq(one)
                if one // 8 == promo_rank:
                    for pr in 'qrbn':
                        moves.append(base + pr)
                elif not captures_only:
                    moves.append(base)
                    two = idx + 2 * step
                    if r == start_rank and 0 <= two < 64 and board[two] is None:
                        moves.append(idx_to_sq(idx) + idx_to_sq(two))

        elif typ == 'N' or typ == 'K':
            offs = KNIGHT_OFFS if typ == 'N' else KING_OFFS
            for dr, df in offs:
                nr, nf = r + dr, f + df
                if not in_bounds(nr, nf):
                    continue
                to = nr * 8 + nf
                target = board[to]
                if target is None:
                    if not captures_only:
                        moves.append(idx_to_sq(idx) + idx_to_sq(to))
                elif target[0] == opp and target[1] != 'K':
                    moves.append(idx_to_sq(idx) + idx_to_sq(to))

            # Inferred castling: if king and rook are still on home squares.
            if typ == 'K' and not captures_only:
                if color == 'w' and idx == 4:
                    if board[7] == 'wR' and board[5] is None and board[6] is None:
                        if not is_attacked(board, 4, opp) and not is_attacked(board, 5, opp) and not is_attacked(board, 6, opp):
                            moves.append('e1g1')
                    if board[0] == 'wR' and board[1] is None and board[2] is None and board[3] is None:
                        if not is_attacked(board, 4, opp) and not is_attacked(board, 3, opp) and not is_attacked(board, 2, opp):
                            moves.append('e1c1')
                elif color == 'b' and idx == 60:
                    if board[63] == 'bR' and board[61] is None and board[62] is None:
                        if not is_attacked(board, 60, opp) and not is_attacked(board, 61, opp) and not is_attacked(board, 62, opp):
                            moves.append('e8g8')
                    if board[56] == 'bR' and board[57] is None and board[58] is None and board[59] is None:
                        if not is_attacked(board, 60, opp) and not is_attacked(board, 59, opp) and not is_attacked(board, 58, opp):
                            moves.append('e8c8')

        elif typ == 'B' or typ == 'R' or typ == 'Q':
            dirs = ()
            if typ == 'B':
                dirs = DIAG_DIRS
            elif typ == 'R':
                dirs = STRAIGHT_DIRS
            else:
                dirs = DIAG_DIRS + STRAIGHT_DIRS
            for dr, df in dirs:
                nr, nf = r + dr, f + df
                while in_bounds(nr, nf):
                    to = nr * 8 + nf
                    target = board[to]
                    if target is None:
                        if not captures_only:
                            moves.append(idx_to_sq(idx) + idx_to_sq(to))
                    else:
                        if target[0] == opp and target[1] != 'K':
                            moves.append(idx_to_sq(idx) + idx_to_sq(to))
                        break
                    nr += dr
                    nf += df
    return moves


def generate_legal(board, color, captures_only=False):
    opp = other(color)
    king_idx = find_king(board, color)
    legal = []
    for mv in generate_pseudo(board, color, captures_only):
        frm = sq_to_idx(mv[:2])
        to = sq_to_idx(mv[2:4])
        piece = board[frm]
        if piece is None:
            continue
        nb = apply_move(board, mv)
        kidx = to if piece[1] == 'K' else king_idx
        if kidx is not None and not is_attacked(nb, kidx, opp):
            legal.append(mv)
    return legal


def order_moves(board, moves, color):
    opp = other(color)

    def key(mv):
        frm = sq_to_idx(mv[:2])
        to = sq_to_idx(mv[2:4])
        piece = board[frm]
        target = board[to]
        score = 0
        if target and target[0] == opp and target[1] != 'K':
            score += 100 * VALUES[target[1]] - VALUES[piece[1]]
        if len(mv) == 5:
            score += VALUES[mv[4].upper()] + 700
        if piece[1] == 'K' and abs(to - frm) == 2:
            score += 45
        return score

    return sorted(moves, key=key, reverse=True)


def evaluate(board, color):
    # One pass collects pawn file bitboards and piece locations.
    pawn_bits = {'w': 0, 'b': 0}
    pawns = []
    rooks = []
    bishops = {'w': 0, 'b': 0}
    kings = {}

    for idx, p in enumerate(board):
        if not p:
            continue
        c, t = p[0], p[1]
        f = idx % 8
        if t == 'P':
            pawn_bits[c] |= (1 << f)
            pawns.append(idx)
        elif t == 'R':
            rooks.append(idx)
        elif t == 'B':
            bishops[c] += 1
        elif t == 'K':
            kings[c] = idx

    endgame = is_endgame(board)
    score = {'w': 0, 'b': 0}

    for idx, p in enumerate(board):
        if not p:
            continue
        c, t = p[0], p[1]
        r = idx // 8
        f = idx % 8
        val = VALUES[t]
        bonus = 0

        if t == 'P':
            adv = r if c == 'w' else (7 - r)
            bonus += adv * 8
            bonus += int((3.5 - abs(f - 3.5)) * 4)
        elif t == 'N':
            dist = abs(f - 3.5) + abs(r - 3.5)
            bonus += int(34 - 6 * dist)
            if not endgame and ((c == 'w' and r == 0) or (c == 'b' and r == 7)):
                bonus -= 8
        elif t == 'B':
            dist = abs(f - 3.5) + abs(r - 3.5)
            bonus += int(18 - 4 * dist)
        elif t == 'R':
            bonus += 4
            # rook on the opponent's second rank is often strong
            if (c == 'w' and r == 6) or (c == 'b' and r == 1):
                bonus += 15
        elif t == 'Q':
            bonus += 0
        elif t == 'K':
            if endgame:
                dist = abs(f - 3.5) + abs(r - 3.5)
                bonus += int(26 - 6 * dist)
            else:
                if c == 'w':
                    if r == 0 and f in (1, 2, 5, 6):
                        bonus += 28
                    if r > 0:
                        bonus -= 18
                    if f in (3, 4):
                        bonus -= 12
                else:
                    if r == 7 and f in (1, 2, 5, 6):
                        bonus += 28
                    if r < 7:
                        bonus -= 18
                    if f in (3, 4):
                        bonus -= 12

        if c == 'w':
            score['w'] += val + bonus
        else:
            score['b'] += val + bonus

    # Bishop pair
    if bishops['w'] >= 2:
        score['w'] += 32
    if bishops['b'] >= 2:
        score['b'] += 32

    # Passed pawns
    for idx in pawns:
        p = board[idx]
        if not p:  # should not happen, but keep evaluation total
            continue
        c = p[0]
        r = idx // 8
        f = idx % 8
        enemy = 'b' if c == 'w' else 'w'
        passed = True
        if c == 'w':
            for nf in (f - 1, f, f + 1):
                if 0 <= nf < 8 and file_has_pawn(pawn_bits[enemy], nf):
                    # scan ranks ahead
                    for rr in range(r + 1, 8):
                        q = board[rr * 8 + nf]
                        if q == enemy + 'P':
                            passed = False
                            break
                    if not passed:
                        break
        else:
            for nf in (f - 1, f, f + 1):
                if 0 <= nf < 8 and file_has_pawn(pawn_bits[enemy], nf):
                    for rr in range(r - 1, -1, -1):
                        q = board[rr * 8 + nf]
                        if q == enemy + 'P':
                            passed = False
                            break
                    if not passed:
                        break
        if passed:
            adv = r if c == 'w' else 7 - r
            if 0 <= adv < len(PASSED):
                score[c] += PASSED[adv]

    # Rook file quality
    for idx in rooks:
        p = board[idx]
        if not p:
            continue
        c = p[0]
        f = idx % 8
        own = file_has_pawn(pawn_bits[c], f)
        enemy = file_has_pawn(pawn_bits[other(c)], f)
        if not own and not enemy:
            score[c] += 18
        elif not own:
            score[c] += 10

    # Check is worth a tempo and often much more.
    kw = kings.get('w')
    kb = kings.get('b')
    if kw is not None and is_attacked(board, kw, 'b'):
        score['b'] += 60
    if kb is not None and is_attacked(board, kb, 'w'):
        score['w'] += 60

    return score['w'] - score['b'] if color == 'w' else score['b'] - score['w']


def qsearch(board, alpha, beta, color, state, qdepth=0):
    state['nodes'] += 1
    if (state['nodes'] & 127) == 0 and time.perf_counter() > state['deadline']:
        raise _Timeout()

    opp = other(color)
    king_idx = find_king(board, color)
    incheck = is_attacked(board, king_idx, opp)

    if incheck:
        moves = generate_legal(board, color, False)
        if not moves:
            return -MATE + min(qdepth, 50)
        if qdepth >= 32:
            return evaluate(board, color)
    else:
        stand = evaluate(board, color)
        if stand >= beta:
            return beta
        if stand > alpha:
            alpha = stand
        if qdepth >= 32:
            return alpha
        moves = generate_legal(board, color, True)

    for mv in order_moves(board, moves, color):
        child = apply_move(board, mv)
        score = -qsearch(child, -beta, -alpha, opp, state, qdepth + 1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def search(board, depth, alpha, beta, color, state):
    state['nodes'] += 1
    if (state['nodes'] & 127) == 0 and time.perf_counter() > state['deadline']:
        raise _Timeout()

    if depth <= 0:
        return qsearch(board, alpha, beta, color, state)

    moves = generate_legal(board, color, False)
    if not moves:
        if is_attacked(board, find_king(board, color), other(color)):
            return -MATE
        return 0

    for mv in order_moves(board, moves, color):
        child = apply_move(board, mv)
        score = -search(child, depth - 1, -beta, -alpha, other(color), state)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha


def policy(pieces: dict[str, str], to_play: str) -> str:
    start = time.perf_counter()
    deadline = start + 0.86

    board = [None] * 64
    for sq, pc in pieces.items():
        try:
            board[sq_to_idx(sq)] = pc
        except Exception:
            pass

    color = 'w' if to_play == 'white' else 'b'
    opp = other(color)

    moves = generate_legal(board, color, False)
    if not moves:
        # Should be unreachable in normal play; never return an empty string.
        fallback = generate_pseudo(board, color, False)
        return fallback[0] if fallback else 'a1a1'
    if len(moves) == 1:
        return moves[0]

    ordered = order_moves(board, moves, color)
    n = len(ordered)
    if n <= 12:
        max_depth = 6
    elif n <= 22:
        max_depth = 5
    elif n <= 42:
        max_depth = 4
    else:
        max_depth = 3

    state = {'nodes': 0, 'deadline': deadline}
    best_move = ordered[0]
    move_scores = {}

    try:
        for depth in range(1, max_depth + 1):
            alpha = -INF
            beta = INF
            current_best = ordered[0]
            current_scores = {}
            for mv in ordered:
                if time.perf_counter() > deadline:
                    raise _Timeout()
                child = apply_move(board, mv)
                score = -search(child, depth - 1, -beta, -alpha, opp, state)
                current_scores[mv] = score
                if score > alpha:
                    alpha = score
                    current_best = mv
            best_move = current_best
            move_scores = current_scores
            ordered = sorted(ordered, key=lambda m: move_scores.get(m, -INF), reverse=True)
            if abs(move_scores.get(best_move, 0)) > MATE - 5000:
                break
    except _Timeout:
        pass

    # Final safety: only return a move known legal by our generator.
    if best_move in moves:
        return best_move
    return moves[0]
