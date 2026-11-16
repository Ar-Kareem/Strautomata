
import time

ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN = 1000000
CENTER_BONUS = 4
SCORE = [0, 1, 10, 100, 100000]

BOTTOM = [1 << (c * 7) for c in range(7)]
TOP_PLAYABLE = [1 << (c * 7 + 5) for c in range(7)]

BOARD_MASK = 0
for _c in range(7):
    BOARD_MASK |= 63 << (_c * 7)

CENTER_MASK = 0
for _r in range(6):
    CENTER_MASK |= 1 << (3 * 7 + _r)

WINDOWS = []
for _r in range(6):
    for _c in range(7):
        if _c <= 3:
            m = 0
            for _i in range(4):
                m |= 1 << ((_c + _i) * 7 + _r)
            WINDOWS.append(m)
        if _r <= 2:
            m = 0
            for _i in range(4):
                m |= 1 << (_c * 7 + _r + _i)
            WINDOWS.append(m)
        if _c <= 3 and _r <= 2:
            m = 0
            for _i in range(4):
                m |= 1 << ((_c + _i) * 7 + _r + _i)
            WINDOWS.append(m)
        if _c <= 3 and _r >= 3:
            m = 0
            for _i in range(4):
                m |= 1 << ((_c + _i) * 7 + _r - _i)
            WINDOWS.append(m)

try:
    _HAS_BITCOUNT = hasattr(int, "bit_count")
except Exception:
    _HAS_BITCOUNT = False

def _pop(x):
    if _HAS_BITCOUNT:
        return x.bit_count()
    return bin(x).count("1")

def has_won(bb):
    m = bb & (bb >> 7)
    if m & (m >> 14):
        return True
    m = bb & (bb >> 6)
    if m & (m >> 12):
        return True
    m = bb & (bb >> 8)
    if m & (m >> 16):
        return True
    m = bb & (bb >> 1)
    if m & (m >> 2):
        return True
    return False

class _Timeout(Exception):
    pass

