
import time

MATE = 10_000_000
INF = 1_000_000_000

OTHER = {"w": "b", "b": "w"}

ROW_MASKS = [(0xFF << (8 * r)) for r in range(8)]
ROW_OF = [i >> 3 for i in range(64)]
COL_OF = [i & 7 for i in range(64)]

CENTER_FILE_BONUS = [0, 1, 2, 3, 3, 2, 1, 0]
CENTER_BONUS_IDX = [CENTER_FILE_BONUS[c] for c in COL_OF]

ADV_W = [ROW_OF[i] for i in range(64)]
ADV_B = [7 - ROW_OF[i] for i in range(64)]

SUPPORT_MASK_W = [0] * 64
SUPPORT_MASK_B = [0] * 64
ATTACK_MASK_W = [0] * 64
ATTACK_MASK_B = [0] * 64
LANE_MASK_W = [0] * 64
LANE_MASK_B = [0] * 64

for idx in range(64):
    r = ROW_OF[idx]
    c = COL_OF[idx]

    sw = 0
    sb = 0
    aw = 0
    ab = 0
    lw = 0
    lb = 0

    # White support squares: one row behind diagonally.
    rr = r - 1
    if rr >= 0:
        if c > 0:
            sw |= 1 << (rr * 8 + (c - 1))
        if c < 7:
            sw |= 1 << (rr * 8 + (c + 1))

    # Black support squares: one row behind diagonally from black's perspective.
    rr = r + 1
    if rr <= 7:
        if c > 0:
            sb |= 1 << (rr * 8 + (c - 1))
        if c < 7:
            sb |= 1 << (rr * 8 + (c + 1))

    # Squares from which black can capture a white piece on idx.
    rr = r + 1
    if rr <= 7:
        if c > 0:
            aw |= 1 << (rr * 8 + (c - 1))
        if c < 7:
            aw |= 1 << (rr * 8 + (c + 1))

    # Squares from which white can capture a black piece on idx.
    rr = r - 1
    if rr >= 0:
        if c > 0:
            ab |= 1 << (rr * 8 + (c - 1))
        if c < 7:
            ab |= 1 << (rr * 8 + (c + 1))

    # Lane masks: same file and adjacent files ahead to goal.
    for rr in range(r + 1, 8):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc <= 7:
                lw |= 1 << (rr * 8 + cc)

    for rr in range(r - 1, -1, -1):
        for cc in (c - 1, c, c + 1):
            if 0 <= cc <= 7:
                lb |= 1 << (rr * 8 + cc)

    SUPPORT_MASK_W[idx] = sw
    SUPPORT_MASK_B[idx] = sb
    ATTACK_MASK_W[idx] = aw
    ATTACK_MASK_B[idx] = ab
    LANE_MASK_W[idx] = lw
    LANE_MASK_B[idx] = lb


def _bits(bb: int):
    while bb:
        lsb = bb & -bb
        yield lsb.bit_length() - 1
        bb ^= lsb


def _to_bitboard(pieces):
    bb = 0
    for r, c in pieces:
        bb |= 1 << (r * 8 + c)
    return bb


def _idx_to_coord(idx: int):
    return (idx >> 3, idx & 7)


def _terminal_score(me: int, opp: int, color: str, ply: int):
    if me == 0:
        return -MATE + ply
    if opp == 0:
        return MATE - ply

    if color == "w":
        if me & ROW_MASKS[7]:
            return MATE - ply
        if opp & ROW_MASKS[0]:
            return -MATE + ply
    else:
        if me & ROW_MASKS[0]:
            return MATE - ply
        if opp & ROW_MASKS[7]:
            return -MATE + ply

    return None


def _count_piece_wins(idx: int, me: int, opp: int, color: str) -> int:
    r = ROW_OF[idx]
    c = COL_OF[idx]
    occ = me | opp
    cnt = 0

    if color == "w":
        if r != 6:
            return 0
        to = idx + 8
        if (occ & (1 << to)) == 0:
            cnt += 1
        if c > 0:
            to = idx + 7
            if (me & (1 << to)) == 0:
                cnt += 1
        if c < 7:
            to = idx + 9
            if (me & (1 << to)) == 0:
                cnt += 1
    else:
        if r != 1:
            return 0
        to = idx - 8
        if (occ & (1 << to)) == 0:
            cnt += 1
        if c > 0:
            to = idx - 9
            if (me & (1 << to)) == 0:
                cnt += 1
        if c < 7:
            to = idx - 7
            if (me & (1 << to)) == 0:
                cnt += 1

    return cnt


