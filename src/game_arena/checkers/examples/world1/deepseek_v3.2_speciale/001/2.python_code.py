
import time

# ---------- Precomputed board geometry ----------
# Dark squares are those with (row + col) % 2 == 0
rc_to_idx = [[-1] * 8 for _ in range(8)]
rc_from_idx = [None] * 32
idx = 0
for r in range(8):
    for c in range(8):
        if (r + c) % 2 == 0:
            rc_to_idx[r][c] = idx
            rc_from_idx[idx] = (r, c)
            idx += 1

# Directions: 0=up-left, 1=up-right, 2=down-left, 3=down-right
dr = [1, 1, -1, -1]
dc = [-1, 1, -1, 1]

neighbors = [[-1] * 4 for _ in range(32)]
jump_targets = [[-1] * 4 for _ in range(32)]
for i in range(32):
    r, c = rc_from_idx[i]
    for d in range(4):
        nr, nc = r + dr[d], c + dc[d]
        if 0 <= nr < 8 and 0 <= nc < 8:
            neighbors[i][d] = rc_to_idx[nr][nc]
            jr, jc = r + 2 * dr[d], c + 2 * dc[d]
            if 0 <= jr < 8 and 0 <= jc < 8:
                jump_targets[i][d] = rc_to_idx[jr][jc]

# Promotion rows
is_promotion_white = [False] * 32
is_promotion_black = [False] * 32
for i, (r, c) in enumerate(rc_from_idx):
    if r == 7:
        is_promotion_white[i] = True
    if r == 0:
        is_promotion_black[i] = True

# King centralization bonus
king_bonus = [0] * 32
for i, (r, c) in enumerate(rc_from_idx):
    drc = min(abs(r - 3), abs(r - 4)) + min(abs(c - 3), abs(c - 4))
    bonus = 5 - drc
    if bonus < 0:
        bonus = 0
    king_bonus[i] = bonus

# Forward move directions for each color
forward_dirs = {'w': [0, 1], 'b': [2, 3]}

# Global storing the AI's own color (set in policy)
AI_COLOR = None
INF = 10 ** 9

# ---------- Helper functions ----------
def opponent_color(player):
    return 'b' if player == 'w' else 'w'

def list_to_bb(sq_list):
    bb = 0
    for r, c in sq_list:
        idx = rc_to_idx[r][c]
        bb |= 1 << idx
    return bb

# ---------- Capture move generation (including multi‑jumps) ----------
def get_capture_sequences_for_piece(start_idx, start_is_king, us_men, us_kings, them_men, them_kings, color):
    # Quick check if any jump is possible from the start position
    init_dirs = range(4) if start_is_king else forward_dirs[color]
    any_jump = False
    for d in init_dirs:
        neigh = neighbors[start_idx][d]
        if neigh == -1:
            continue
        if not ((them_men | them_kings) & (1 << neigh)):
            continue
        tgt = jump_targets[start_idx][d]
        if tgt == -1:
            continue
        if (us_men | us_kings | them_men | them_kings) & (1 << tgt):
            continue
        any_jump = True
        break
    if not any_jump:
        return []

    # Depth‑first search to build all maximal capture sequences
    def dfs(cur_idx, cur_is_king, us_m, us_k, them_m, them_k, capt):
        dirs = range(4) if cur_is_king else forward_dirs[color]
        jumped = False
        for d in dirs:
            neigh = neighbors[cur_idx][d]
            if neigh == -1:
                continue
            if not ((them_m | them_k) & (1 << neigh)):
                continue
            tgt = jump_targets[cur_idx][d]
            if tgt == -1:
                continue
            all_cur = us_m | us_k | them_m | them_k
            if all_cur & (1 << tgt):
                continue

            jumped = True
            # Copy state
            new_us_m, new_us_k, new_them_m, new_them_k = us_m, us_k, them_m, them_k

            # Remove moving piece from current square
            if cur_is_king:
                new_us_k ^= (1 << cur_idx)
            else:
                new_us_m ^= (1 << cur_idx)

            # Promotion test
            promote = False
            if not cur_is_king:
                if (color == 'w' and is_promotion_white[tgt]) or (color == 'b' and is_promotion_black[tgt]):
                    promote = True

            # Place piece at target
            if cur_is_king or promote:
                new_us_k ^= (1 << tgt)
            else:
                new_us_m ^= (1 << tgt)

            # Remove captured piece
            if new_them_m & (1 << neigh):
                new_them_m ^= (1 << neigh)
            elif new_them_k & (1 << neigh):
                new_them_k ^= (1 << neigh)

            # Recurse
            yield from dfs(tgt, cur_is_king or promote,
                           new_us_m, new_us_k, new_them_m, new_them_k,
                           capt + [neigh])

        if not jumped:
            yield (start_idx, cur_idx, tuple(capt), start_is_king, cur_is_king)

    return list(dfs(start_idx, start_is_king,
                    us_men, us_kings, them_men, them_kings, []))

