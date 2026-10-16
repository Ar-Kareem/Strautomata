
import time

WIN_MASKS = [
    0x000F,  # row 0: 0,1,2,3
    0x00F0,  # row 1: 4,5,6,7
    0x0F00,  # row 2: 8,9,10,11
    0xF000,  # row 3: 12,13,14,15
    0x1111,  # col 0: 0,4,8,12
    0x2222,  # col 1: 1,5,9,13
    0x4444,  # col 2: 2,6,10,14
    0x8888,  # col 3: 3,7,11,15
    0x8421,  # diag main: 0,5,10,15  (33825)
    0x1248,  # diag anti: 3,6,9,12 (4680)
]
# check masks values: 0x8421 = 33825, 0x1248 = 4680
FULL = 0xFFFF
WIN = 1000000
INF = 10000000

CENTER_ORDER = [5, 6, 9, 10, 1, 2, 4, 7, 8, 11, 13, 14, 0, 3, 12, 15]
ORDER_POS = {v: i for i, v in enumerate(CENTER_ORDER)}

def _is_win(bits):
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False

def _popcnt(x):
    try:
        return x.bit_count()
    except AttributeError:
        return bin(x).count("1")

def _evaluate(my_bits, opp_bits):
    s = 0
    for m in WIN_MASKS:
        has_my = my_bits & m
        has_opp = opp_bits & m
        if has_my and has_opp:
            continue
        if has_opp:
            c = _popcnt(has_opp)
            if c == 1:
                s -= 1
            elif c == 2:
                s -= 12
            elif c == 3:
                s -= 1200
            elif c >= 4:
                s -= WIN
        elif has_my:
            c = _popcnt(has_my)
            if c == 1:
                s += 1
            elif c == 2:
                s += 12
            elif c == 3:
                s += 1200
            elif c >= 4:
                s += WIN
    return s

class _Timeout(Exception):
    pass

