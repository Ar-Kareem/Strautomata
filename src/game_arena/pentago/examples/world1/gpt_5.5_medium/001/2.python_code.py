
# Pentago policy: tactical 2-ply minimax with pattern evaluation.
# Required API:
#   def policy(you, opponent) -> str

BOARD = 6
N = 36
ALL_MASK = (1 << N) - 1
WIN_SCORE = 1_000_000_000

# ---------------------------------------------------------------------
# Precomputation
# ---------------------------------------------------------------------

def _bit(r, c):
    return 1 << (r * 6 + c)

# All contiguous 5-cell lines in the 6x6 board.
WIN_MASKS = []
for dr, dc in ((0, 1), (1, 0), (1, 1), (1, -1)):
    for r in range(6):
        for c in range(6):
            r2 = r + 4 * dr
            c2 = c + 4 * dc
            if 0 <= r2 < 6 and 0 <= c2 < 6:
                m = 0
                for k in range(5):
                    m |= _bit(r + k * dr, c + k * dc)
                WIN_MASKS.append(m)

# Rotation maps. Rotation index ri = quad * 2 + d, d=0 for L, d=1 for R.
_ROT_KEEP = []
_ROT_PAIRS = []

for q in range(4):
    br = (q // 2) * 3
    bc = (q % 2) * 3

    qmask = 0
    for i in range(3):
        for j in range(3):
            qmask |= _bit(br + i, bc + j)

    for d in range(2):
        pairs = []
        for i in range(3):
            for j in range(3):
                sr = br + i
                sc = bc + j

                if d == 0:       # L / anticlockwise
                    ni, nj = 2 - j, i
                else:            # R / clockwise
                    ni, nj = j, 2 - i

                dr_ = br + ni
                dc_ = bc + nj
                pairs.append((_bit(sr, sc), _bit(dr_, dc_)))

        _ROT_KEEP.append(ALL_MASK ^ qmask)
        _ROT_PAIRS.append(pairs)

# Small positional preference. Quadrant centers are useful because rotations
# do not move them; central-ish cells tend to participate in more threats.
_POS_W = [
    3, 4, 4, 4, 4, 3,
    4, 9, 6, 6, 9, 4,
    4, 6, 7, 7, 6, 4,
    4, 6, 7, 7, 6, 4,
    4, 9, 6, 6, 9, 4,
    3, 4, 4, 4, 4, 3,
]

# Pattern weights for an unblocked 5-cell line containing k marbles.
_LINE_W = [0, 2, 15, 120, 1800, 200000]


# ---------------------------------------------------------------------
# Core helpers
# ---------------------------------------------------------------------

def _rotate(bb, ri):
    out = bb & _ROT_KEEP[ri]
    for src, dst in _ROT_PAIRS[ri]:
        if bb & src:
            out |= dst
    return out


def _apply_move(me, other, pos, ri):
    """Place for 'me' at pos, rotate ri, return rotated (me, other)."""
    me |= (1 << pos)
    return _rotate(me, ri), _rotate(other, ri)


def _is_win(bb):
    for m in WIN_MASKS:
        if (bb & m) == m:
            return True
    return False


def _evaluate(us, them):
    """Static evaluation from root player's perspective."""
    score = 0

    for m in WIN_MASKS:
        uc = (us & m).bit_count()
        tc = (them & m).bit_count()

        if uc and tc:
            continue
        if uc:
            score += _LINE_W[uc]
        elif tc:
            # Slight defensive bias: blocking opponent threats is critical.
            score -= (_LINE_W[tc] * 6) // 5

    b = us
    while b:
        lsb = b & -b
        p = lsb.bit_length() - 1
        score += _POS_W[p]
        b ^= lsb

    b = them
    while b:
        lsb = b & -b
        p = lsb.bit_length() - 1
        score -= _POS_W[p]
        b ^= lsb

    return score


def _move_string(pos, ri):
    r = pos // 6 + 1
    c = pos % 6 + 1
    q = ri // 2
    d = "L" if (ri % 2 == 0) else "R"
    return f"{r},{c},{q},{d}"


def _parse_board(you, opponent):
    us = 0
    them = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            if int(yr[c]):
                us |= _bit(r, c)
            elif int(orow[c]):
                them |= _bit(r, c)
    return us, them


def _fallback_move(you, opponent):
    for r in range(6):
        for c in range(6):
            try:
                if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                    return f"{r+1},{c+1},0,L"
            except Exception:
                pass
    # The caller promises at least one empty cell, so this should never happen.
    return "1,1,0,L"


def _opponent_best_reply_value(us, them, alpha):
    """
    After our candidate move, opponent moves.
    Return the resulting value assuming opponent minimizes our score.
    """
    empty = ALL_MASK ^ (us | them)
    if empty == 0:
        return 0

    worst = WIN_SCORE

    e = empty
    while e:
        lsb = e & -e
        pos = lsb.bit_length() - 1
        e ^= lsb

        for ri in range(8):
            # Opponent places; _apply_move returns (opponent_after, us_after).
            them2, us2 = _apply_move(them, us, pos, ri)

            uw = _is_win(us2)
            tw = _is_win(them2)

            if tw and not uw:
                val = -WIN_SCORE
            elif uw and not tw:
                val = WIN_SCORE
            elif uw and tw:
                val = 0
            elif (us2 | them2) == ALL_MASK:
                val = 0
            else:
                val = _evaluate(us2, them2)

            if val < worst:
                worst = val
                # Alpha pruning: this candidate cannot beat the best root move.
                if worst <= alpha:
                    return worst

    return worst


# ---------------------------------------------------------------------
# Required API
# ---------------------------------------------------------------------

def policy(you, opponent) -> str:
    try:
        return _policy_core(you, opponent)
    except Exception:
        return _fallback_move(you, opponent)


def _policy_core(you, opponent) -> str:
    us, them = _parse_board(you, opponent)
    occupied = us | them
    empty = ALL_MASK ^ occupied

    # Strong deterministic opening on an empty board.
    if occupied == 0:
        return "2,2,0,L"

    candidates = []
    drawing_moves = []

    e = empty
    while e:
        lsb = e & -e
        pos = lsb.bit_length() - 1
        e ^= lsb

        for ri in range(8):
            us1, them1 = _apply_move(us, them, pos, ri)

            uw = _is_win(us1)
            tw = _is_win(them1)

            # Best case: immediate clean win.
            if uw and not tw:
                return _move_string(pos, ri)

            static = _evaluate(us1, them1)

            if uw and tw:
                # Draw after our move.
                drawing_moves.append((static, pos, ri, us1, them1, 0))
                candidates.append((static, pos, ri, us1, them1, 0))
            elif tw:
                # We rotated into an opponent win. Keep only as emergency.
                candidates.append((static, pos, ri, us1, them1, -WIN_SCORE))
            elif (us1 | them1) == ALL_MASK:
                candidates.append((static, pos, ri, us1, them1, 0))
            else:
                candidates.append((static, pos, ri, us1, them1, None))

    if not candidates:
        return _fallback_move(you, opponent)

    # Search promising-looking moves first to improve pruning.
    candidates.sort(key=lambda x: x[0], reverse=True)

    best_score = -10**30
    best_pos = candidates[0][1]
    best_ri = candidates[0][2]

    for static, pos, ri, us1, them1, terminal in candidates:
        if terminal is not None:
            score = terminal + static * 0.0001
        else:
            reply_value = _opponent_best_reply_value(us1, them1, best_score)
            # Tiny tie-breaker for better-looking positions.
            score = reply_value + static * 0.0001

        if score > best_score:
            best_score = score
            best_pos = pos
            best_ri = ri

    return _move_string(best_pos, best_ri)
