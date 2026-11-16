
import time

FILE_A = 0x0101010101010101
FILE_H = 0x8080808080808080

ROW_0 = 0x00000000000000FF
ROW_1 = 0x000000000000FF00
ROW_6 = 0x00FF000000000000
ROW_7 = 0xFF00000000000000

MATE = 10**9
EXACT, LOWER, UPPER = 0, 1, 2

CENTER = [0, 1, 2, 3, 3, 2, 1, 0]
PROG = [0, 2, 5, 9, 15, 24, 36, 0]

WHITE_SQ = [8 * PROG[i >> 3] + 2 * CENTER[i & 7] for i in range(64)]
BLACK_SQ = [8 * PROG[7 - (i >> 3)] + 2 * CENTER[i & 7] for i in range(64)]


class SearchTimeout(Exception):
    pass


def opponent(side: str) -> str:
    return 'b' if side == 'w' else 'w'


def list_to_bits(pieces: list[tuple[int, int]]) -> int:
    bb = 0
    for r, c in pieces:
        if 0 <= r < 8 and 0 <= c < 8:
            bb |= 1 << (r * 8 + c)
    return bb


def idx_to_coord(idx: int) -> tuple[int, int]:
    return (idx >> 3, idx & 7)


def terminal_winner(w: int, b: int):
    if (w & ROW_7) or b == 0:
        return 'w'
    if (b & ROW_0) or w == 0:
        return 'b'
    return None


def move_wins_immediately(w: int, b: int, side: str, dst: int) -> bool:
    dstm = 1 << dst
    if side == 'w':
        return dst >= 56 or b == dstm
    return dst < 8 or w == dstm


def apply_move(w: int, b: int, side: str, src: int, dst: int) -> tuple[int, int]:
    srcm = 1 << src
    dstm = 1 << dst
    if side == 'w':
        return ((w ^ srcm) | dstm), (b & ~dstm)
    return (w & ~dstm), ((b ^ srcm) | dstm)


def gen_moves(w: int, b: int, side: str) -> list[tuple[int, int]]:
    own = w if side == 'w' else b
    opp = b if side == 'w' else w
    occ = own | opp
    moves = []

    bb = own
    if side == 'w':
        while bb:
            lsb = bb & -bb
            bb ^= lsb
            src = lsb.bit_length() - 1
            c = src & 7

            dst = src + 8
            if dst < 64:
                dstm = 1 << dst
                if (occ & dstm) == 0:
                    moves.append((src, dst))

            if c > 0:
                dst = src + 7
                dstm = 1 << dst
                if (own & dstm) == 0:
                    moves.append((src, dst))

            if c < 7:
                dst = src + 9
                dstm = 1 << dst
                if (own & dstm) == 0:
                    moves.append((src, dst))
    else:
        while bb:
            lsb = bb & -bb
            bb ^= lsb
            src = lsb.bit_length() - 1
            c = src & 7

            dst = src - 8
            if dst >= 0:
                dstm = 1 << dst
                if (occ & dstm) == 0:
                    moves.append((src, dst))

            if c > 0:
                dst = src - 9
                if dst >= 0:
                    dstm = 1 << dst
                    if (own & dstm) == 0:
                        moves.append((src, dst))

            if c < 7:
                dst = src - 7
                if dst >= 0:
                    dstm = 1 << dst
                    if (own & dstm) == 0:
                        moves.append((src, dst))

    return moves


def mobility_count_side(own: int, opp: int, side: str) -> int:
    occ = own | opp
    count = 0
    bb = own

    if side == 'w':
        while bb:
            lsb = bb & -bb
            bb ^= lsb
            src = lsb.bit_length() - 1
            c = src & 7

            dst = src + 8
            if dst < 64 and (occ & (1 << dst)) == 0:
                count += 1
            if c > 0 and (own & (1 << (src + 7))) == 0:
                count += 1
            if c < 7 and (own & (1 << (src + 9))) == 0:
                count += 1
    else:
        while bb:
            lsb = bb & -bb
            bb ^= lsb
            src = lsb.bit_length() - 1
            c = src & 7

            dst = src - 8
            if dst >= 0 and (occ & (1 << dst)) == 0:
                count += 1
            if c > 0 and (own & (1 << (src - 9))) == 0:
                count += 1
            if c < 7 and (own & (1 << (src - 7))) == 0:
                count += 1

    return count