def policy(board: list[list[int]]) -> tuple[int, int]:
    try:
        start = time.perf_counter()
        deadline = start + 0.88

        my_bits = 0
        opp_bits = 0
        empties_rc = []
        for r in range(4):
            row = board[r]
            for c in range(4):
                v = row[c]
                idx = r * 4 + c
                if v == 1:
                    my_bits |= (1 << idx)
                elif v == -1:
                    opp_bits |= (1 << idx)
                else:
                    empties_rc.append((r, c))

        if not empties_rc:
            return (0, 0)

        # single move
        if len(empties_rc) == 1:
            return empties_rc[0]

        # immediate win
        for (r, c) in empties_rc:
            bit = 1 << (r * 4 + c)
            if _is_win(my_bits | bit):
                return (r, c)

        # immediate block (collect all threats)
        threats = []
        for (r, c) in empties_rc:
            bit = 1 << (r * 4 + c)
            if _is_win(opp_bits | bit):
                threats.append((r, c))
        if len(threats) == 1:
            return threats[0]
        if len(threats) > 1:
            # double threat -> we lose, but block one (return first)
            return threats[0]

        # opening book: empty board play center
        empty_cnt = len(empties_rc)
        if empty_cnt == 16:
            return (1, 1)
        # if centre free early, prefer it via search, but quick opening:
        # order empties by center order for fallback
        empties_idx = [(r * 4 + c) for (r, c) in empties_rc]
        empties_idx.sort(key=lambda x: ORDER_POS.get(x, 99))

        # fallback best
        best_overall = (empties_idx[0] // 4, empties_idx[0] % 4)

        # if only few empties, we can solve exactly; otherwise iterative deepening
        # set up negamax closure
        nodes = 0

        def negamax(my_b, opp_b, depth, alpha, beta, ply):
            nonlocal nodes
            nodes += 1
            if (nodes & 1023) == 0 and time.perf_counter() > deadline:
                raise _Timeout()

            # terminal: previous player (opp_b is now opp from current view?
            # actually opp_b = opponent stones. If opp_b has line, current player lost
            # check opp win first
            # inline win check for speed
            for m in WIN_MASKS:
                if (opp_b & m) == m:
                    return -WIN + ply
            # current player already winning (should not happen in search, but check initial)
            for m in WIN_MASKS:
                if (my_b & m) == m:
                    return WIN - ply
            occ = my_b | opp_b
            if occ == FULL:
                return 0
            if depth == 0:
                return _evaluate(my_b, opp_b)

            # generate moves
            empty_mask = (~occ) & FULL
            # collect moves in static order, winning moves first
            # quick pass: find winning moves
            # To avoid two passes, first build list in center order
            moves = []
            win_moves = []
            # iterate center order for good ordering
            for idx in CENTER_ORDER:
                if empty_mask & (1 << idx):
                    if _is_win(my_b | (1 << idx)):
                        win_moves.append(idx)
                    else:
                        moves.append(idx)
            if win_moves:
                # immediate win available in this node -> return win score
                # fastest win, ply+1
                return WIN - (ply + 1)

            best = -INF
            for idx in moves:
                bit = 1 << idx
                new_my_child = opp_b
                new_opp_child = my_b | bit
                score = -negamax(new_my_child, new_opp_child, depth - 1, -beta, -alpha, ply + 1)
                if score > best:
                    best = score
                    if best > alpha:
                        alpha = best
                    if alpha >= beta:
                        break
            return best

        # iterative deepening at root
        # initial root order: center order
        root_order = empties_idx[:]
        # improve root order by shallow eval (cheap, only at root)
        # score each move by evaluate after move
        try:
            scored = []
            for idx in root_order:
                sc = _evaluate(my_bits | (1 << idx), opp_bits)
                scored.append((sc, idx))
            scored.sort(reverse=True, key=lambda x: x[0])
            root_order = [idx for _, idx in scored]
        except Exception:
            pass

        max_depth = empty_cnt
        # limit max depth for large branching to avoid wasting time on impossible full search
        # iterative deepening will stop by time anyway
        best_score_prev = -INF
        # depth 1 already handled (no immediate win), start at 2
        # but do full iterative to get move ordering
        for depth in range(1, max_depth + 1):
            # time check
            if time.perf_counter() > deadline:
                break
            # if remaining time small and depth large, break early for big boards
            # adapt: for empty_cnt > 10, max searchable depth ~ 5-6
            cur_best_score = -INF
            cur_best_idx = root_order[0]
            alpha = -INF
            beta = INF
            # store scores for reordering
            move_scores = []
            try:
                for idx in root_order:
                    bit = 1 << idx
                    # child perspective: opponent to move
                    s = -negamax(opp_bits, my_bits | bit, depth - 1, -beta, -alpha, 1)
                    move_scores.append((s, idx))
                    if s > cur_best_score:
                        cur_best_score = s
                        cur_best_idx = idx
                    if s > alpha:
                        alpha = s
                    # beta cutoff at root still continue to get scores? we keep full window for ordering
                    # but for speed, keep alpha update
                    if alpha >= beta:
                        # fill remaining with very low to keep ordering stable
                        # assign remaining moves -INF
                        # need to add remaining moves to move_scores
                        remaining = [i for i in root_order if all(i != x[1] for x in move_scores)]
                        for ridx in remaining:
                            move_scores.append((-INF, ridx))
                        break
                # completed this depth
                best_overall = (cur_best_idx // 4, cur_best_idx % 4)
                best_score_prev = cur_best_score
                # reorder for next depth by score descending
                move_scores.sort(reverse=True, key=lambda x: x[0])
                root_order = [idx for _, idx in move_scores]
                # if forced win found, stop
                if cur_best_score >= WIN - 20:
                    break
                # if forced loss and depth is full, break
                if depth == max_depth:
                    break
                # early exit if time low
                if time.perf_counter() > deadline:
                    break
                # heuristic: if empty large and depth >=6, stop to save time (diminishing returns)
                # continue anyway until timeout, since evaluation may improve
                if empty_cnt > 11 and depth >= 6:
                    # check time: if less than 0.2 left, break else continue one more?
                    if time.perf_counter() > deadline - 0.25:
                        break
                if empty_cnt > 8 and depth >= 7:
                    if time.perf_counter() > deadline - 0.2:
                        break
            except _Timeout:
                break
            except Exception:
                break

        return best_overall
    except Exception:
        pass
    # absolute fallback: first empty cell
    try:
        for r in range(4):
            for c in range(4):
                if board[r][c] == 0:
                    return (r, c)
    except Exception:
        pass
    return (0, 0)
