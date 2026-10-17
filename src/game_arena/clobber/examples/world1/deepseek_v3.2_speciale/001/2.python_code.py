
def policy(you, opponent):
    # ---------- board constants ----------
    ROWS, COLS = 5, 6
    CELLS = ROWS * COLS
    MASK_ALL = (1 << CELLS) - 1

    # masks to avoid wrapping in left/right moves
    mask_not_col0 = 0
    mask_not_col5 = 0
    for i in range(CELLS):
        if i % COLS != 0:
            mask_not_col0 |= 1 << i
        if i % COLS != 5:
            mask_not_col5 |= 1 << i

    # ---------- conversion to bitboards ----------
    us = 0
    opp = 0
    for r in range(ROWS):
        for c in range(COLS):
            idx = r * COLS + c
            if you[r][c]:
                us |= 1 << idx
            if opponent[r][c]:
                opp |= 1 << idx

    # ---------- helper functions ----------
    def apply_move(my, opp, src, dest):
        """Return new (my, opp) after moving from src to dest (capturing)."""
        new_my = my ^ (1 << src) ^ (1 << dest)
        new_opp = opp ^ (1 << dest)
        return new_my, new_opp

    def count_moves(my, opp):
        """Number of legal moves for the player with pieces `my`."""
        up   = ((my >> COLS) & opp).bit_count()
        down = (((my << COLS) & MASK_ALL) & opp).bit_count()
        left = (((my & mask_not_col0) >> 1) & opp).bit_count()
        right= (((my & mask_not_col5) << 1) & opp).bit_count()
        return up + down + left + right

    def eval_pos(my, opp):
        """Heuristic value from the perspective of the player whose pieces are `my`."""
        mob = count_moves(my, opp) - count_moves(opp, my)
        pieces = my.bit_count() - opp.bit_count()
        return mob * 100 + pieces   # mobility dominates, piece count breaks ties

    def generate_moves(my, opp):
        """Return list of (src, dest, dir) for all legal moves of `my`."""
        moves = []
        # up
        dests = (my >> COLS) & opp
        while dests:
            lsb = dests & -dests
            dest = lsb.bit_length() - 1
            src = dest + COLS
            moves.append((src, dest, 'U'))
            dests ^= lsb
        # down
        dests = ((my << COLS) & MASK_ALL) & opp
        while dests:
            lsb = dests & -dests
            dest = lsb.bit_length() - 1
            src = dest - COLS
            moves.append((src, dest, 'D'))
            dests ^= lsb
        # left
        dests = ((my & mask_not_col0) >> 1) & opp
        while dests:
            lsb = dests & -dests
            dest = lsb.bit_length() - 1
            src = dest + 1
            moves.append((src, dest, 'L'))
            dests ^= lsb
        # right
        dests = ((my & mask_not_col5) << 1) & opp
        while dests:
            lsb = dests & -dests
            dest = lsb.bit_length() - 1
            src = dest - 1
            moves.append((src, dest, 'R'))
            dests ^= lsb
        return moves

    def get_children(my, opp):
        """Return list of (heuristic, new_my, new_opp) for all children, sorted."""
        children = []
        # up
        dests = (my >> COLS) & opp
        while dests:
            lsb = dests & -dests
            dest = lsb.bit_length() - 1
            src = dest + COLS
            nmy, nop = apply_move(my, opp, src, dest)
            h = eval_pos(nmy, nop)
            children.append((h, nmy, nop))
            dests ^= lsb
        # down
        dests = ((my << COLS) & MASK_ALL) & opp
        while dests:
            lsb = dests & -dests
            dest = lsb.bit_length() - 1
            src = dest - COLS
            nmy, nop = apply_move(my, opp, src, dest)
            h = eval_pos(nmy, nop)
            children.append((h, nmy, nop))
            dests ^= lsb
        # left
        dests = ((my & mask_not_col0) >> 1) & opp
        while dests:
            lsb = dests & -dests
            dest = lsb.bit_length() - 1
            src = dest + 1
            nmy, nop = apply_move(my, opp, src, dest)
            h = eval_pos(nmy, nop)
            children.append((h, nmy, nop))
            dests ^= lsb
        # right
        dests = ((my & mask_not_col5) << 1) & opp
        while dests:
            lsb = dests & -dests
            dest = lsb.bit_length() - 1
            src = dest - 1
            nmy, nop = apply_move(my, opp, src, dest)
            h = eval_pos(nmy, nop)
            children.append((h, nmy, nop))
            dests ^= lsb
        children.sort(key=lambda x: x[0], reverse=True)
        return children

    # ---------- search ----------
    INF = 10 ** 8
    NODE_LIMIT = 200000
    class NodeLimitExceeded(Exception):
        pass

    node_count = 0

    def negamax(my, opp, depth, alpha, beta):
        """Negamax search returning score for player to move."""
        nonlocal node_count
        node_count += 1
        if node_count > NODE_LIMIT:
            raise NodeLimitExceeded

        # terminal: player cannot move -> loss
        if count_moves(my, opp) == 0:
            return -INF

        if depth == 0:
            return eval_pos(my, opp)

        children = get_children(my, opp)
        best = -INF
        for _, nmy, nop in children:
            score = -negamax(nop, nmy, depth - 1, -beta, -alpha)
            if score > best:
                best = score
            if score > alpha:
                alpha = score
            if alpha >= beta:
                break
        return best

    # ---------- root ----------
    root_moves = generate_moves(us, opp)
    # should always have at least one legal move
    if not root_moves:
        return "0,0,U"   # fallback (should never happen)

    # build root moves with heuristic for ordering
    moves_info = []
    for src, dest, dir in root_moves:
        nus, nopp = apply_move(us, opp, src, dest)
        h = eval_pos(nus, nopp)
        moves_info.append((h, nus, nopp, src, dest, dir))
    moves_info.sort(key=lambda x: x[0], reverse=True)

    # fallback best move (first after sorting)
    fb_src, fb_dest, fb_dir = moves_info[0][3], moves_info[0][4], moves_info[0][5]
    best_move = (fb_src, fb_dest, fb_dir)

    # iterative deepening
    MAX_DEPTH = 20
    for depth in range(1, MAX_DEPTH + 1):
        try:
            node_count = 0
            best_score = -INF
            best_move_at_depth = None
            alpha, beta = -INF, INF
            for h, nus, nopp, src, dest, dir in moves_info:
                score = -negamax(nopp, nus, depth - 1, -beta, -alpha)
                if score > best_score:
                    best_score = score
                    best_move_at_depth = (src, dest, dir)
                    if score > alpha:
                        alpha = score
                if alpha >= beta:
                    break
            if best_move_at_depth is not None:
                best_move = best_move_at_depth
        except NodeLimitExceeded:
            break

    # format result
    src_idx, _, dir = best_move
    row = src_idx // COLS
    col = src_idx % COLS
    return f"{row},{col},{dir}"
