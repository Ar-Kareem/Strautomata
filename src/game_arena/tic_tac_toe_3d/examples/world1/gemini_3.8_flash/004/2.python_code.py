
import time

# Precompute all 49 winning lines in a 3x3x3 grid
LINES = []

# 1. Axis-parallel lines (27 lines)
for j in range(3):
    for k in range(3):
        LINES.append(tuple(i * 9 + j * 3 + k for i in range(3)))
for i in range(3):
    for k in range(3):
        LINES.append(tuple(i * 9 + j * 3 + k for j in range(3)))
for i in range(3):
    for j in range(3):
        LINES.append(tuple(i * 9 + j * 3 + k for k in range(3)))

# 2. Planar diagonals (18 lines)
for i in range(3):
    LINES.append(tuple(i * 9 + t * 3 + t for t in range(3)))
    LINES.append(tuple(i * 9 + t * 3 + (2 - t) for t in range(3)))
for j in range(3):
    LINES.append(tuple(t * 9 + j * 3 + t for t in range(3)))
    LINES.append(tuple(t * 9 + j * 3 + (2 - t) for t in range(3)))
for k in range(3):
    LINES.append(tuple(t * 9 + t * 3 + k for t in range(3)))
    LINES.append(tuple(t * 9 + (2 - t) * 3 + k for t in range(3)))

# 3. Space diagonals (4 lines)
LINES.append(tuple(t * 9 + t * 3 + t for t in range(3)))
LINES.append(tuple(t * 9 + t * 3 + (2 - t) for t in range(3)))
LINES.append(tuple(t * 9 + (2 - t) * 3 + t for t in range(3)))
LINES.append(tuple(t * 9 + (2 - t) * 3 + (2 - t) for t in range(3)))

# Map each cell to the indices of lines passing through it
CELL_LINES = [[] for _ in range(27)]
for line_idx, line in enumerate(LINES):
    for c in line:
        CELL_LINES[c].append(line_idx)

CELL_WEIGHTS = [len(CELL_LINES[c]) for c in range(27)]

WIN_SCORE = 1_000_000
INF = 2_000_000

EXACT = 0
LOWER = 1
UPPER = 2


