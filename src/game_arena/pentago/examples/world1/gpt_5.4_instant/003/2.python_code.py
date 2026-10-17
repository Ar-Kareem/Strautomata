
import time
from math import inf

# Pentago policy: place a marble, then rotate one quadrant.
# Returns move string "row,col,quad,dir"

SIZE = 6
QUADS = {
    0: (0, 0),
    1: (0, 3),
    2: (3, 0),
    3: (3, 3),
}

# Precompute all 5- and 6-cell lines relevant for win/eval
LINES5 = []
# horizontals len 5 and 6 windows
for r in range(6):
    for c in range(2):
        LINES5.append([(r, c + i) for i in range(5)])
# verticals
for c in range(6):
    for r in range(2):
        LINES5.append([(r + i, c) for i in range(5)])
# diagonals down-right
for r in range(2):
    for c in range(2):
        LINES5.append([(r + i, c + i) for i in range(5)])
# diagonals down-left
for r in range(2):
    for c in range(4, 6):
        LINES5.append([(r + i, c - i) for i in range(5)])

# Full 6-cell lines for broader evaluation
LINES6 = []
for r in range(6):
    LINES6.append([(r, c) for c in range(6)])
for c in range(6):
    LINES6.append([(r, c) for r in range(6)])
LINES6.append([(i, i) for i in range(6)])
LINES6.append([(i, 5 - i) for i in range(6)])


def _to_masks(you, opp):
    my_mask = 0
    opp_mask = 0
    bit = 1
    for r in range(6):
        yr = you[r]
        orow = opp[r]
        for c in range(6):
            if yr[c]:
                my_mask |= bit
            elif orow[c]:
                opp_mask |= bit
            bit <<= 1
    return my_mask, opp_mask


def _bit(r, c):
    return 1 << (r * 6 + c)


def _cell_empty(my_mask, opp_mask, r, c):
    b = _bit(r, c)
    return ((my_mask | opp_mask) & b) == 0


def _rotate_submask(mask, quad, direction):
    r0, c0 = QUADS[quad]
    # extract 3x3
    vals = [[0] * 3 for _ in range(3)]
    for i in range(3):
        for j in range(3):
            if mask & _bit(r0 + i, c0 + j):
                vals[i][j] = 1
    # clear old quadrant
    for i in range(3):
        for j in range(3):
            mask &= ~_bit(r0 + i, c0 + j)
    # rotate and write back
    for i in range(3):
        for j in range(3):
            if direction == 'R':
                ni, nj = j, 2 - i
            else:
                ni, nj = 2 - j, i
            if vals[i][j]:
                mask |= _bit(r0 + ni, c0 + nj)
    return mask


def _apply_move(my_mask, opp_mask, r, c, quad, direction):
    my_mask |= _bit(r, c)
    my_mask = _rotate_submask(my_mask, quad, direction)
    opp_mask = _rotate_submask(opp_mask, quad, direction)
    return my_mask, opp_mask


def _has_five(mask):
    for line in LINES5:
        ok = True
        for r, c in line:
            if not (mask & _bit(r, c)):
                ok = False
                break
        if ok:
            return True
    return False


def _terminal_value(my_mask, opp_mask):
    my_win = _has_five(my_mask)
    opp_win = _has_five(opp_mask)
    if my_win and opp_win:
        return 0
    if my_win:
        return 10**9
    if opp_win:
        return -10**9
    if (my_mask | opp_mask).bit_count() == 36:
        return 0
    return None


def _line_score(my_count, opp_count, length):
    if my_count and opp_count:
        return 0
    if my_count == 0 and opp_count == 0:
        return 0

    # Strongly prefer uncontested longer lines
    table5 = {1: 2, 2: 12, 3: 80, 4: 1200, 5: 200000}
    table6 = {1: 2, 2: 10, 3: 60, 4: 600, 5: 5000, 6: 300000}
    table = table5 if length == 5 else table6

    if opp_count == 0:
        return table.get(my_count, 0)
    else:
        return -table.get(opp_count, 0)


CENTER_WEIGHTS = [
    [0, 1, 2, 2, 1, 0],
    [1, 3, 4, 4, 3, 1],
    [2, 4, 5, 5, 4, 2],
    [2, 4, 5, 5, 4, 2],
    [1, 3, 4, 4, 3, 1],
    [0, 1, 2, 2, 1, 0],
]


