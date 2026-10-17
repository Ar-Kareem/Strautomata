
from __future__ import annotations

import time

ROWS = 6
COLS = 7
CENTER_COL = 3
BASE_ORDER = (3, 2, 4, 1, 5, 0, 6)

WIN_SCORE = 1_000_000
INF = 10**18


class SearchTimeout(Exception):
    pass


def _build_line_masks():
    masks = []

    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            mask = 0
            for i in range(4):
                mask |= 1 << ((c + i) * 7 + r)
            masks.append(mask)

    # Vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            mask = 0
            for i in range(4):
                mask |= 1 << (c * 7 + (r + i))
            masks.append(mask)

    # Diagonal up-right
    for c in range(COLS - 3):
        for r in range(ROWS - 3):
            mask = 0
            for i in range(4):
                mask |= 1 << ((c + i) * 7 + (r + i))
            masks.append(mask)

    # Diagonal down-right
    for c in range(COLS - 3):
        for r in range(3, ROWS):
            mask = 0
            for i in range(4):
                mask |= 1 << ((c + i) * 7 + (r - i))
            masks.append(mask)

    return tuple(masks)


LINE_MASKS = _build_line_masks()
BIT_TO_POS = {1 << (c * 7 + r): (c, r) for c in range(COLS) for r in range(ROWS)}
CENTER_MASK = sum(1 << (CENTER_COL * 7 + r) for r in range(ROWS))

BIT_WEIGHT = {bit: 0 for bit in BIT_TO_POS}
for mask in LINE_MASKS:
    m = mask
    while m:
        lsb = m & -m
        BIT_WEIGHT[lsb] += 1
        m ^= lsb

LANDING_PRIORITY = [
    [BIT_WEIGHT[1 << (c * 7 + r)] * 10 - abs(CENTER_COL - c) for r in range(ROWS)]
    for c in range(COLS)
]


def has_won(bits):
    m = bits & (bits >> 1)
    if m & (m >> 2):
        return True
    m = bits & (bits >> 7)
    if m & (m >> 14):
        return True
    m = bits & (bits >> 6)
    if m & (m >> 12):
        return True
    m = bits & (bits >> 8)
    return bool(m & (m >> 16))


def board_to_state(board):
    bits = [0, 0]  # bits[0] = current player, bits[1] = opponent
    heights = [0] * COLS

    for c in range(COLS):
        h = 0
        for r in range(ROWS - 1, -1, -1):  # bottom to top in board coordinates
            v = board[r][c]
            if v == 0:
                break
            rr = ROWS - 1 - r  # internal row: 0 is bottom
            bit = 1 << (c * 7 + rr)
            if v == 1:
                bits[0] |= bit
            else:
                bits[1] |= bit
            h += 1
        heights[c] = h

    return bits, heights


def fallback_move(board):
    for c in BASE_ORDER:
        if board[0][c] == 0:
            return c
    return 0


def bit_weight_score(bb):
    s = 0
    while bb:
        lsb = bb & -bb
        s += BIT_WEIGHT[lsb]
        bb ^= lsb
    return s