def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    start_time = time.time()
    time_limit = 0.85

    # Flatten board state: 1 (us), -1 (opponent), 0 (empty)
    board_state = [0] * 27
    empty_cells = []
    p1_mask = 0
    p2_mask = 0

    for i in range(3):
        for j in range(3):
            for k in range(3):
                idx = i * 9 + j * 3 + k
                val = board[i][j][k]
                board_state[idx] = val
                if val == 0:
                    empty_cells.append(idx)
                elif val == 1:
                    p1_mask |= 1 << idx
                else:
                    p2_mask |= 1 << idx

    # If first move of the game, take the center immediately
    if len(empty_cells) == 27:
        return (1, 1, 1)

    # If center is empty and available, prioritize it
    center_idx = 13
    if board_state[center_idx] == 0 and len(empty_cells) >= 25:
        return (1, 1, 1)

    # Initialize line occupancy counters
    counts = {1: [0] * 49, -1: [0] * 49}
    for c in range(27):
        val = board_state[c]
        if val != 0:
            for L in CELL_LINES[c]:
                counts[val][L] += 1

    # Heuristic move ordering
    def move_heuristic(c, turn):
        h = CELL_WEIGHTS[c]
        my_c = counts[turn]
        opp_c = counts[-turn]
        for L in CELL_LINES[c]:
            mc = my_c[L]
            oc = opp_c[L]
            if oc == 0:
                if mc == 1:
                    h += 50
                elif mc == 0:
                    h += 10
            elif mc == 0:
                if oc == 1:
                    h += 20
        return h

    # Static position evaluation
    def evaluate(turn):
        score = 0
        my_c = counts[turn]
        opp_c = counts[-turn]
        for L in range(49):
            mc = my_c[L]
            oc = opp_c[L]
            if mc == 1 and oc == 0:
                score += 15
            elif oc == 1 and mc == 0:
                score -= 15
        return score

    # Transposition table
    TT = {}
    node_count = 0

    # Negamax search
    def search(turn, depth, ply, alpha, beta):
        nonlocal node_count, p1_mask, p2_mask
        node_count += 1
        if (node_count & 127) == 0:
            if time.time() - start_time > time_limit:
                raise TimeoutError()

        # 1. Immediate win check
        for L in range(49):
            if counts[turn][L] == 2 and counts[-turn][L] == 0:
                for c in LINES[L]:
                    if board_state[c] == 0:
                        return WIN_SCORE - ply, c

        # 2. Opponent threat detection
        threat_cells = []
        for L in range(49):
            if counts[-turn][L] == 2 and counts[turn][L] == 0:
                for c in LINES[L]:
                    if board_state[c] == 0 and c not in threat_cells:
                        threat_cells.append(c)
                        if len(threat_cells) >= 2:
                            break
                if len(threat_cells) >= 2:
                    break

        if len(threat_cells) >= 2:
            return -(WIN_SCORE - (ply + 1)), None

        if len(threat_cells) == 1:
            moves = [threat_cells[0]]
        else:
            if depth <= 0:
                return evaluate(turn), None

            moves = [c for c in range(27) if board_state[c] == 0]
            if not moves:
                return 0, None

        # TT lookup
        tt_key = (p1_mask, p2_mask, turn)
        tt_move = None
        original_alpha = alpha
        if tt_key in TT:
            e_depth, e_score, e_flag, e_move = TT[tt_key]
            # Adjust score for mate distance
            if e_score > WIN_SCORE - 100:
                e_score -= ply
            elif e_score < -WIN_SCORE + 100:
                e_score += ply

            if e_depth >= depth:
                if e_flag == EXACT:
                    return e_score, e_move
                elif e_flag == LOWER:
                    alpha = max(alpha, e_score)
                elif e_flag == UPPER:
                    beta = min(beta, e_score)
                if alpha >= beta:
                    return e_score, e_move
            tt_move = e_move

        # Move ordering
        if tt_move is not None and tt_move in moves:
            moves.remove(tt_move)
            moves.sort(key=lambda c: move_heuristic(c, turn), reverse=True)
            moves.insert(0, tt_move)
        else:
            moves.sort(key=lambda c: move_heuristic(c, turn), reverse=True)

        best_score = -INF
        best_move = moves[0]

        for c in moves:
            board_state[c] = turn
            if turn == 1:
                p1_mask ^= 1 << c
            else:
                p2_mask ^= 1 << c
            for L in CELL_LINES[c]:
                counts[turn][L] += 1

            score, _ = search(-turn, depth - 1, ply + 1, -beta, -alpha)
            score = -score

            board_state[c] = 0
            if turn == 1:
                p1_mask ^= 1 << c
            else:
                p2_mask ^= 1 << c
            for L in CELL_LINES[c]:
                counts[turn][L] -= 1

            if score > best_score:
                best_score = score
                best_move = c
            alpha = max(alpha, score)
            if alpha >= beta:
                break

        # Save to TT
        store_score = best_score
        if store_score > WIN_SCORE - 100:
            store_score += ply
        elif store_score < -WIN_SCORE + 100:
            store_score -= ply

        if best_score <= original_alpha:
            flag = UPPER
        elif best_score >= beta:
            flag = LOWER
        else:
            flag = EXACT

        TT[tt_key] = (depth, store_score, flag, best_move)
        return best_score, best_move

    # Default fallback move based on heuristic
    empty_cells.sort(key=lambda c: move_heuristic(c, 1), reverse=True)
    best_move_idx = empty_cells[0]

    # Iterative deepening
    for depth in range(1, len(empty_cells) + 1):
        try:
            score, move = search(
                turn=1, depth=depth, ply=0, alpha=-INF, beta=INF
            )
            if move is not None:
                best_move_idx = move
            if score >= WIN_SCORE - 50 or score <= -WIN_SCORE + 50:
                break
        except TimeoutError:
            break

    # Convert 1D index back to 3D coordinate (i, j, k)
    i = best_move_idx // 9
    j = (best_move_idx // 3) % 3
    k = best_move_idx % 3
    return (i, j, k)