def _evaluate(my_mask, opp_mask):
    tv = _terminal_value(my_mask, opp_mask)
    if tv is not None:
        return tv

    score = 0

    # Positional centrality
    for r in range(6):
        for c in range(6):
            b = _bit(r, c)
            if my_mask & b:
                score += CENTER_WEIGHTS[r][c]
            elif opp_mask & b:
                score -= CENTER_WEIGHTS[r][c]

    # 5-cell lines
    for line in LINES5:
        my_count = 0
        opp_count = 0
        for r, c in line:
            b = _bit(r, c)
            if my_mask & b:
                my_count += 1
            elif opp_mask & b:
                opp_count += 1
        score += _line_score(my_count, opp_count, 5)

    # 6-cell lines
    for line in LINES6:
        my_count = 0
        opp_count = 0
        for r, c in line:
            b = _bit(r, c)
            if my_mask & b:
                my_count += 1
            elif opp_mask & b:
                opp_count += 1
        score += _line_score(my_count, opp_count, 6)

    return score


def _generate_moves(my_mask, opp_mask):
    occ = my_mask | opp_mask
    moves = []
    for r in range(6):
        for c in range(6):
            b = _bit(r, c)
            if occ & b:
                continue
            for q in range(4):
                moves.append((r, c, q, 'L'))
                moves.append((r, c, q, 'R'))
    return moves


def _ordered_moves(my_mask, opp_mask):
    moves = _generate_moves(my_mask, opp_mask)
    scored = []
    for mv in moves:
        nm, no = _apply_move(my_mask, opp_mask, *mv)
        tv = _terminal_value(nm, no)
        if tv is not None and tv >= 10**9:
            s = 10**12
        else:
            s = _evaluate(nm, no)
        scored.append((s, mv))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [mv for _, mv in scored]


def _format_move(mv):
    r, c, q, d = mv
    return f"{r+1},{c+1},{q},{d}"


def policy(you, opponent) -> str:
    my_mask, opp_mask = _to_masks(you, opponent)
    start = time.time()
    time_limit = 0.92

    legal_moves = _ordered_moves(my_mask, opp_mask)
    if not legal_moves:
        # Should not happen per prompt, but keep a legal-looking fallback
        return "1,1,0,L"

    # 1) Immediate winning move
    for mv in legal_moves:
        nm, no = _apply_move(my_mask, opp_mask, *mv)
        tv = _terminal_value(nm, no)
        if tv is not None and tv >= 10**9:
            return _format_move(mv)

    # 2) Score moves by opponent immediate reply danger + heuristic
    best_move = legal_moves[0]
    best_value = -inf

    # Search breadth adapts to game stage
    empties = 36 - (my_mask | opp_mask).bit_count()
    top_k = 18 if empties > 18 else 24 if empties > 10 else 32
    cand_moves = legal_moves[:top_k]

    for mv in cand_moves:
        if time.time() - start > time_limit:
            break

        nm, no = _apply_move(my_mask, opp_mask, *mv)
        tv = _terminal_value(nm, no)
        if tv is not None:
            val = tv
            if val > best_value:
                best_value = val
                best_move = mv
            continue

        # Opponent to move: they become "my" in swapped perspective
        opp_moves = _ordered_moves(no, nm)

        # Limit replies for speed
        reply_k = 12 if empties > 18 else 18 if empties > 10 else 28
        worst = inf
        saw_reply = False

        for omv in opp_moves[:reply_k]:
            if time.time() - start > time_limit:
                break
            rmy, ropp = _apply_move(no, nm, *omv)  # opponent places, then rotate
            # convert back to our perspective after opponent move
            my2, opp2 = ropp, rmy
            val2 = _evaluate(my2, opp2)
            if val2 < worst:
                worst = val2
            saw_reply = True
            # immediate pruning if opponent can force a win now
            if val2 <= -10**9:
                worst = val2
                break

        if not saw_reply:
            worst = _evaluate(nm, no)

        # Small optimism for current tactical strength
        val = worst + 0.05 * _evaluate(nm, no)

        if val > best_value:
            best_value = val
            best_move = mv

    # 3) Safety fallback: if chosen move allows immediate opp win and another doesn't, prefer safe
    chosen_nm, chosen_no = _apply_move(my_mask, opp_mask, *best_move)
    chosen_bad = False
    for omv in _ordered_moves(chosen_no, chosen_nm)[:16]:
        rmy, ropp = _apply_move(chosen_no, chosen_nm, *omv)
        my2, opp2 = ropp, rmy
        tv = _terminal_value(my2, opp2)
        if tv is not None and tv <= -10**9:
            chosen_bad = True
            break

    if chosen_bad:
        for mv in legal_moves:
            nm, no = _apply_move(my_mask, opp_mask, *mv)
            safe = True
            for omv in _ordered_moves(no, nm)[:16]:
                rmy, ropp = _apply_move(no, nm, *omv)
                my2, opp2 = ropp, rmy
                tv = _terminal_value(my2, opp2)
                if tv is not None and tv <= -10**9:
                    safe = False
                    break
            if safe:
                return _format_move(mv)

    # 4) Guaranteed legal move output
    return _format_move(best_move)