def evaluate_position(cur, opp, heights):
    occ = cur | opp
    score = 0

    # Positional value: center + cells that belong to many possible 4-lines.
    score += 3 * ((cur & CENTER_MASK).bit_count() - (opp & CENTER_MASK).bit_count())
    score += 2 * (bit_weight_score(cur) - bit_weight_score(opp))

    # Pattern-based evaluation.
    for mask in LINE_MASKS:
        c = (cur & mask).bit_count()
        if c:
            if opp & mask:
                continue
            if c == 4:
                return WIN_SCORE // 2
            if c == 1:
                score += 1
            elif c == 2:
                score += 12
            elif c == 3:
                score += 70
                empty = mask & ~occ
                pos = BIT_TO_POS.get(empty)
                if pos is not None and heights[pos[0]] == pos[1]:
                    score += 380
        else:
            o = (opp & mask).bit_count()
            if not o:
                continue
            if o == 4:
                return -(WIN_SCORE // 2)
            if o == 1:
                score -= 1
            elif o == 2:
                score -= 14
            elif o == 3:
                score -= 90
                empty = mask & ~occ
                pos = BIT_TO_POS.get(empty)
                if pos is not None and heights[pos[0]] == pos[1]:
                    score -= 430

    return score


def winning_cols(player_bits, heights):
    wins = []
    for c in BASE_ORDER:
        r = heights[c]
        if r < ROWS and has_won(player_bits | (1 << (c * 7 + r))):
            wins.append(c)
    return wins


def any_winning_move(player_bits, heights):
    for c in BASE_ORDER:
        r = heights[c]
        if r < ROWS and has_won(player_bits | (1 << (c * 7 + r))):
            return True
    return False


def ordered_moves(bits, heights, turn, best_move_table):
    moves = [c for c in BASE_ORDER if heights[c] < ROWS]
    if len(moves) <= 1:
        return moves

    moves.sort(key=lambda c: LANDING_PRIORITY[c][heights[c]], reverse=True)

    pref = best_move_table.get((bits[0], bits[1], turn))
    if pref in moves:
        moves.remove(pref)
        moves.insert(0, pref)

    return moves


def policy(board: list[list[int]]) -> int:
    fallback = fallback_move(board)

    try:
        bits, heights = board_to_state(board)
        legal = [c for c in BASE_ORDER if heights[c] < ROWS]

        if not legal:
            return fallback
        if len(legal) == 1:
            return legal[0]
        if sum(heights) == 0:
            return CENTER_COL

        # Exact urgent tactics at root.
        my_wins = winning_cols(bits[0], heights)
        if my_wins:
            return my_wins[0]

        opp_wins = winning_cols(bits[1], heights)
        if opp_wins:
            # One threat => forced block. Multiple threats => lost anyway, but still legal.
            return opp_wins[0]

        deadline = time.perf_counter() + 0.92
        tt = {}
        best_move_table = {}
        node_counter = 0

        has_won_fn = has_won
        eval_fn = evaluate_position
        order_fn = ordered_moves
        any_win_fn = any_winning_move

        def play(turn, col):
            row = heights[col]
            bit = 1 << (col * 7 + row)
            bits[turn] |= bit
            heights[col] = row + 1
            return bit

        def undo(turn, col, bit):
            heights[col] -= 1
            bits[turn] ^= bit

        def negamax(depth, alpha, beta, turn, ply):
            nonlocal node_counter

            key = (bits[0], bits[1], turn, depth)
            if key in tt:
                return tt[key]

            node_counter += 1
            if (node_counter & 511) == 0 and time.perf_counter() >= deadline:
                raise SearchTimeout

            moves = order_fn(bits, heights, turn, best_move_table)
            if not moves:
                tt[key] = 0
                return 0

            cur = bits[turn]
            opp = bits[1 - turn]

            # Immediate win for side to move.
            for c in moves:
                r = heights[c]
                if has_won_fn(cur | (1 << (c * 7 + r))):
                    val = WIN_SCORE - ply
                    tt[key] = val
                    best_move_table[(bits[0], bits[1], turn)] = c
                    return val

            # Opponent's immediate threats:
            # - 2+ winning moves means current side is lost.
            # - 1 winning move means that block is forced.
            opp_wins_local = []
            for c in moves:
                r = heights[c]
                if has_won_fn(opp | (1 << (c * 7 + r))):
                    opp_wins_local.append(c)
                    if len(opp_wins_local) >= 2:
                        val = -(WIN_SCORE - ply - 1)
                        tt[key] = val
                        return val

            forced_move = opp_wins_local[0] if opp_wins_local else None

            # Quiescent leaf: only stop if there is no tactical urgency.
            if depth == 0 and forced_move is None:
                val = eval_fn(cur, opp, heights)
                tt[key] = val
                return val

            if forced_move is not None:
                moves = [forced_move]
            elif len(moves) > 1:
                # Safe-move pruning:
                # if any move avoids giving the opponent an immediate win, ignore unsafe moves.
                safe = []
                for c in moves:
                    bit = play(turn, c)
                    opp_has = any_win_fn(bits[1 - turn], heights)
                    undo(turn, c, bit)
                    if not opp_has:
                        safe.append(c)
                if safe:
                    moves = safe

            best = -INF
            best_col = moves[0]
            searched_all = True
            next_depth = depth - 1 if depth > 0 else 0

            for c in moves:
                bit = play(turn, c)
                if has_won_fn(bits[turn]):
                    score = WIN_SCORE - ply
                else:
                    score = -negamax(next_depth, -beta, -alpha, 1 - turn, ply + 1)
                undo(turn, c, bit)

                if score > best:
                    best = score
                    best_col = c
                if score > alpha:
                    alpha = score
                if alpha >= beta:
                    searched_all = False
                    break

            best_move_table[(bits[0], bits[1], turn)] = best_col
            if searched_all or len(moves) == 1:
                tt[key] = best
            return best

        def search_root(depth, preferred):
            if time.perf_counter() >= deadline:
                raise SearchTimeout

            moves = order_fn(bits, heights, 0, best_move_table)
            if preferred in moves:
                moves.remove(preferred)
                moves.insert(0, preferred)

            if len(moves) > 1:
                safe = []
                for c in moves:
                    bit = play(0, c)
                    if has_won_fn(bits[0]):
                        undo(0, c, bit)
                        return c, WIN_SCORE
                    opp_has = any_win_fn(bits[1], heights)
                    undo(0, c, bit)
                    if not opp_has:
                        safe.append(c)
                if safe:
                    moves = safe
                    if preferred in moves:
                        moves.remove(preferred)
                        moves.insert(0, preferred)

            best_col = moves[0]
            best = -INF
            alpha = -INF
            beta = INF
            next_depth = depth - 1 if depth > 0 else 0

            for c in moves:
                if time.perf_counter() >= deadline:
                    raise SearchTimeout

                bit = play(0, c)
                if has_won_fn(bits[0]):
                    score = WIN_SCORE
                else:
                    score = -negamax(next_depth, -beta, -alpha, 1, 1)
                undo(0, c, bit)

                if score > best:
                    best = score
                    best_col = c
                if score > alpha:
                    alpha = score

            best_move_table[(bits[0], bits[1], 0)] = best_col
            return best_col, best

        best = legal[0]
        empties = ROWS * COLS - sum(heights)
        depth = 1

        while depth <= empties:
            try:
                candidate, score = search_root(depth, best)
                best = candidate
                if score >= WIN_SCORE - 2:
                    break
                depth += 1
            except SearchTimeout:
                break

        if heights[best] < ROWS:
            return best

        for c in BASE_ORDER:
            if heights[c] < ROWS:
                return c

        return fallback

    except Exception:
        return fallback