def has_last_capture_win(w: int, b: int, side: str) -> bool:
    if side == 'w':
        if b == 0 or (b & (b - 1)) != 0:
            return False
        t = b.bit_length() - 1
        r = t >> 3
        c = t & 7
        if r == 0:
            return False
        if c < 7 and (w & (1 << ((r - 1) * 8 + (c + 1)))):
            return True
        if c > 0 and (w & (1 << ((r - 1) * 8 + (c - 1)))):
            return True
        return False
    else:
        if w == 0 or (w & (w - 1)) != 0:
            return False
        t = w.bit_length() - 1
        r = t >> 3
        c = t & 7
        if r == 7:
            return False
        if c < 7 and (b & (1 << ((r + 1) * 8 + (c + 1)))):
            return True
        if c > 0 and (b & (1 << ((r + 1) * 8 + (c - 1)))):
            return True
        return False


def has_immediate_win(w: int, b: int, side: str) -> bool:
    if side == 'w':
        if w & ROW_6:
            return True
    else:
        if b & ROW_1:
            return True
    return has_last_capture_win(w, b, side)


def evaluate_white(w: int, b: int) -> int:
    wc = w.bit_count()
    bc = b.bit_count()

    score = 125 * (wc - bc)

    psw = 0
    bb = w
    while bb:
        lsb = bb & -bb
        bb ^= lsb
        psw += WHITE_SQ[lsb.bit_length() - 1]

    psb = 0
    bb = b
    while bb:
        lsb = bb & -bb
        bb ^= lsb
        psb += BLACK_SQ[lsb.bit_length() - 1]

    score += psw - psb

    white_front = (w.bit_length() - 1) >> 3
    black_front = 7 - (((b & -b).bit_length() - 1) >> 3)
    score += 24 * (white_front - black_front)

    white_att = ((w & ~FILE_A) << 7) | ((w & ~FILE_H) << 9)
    black_att = ((b & ~FILE_A) >> 9) | ((b & ~FILE_H) >> 7)

    defended_w = (w & white_att).bit_count()
    defended_b = (b & black_att).bit_count()
    score += 10 * (defended_w - defended_b)

    caps_w = (white_att & b).bit_count()
    caps_b = (black_att & w).bit_count()
    score += 14 * (caps_w - caps_b)

    undef_w = (w & black_att & ~white_att).bit_count()
    undef_b = (b & white_att & ~black_att).bit_count()
    score += 18 * (undef_b - undef_w)

    score += 3 * (mobility_count_side(w, b, 'w') - mobility_count_side(b, w, 'b'))

    score += 90 * ((w & ROW_6).bit_count() - (b & ROW_1).bit_count())

    return score


def move_order_key(
    src: int,
    dst: int,
    w: int,
    b: int,
    side: str,
    tt_move,
    killer_row,
    history,
) -> int:
    score = 0
    move = (src, dst)

    if tt_move == move:
        score += 2_000_000

    if killer_row is not None:
        if killer_row[0] == move:
            score += 120_000
        elif killer_row[1] == move:
            score += 110_000

    if history is not None:
        score += history.get(move, 0)

    opp = b if side == 'w' else w
    dstm = 1 << dst
    capture = 1 if (opp & dstm) else 0

    if side == 'w':
        srow = src >> 3
        drow = dst >> 3
        if drow == 7:
            score += 10_000_000
        if drow == 6:
            score += 60_000
        score += 150 * (PROG[drow] - PROG[srow])
        if capture:
            enemy_prog = 7 - drow
            score += 40_000 + 100 * PROG[enemy_prog]
    else:
        sprog = 7 - (src >> 3)
        dprog = 7 - (dst >> 3)
        drow = dst >> 3
        if dst < 8:
            score += 10_000_000
        if drow == 1:
            score += 60_000
        score += 150 * (PROG[dprog] - PROG[sprog])
        if capture:
            enemy_prog = drow
            score += 40_000 + 100 * PROG[enemy_prog]

    score += 12 * CENTER[dst & 7]
    return score


