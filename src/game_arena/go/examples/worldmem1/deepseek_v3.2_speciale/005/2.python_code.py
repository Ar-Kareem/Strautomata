
import random

SIZE = 19
ALL_COORDS = list(range(SIZE * SIZE))

# ----------------------------------------------------------------------
# Precomputed neighbours (4‑connectivity)
NEIGHBORS = []
for r in range(SIZE):
    for c in range(SIZE):
        idx = r * SIZE + c
        nb = []
        if r > 0:
            nb.append((r - 1) * SIZE + c)
        if r < SIZE - 1:
            nb.append((r + 1) * SIZE + c)
        if c > 0:
            nb.append(r * SIZE + (c - 1))
        if c < SIZE - 1:
            nb.append(r * SIZE + (c + 1))
        NEIGHBORS.append(tuple(nb))

# ----------------------------------------------------------------------
# Precomputed total influence contribution of a stone at each intersection
def precompute_total_contrib():
    contrib = [0.0] * (SIZE * SIZE)
    for i in range(SIZE * SIZE):
        r1 = i // SIZE
        c1 = i % SIZE
        total = 0.0
        for j in range(SIZE * SIZE):
            r2 = j // SIZE
            c2 = j % SIZE
            dr = r1 - r2
            dc = c1 - c2
            d2 = dr * dr + dc * dc
            total += 1.0 / (d2 + 1.0)
        contrib[i] = total
    return contrib

TOTAL_CONTRIB = precompute_total_contrib()

# ----------------------------------------------------------------------
# Helper: indices within Chebyshev distance ≤ 3 of any stone
def near_candidates(board):
    cand = set()
    for i in range(SIZE * SIZE):
        if board[i] != 0:
            r = i // SIZE
            c = i % SIZE
            for dr in range(-3, 4):
                for dc in range(-3, 4):
                    if max(abs(dr), abs(dc)) <= 3:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < SIZE and 0 <= nc < SIZE:
                            cand.add(nr * SIZE + nc)
    return list(cand)

# ----------------------------------------------------------------------
# Move legality and capture detection
def is_legal_move(board, idx, color):
    if board[idx] != 0:
        return False, []
    enemy = 3 - color
    captured = set()
    processed = set()                      # already examined enemy groups

    # Find opponent groups that would be captured
    for nb in NEIGHBORS[idx]:
        if board[nb] == enemy and nb not in processed:
            stack = [nb]
            group = set()
            liberties = set()
            visited = set()
            while stack:
                cur = stack.pop()
                if cur in visited:
                    continue
                visited.add(cur)
                group.add(cur)
                for nb2 in NEIGHBORS[cur]:
                    if board[nb2] == 0:
                        liberties.add(nb2)
                    elif board[nb2] == enemy and nb2 not in visited:
                        stack.append(nb2)
            processed.update(group)
            if len(liberties) == 1 and idx in liberties:
                captured.update(group)

    # Suicide check after capturing
    stack = [idx]
    visited = set()
    has_liberty = False
    while stack:
        cur = stack.pop()
        if cur in visited:
            continue
        visited.add(cur)
        for nb in NEIGHBORS[cur]:
            if board[nb] == color:
                if nb not in visited:
                    stack.append(nb)
            elif board[nb] == 0 or nb in captured:
                has_liberty = True
    if not has_liberty:
        return False, []
    return True, list(captured)

# ----------------------------------------------------------------------
# Apply a move (assumes legal)
def apply_move(board, idx, color, captured):
    board[idx] = color
    for cap in captured:
        board[cap] = 0

# ----------------------------------------------------------------------
# Evaluation of a board from the perspective of the original player
def evaluate_board(board, my_color, opp_color, safety_weight=5):
    # Influence difference
    my_inf = 0.0
    opp_inf = 0.0
    for i in range(SIZE * SIZE):
        if board[i] == my_color:
            my_inf += TOTAL_CONTRIB[i]
        elif board[i] == opp_color:
            opp_inf += TOTAL_CONTRIB[i]
    inf_diff = my_inf - opp_inf

    # Group safety: penalty for our groups in atari, bonus for opponent's
    visited = [False] * (SIZE * SIZE)
    my_atari = 0
    opp_atari = 0
    for i in range(SIZE * SIZE):
        if not visited[i] and board[i] != 0:
            color = board[i]
            stack = [i]
            group = []
            libs = set()
            while stack:
                cur = stack.pop()
                if visited[cur]:
                    continue
                visited[cur] = True
                group.append(cur)
                for nb in NEIGHBORS[cur]:
                    if board[nb] == 0:
                        libs.add(nb)
                    elif board[nb] == color and not visited[nb]:
                        stack.append(nb)
            if len(libs) == 1:
                if color == my_color:
                    my_atari += len(group)
                else:
                    opp_atari += len(group)

    safety = safety_weight * (opp_atari - my_atari)
    return inf_diff + safety