def policy(board: list[list[int]]) -> int:
    try:
        myBB = 0
        oppBB = 0
        heights = [0] * 7
        for c in range(7):
            h = 0
            for r in range(6):
                v = board[r][c]
                if v != 0:
                    h += 1
                    bit_row = 5 - r
                    if bit_row < 0:
                        bit_row = 0
                    if bit_row > 5:
                        bit_row = 5
                    bit = 1 << (c * 7 + bit_row)
                    if v == 1:
                        myBB |= bit
                    elif v == -1:
                        oppBB |= bit
            heights[c] = h
        # fix heights to be number of stones (stacked assumption)
        # recompute correctly by counting (already), but ensure contiguity:
        # heights as counted equals discs; bit positions above assume no gaps.
        # For safety recompute heights as counts:
        # (already done)
        mask = myBB | oppBB
        legal = [c for c in range(7) if heights[c] < 6]
        if not legal:
            return 0
        if len(legal) == 1:
            return legal[0]
        ordered_legal_center = [c for c in ORDER if heights[c] < 6]

        # immediate win
        for c in legal:
            mv = 1 << (c * 7 + heights[c])
            if has_won(myBB | mv):
                return c
        # immediate block (must block)
        opp_threats = []
        for c in legal:
            mv = 1 << (c * 7 + heights[c])
            if has_won(oppBB | mv):
                opp_threats.append(c)
        if len(opp_threats) == 1:
            return opp_threats[0]
        if len(opp_threats) > 1:
            # lost, block one
            return opp_threats[0]

        deadline = time.perf_counter() + 0.88
        nodes = [0]
        TT = {}

        windows_local = WINDOWS
        score_local = SCORE
        center_mask_local = CENTER_MASK

        def evaluate(pos, opp):
            s = 0
            for w in windows_local:
                pw = pos & w
                if pw:
                    if opp & w:
                        continue
                    s += score_local[_pop(pw)]
                else:
                    ow = opp & w
                    if ow:
                        s -= score_local[_pop(ow)]
            s += (_pop(pos & center_mask_local) - _pop(opp & center_mask_local)) * CENTER_BONUS
            return s

        # negamax with alpha beta
        def negamax(pos, msk, depth, alpha, beta, ply):
            nodes[0] += 1
            if (nodes[0] & 1023) == 0:
                if time.perf_counter() > deadline:
                    raise _Timeout()
            opp = msk ^ pos
            # opponent already won? (should not happen)
            if has_won(opp):
                return -(WIN - ply)
            if msk == BOARD_MASK:
                return 0
            # generate legal cols in center order
            # check TT
            key = (pos, msk)
            tt_entry = TT.get(key)
            tt_move = -1
            if tt_entry is not None:
                t_depth, t_val, t_flag, t_move = tt_entry
                tt_move = t_move
                if t_depth >= depth:
                    if t_flag == 0:
                        return t_val
                    elif t_flag == 1:
                        if t_val > alpha:
                            alpha = t_val
                    elif t_flag == 2:
                        if t_val < beta:
                            beta = t_val
                    if alpha >= beta:
                        return t_val
            # immediate winning move for side to move?
            # collect legal moves and winning check
            # also collect opp threats for pruning
            # first find all legal
            leg = []
            for c in ORDER:
                if heights[c] < 6:
                    # heights is mutated along path, but at this node it reflects msk
                    leg.append(c)
            # quick win check
            for c in leg:
                mv = 1 << (c * 7 + heights[c])
                if has_won(pos | mv):
                    return WIN - ply
            # opponent threats (opponent = opp)
            threat_count = 0
            threat_col = -1
            for c in leg:
                mv = 1 << (c * 7 + heights[c])
                if has_won(opp | mv):
                    threat_count += 1
                    threat_col = c
                    if threat_count >= 2:
                        break
            if threat_count >= 2:
                return -(WIN - ply - 1)
            if threat_count == 1:
                # forced block
                c = threat_col
                mv = 1 << (c * 7 + heights[c])
                heights[c] += 1
                new_mask = msk | mv
                # child pos is opp
                v = -negamax(opp, new_mask, depth - 1 if depth > 0 else 0, -beta, -alpha, ply + 1)
                heights[c] -= 1
                # store TT
                TT[key] = (depth, v, 0, c)
                return v
            if depth <= 0:
                return evaluate(pos, opp)

            # order moves: tt_move first then center order
            if tt_move in leg:
                leg.remove(tt_move)
                leg = [tt_move] + leg

            best_val = -WIN - 1
            best_c = leg[0]
            orig_alpha = alpha
            for c in leg:
                mv = 1 << (c * 7 + heights[c])
                heights[c] += 1
                new_mask = msk | mv
                # pos|mv win already checked above, so no win here
                v = -negamax(opp, new_mask, depth - 1, -beta, -alpha, ply + 1)
                heights[c] -= 1
                if v > best_val:
                    best_val = v
                    best_c = c
                if v > alpha:
                    alpha = v
                if alpha >= beta:
                    break
            # store TT
            if best_val <= orig_alpha:
                flag = 2
            elif best_val >= beta:
                flag = 1
            else:
                flag = 0
            TT[key] = (depth, best_val, flag, best_c)
            return best_val

        pos_root = myBB
        mask_root = mask
        best = ordered_legal_center[0]
        prev_scores = {c: 0 for c in legal}
        # small bonus for center in ordering
        # iterative deepening
        empties = 42 - sum(heights)
        max_depth = 7
        if empties < 12:
            max_depth = 10
        if empties < 6:
            max_depth = 12
        # depth 1..max
        for depth in range(1, max_depth + 1):
            # order by prev scores
            ordered_root = sorted(ordered_legal_center, key=lambda c: prev_scores.get(c, 0), reverse=True)
            cur_scores = {}
            alpha = -WIN
            beta = WIN
            try:
                for c in ordered_root:
                    mv = 1 << (c * 7 + heights[c])
                    # win already excluded, but keep check
                    if has_won(pos_root | mv):
                        best = c
                        cur_scores[c] = WIN
                        continue
                    heights[c] += 1
                    new_mask = mask_root | mv
                    child_pos = mask_root ^ pos_root
                    v = -negamax(child_pos, new_mask, depth - 1, -beta, -alpha, 1)
                    heights[c] -= 1
                    cur_scores[c] = v
                    if v > alpha:
                        alpha = v
                        best = c
                prev_scores = cur_scores
                # if winning line found, stop
                if prev_scores.get(best, 0) >= WIN - 50:
                    break
                # if time nearly up, stop
                if time.perf_counter() > deadline - 0.05:
                    break
            except _Timeout:
                break
        if best not in legal:
            return ordered_legal_center[0]
        return int(best)
    except Exception:
        try:
            for c in [3, 2, 4, 1, 5, 0, 6]:
                if board[0][c] == 0:
                    return c
            for c in range(7):
                if board[0][c] == 0:
                    return c
        except Exception:
            pass
        return 3