def order_moves(
    moves: list[tuple[int, int]],
    w: int,
    b: int,
    side: str,
    tt_move,
    killers,
    ply: int,
    history,
) -> list[tuple[int, int]]:
    killer_row = killers[ply] if ply < len(killers) else None
    scored = []
    for src, dst in moves:
        scored.append((
            move_order_key(src, dst, w, b, side, tt_move, killer_row, history),
            src,
            dst,
        ))
    scored.sort(reverse=True)
    return [(src, dst) for _, src, dst in scored]


def fallback_best_move(w: int, b: int, side: str, moves: list[tuple[int, int]]) -> tuple[int, int]:
    best = moves[0]
    best_score = -10**18
    opp = opponent(side)

    for src, dst in moves:
        if move_wins_immediately(w, b, side, dst):
            return (src, dst)

        nw, nb = apply_move(w, b, side, src, dst)
        score = evaluate_white(nw, nb)
        if side == 'b':
            score = -score

        if has_immediate_win(nw, nb, opp):
            score -= 600_000
        if has_immediate_win(nw, nb, side):
            score += 20_000

        score += move_order_key(src, dst, w, b, side, None, None, None) // 100

        if score > best_score:
            best_score = score
            best = (src, dst)

    return best


def negamax(
    w: int,
    b: int,
    side: str,
    depth: int,
    alpha: int,
    beta: int,
    ply: int,
    deadline: float,
    tt: dict,
    history: dict,
    killers: list,
    nodes: list[int],
) -> int:
    nodes[0] += 1
    if (nodes[0] & 1023) == 0 and time.perf_counter() >= deadline:
        raise SearchTimeout

    winner = terminal_winner(w, b)
    if winner is not None:
        return MATE if winner == side else -MATE

    opp_side = opponent(side)

    if depth <= 0:
        if has_immediate_win(w, b, side):
            return MATE - 1
        if has_immediate_win(w, b, opp_side):
            depth = 1
        else:
            raw = evaluate_white(w, b)
            return raw if side == 'w' else -raw

    key = (w, b, side)
    alpha_orig = alpha
    beta_orig = beta
    tt_move = None

    entry = tt.get(key)
    if entry is not None:
        e_depth, e_flag, e_score, e_move = entry
        tt_move = e_move
        if e_depth >= depth:
            if e_flag == EXACT:
                return e_score
            if e_flag == LOWER:
                if e_score > alpha:
                    alpha = e_score
            else:
                if e_score < beta:
                    beta = e_score
            if alpha >= beta:
                return e_score

    moves = gen_moves(w, b, side)
    if not moves:
        return -MATE

    ordered = order_moves(moves, w, b, side, tt_move, killers, ply, history)

    best_score = -MATE
    best_move = ordered[0]

    for i, (src, dst) in enumerate(ordered):
        dstm = 1 << dst
        capture = ((b if side == 'w' else w) & dstm) != 0

        if move_wins_immediately(w, b, side, dst):
            score = MATE
        else:
            nw, nb = apply_move(w, b, side, src, dst)

            if i == 0:
                score = -negamax(
                    nw, nb, opp_side, depth - 1,
                    -beta, -alpha, ply + 1,
                    deadline, tt, history, killers, nodes
                )
            else:
                score = -negamax(
                    nw, nb, opp_side, depth - 1,
                    -alpha - 1, -alpha, ply + 1,
                    deadline, tt, history, killers, nodes
                )
                if alpha < score < beta:
                    score = -negamax(
                        nw, nb, opp_side, depth - 1,
                        -beta, -alpha, ply + 1,
                        deadline, tt, history, killers, nodes
                    )

        if score > best_score:
            best_score = score
            best_move = (src, dst)

        if score > alpha:
            alpha = score

        if alpha >= beta:
            if not capture and ply < len(killers):
                km = killers[ply]
                mv = (src, dst)
                if km[0] != mv:
                    km[1] = km[0]
                    km[0] = mv
            history[(src, dst)] = history.get((src, dst), 0) + depth * depth
            break

    if best_score <= alpha_orig:
        flag = UPPER
    elif best_score >= beta_orig:
        flag = LOWER
    else:
        flag = EXACT
    tt[key] = (depth, flag, best_score, best_move)

    return best_score