# ----------------------------------------------------------------------
# Main policy
def policy(me, opponent, memory):
    MY_COLOR = 1
    OPP_COLOR = 2
    CAPTURE_WEIGHT = 100
    SAFETY_WEIGHT = 5
    TOP_MY = 20
    TOP_OPP = 15

    # Initialise memory for ko
    if not memory:
        memory['prev_me'] = None
        memory['prev_opp'] = None

    # Convert input to board (0‑based indices)
    current_board = [0] * (SIZE * SIZE)
    my_stones = []
    opp_stones = []
    for r, c in me:
        idx = (r - 1) * SIZE + (c - 1)
        current_board[idx] = MY_COLOR
        my_stones.append(idx)
    for r, c in opponent:
        idx = (r - 1) * SIZE + (c - 1)
        current_board[idx] = OPP_COLOR
        opp_stones.append(idx)

    # --------------------------------------------------------------
    # 1. Generate candidate moves for us (ignore ko)
    total_stones = sum(1 for x in current_board if x != 0)
    if total_stones < 10:
        candidate_idxs = ALL_COORDS[:]          # whole board in opening
    else:
        candidate_idxs = near_candidates(current_board)

    my_moves = []                               # (idx, captures, quick_score)
    for idx in candidate_idxs:
        if current_board[idx] != 0:
            continue
        legal, caps = is_legal_move(current_board, idx, MY_COLOR)
        if legal:
            quick = len(caps) * CAPTURE_WEIGHT + TOTAL_CONTRIB[idx]
            my_moves.append((idx, caps, quick))
    # Add pass
    my_moves.append((-1, [], 0))

    # Keep top moves (force pass to be considered)
    my_moves.sort(key=lambda x: x[2], reverse=True)
    non_pass = [m for m in my_moves if m[0] != -1]
    pass_move = [m for m in my_moves if m[0] == -1][0]
    top_my = non_pass[:TOP_MY - 1] + [pass_move]

    # --------------------------------------------------------------
    # 2. Depth‑2 search
    candidate_results = []   # (idx, value)
    for idx, caps, _ in top_my:
        board1 = current_board[:]
        if idx != -1:
            apply_move(board1, idx, MY_COLOR, caps)

        # Opponent move generation
        stones1 = sum(1 for x in board1 if x != 0)
        if stones1 < 10:
            opp_cand_idxs = ALL_COORDS[:]
        else:
            opp_cand_idxs = near_candidates(board1)

        opp_moves = []
        for oidx in opp_cand_idxs:
            if board1[oidx] != 0:
                continue
            legal, ocaps = is_legal_move(board1, oidx, OPP_COLOR)
            if legal:
                quick = len(ocaps) * CAPTURE_WEIGHT + TOTAL_CONTRIB[oidx]
                opp_moves.append((oidx, ocaps, quick))
        # Add opponent pass
        opp_moves.append((-1, [], 0))
        opp_moves.sort(key=lambda x: x[2], reverse=True)
        selected_opp = opp_moves[:TOP_OPP]
        if not any(m[0] == -1 for m in selected_opp):
            selected_opp.append((-1, [], 0))

        # Minimum evaluation over opponent replies
        min_eval = float('inf')
        for oidx, ocaps, _ in selected_opp:
            board2 = board1[:]
            if oidx != -1:
                apply_move(board2, oidx, OPP_COLOR, ocaps)
            eval_ = evaluate_board(board2, MY_COLOR, OPP_COLOR, SAFETY_WEIGHT)
            if eval_ < min_eval:
                min_eval = eval_
        if min_eval == float('inf'):
            min_eval = -1e9
        candidate_results.append((idx, min_eval))

    # Choose best move (random tie‑break)
    max_val = max(v for _, v in candidate_results)
    best_options = [idx for idx, v in candidate_results if abs(v - max_val) < 1e-9]
    best_idx = random.choice(best_options)

    # --------------------------------------------------------------
    # 3. Ko check (simple: compare with board after our last move)
    prev_me = memory.get('prev_me')
    prev_opp = memory.get('prev_opp')
    if best_idx != -1 and prev_me is not None and prev_opp is not None:
        # Recompute board after this move
        caps_for_best = next(caps for idx0, caps, _ in top_my if idx0 == best_idx)
        my_after = set(my_stones)
        opp_after = set(opp_stones)
        my_after.add(best_idx)
        for cap in caps_for_best:
            opp_after.remove(cap)
        if my_after == prev_me and opp_after == prev_opp:
            # Ko violation – fall back to next best legal move
            sorted_cands = sorted(candidate_results, key=lambda x: x[1], reverse=True)
            for idx, _ in sorted_cands:
                if idx == -1:
                    best_idx = -1
                    break
                caps = next(caps for idx0, caps, _ in top_my if idx0 == idx)
                my_try = set(my_stones)
                opp_try = set(opp_stones)
                my_try.add(idx)
                for cap in caps:
                    opp_try.remove(cap)
                if not (my_try == prev_me and opp_try == prev_opp):
                    best_idx = idx
                    break
            else:
                best_idx = -1   # all ko‑illegal → pass

    # --------------------------------------------------------------
    # 4. Prepare return value and update memory
    if best_idx == -1:
        action = (0, 0)
        new_my = set(my_stones)
        new_opp = set(opp_stones)
    else:
        caps = next(caps for idx0, caps, _ in top_my if idx0 == best_idx)
        r = best_idx // SIZE + 1
        c = best_idx % SIZE + 1
        action = (r, c)
        new_my = set(my_stones)
        new_opp = set(opp_stones)
        new_my.add(best_idx)
        for cap in caps:
            new_opp.remove(cap)

    memory['prev_me'] = new_my
    memory['prev_opp'] = new_opp
    return action, memory
