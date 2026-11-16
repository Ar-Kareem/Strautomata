
# Pentago policy
# Returns moves in the format: "row,col,quad,dir"

WIN_MASKS = []
ROT_MAPS = []
QUAD_MASKS = []


def _init():
    global WIN_MASKS, ROT_MAPS, QUAD_MASKS
    if WIN_MASKS:
        return

    def idx(r, c):
        return r * 6 + c

    # All contiguous 5-cell lines on a 6x6 board.
    dirs = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in dirs:
        for r in range(6):
            for c in range(6):
                rr = r + 4 * dr
                cc = c + 4 * dc
                if 0 <= rr < 6 and 0 <= cc < 6:
                    m = 0
                    for k in range(5):
                        m |= 1 << idx(r + k * dr, c + k * dc)
                    WIN_MASKS.append(m)

    # Quadrant masks and rotation maps.
    for q in range(4):
        br = 0 if q < 2 else 3
        bc = 0 if q % 2 == 0 else 3

        qm = 0
        for r in range(3):
            for c in range(3):
                qm |= 1 << idx(br + r, bc + c)
        QUAD_MASKS.append(qm)

        for d in ("L", "R"):
            mp = {}
            for r in range(3):
                for c in range(3):
                    old = idx(br + r, bc + c)
                    if d == "R":
                        nr, nc = c, 2 - r
                    else:
                        nr, nc = 2 - c, r
                    new = idx(br + nr, bc + nc)
                    mp[old] = new
            ROT_MAPS.append(mp)


def _to_bits(arr):
    b = 0
    for r in range(6):
        row = arr[r]
        for c in range(6):
            if row[c]:
                b |= 1 << (r * 6 + c)
    return b


def _has_win(bits):
    for m in WIN_MASKS:
        if bits & m == m:
            return True
    return False


def _rotate_bits(bits, q, d):
    ri = q * 2 + (0 if d == "L" else 1)
    mp = ROT_MAPS[ri]
    qm = QUAD_MASKS[q]

    out = bits & ~qm
    part = bits & qm

    while part:
        lsb = part & -part
        old = lsb.bit_length() - 1
        out |= 1 << mp[old]
        part -= lsb

    return out


def _apply_move(my_bits, opp_bits, pos, q, d):
    my_bits |= 1 << pos
    my_bits = _rotate_bits(my_bits, q, d)
    opp_bits = _rotate_bits(opp_bits, q, d)
    return my_bits, opp_bits


def _legal_positions(my_bits, opp_bits):
    occ = my_bits | opp_bits
    return [i for i in range(36) if not ((occ >> i) & 1)]


def _move_string(pos, q, d):
    r = pos // 6 + 1
    c = pos % 6 + 1
    return f"{r},{c},{q},{d}"


def _all_moves(my_bits, opp_bits):
    for pos in _legal_positions(my_bits, opp_bits):
        for q in range(4):
            yield pos, q, "L"
            yield pos, q, "R"


def _terminal_score(my_bits, opp_bits):
    mw = _has_win(my_bits)
    ow = _has_win(opp_bits)
    if mw and ow:
        return 0
    if mw:
        return 10000000
    if ow:
        return -10000000
    return None


def _heuristic(my_bits, opp_bits):
    ts = _terminal_score(my_bits, opp_bits)
    if ts is not None:
        return ts

    # Pattern values for 5-cell windows.
    vals = [0, 2, 12, 90, 1200, 100000]
    score = 0

    for m in WIN_MASKS:
        a = (my_bits & m).bit_count()
        b = (opp_bits & m).bit_count()

        if a and b:
            continue
        if a:
            score += vals[a]
        elif b:
            score -= vals[b] * 11 // 10

    # Positional preference: centers and near-centers are useful in Pentago.
    center_weights = [
        2, 3, 3, 3, 3, 2,
        3, 5, 5, 5, 5, 3,
        3, 5, 6, 6, 5, 3,
        3, 5, 6, 6, 5, 3,
        3, 5, 5, 5, 5, 3,
        2, 3, 3, 3, 3, 2,
    ]

    mb = my_bits
    while mb:
        lsb = mb & -mb
        i = lsb.bit_length() - 1
        score += center_weights[i]
        mb -= lsb

    ob = opp_bits
    while ob:
        lsb = ob & -ob
        i = lsb.bit_length() - 1
        score -= center_weights[i]
        ob -= lsb

    return score