def root_search(
    w: int,
    b: int,
    side: str,
    depth: int,
    deadline: float,
    tt: dict,
    history: dict,
    killers: list,
    nodes: list[int],
    preferred_move,
):
    if time.perf_counter() >= deadline:
        raise SearchTimeout

    moves = gen_moves(w, b, side)
    if not moves:
        return -MATE, None

    root_entry = tt.get((w, b, side))
    tt_move = preferred_move
    if root_entry is not None and root_entry[3] is not None:
        tt_move = root_entry[3]

    ordered = order_moves(moves, w, b, side, tt_move, killers, 0, history)

    alpha = -MATE
    beta = MATE
    best_score = -MATE
    best_move = ordered[0]
    opp_side = opponent(side)

    for i, (src, dst) in enumerate(ordered):
        if (i & 7) == 0 and time.perf_counter() >= deadline:
            raise SearchTimeout

        if move_wins_immediately(w, b, side, dst):
            score = MATE
        else:
            nw, nb = apply_move(w, b, side, src, dst)

            if i == 0:
                score = -negamax(
                    nw, nb, opp_side, depth - 1,
                    -beta, -alpha, 1,
                    deadline, tt, history, killers, nodes
                )
            else:
                score = -negamax(
                    nw, nb, opp_side, depth - 1,
                    -alpha - 1, -alpha, 1,
                    deadline, tt, history, killers, nodes
                )
                if alpha < score < beta:
                    score = -negamax(
                        nw, nb, opp_side, depth - 1,
                        -beta, -alpha, 1,
                        deadline, tt, history, killers, nodes
                    )

        if score > best_score:
            best_score = score
            best_move = (src, dst)

        if score > alpha:
            alpha = score

    tt[(w, b, side)] = (depth, EXACT, best_score, best_move)
    return best_score, best_move


def policy(
    me: list[tuple[int, int]],
    opp: list[tuple[int, int]],
    color: str
) -> tuple[tuple[int, int], tuple[int, int]]:
    side = 'b' if color == 'b' else 'w'

    if side == 'w':
        w = list_to_bits(me)
        b = list_to_bits(opp)
    else:
        b = list_to_bits(me)
        w = list_to_bits(opp)

    moves = gen_moves(w, b, side)

    if not moves:
        # Should not happen in valid non-terminal positions.
        if me:
            fr = me[0]
            step = 1 if side == 'w' else -1
            to = (max(0, min(7, fr[0] + step)), fr[1])
            return fr, to
        return ((0, 0), (0, 0))

    for src, dst in moves:
        if move_wins_immediately(w, b, side, dst):
            return idx_to_coord(src), idx_to_coord(dst)

    best_move = fallback_best_move(w, b, side, moves)

    deadline = time.perf_counter() + 0.92
    tt = {}
    history = {}
    killers = [[None, None] for _ in range(128)]
    nodes = [0]

    total_pieces = len(me) + len(opp)
    if total_pieces >= 24:
        max_depth = 6
    elif total_pieces >= 16:
        max_depth = 8
    elif total_pieces >= 10:
        max_depth = 10
    else:
        max_depth = 14

    for depth in range(1, max_depth + 1):
        try:
            score, move = root_search(
                w, b, side, depth,
                deadline, tt, history, killers, nodes, best_move
            )
            if move is not None:
                best_move = move
            if score >= MATE // 2:
                break
        except SearchTimeout:
            break

    return idx_to_coord(best_move[0]), idx_to_coord(best_move[1])