def _has_immediate_win(me: int, opp: int, color: str) -> bool:
    occ = me | opp

    if color == "w":
        bb = me & ROW_MASKS[6]
        while bb:
            lsb = bb & -bb
            idx = lsb.bit_length() - 1
            bb ^= lsb
            c = COL_OF[idx]
            if (occ & (1 << (idx + 8))) == 0:
                return True
            if c > 0 and (me & (1 << (idx + 7))) == 0:
                return True
            if c < 7 and (me & (1 << (idx + 9))) == 0:
                return True
    else:
        bb = me & ROW_MASKS[1]
        while bb:
            lsb = bb & -bb
            idx = lsb.bit_length() - 1
            bb ^= lsb
            c = COL_OF[idx]
            if (occ & (1 << (idx - 8))) == 0:
                return True
            if c > 0 and (me & (1 << (idx - 9))) == 0:
                return True
            if c < 7 and (me & (1 << (idx - 7))) == 0:
                return True

    return False


def _move_is_immediate_win(frm: int, to: int, me: int, opp: int, color: str) -> bool:
    new_opp = opp & ~(1 << to)
    if new_opp == 0:
        return True
    return ROW_OF[to] == (7 if color == "w" else 0)


def _evaluate(me: int, opp: int, color: str) -> int:
    term = _terminal_score(me, opp, color, 0)
    if term is not None:
        return term

    opp_color = OTHER[color]

    adv_me = ADV_W if color == "w" else ADV_B
    adv_opp = ADV_W if opp_color == "w" else ADV_B

    support_me = SUPPORT_MASK_W if color == "w" else SUPPORT_MASK_B
    support_opp = SUPPORT_MASK_W if opp_color == "w" else SUPPORT_MASK_B

    attack_me = ATTACK_MASK_W if color == "w" else ATTACK_MASK_B
    attack_opp = ATTACK_MASK_W if opp_color == "w" else ATTACK_MASK_B

    lane_me = LANE_MASK_W if color == "w" else LANE_MASK_B
    lane_opp = LANE_MASK_W if opp_color == "w" else LANE_MASK_B

    score = 180 * (me.bit_count() - opp.bit_count())

    my_adv = 0
    opp_adv = 0
    my_best = -1
    opp_best = -1
    my_support = 0
    opp_support = 0
    my_attacked = 0
    opp_attacked = 0
    my_passed = 0
    opp_passed = 0
    my_center = 0
    opp_center = 0
    my_threats = 0
    opp_threats = 0

    bb = me
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb

        adv = adv_me[idx]
        my_adv += adv
        if adv > my_best:
            my_best = adv

        my_center += CENTER_BONUS_IDX[idx]
        my_support += (support_me[idx] & me).bit_count()
        my_attacked += (attack_me[idx] & opp).bit_count()

        if (lane_me[idx] & opp) == 0:
            my_passed += 1 + adv + (adv * adv) // 2

        if (color == "w" and ROW_OF[idx] == 6) or (color == "b" and ROW_OF[idx] == 1):
            my_threats += _count_piece_wins(idx, me, opp, color)

    bb = opp
    while bb:
        lsb = bb & -bb
        idx = lsb.bit_length() - 1
        bb ^= lsb

        adv = adv_opp[idx]
        opp_adv += adv
        if adv > opp_best:
            opp_best = adv

        opp_center += CENTER_BONUS_IDX[idx]
        opp_support += (support_opp[idx] & opp).bit_count()
        opp_attacked += (attack_opp[idx] & me).bit_count()

        if (lane_opp[idx] & me) == 0:
            opp_passed += 1 + adv + (adv * adv) // 2

        if (opp_color == "w" and ROW_OF[idx] == 6) or (opp_color == "b" and ROW_OF[idx] == 1):
            opp_threats += _count_piece_wins(idx, opp, me, opp_color)

    score += 14 * (my_adv - opp_adv)
    score += 50 * (my_best - opp_best)
    score += 10 * (my_center - opp_center)
    score += 10 * (my_support - opp_support)
    score += 18 * (opp_attacked - my_attacked)
    score += 22 * (my_passed - opp_passed)
    score += 170 * (my_threats - opp_threats)

    return score


