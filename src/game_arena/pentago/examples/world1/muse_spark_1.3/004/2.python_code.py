
import time

FULL_MASK = (1 << 36) - 1

# quadrant origins
_QUAD_ORIGINS = [(0,0),(0,3),(3,0),(3,3)]
QUAD_CELLS = []
QUAD_MASK = []
for (r0,c0) in _QUAD_ORIGINS:
    cells = []
    m = 0
    for lr in range(3):
        for lc in range(3):
            r = r0 + lr
            c = c0 + lc
            idx = r*6 + c
            cells.append(idx)
            m |= (1 << idx)
    # cells order k = lr*3+lc
    # need order exactly lr*3+lc, above loop already does that
    QUAD_CELLS.append(cells)
    QUAD_MASK.append(m)

# win masks : 32 windows of 5
WIN_MASKS = []
for r in range(6):
    for cs in (0,1):
        mm = 0
        for k in range(5):
            mm |= 1 << (r*6 + cs + k)
        WIN_MASKS.append(mm)
for c in range(6):
    for rs in (0,1):
        mm = 0
        for k in range(5):
            mm |= 1 << ((rs+k)*6 + c)
        WIN_MASKS.append(mm)
for rs in (0,1):
    for cs in (0,1):
        mm = 0
        for k in range(5):
            mm |= 1 << ((rs+k)*6 + cs + k)
        WIN_MASKS.append(mm)
for rs in (0,1):
    for cs in (4,5):
        mm = 0
        for k in range(5):
            mm |= 1 << ((rs+k)*6 + cs - k)
        WIN_MASKS.append(mm)

CENTER_MASK = (1<<14)|(1<<15)|(1<<20)|(1<<21)

# rotation transition tables: TRANS_R[q][p], TRANS_L[q][p]
TRANS_R = [[0]*512 for _ in range(4)]
TRANS_L = [[0]*512 for _ in range(4)]
for q in range(4):
    cells = QUAD_CELLS[q]
    for p in range(512):
        gr = 0
        gl = 0
        # iterate bits
        pp = p
        k = 0
        while pp:
            if pp & 1:
                lr = k // 3
                lc = k % 3
                nk_r = lc*3 + (2-lr)
                gr |= 1 << cells[nk_r]
                nk_l = (2-lc)*3 + lr
                gl |= 1 << cells[nk_l]
            pp >>= 1
            k += 1
        # remaining k up to 8 have no bits, nothing to add
        TRANS_R[q][p] = gr
        TRANS_L[q][p] = gl

try:
    _bc = int.bit_count
    def _pop(n):
        return n.bit_count()
except Exception:
    def _pop(n):
        return bin(n).count("1")

def _is_win(b):
    for m in WIN_MASKS:
        if (b & m) == m:
            return True
    return False

def _evaluate(my, opp):
    s = 0
    # local for speed
    for m in WIN_MASKS:
        a = my & m
        if a:
            if opp & m:
                continue
            c = _pop(a)
            if c == 1:
                s += 1
            elif c == 2:
                s += 12
            elif c == 3:
                s += 150
            elif c == 4:
                s += 2000
            else:
                s += 100000
        else:
            b = opp & m
            if b:
                c = _pop(b)
                if c == 1:
                    s -= 2
                elif c == 2:
                    s -= 15
                elif c == 3:
                    s -= 200
                elif c == 4:
                    s -= 3000
                else:
                    s -= 100000
    s += (_pop(my & CENTER_MASK) - _pop(opp & CENTER_MASK)) * 3
    return s

