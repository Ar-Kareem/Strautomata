
import time
import random

WIN_MASKS = [
    0x000F, 0x00F0, 0x0F00, 0xF000,
    0x1111, 0x2222, 0x4444, 0x8888,
    0x8421, 0x1248,
]
WIN_SCORE = 100000
FULL = 0xFFFF

# center first, then corners, then edges
BASE_ORDER = [5, 6, 9, 10, 0, 3, 12, 15, 1, 2, 4, 7, 8, 11, 13, 14]

try:
    _bc = int.bit_count
    def _pop(x: int) -> int:
        return x.bit_count()
except Exception:
    def _pop(x: int) -> int:
        return bin(x).count("1")

def _is_win(b: int) -> bool:
    for m in WIN_MASKS:
        if (b & m) == m:
            return True
    return False

def _static(cur: int, opp: int) -> int:
    s = 0
    for m in WIN_MASKS:
        c = _pop(cur & m)
        o = _pop(opp & m)
        if c and o:
            continue
        if c:
            if c == 1:
                s += 1
            elif c == 2:
                s += 12
            elif c == 3:
                s += 150
            else:
                s += WIN_SCORE
        elif o:
            if o == 1:
                s -= 1
            elif o == 2:
                s -= 12
            elif o == 3:
                s -= 150
            else:
                s -= WIN_SCORE
    return s

class _Timeout(Exception):
    pass

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        return _policy_inner(board)
    except Exception:
        try:
            for r in range(4):
                for c in range(4):
                    if board[r][c] == 0:
                        return (r, c)
        except Exception:
            pass
        return (0, 0)