def _generate_moves(
    me: int,
    opp: int,
    color: str,
    tt_move=None,
    killer1=None,
    killer2=None,
    history=None,
):
    occ = me | opp
    moves = []
    goal_row = 7 if color == "w" else 0
    adv = ADV_W if color == "w" else ADV_B
    hist = history if history is not None else {}

    if color == "w":
        bb = me
        while bb:
            lsb = bb & -bb
            frm = lsb.bit_length() - 1
            bb ^= lsb
            r = ROW_OF[frm]
            c = COL_OF[frm]
            if r == 7:
                continue

            # Forward
            to = frm + 8
            if (occ & (1 << to)) == 0:
                score = 300 * adv[to] + 20 * CENTER_BONUS_IDX[to]
                if ROW_OF[to] == goal_row:
                    score += 500_000
                move = (frm, to)
                if move == tt_move:
                    score += 1_000_000
                elif move == killer1:
                    score += 60_000
                elif move == killer2:
                    score += 50_000
                score += hist.get(("w", frm, to), 0)
                moves.append((score, frm, to))

            # Diagonal left
            if c > 0:
                to = frm + 7
                if (me & (1 << to)) == 0:
                    capture = (opp & (1 << to)) != 0
                    score = 300 * adv[to] + 20 * CENTER_BONUS_IDX[to]
                    if ROW_OF[to] == goal_row:
                        score += 500_000
                    if capture:
                        score += 70_000 + 100 * ADV_B[to]
                    move = (frm, to)
                    if move == tt_move:
                        score += 1_000_000
                    elif move == killer1:
                        score += 60_000
                    elif move == killer2:
                        score += 50_000
                    score += hist.get(("w", frm, to), 0)
                    moves.append((score, frm, to))

            # Diagonal right
            if c < 7:
                to = frm + 9
                if (me & (1 << to)) == 0:
                    capture = (opp & (1 << to)) != 0
                    score = 300 * adv[to] + 20 * CENTER_BONUS_IDX[to]
                    if ROW_OF[to] == goal_row:
                        score += 500_000
                    if capture:
                        score += 70_000 + 100 * ADV_B[to]
                    move = (frm, to)
                    if move == tt_move:
                        score += 1_000_000
                    elif move == killer1:
                        score += 60_000
                    elif move == killer2:
                        score += 50_000
                    score += hist.get(("w", frm, to), 0)
                    moves.append((score, frm, to))
    else:
        bb = me
        while bb:
            lsb = bb & -bb
            frm = lsb.bit_length() - 1
            bb ^= lsb
            r = ROW_OF[frm]
            c = COL_OF[frm]
            if r == 0:
                continue

            # Forward
            to = frm - 8
            if (occ & (1 << to)) == 0:
                score = 300 * adv[to] + 20 * CENTER_BONUS_IDX[to]
                if ROW_OF[to] == goal_row:
                    score += 500_000
                move = (frm, to)
                if move == tt_move:
                    score += 1_000_000
                elif move == killer1:
                    score += 60_000
                elif move == killer2:
                    score += 50_000
                score += hist.get(("b", frm, to), 0)
                moves.append((score, frm, to))

            # Diagonal left
            if c > 0:
                to = frm - 9
                if (me & (1 << to)) == 0:
                    capture = (opp & (1 << to)) != 0
                    score = 300 * adv[to] + 20 * CENTER_BONUS_IDX[to]
                    if ROW_OF[to] == goal_row:
                        score += 500_000
                    if capture:
                        score += 70_000 + 100 * ADV_W[to]
                    move = (frm, to)
                    if move == tt_move:
                        score += 1_000_000
                    elif move == killer1:
                        score += 60_000
                    elif move == killer2:
                        score += 50_000
                    score += hist.get(("b", frm, to), 0)
                    moves.append((score, frm, to))

            # Diagonal right
            if c < 7:
                to = frm - 7
                if (me & (1 << to)) == 0:
                    capture = (opp & (1 << to)) != 0
                    score = 300 * adv[to] + 20 * CENTER_BONUS_IDX[to]
                    if ROW_OF[to] == goal_row:
                        score += 500_000
                    if capture:
                        score += 70_000 + 100 * ADV_W[to]
                    move = (frm, to)
                    if move == tt_move:
                        score += 1_000_000
                    elif move == killer1:
                        score += 60_000
                    elif move == killer2:
                        score += 50_000
                    score += hist.get(("b", frm, to), 0)
                    moves.append((score, frm, to))

    moves.sort(key=lambda x: x[0], reverse=True)
    return [(frm, to) for _, frm, to in moves]


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    me_bb = _to_bitboard(me)
    opp_bb = _to_bitboard(opp)

    # Fast legal fallback.
    initial_moves = _generate_moves(me_bb, opp_bb, color)
    if not initial_moves:
        # Should not happen in a valid non-terminal Breakthrough position.
        # Fallback only for robustness.
        if me:
            r, c = me[0]
            return ((r, c), (r, c))
        return ((0, 0), (0, 0))

    # Immediate win if available.
    for frm, to in initial_moves:
        if _move_is_immediate_win(frm, to, me_bb, opp_bb, color):
            return (_idx_to_coord(frm), _idx_to_coord(to))

    if len(initial_moves) == 1:
        frm, to = initial_moves[0]
        return (_idx_to_coord(frm), _idx_to_coord(to))

    deadline = time.perf_counter() + 0.90
    tt = {}
    history = {}
    killers = [[None, None] for _ in range(64)]
    node_counter = 0

    class Timeout(Exception):
        pass

    def search(meb: int, oppb: int, turn: str, depth: int, alpha: int, beta: int, ply: int) -> int:
        nonlocal node_counter

        node_counter += 1
        if (node_counter & 511) == 0 and time.perf_counter() >= deadline:
            raise Timeout

        term = _terminal_score(meb, oppb, turn, ply)
        if term is not None:
            return term

        oppturn = OTHER[turn]

        if depth <= 0:
            if _has_immediate_win(meb, oppb, turn) or _has_immediate_win(oppb, meb, oppturn):
                depth = 1
            else:
                return _evaluate(meb, oppb, turn)

        key = (meb, oppb, turn)
        entry = tt.get(key)
        tt_move = None

        if entry is not None:
            e_depth, e_flag, e_score, e_move = entry
            tt_move = e_move
            if e_depth >= depth:
                if e_flag == 0:
                    return e_score
                elif e_flag == 1:
                    if e_score > alpha:
                        alpha = e_score
                else:
                    if e_score < beta:
                        beta = e_score
                if alpha >= beta:
                    return e_score

        alpha_orig = alpha
        killer1, killer2 = killers[ply]
        moves = _generate_moves(meb, oppb, turn, tt_move, killer1, killer2, history)

        if not moves:
            return -MATE + ply

        best_score = -INF
        best_move = moves[0]

        for frm, to in moves:
            captured = (oppb & (1 << to)) != 0
            new_me = (meb ^ (1 << frm)) | (1 << to)
            new_opp = oppb & ~(1 << to)

            score = -search(new_opp, new_me, oppturn, depth - 1, -beta, -alpha, ply + 1)

            if score > best_score:
                best_score = score
                best_move = (frm, to)

            if score > alpha:
                alpha = score

            if alpha >= beta:
                if not captured:
                    if killers[ply][0] != (frm, to):
                        killers[ply][1] = killers[ply][0]
                        killers[ply][0] = (frm, to)
                    hkey = (turn, frm, to)
                    history[hkey] = history.get(hkey, 0) + depth * depth
                break

        if best_score <= alpha_orig:
            flag = 2  # upper bound
        elif best_score >= beta:
            flag = 1  # lower bound
        else:
            flag = 0  # exact

        tt[key] = (depth, flag, best_score, best_move)
        return best_score

    def root_search(depth: int, hint_move):
        if time.perf_counter() >= deadline:
            raise Timeout

        tt_move = hint_move
        root_entry = tt.get((me_bb, opp_bb, color))
        if tt_move is None and root_entry is not None:
            tt_move = root_entry[3]

        killer1, killer2 = killers[0]
        moves = _generate_moves(me_bb, opp_bb, color, tt_move, killer1, killer2, history)

        best_score = -INF
        best_move = moves[0]
        alpha = -MATE
        beta = MATE
        oppturn = OTHER[color]

        for frm, to in moves:
            if time.perf_counter() >= deadline:
                raise Timeout

            new_me = (me_bb ^ (1 << frm)) | (1 << to)
            new_opp = opp_bb & ~(1 << to)

            score = -search(new_opp, new_me, oppturn, depth - 1, -beta, -alpha, 1)

            if score > best_score:
                best_score = score
                best_move = (frm, to)

            if score > alpha:
                alpha = score

        tt[(me_bb, opp_bb, color)] = (depth, 0, best_score, best_move)
        return best_score, best_move

    best_move = initial_moves[0]
    hint_move = best_move
    depth = 1

    while True:
        if time.perf_counter() >= deadline:
            break
        try:
            score, move = root_search(depth, hint_move)
            best_move = move
            hint_move = move
            depth += 1
            if abs(score) >= MATE - 1000:
                break
        except Timeout:
            break

    return (_idx_to_coord(best_move[0]), _idx_to_coord(best_move[1]))
