
# Pentago policy implementation

# The arena calls:
#     policy(you, opponent) -> "row,col,quad,dir"
#
# Board convention:
# - you and opponent are 6x6 array-like objects of 0/1 values.
# - We are always the player to move.

BOARD_N = 6
ALL_MASK = (1 << 36) - 1
BITS = [1 << i for i in range(36)]
DIR_CHARS = ("L", "R")
ROTATIONS = [(q, d) for q in range(4) for d in range(2)]

WIN_SCORE = 10_000_000
INF = 10**18


def _idx(r, c):
    return r * 6 + c


def _make_win_masks():
    masks = []
    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for r in range(6):
        for c in range(6):
            for dr, dc in dirs:
                rr = r + 4 * dr
                cc = c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    m = 0
                    for k in range(5):
                        m |= BITS[_idx(r + k * dr, c + k * dc)]
                    masks.append(m)
    # Remove accidental duplicates, preserving order.
    seen = set()
    out = []
    for m in masks:
        if m not in seen:
            seen.add(m)
            out.append(m)
    return out


WIN_MASKS = _make_win_masks()


def _make_rotation_data():
    quad_origins = {
        0: (0, 0),
        1: (0, 3),
        2: (3, 0),
        3: (3, 3),
    }

    quad_masks = []
    rot_pairs = {}

    for q in range(4):
        r0, c0 = quad_origins[q]
        qm = 0
        positions = []
        for lr in range(3):
            for lc in range(3):
                old = _idx(r0 + lr, c0 + lc)
                positions.append(old)
                qm |= BITS[old]
        quad_masks.append(qm)

        for d in range(2):
            pairs = []
            for lr in range(3):
                for lc in range(3):
                    old = _idx(r0 + lr, c0 + lc)
                    if d == 0:  # L / anticlockwise
                        nlr, nlc = 2 - lc, lr
                    else:       # R / clockwise
                        nlr, nlc = lc, 2 - lr
                    new = _idx(r0 + nlr, c0 + nlc)
                    pairs.append((old, new))
            rot_pairs[(q, d)] = pairs

    return quad_masks, rot_pairs


QUAD_MASKS, ROT_PAIRS = _make_rotation_data()


# Mild positional preference. The centers of the four 3x3 quadrants are stable
# under rotations and are strategically valuable.
POS_WEIGHTS = [
    3, 4, 3, 3, 4, 3,
    4, 8, 4, 4, 8, 4,
    3, 4, 3, 3, 4, 3,
    3, 4, 3, 3, 4, 3,
    4, 8, 4, 4, 8, 4,
    3, 4, 3, 3, 4, 3,
]

LINE_WEIGHTS = (0, 2, 15, 120, 1800, 0)


def _bits_from_arrays(you, opponent):
    y = 0
    o = 0
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            b = BITS[_idx(r, c)]
            if int(yr[c]):
                y |= b
            elif int(orow[c]):
                o |= b
    return y, o


def _has_win(bits):
    for m in WIN_MASKS:
        if (bits & m) == m:
            return True
    return False


def _rotate_bits(bits, q, d):
    outside = bits & ~QUAD_MASKS[q]
    inside = 0
    for old, new in ROT_PAIRS[(q, d)]:
        if bits & BITS[old]:
            inside |= BITS[new]
    return outside | inside


def _apply_move(y, o, cell, q, d, player):
    if player == 1:
        y |= BITS[cell]
    else:
        o |= BITS[cell]

    y = _rotate_bits(y, q, d)
    o = _rotate_bits(o, q, d)
    return y, o


def _empty_cells(y, o):
    occ = y | o
    return [i for i in range(36) if not (occ & BITS[i])]


def _move_string(cell, q, d):
    r = cell // 6 + 1
    c = cell % 6 + 1
    return f"{r},{c},{q},{DIR_CHARS[d]}"


def _heuristic(y, o):
    yw = _has_win(y)
    ow = _has_win(o)
    if yw and not ow:
        return WIN_SCORE
    if ow and not yw:
        return -WIN_SCORE
    if yw and ow:
        return 0

    score = 0

    # Line-pattern scoring.
    for m in WIN_MASKS:
        yc = (y & m).bit_count()
        oc = (o & m).bit_count()
        if yc and oc:
            continue
        if yc:
            score += LINE_WEIGHTS[yc]
        elif oc:
            score -= int(1.18 * LINE_WEIGHTS[oc])

    # Positional scoring.
    yy = y
    while yy:
        lb = yy & -yy
        i = lb.bit_length() - 1
        score += POS_WEIGHTS[i]
        yy -= lb

    oo = o
    while oo:
        lb = oo & -oo
        i = lb.bit_length() - 1
        score -= POS_WEIGHTS[i]
        oo -= lb

    return score