def _policy_inner(board):
    start = time.time()
    limit = 0.88

    my = 0
    op = 0
    empties = []
    for r in range(4):
        row = board[r]
        for c in range(4):
            v = row[c]
            bit = 1 << (r * 4 + c)
            if v == 1:
                my |= bit
            elif v == -1:
                op |= bit
            else:
                empties.append(r * 4 + c)

    if not empties:
        return (0, 0)
    if len(empties) == 1:
        p = empties[0]
        return (p // 4, p % 4)
    if len(empties) == 16:
        # random central to avoid determinism
        p = random.choice([5, 6, 9, 10])
        return (p // 4, p % 4)

    # immediate win
    for p in empties:
        b = 1 << p
        if _is_win(my | b):
            return (p // 4, p % 4)

    # immediate block(s)
    blocks = []
    for p in empties:
        b = 1 << p
        if _is_win(op | b):
            blocks.append(p)
    if len(blocks) == 1:
        # must block unless we already won (handled above)
        # still verify with search if blocking loses anyway? blocking is forced
        # quick check: if only one threat, block it
        return (blocks[0] // 4, blocks[0] % 4)
    # if >=2 threats, we are likely lost, fall through to search to delay

    # order empties by base order preference
    order_idx = {p: i for i, p in enumerate(BASE_ORDER)}
    empties_sorted = sorted(empties, key=lambda p: order_idx.get(p, 99))

    # heuristic fallback: best static after move
    def heuristic_pick():
        best_s = -10**9
        best_p = empties_sorted[0]
        # prefer block moves slightly in tie
        block_set = set(blocks)
        for p in empties_sorted:
            b = 1 << p
            # score from our perspective after we move
            # evaluate as -static(opp, my|b)
            s = -_static(op, my | b)
            if p in block_set:
                s += 5
            # tiny center bonus + randomness to break ties
            s += random.random() * 0.5
            if s > best_s:
                best_s = s
                best_p = p
        return (best_p // 4, best_p % 4)

    # if very little time needed, use search
    TT = {}
    nodes = 0

    # closure for speed
    win_masks_local = WIN_MASKS
    pop_local = _pop
    static_local = _static
    is_win_local = _is_win

    def negamax(cur: int, opp: int, depth: int, alpha: int, beta: int, ply: int):
        nonlocal nodes
        nodes += 1
        if (nodes & 2047) == 0:
            if time.time() - start > limit:
                raise _Timeout()
        # opponent just moved -> if opp won, we lost
        # check win fast
        for m in win_masks_local:
            if (opp & m) == m:
                return -WIN_SCORE + ply
        if depth == 0:
            occ = cur | opp
            if occ == FULL:
                return 0
            return static_local(cur, opp)
        occ = cur | opp
        if occ == FULL:
            return 0

        alpha_orig = alpha
        # TT probe
        key = (cur, opp)
        tt_best = -1
        if key in TT:
            sd, ss, sf, sm = TT[key]
            if sd >= depth:
                if sf == 0:
                    return ss
                elif sf == 1:
                    if ss >= beta:
                        return ss
                    if ss > alpha:
                        alpha = ss
                else:
                    if ss <= alpha:
                        return ss
                    if ss < beta:
                        beta = ss
                tt_best = sm
            else:
                tt_best = sm

        # generate moves
        # empty bits
        empty_mask = (~occ) & FULL
        # build list in preferred order
        # use base order + tt_best first
        moves = []
        if tt_best != -1 and (empty_mask >> tt_best) & 1:
            moves.append(tt_best)
        for p in BASE_ORDER:
            if p == tt_best:
                continue
            if (empty_mask >> p) & 1:
                moves.append(p)

        best = -10**9
        best_m = moves[0] if moves else -1
        for p in moves:
            bit = 1 << p
            # cur makes move, then swap
            n_cur = opp
            n_opp = cur | bit
            # immediate win for cur? then opponent loses next ply,
            # but our generic opp-win check at child will catch it.
            # quick shortcut:
            # if cur|bit is win, this move wins instantly
            w = False
            for m in win_masks_local:
                if ((cur | bit) & m) == m:
                    w = True
                    break
            if w:
                score = WIN_SCORE - (ply + 1)
            else:
                score = -negamax(n_cur, n_opp, depth - 1, -beta, -alpha, ply + 1)
            if score > best:
                best = score
                best_m = p
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break
            # early exit on proven win
            if best >= WIN_SCORE - 20:
                break

        # store TT
        if best <= alpha_orig:
            flag = 2  # upper
        elif best >= beta:
            flag = 1  # lower
        else:
            flag = 0  # exact
        TT[key] = (depth, best, flag, best_m)
        return best

    # iterative deepening at root
    max_depth = len(empties)
    # cap max depth for huge branching to avoid wasting time on depth 1..N loop overhead?
    # let it go until timeout
    best_move = empties_sorted[0]
    # move ordering for root evolves
    root_order = empties_sorted[:]
    # if double threat, root must try to block one; keep blocks front
    if len(blocks) >= 2:
        bset = set(blocks)
        root_order = sorted(root_order, key=lambda p: 0 if p in bset else 1)

    try:
        for depth in range(1, max_depth + 1):
            alpha = -10**9
            beta = 10**9
            cur_best = root_order[0]
            cur_best_score = -10**9
            # collect scores for randomization among equals
            scores = {}
            for p in root_order:
                bit = 1 << p
                w = False
                for m in win_masks_local:
                    if ((my | bit) & m) == m:
                        w = True
                        break
                if w:
                    score = WIN_SCORE - 1
                else:
                    score = -negamax(op, my | bit, depth - 1, -beta, -alpha, 1)
                scores[p] = score
                if score > cur_best_score:
                    cur_best_score = score
                    cur_best = p
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    # still need to evaluate remaining? no, cutoff
                    # assign remaining as -inf for ordering
                    break
            # if cutoff happened, fill missing scores with low value
            best_move = cur_best
            # reorder for next depth: sort by score descending
            # for moves not searched due to cutoff, keep old order at end
            searched = [p for p in root_order if p in scores]
            unsearched = [p for p in root_order if p not in scores]
            searched.sort(key=lambda p: scores[p], reverse=True)
            root_order = searched + unsearched
            # if found forced win, stop
            if cur_best_score >= WIN_SCORE - 50:
                best_move = cur_best
                break
            # if time is running out, stop
            if time.time() - start > limit * 0.7 and depth >= 4 and len(empties) > 8:
                # allow one more depth only if fast
                elapsed = time.time() - start
                if elapsed > limit * 0.85:
                    break
            if depth >= 6 and len(empties) > 10:
                # deep enough for opening, avoid timeout risk
                if time.time() - start > 0.5:
                    break
    except _Timeout:
        pass
    except Exception:
        pass

    # choose among equally good root moves randomly to avoid predictability
    # if TT has root info, we already have best_move; add tie randomization
    # only if enough time left, do quick tie check via static
    try:
        if time.time() - start < limit:
            pass
    except Exception:
        pass

    if best_move is None:
        return heuristic_pick()
    # validate legality
    bp = best_move
    br, bc = bp // 4, bp % 4
    if board[br][bc] != 0:
        # fallback
        return heuristic_pick()
    return (br, bc)