def _static_order_moves(my_bits, opp_bits, limit=None):
    scored = []
    for pos, q, d in _all_moves(my_bits, opp_bits):
        nb_my, nb_opp = _apply_move(my_bits, opp_bits, pos, q, d)
        s = _heuristic(nb_my, nb_opp)
        scored.append((s, pos, q, d))

    scored.sort(reverse=True, key=lambda x: x[0])
    if limit is not None and len(scored) > limit:
        scored = scored[:limit]
    return scored


def policy(you, opponent) -> str:
    _init()

    try:
        my_bits = _to_bits(you)
        opp_bits = _to_bits(opponent)

        legal_pos = _legal_positions(my_bits, opp_bits)
        if not legal_pos:
            return "1,1,0,L"

        fallback = _move_string(legal_pos[0], 0, "L")

        # 1. Immediate clean win.
        draw_wins = []
        for pos, q, d in _all_moves(my_bits, opp_bits):
            nb_my, nb_opp = _apply_move(my_bits, opp_bits, pos, q, d)
            mw = _has_win(nb_my)
            ow = _has_win(nb_opp)
            if mw and not ow:
                return _move_string(pos, q, d)
            if mw and ow:
                draw_wins.append((pos, q, d))

        # 2. Minimax one opponent reply deep.
        # Search strongest-looking candidate moves first.
        empties = len(legal_pos)
        if empties >= 24:
            my_limit = 72
            opp_limit = 96
        elif empties >= 14:
            my_limit = 120
            opp_limit = 160
        else:
            my_limit = None
            opp_limit = None

        candidates = _static_order_moves(my_bits, opp_bits, my_limit)

        best_score = -10**18
        best_move = None

        for base_score, pos, q, d in candidates:
            nb_my, nb_opp = _apply_move(my_bits, opp_bits, pos, q, d)

            ts = _terminal_score(nb_my, nb_opp)
            if ts is not None:
                worst = ts
            else:
                # Opponent is now the mover.  Evaluate from our perspective.
                worst = 10**18

                opp_candidates = _static_order_moves(nb_opp, nb_my, opp_limit)

                for _, opos, oq, od in opp_candidates:
                    after_opp, after_us = _apply_move(nb_opp, nb_my, opos, oq, od)

                    opp_win = _has_win(after_opp)
                    us_win = _has_win(after_us)

                    if opp_win and not us_win:
                        val = -10000000
                    elif opp_win and us_win:
                        val = 0
                    elif us_win and not opp_win:
                        val = 10000000
                    else:
                        val = _heuristic(after_us, after_opp)

                    if val < worst:
                        worst = val

                    # Alpha-style cutoff: this move is already worse than best.
                    if worst < best_score:
                        break

            # Small tie-breaker from static score.
            total = worst * 1000 + base_score

            if total > best_score:
                best_score = total
                best_move = (pos, q, d)

        if best_move is not None:
            return _move_string(best_move[0], best_move[1], best_move[2])

        # 3. If no safe move was found, accept a drawing win if available.
        if draw_wins:
            pos, q, d = draw_wins[0]
            return _move_string(pos, q, d)

        return fallback

    except Exception:
        # Absolute safety fallback: find the first empty-looking cell.
        try:
            for r in range(6):
                for c in range(6):
                    if not you[r][c] and not opponent[r][c]:
                        return f"{r+1},{c+1},0,L"
        except Exception:
            pass
        return "1,1,0,L"