def get_capture_moves(us_men, us_kings, them_men, them_kings, color):
    moves = []
    all_us = us_men | us_kings
    for i in range(32):
        if (all_us >> i) & 1:
            is_king = (us_kings >> i) & 1
            seqs = get_capture_sequences_for_piece(i, is_king,
                                                   us_men, us_kings,
                                                   them_men, them_kings,
                                                   color)
            moves.extend(seqs)
    return moves

# ---------- Non‑capture move generation ----------
def get_noncapture_moves(us_men, us_kings, them_men, them_kings, color):
    moves = []
    all_us = us_men | us_kings
    all_pieces = all_us | them_men | them_kings
    for i in range(32):
        if (all_us >> i) & 1:
            is_king = (us_kings >> i) & 1
            dirs = range(4) if is_king else forward_dirs[color]
            for d in dirs:
                nbr = neighbors[i][d]
                if nbr == -1:
                    continue
                if all_pieces & (1 << nbr):
                    continue
                promote = False
                if not is_king:
                    if (color == 'w' and is_promotion_white[nbr]) or (color == 'b' and is_promotion_black[nbr]):
                        promote = True
                end_is_king = is_king or promote
                moves.append((i, nbr, (), is_king, end_is_king))
    return moves

# ---------- Move generation for a player (with mandatory capture) ----------
def get_moves(state, player):
    my_men, my_kings, opp_men, opp_kings = state
    if player == AI_COLOR:
        us_men, us_kings = my_men, my_kings
        them_men, them_kings = opp_men, opp_kings
    else:
        us_men, us_kings = opp_men, opp_kings
        them_men, them_kings = my_men, my_kings

    cap_moves = get_capture_moves(us_men, us_kings, them_men, them_kings, player)
    if cap_moves:
        return cap_moves
    return get_noncapture_moves(us_men, us_kings, them_men, them_kings, player)

# ---------- Apply a move to the state ----------
def apply_move(state, move, player):
    my_men, my_kings, opp_men, opp_kings = state
    start, end, captured, start_king, end_king = move

    if player == AI_COLOR:
        # Moving piece belongs to AI
        if start_king:
            my_kings ^= (1 << start)
        else:
            my_men ^= (1 << start)

        if end_king:
            my_kings ^= (1 << end)
        else:
            my_men ^= (1 << end)

        for cap in captured:
            if opp_men & (1 << cap):
                opp_men ^= (1 << cap)
            elif opp_kings & (1 << cap):
                opp_kings ^= (1 << cap)
    else:
        # Opponent moves
        if start_king:
            opp_kings ^= (1 << start)
        else:
            opp_men ^= (1 << start)

        if end_king:
            opp_kings ^= (1 << end)
        else:
            opp_men ^= (1 << end)

        for cap in captured:
            if my_men & (1 << cap):
                my_men ^= (1 << cap)
            elif my_kings & (1 << cap):
                my_kings ^= (1 << cap)

    return (my_men, my_kings, opp_men, opp_kings)

