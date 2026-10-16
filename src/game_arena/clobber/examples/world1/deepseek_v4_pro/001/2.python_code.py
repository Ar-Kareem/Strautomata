
import time

def policy(you, opponent):
    # Convert board to bitboards: 30 bits, index = row * 6 + col
    my = 0
    opp = 0
    for r in range(5):
        for c in range(6):
            if you[r][c]:
                my |= 1 << (r * 6 + c)
            if opponent[r][c]:
                opp |= 1 << (r * 6 + c)

    # Precompute neighbor masks for all 30 cells
    NEIGHBOR_MASK = [0] * 30
    for r in range(5):
        for c in range(6):
            idx = r * 6 + c
            mask = 0
            if r > 0: mask |= 1 << ((r - 1) * 6 + c)
            if r < 4: mask |= 1 << ((r + 1) * 6 + c)
            if c > 0: mask |= 1 << (r * 6 + (c - 1))
            if c < 5: mask |= 1 << (r * 6 + (c + 1))
            NEIGHBOR_MASK[idx] = mask

    # Fast count of legal moves for p1 given p2
    def count_moves(p1, p2):
        c = 0
        bits = p1
        while bits:
            b = bits & -bits
            idx = (b.bit_length() - 1)
            c += (NEIGHBOR_MASK[idx] & p2).bit_count()
            bits ^= b
        return c

    # Generate all legal moves as list of (src, dst) indices
    def get_moves(p1, p2):
        moves = []
        bits = p1
        while bits:
            b = bits & -bits
            src = (b.bit_length() - 1)
            targets = NEIGHBOR_MASK[src] & p2
            while targets:
                t = targets & -targets
                dst = (t.bit_length() - 1)
                moves.append((src, dst))
                targets ^= t
            bits ^= b
        return moves

    # Apply a move: p1 piece moves from src to dst, capturing p2 piece at dst
    def apply_move(p1, p2, src, dst):
        new_p1 = (p1 ^ (1 << src)) | (1 << dst)
        new_p2 = p2 ^ (1 << dst)
        return new_p1, new_p2

    # Heuristic evaluation from perspective of p1
    def eval_state(p1, p2):
        return count_moves(p1, p2) - count_moves(p2, p1)

    # Time management
    start_time = time.time()
    TIME_LIMIT = 0.95
    end_time = start_time + TIME_LIMIT
    abort = False

    # Negamax with alpha-beta pruning
    def negamax(p1, p2, depth, alpha, beta):
        nonlocal abort
        if abort:
            return 0
        if time.time() > end_time:
            abort = True
            return 0

        # Check for terminal state (no moves for current player)
        if count_moves(p1, p2) == 0:
            return -100000 + depth  # prefer to delay loss

        if depth == 0:
            return eval_state(p1, p2)

        # Generate and order moves by heuristic evaluation of resulting state
        moves = get_moves(p1, p2)
        scored_moves = []
        for src, dst in moves:
            new_p1, new_p2 = apply_move(p1, p2, src, dst)
            score = eval_state(new_p1, new_p2)
            scored_moves.append((score, src, dst))
        scored_moves.sort(reverse=True, key=lambda x: x[0])

        value = -100000
        for _, src, dst in scored_moves:
            new_p1, new_p2 = apply_move(p1, p2, src, dst)
            val = -negamax(new_p2, new_p1, depth - 1, -beta, -alpha)
            if val > value:
                value = val
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value

    # Iterative deepening
    best_move = None
    depth = 1
    while True:
        if time.time() > end_time:
            break
        abort = False

        moves = get_moves(my, opp)
        if not moves:
            # No legal moves (should not be called in this state)
            return "0,0,U"

        # Order root moves
        scored_moves = []
        for src, dst in moves:
            new_my, new_opp = apply_move(my, opp, src, dst)
            score = eval_state(new_my, new_opp)
            scored_moves.append((score, src, dst))
        scored_moves.sort(reverse=True, key=lambda x: x[0])

        best_score = -100000
        current_best = scored_moves[0][1:]  # default move
        for _, src, dst in scored_moves:
            new_my, new_opp = apply_move(my, opp, src, dst)
            val = -negamax(new_opp, new_my, depth - 1, -100000, -best_score)
            if abort:
                break
            if val > best_score:
                best_score = val
                current_best = (src, dst)

        if not abort:
            best_move = current_best
            depth += 1
        else:
            break

    # Fallback: if no move found, return the first legal move
    if best_move is None:
        moves = get_moves(my, opp)
        if moves:
            best_move = moves[0]
        else:
            return "0,0,U"

    src, dst = best_move
    src_r, src_c = divmod(src, 6)
    dst_r, dst_c = divmod(dst, 6)
    if dst_r == src_r - 1:
        dir = 'U'
    elif dst_r == src_r + 1:
        dir = 'D'
    elif dst_c == src_c - 1:
        dir = 'L'
    else:
        dir = 'R'
    return f"{src_r},{src_c},{dir}"