def _rotate_pair(my1, opp1, q, is_R):
    cells = QUAD_CELLS[q]
    qm = QUAD_MASK[q]
    p_my = 0
    p_opp = 0
    # unrolled loop of 9
    # manual for speed
    c0 = cells[0]; bit0 = 1 << c0
    if my1 & bit0: p_my |= 1
    if opp1 & bit0: p_opp |= 1
    c1 = cells[1]; bit1 = 1 << c1
    if my1 & bit1: p_my |= 2
    if opp1 & bit1: p_opp |= 2
    c2 = cells[2]; bit2 = 1 << c2
    if my1 & bit2: p_my |= 4
    if opp1 & bit2: p_opp |= 4
    c3 = cells[3]; bit3 = 1 << c3
    if my1 & bit3: p_my |= 8
    if opp1 & bit3: p_opp |= 8
    c4 = cells[4]; bit4 = 1 << c4
    if my1 & bit4: p_my |= 16
    if opp1 & bit4: p_opp |= 16
    c5 = cells[5]; bit5 = 1 << c5
    if my1 & bit5: p_my |= 32
    if opp1 & bit5: p_opp |= 32
    c6 = cells[6]; bit6 = 1 << c6
    if my1 & bit6: p_my |= 64
    if opp1 & bit6: p_opp |= 64
    c7 = cells[7]; bit7 = 1 << c7
    if my1 & bit7: p_my |= 128
    if opp1 & bit7: p_opp |= 128
    c8 = cells[8]; bit8 = 1 << c8
    if my1 & bit8: p_my |= 256
    if opp1 & bit8: p_opp |= 256
    nmask = ~qm
    if is_R:
        my2 = (my1 & nmask) | TRANS_R[q][p_my]
        opp2 = (opp1 & nmask) | TRANS_R[q][p_opp]
    else:
        my2 = (my1 & nmask) | TRANS_L[q][p_my]
        opp2 = (opp1 & nmask) | TRANS_L[q][p_opp]
    return my2, opp2