# ---------- Heuristic for move ordering ----------
def move_score(move, player):
    start, end, captured, start_king, end_king = move
    score = 0
    if captured:
        score += 1000 * len(captured)
    if not start_king and end_king:
        score += 500
    if not captured:   # non‑capture
        r1, c1 = rc_from_idx[start]
        r2, c2 = rc_from_idx[end]
        if not start_king:
            if player == 'w':
                score += (r2 - r1) * 10
            else:
                score += (r1 - r2) * 10
        else:
            score += (king_bonus[end] - king_bonus[start]) * 5
    return score

# ---------- Evaluation from the perspective of a given player ----------
def evaluate_for_player(state, player):
    my_men, my_kings, opp_men, opp_kings = state
    if player == AI_COLOR:
        us_men, us_kings = my_men, my_kings
        them_men, them_kings = opp_men, opp_kings
    else:
        us_men, us_kings = opp_men, opp_kings
        them_men, them_kings = my_men, my_kings

    # Material
    man_val = 100
    king_val = 200
    us_mat = man_val * us_men.bit_count() + king_val * us_kings.bit_count()
    them_mat = man_val * them_men.bit_count() + king_val * them_kings.bit_count()

    # Advancement for men
    us_adv = 0
    for i in range(32):
        if (us_men >> i) & 1:
            r, _ = rc_from_idx[i]
            if player == 'w':
                us_adv += r
            else:
                us_adv += 7 - r
    us_adv *= 10

    them_adv = 0
    opp = opponent_color(player)
    for i in range(32):
        if (them_men >> i) & 1:
            r, _ = rc_from_idx[i]
            if opp == 'w':
                them_adv += r
            else:
                them_adv += 7 - r
    them_adv *= 10

    # King centralization
    us_king_bonus = sum(king_bonus[i] for i in range(32) if (us_kings >> i) & 1)
    them_king_bonus = sum(king_bonus[i] for i in range(32) if (them_kings >> i) & 1)

    return (us_mat + us_adv + us_king_bonus) - (them_mat + them_adv + them_king_bonus)

# ---------- Negamax search with alpha‑beta ----------
def negamax(state, depth, alpha, beta, player):
    moves = get_moves(state, player)
    if not moves:
        return -INF   # loss
    if depth == 0:
        return evaluate_for_player(state, player)

    moves.sort(key=lambda m: move_score(m, player), reverse=True)
    best = -INF
    for move in moves:
        new_state = apply_move(state, move, player)
        val = -negamax(new_state, depth - 1, -beta, -alpha, opponent_color(player))
        if val > best:
            best = val
        if val > alpha:
            alpha = val
        if alpha >= beta:
            break
    return best

# ---------- Main policy ----------
def policy(my_men, my_kings, opp_men, opp_kings, color):
    global AI_COLOR
    AI_COLOR = color

    # Convert input lists to bitboards
    my_men_bb = list_to_bb(my_men)
    my_kings_bb = list_to_bb(my_kings)
    opp_men_bb = list_to_bb(opp_men)
    opp_kings_bb = list_to_bb(opp_kings)
    state = (my_men_bb, my_kings_bb, opp_men_bb, opp_kings_bb)

    # Root moves – mandatory capture already enforced
    root_moves = get_moves(state, AI_COLOR)
    if not root_moves:                     # should not happen, but fallback
        return ((0, 0), (0, 0))

    root_moves.sort(key=lambda m: move_score(m, AI_COLOR), reverse=True)
    best_move = root_moves[0]              # default
    start_time = time.time()
    max_depth = 1
    TIME_LIMIT = 0.8

    while True:
        # Do not start a new depth if we are already near the time limit
        if time.time() - start_time > TIME_LIMIT:
            break

        best_val = -INF
        current_best = None
        for move in root_moves:
            new_state = apply_move(state, move, AI_COLOR)
            val = -negamax(new_state, max_depth - 1, -INF, INF, opponent_color(AI_COLOR))
            if val > best_val:
                best_val = val
                current_best = move

        if current_best is not None:
            best_move = current_best

        max_depth += 1
        if max_depth > 20:      # safety cap
            break

    # Convert back to coordinates
    start_idx, end_idx, _, _, _ = best_move
    from_rc = rc_from_idx[start_idx]
    to_rc = rc_from_idx[end_idx]
    return (from_rc, to_rc)
