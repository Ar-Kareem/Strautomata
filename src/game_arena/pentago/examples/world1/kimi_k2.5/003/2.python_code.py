
def policy(you, opponent):
    # ------------------------------------------------------------------ #
    # Static pre‑computations (executed once)
    # ------------------------------------------------------------------ #
    if not hasattr(policy, "LINE_MASKS"):
        masks = []
        # horizontal
        for r in range(6):
            base = r * 6
            for c in range(2):
                m = sum(1 << (base + c + i) for i in range(5))
                masks.append(m)
        # vertical
        for c in range(6):
            for r in range(2):
                m = sum(1 << ((r + i) * 6 + c) for i in range(5))
                masks.append(m)
        # diagonal \
        for r in range(2):
            for c in range(2):
                m = sum(1 << ((r + i) * 6 + (c + i)) for i in range(5))
                masks.append(m)
        # diagonal /
        for r in range(2):
            for c in range(4, 6):
                m = sum(1 << ((r + i) * 6 + (c - i)) for i in range(5))
                masks.append(m)
        policy.LINE_MASKS = masks

        # quadrant bit positions (0‑35 flat index)
        q0 = [0, 1, 2, 6, 7, 8, 12, 13, 14]
        q1 = [3, 4, 5, 9, 10, 11, 15, 16, 17]
        q2 = [18, 19, 20, 24, 25, 26, 30, 31, 32]
        q3 = [21, 22, 23, 27, 28, 29, 33, 34, 35]
        policy.QUAD_INDICES = [q0, q1, q2, q3]
        policy.QUAD_MASKS = [sum(1 << i for i in q) for q in [q0, q1, q2, q3]]

        # rotation permutations (old_local_index -> None:
        """Return new mask after rotating the given quadrant."""
        perm = PL if direction == 'L' else PR
        idx = QI[quad]
        # clear the quadrant
        new_mask = mask & ~QM[quad]
        # move the nine bits
        for k in range(9):
            bit = 1 << idx[k]
            if mask & bit:
                new_mask |= 1 << idx[perm[k]]
        return new_mask

    def has_win(mask):
        for m in LM:
            if (mask & m) == m:
                return True
        return False

    def evaluate(my_mask, op_mask):
        """Heuristic score: open lines + center control."""
        score = 0
        for m in LM:
            mc = (my_mask & m).bit_count()
            oc = (op_mask & m).bit_count()
            if mc and not oc:
                score += 1 << mc      # 2,4,8,16,…
            elif oc and not mc:
                score -= 1 << oc
        # centre squares are valuable
        score += 3 * ((my_mask & CENTER).bit_count() - (op_mask & CENTER).bit_count())
        return score

    # ------------------------------------------------------------------ #
    # Parse input masks
    # ------------------------------------------------------------------ #
    mine = 0
    other = 0
    for r in range(6):
        y_row = you[r]
        o_row = opponent[r]
        for c in range(6):
            pos = r * 6 + c
            if y_row[c]:
                mine |= 1 << pos
            if o_row[c]:
                other |= 1 << pos

    empty = FULL ^ (mine | other)

    best_score = -10 ** 9
    best_move = None  # (idx, quad, dir)

    # ------------------------------------------------------------------ #
    # Main search (depth‑1 + immediate opponent reply check)
    # ------------------------------------------------------------------ #
    e = empty
    while e:
        lsb = e & -e
        idx = lsb.bit_length() - 1
        e ^= lsb

        placed = mine | (1 << idx)

        for q in range(4):
            for d in ('L', 'R'):
                my_new = rotate(placed, q, d)
                op_new = rotate(other, q, d)

                # Immediate win?
                if has_win(my_new):
                    r = idx // 6 + 1
                    c = idx % 6 + 1
                    return f"{r},{c},{q},{d}"

                # If opponent already has 5, this is a disaster
                if has_win(op_new):
                    sc = -2000
                else:
                    # Can opponent win in one move?
                    empty2 = FULL ^ (my_new | op_new)
                    opp_can = False
                    e2 = empty2
                    while e2:
                        lsb2 = e2 & -e2
                        idx2 = lsb2.bit_length() - 1
                        e2 ^= lsb2
                        op_place = op_new | (1 << idx2)
                        # try all rotations for opponent
                        for q2 in range(4):
                            for d2 in ('L', 'R'):
                                op_rot = rotate(op_place, q2, d2)
                                if has_win(op_rot):
                                    opp_can = True
                                    break
                            if opp_can:
                                break
                        if opp_can:
                            break
                    sc = -1000 if opp_can else evaluate(my_new, op_new)

                if sc > best_score:
                    best_score = sc
                    best_move = (idx, q, d)

    # ------------------------------------------------------------------ #
    # Fallback (should only occur in lost or filled positions)
    # ------------------------------------------------------------------ #
    if best_move is None:
        # any empty cell
        for i in range(36):
            if (empty >> i) & 1:
                best_move = (i, 0, 'L')
                break

    idx, q, d = best_move
    r = idx // 6 + 1
    c = idx % 6 + 1
    return f"{r},{c},{q},{d}"