def policy(you, opponent) -> str:
    t0 = time.time()
    deadline = t0 + 0.90
    # parse
    try:
        my = 0
        opp = 0
        empties = []
        for r in range(6):
            yr = you[r]
            opr = opponent[r]
            base = r*6
            for c in range(6):
                a = int(yr[c])
                b = int(opr[c])
                idx = base + c
                if a == 1:
                    my |= (1 << idx)
                elif b == 1:
                    opp |= (1 << idx)
                else:
                    empties.append(idx)
        if not empties:
            return "1,1,0,R"
        # fallback legal
        p0 = empties[0]
        fallback = f"{p0//6+1},{p0%6+1},0,R"

        WIN_SCORE = 10000000
        # generate our moves, immediate win check
        our_moves = []  # list of [pos,q,is_R,my1,opp1,static]
        seen = set()
        # quick win loop
        for pos in empties:
            bitp = 1 << pos
            my_p = my | bitp
            # opp unchanged before rotation
            for q in range(4):
                # R
                my1, opp1 = _rotate_pair(my_p, opp, q, True)
                key = (my1, opp1)
                if key not in seen:
                    seen.add(key)
                    mw = _is_win(my1)
                    ow = _is_win(opp1)
                    if mw and not ow:
                        return f"{pos//6+1},{pos%6+1},{q},R"
                    our_moves.append([pos, q, True, my1, opp1, mw, ow, 0])
                else:
                    # still need win check? same board already checked
                    pass
                if time.time() > deadline:
                    break
                # L
                my1b, opp1b = _rotate_pair(my_p, opp, q, False)
                keyb = (my1b, opp1b)
                if keyb not in seen:
                    seen.add(keyb)
                    mw = _is_win(my1b)
                    ow = _is_win(opp1b)
                    if mw and not ow:
                        return f"{pos//6+1},{pos%6+1},{q},L"
                    our_moves.append([pos, q, False, my1b, opp1b, mw, ow, 0])
            if time.time() > deadline:
                break

        if not our_moves:
            return fallback

        # separate terminal
        nonterm = []
        draw_moves = []
        for e in our_moves:
            mw = e[5]; ow = e[6]
            if mw and ow:
                draw_moves.append(e)
            elif ow and not mw:
                # suicide immediate loss, skip unless all
                continue
            elif mw and not ow:
                # already returned
                continue
            else:
                # check full board draw (only when empties==1)
                if len(empties) == 1:
                    draw_moves.append(e)
                else:
                    nonterm.append(e)
        if not nonterm:
            if draw_moves:
                e = draw_moves[0]
                d = 'R' if e[2] else 'L'
                return f"{e[0]//6+1},{e[0]%6+1},{e[1]},{d}"
            # all suicide, return first (least bad)
            e = our_moves[0]
            d = 'R' if e[2] else 'L'
            return f"{e[0]//6+1},{e[0]%6+1},{e[1]},{d}"

        # static eval
        for e in nonterm:
            e[7] = _evaluate(e[3], e[4])
            if time.time() > deadline:
                break
        nonterm.sort(key=lambda x: x[7], reverse=True)

        # if time almost out, return static best
        if time.time() > deadline - 0.05:
            e = nonterm[0]
            d = 'R' if e[2] else 'L'
            return f"{e[0]//6+1},{e[0]%6+1},{e[1]},{d}"

        # depth-2 with alpha pruning
        # limit breadth if many empties to save time? keep all but prune
        # if huge branching, keep top 60 by static for depth2, but ensure safety:
        # first check safety for all? we do depth2 for all in order; pruning helps.
        # To bound time, if len(nonterm)>60, we will still iterate all but early break on timeout.
        best_val = -10**18
        best_e = nonterm[0]
        # values for later depth3
        vals = [0]*len(nonterm)
        # precompute empties set for fast skip
        for idx_nt, e in enumerate(nonterm):
            if time.time() > deadline - 0.08:
                break
            pos = e[0]; my1 = e[3]; opp1 = e[4]
            cur_min = 10**18
            has_legal = False
            losing = False
            # iterate opp moves
            # order opp positions: try all
            for pos2 in empties:
                if pos2 == pos:
                    continue
                bitp2 = 1 << pos2
                opp_p = opp1 | bitp2
                for q2 in range(4):
                    # R
                    my2, opp2 = _rotate_pair(my1, opp_p, q2, True)
                    mw2 = _is_win(my2)
                    ow2 = _is_win(opp2)
                    if ow2 and not mw2:
                        losing = True
                        cur_min = -WIN_SCORE
                        break
                    if mw2 and not ow2:
                        # opp suicide, skip
                        continue
                    if mw2 and ow2:
                        v = 0
                    else:
                        v = _evaluate(my2, opp2)
                    has_legal = True
                    if v < cur_min:
                        cur_min = v
                        if cur_min <= best_val:
                            break
                if losing or cur_min <= best_val:
                    break
                if time.time() > deadline - 0.08:
                    break
                for q2 in range(4):
                    my2, opp2 = _rotate_pair(my1, opp_p, q2, False)
                    mw2 = _is_win(my2)
                    ow2 = _is_win(opp2)
                    if ow2 and not mw2:
                        losing = True
                        cur_min = -WIN_SCORE
                        break
                    if mw2 and not ow2:
                        continue
                    if mw2 and ow2:
                        v = 0
                    else:
                        v = _evaluate(my2, opp2)
                    has_legal = True
                    if v < cur_min:
                        cur_min = v
                        if cur_min <= best_val:
                            break
                if losing or cur_min <= best_val:
                    break
                if time.time() > deadline - 0.08:
                    break
            if losing:
                vals[idx_nt] = -WIN_SCORE
                continue
            if not has_legal:
                # all opp moves suicide -> we win
                vals[idx_nt] = WIN_SCORE
                best_val = WIN_SCORE
                best_e = e
                break
            vals[idx_nt] = cur_min
            if cur_min > best_val:
                best_val = cur_min
                best_e = e
        # if all losing, prefer draw
        if best_val <= -WIN_SCORE + 1:
            if draw_moves:
                e = draw_moves[0]
                d = 'R' if e[2] else 'L'
                return f"{e[0]//6+1},{e[0]%6+1},{e[1]},{d}"
            e = nonterm[0]
            d = 'R' if e[2] else 'L'
            return f"{e[0]//6+1},{e[0]%6+1},{e[1]},{d}"

        # depth-3 refinement for top candidates if time left
        try:
            time_left = deadline - time.time()
            if time_left > 0.30 and len(nonterm) > 1:
                # pick top K by vals
                order = sorted(range(len(nonterm)), key=lambda i: vals[i], reverse=True)
                # filter losing
                order = [i for i in order if vals[i] > -WIN_SCORE/2][:10]
                if len(order) > 1:
                    Kopp = 10  # opp breadth
                    best3_val = -10**18
                    best3_e = best_e
                    for ii in order:
                        if time.time() > deadline - 0.05:
                            break
                        e = nonterm[ii]
                        pos = e[0]; my1 = e[3]; opp1 = e[4]
                        # collect opp replies with eval
                        opp_list = []  # (eval, pos2,q2,isR,my2,opp2)
                        lose_flag = False
                        for pos2 in empties:
                            if pos2 == pos:
                                continue
                            opp_p = opp1 | (1 << pos2)
                            for q2 in range(4):
                                for isR2 in (True, False):
                                    my2, opp2 = _rotate_pair(my1, opp_p, q2, isR2)
                                    mw2 = _is_win(my2); ow2 = _is_win(opp2)
                                    if ow2 and not mw2:
                                        lose_flag = True
                                        break
                                    if mw2 and not ow2:
                                        continue
                                    if mw2 and ow2:
                                        opp_list.append((0, pos2, q2, isR2, my2, opp2))
                                    else:
                                        opp_list.append((_evaluate(my2, opp2), pos2, q2, isR2, my2, opp2))
                                if lose_flag:
                                    break
                            if lose_flag:
                                break
                        if lose_flag:
                            continue
                        if not opp_list:
                            # opp has no safe move -> winning
                            best3_val = WIN_SCORE
                            best3_e = e
                            break
                        opp_list.sort(key=lambda x: x[0])
                        opp_list = opp_list[:Kopp]
                        # min over opp of max counter
                        cur_min3 = 10**18
                        for (_, pos2, q2, isR2, my2, opp2) in opp_list:
                            if time.time() > deadline - 0.05:
                                break
                            # compute best counter for us from board2
                            # gather empties2
                            best_counter = -10**18
                            found_win = False
                            has_c = False
                            for pos3 in empties:
                                if pos3 == pos or pos3 == pos2:
                                    continue
                                # quick timeout
                                my_p3 = my2 | (1 << pos3)
                                for q3 in range(4):
                                    for isR3 in (True, False):
                                        my3, opp3 = _rotate_pair(my_p3, opp2, q3, isR3)
                                        mw3 = _is_win(my3); ow3 = _is_win(opp3)
                                        if mw3 and not ow3:
                                            found_win = True
                                            break
                                        if ow3 and not mw3:
                                            continue
                                        if mw3 and ow3:
                                            v3 = 0
                                        else:
                                            v3 = _evaluate(my3, opp3)
                                        has_c = True
                                        if v3 > best_counter:
                                            best_counter = v3
                                    if found_win:
                                        break
                                if found_win:
                                    break
                            if found_win:
                                best_counter = WIN_SCORE
                            elif not has_c:
                                # all counters suicide -> this opp move wins for opp? treat as losing for us
                                best_counter = -WIN_SCORE
                            if best_counter < cur_min3:
                                cur_min3 = best_counter
                                if cur_min3 <= best3_val:
                                    break
                            if time.time() > deadline - 0.05:
                                break
                        if cur_min3 > best3_val:
                            best3_val = cur_min3
                            best3_e = e
                    if best3_val > -WIN_SCORE/2:
                        d = 'R' if best3_e[2] else 'L'
                        return f"{best3_e[0]//6+1},{best3_e[0]%6+1},{best3_e[1]},{d}"
        except Exception:
            pass

        d = 'R' if best_e[2] else 'L'
        return f"{best_e[0]//6+1},{best_e[0]%6+1},{best_e[1]},{d}"
    except Exception:
        try:
            for r in range(6):
                for c in range(6):
                    if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                        return f"{r+1},{c+1},0,R"
        except Exception:
            pass
        return "1,1,0,R"