def _opponent_analysis(y, o):
    """
    From a position after our move, determine whether the opponent has an
    immediate winning reply. If not, return the worst heuristic position they
    can choose for us.
    """
    cells = _empty_cells(y, o)
    if not cells:
        return False, 0

    worst = INF
    seen = set()

    for cell in cells:
        for q, d in ROTATIONS:
            y2, o2 = _apply_move(y, o, cell, q, d, -1)
            key = (y2, o2)
            if key in seen:
                continue
            seen.add(key)

            yw = _has_win(y2)
            ow = _has_win(o2)

            # Opponent can win immediately and alone: this move is unsafe.
            if ow and not yw:
                return True, -WIN_SCORE

            if ow and yw:
                val = 0          # simultaneous five-in-a-row is a draw
            elif yw and not ow:
                val = WIN_SCORE  # opponent blunder
            elif not _empty_cells(y2, o2):
                val = 0
            else:
                val = _heuristic(y2, o2)

            if val < worst:
                worst = val

    if worst == INF:
        worst = 0
    return False, worst


def _count_our_winning_moves(y, o, cap=3):
    """
    Count, up to cap, how many distinct immediate winning continuations we have
    from this position. Used as a threat bonus.
    """
    count = 0
    seen = set()

    for cell in _empty_cells(y, o):
        for q, d in ROTATIONS:
            y2, o2 = _apply_move(y, o, cell, q, d, 1)
            key = (y2, o2)
            if key in seen:
                continue
            seen.add(key)

            if _has_win(y2) and not _has_win(o2):
                count += 1
                if count >= cap:
                    return count

    return count


def _simple_fallback(you, opponent):
    """Guaranteed legal fallback under the problem assumption that an empty cell exists."""
    for r in range(6):
        for c in range(6):
            try:
                if int(you[r][c]) == 0 and int(opponent[r][c]) == 0:
                    return f"{r + 1},{c + 1},0,L"
            except Exception:
                pass
    # Should never be reached if the arena respects the API.
    return "1,1,0,L"


def policy(you, opponent) -> str:
    try:
        y, o = _bits_from_arrays(you, opponent)
        cells = _empty_cells(y, o)

        if not cells:
            return _simple_fallback(you, opponent)

        draw_move = None
        candidates = []
        seen_root = set()

        # Generate all legal moves.
        for cell in cells:
            for q, d in ROTATIONS:
                y2, o2 = _apply_move(y, o, cell, q, d, 1)
                key = (y2, o2)
                if key in seen_root:
                    continue
                seen_root.add(key)

                move = _move_string(cell, q, d)

                yw = _has_win(y2)
                ow = _has_win(o2)

                # Winning alone is always best.
                if yw and not ow:
                    return move

                # Simultaneous win is a draw.
                if yw and ow:
                    if draw_move is None:
                        draw_move = move
                    continue

                # Do not voluntarily rotate the opponent into a win.
                if ow and not yw:
                    continue

                # Board full and no winner: draw.
                if not _empty_cells(y2, o2):
                    if draw_move is None:
                        draw_move = move
                    continue

                base = _heuristic(y2, o2)
                candidates.append((base, move, y2, o2))

        if not candidates:
            if draw_move is not None:
                return draw_move
            return _simple_fallback(you, opponent)

        # Examine promising candidates first.
        candidates.sort(key=lambda x: x[0], reverse=True)

        safe_choices = []
        checked = 0

        for base, move, y2, o2 in candidates:
            unsafe, worst = _opponent_analysis(y2, o2)
            checked += 1

            if not unsafe:
                threats = _count_our_winning_moves(y2, o2, cap=3)
                final_score = worst + int(0.10 * base) + threats * 50000
                safe_choices.append((final_score, base, move))

            # Usually enough for time, but if no safe move has been found,
            # continue searching all candidates.
            if checked >= 50 and len(safe_choices) >= 6:
                break

        if safe_choices:
            safe_choices.sort(reverse=True)
            return safe_choices[0][2]

        # If every searched non-terminal move allows an immediate opponent win,
        # take an immediate draw if available.
        if draw_move is not None:
            return draw_move

        # Otherwise play the best static candidate.
        return candidates[0][1]

    except Exception:
        return _simple_fallback(you, opponent)
