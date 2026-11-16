
from collections import deque

BOARD_SIZE = 19
EMPTY = 0
ME = 1
OPP = 2

DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

OPENING_POINTS = [
    (4, 4), (4, 16), (16, 4), (16, 16),
    (10, 10),
    (4, 10), (10, 4), (10, 16), (16, 10),
    (7, 7), (7, 13), (13, 7), (13, 13),
]

def inside(r, c):
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE

def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if inside(nr, nc):
            yield nr, nc

def build_board(me, opponent):
    board = [[EMPTY] * (BOARD_SIZE + 1) for _ in range(BOARD_SIZE + 1)]
    for r, c in me:
        if inside(r, c):
            board[r][c] = ME
    for r, c in opponent:
        if inside(r, c):
            board[r][c] = OPP
    return board

def copy_board(board):
    return [row[:] for row in board]

def get_group_and_liberties(board, r, c):
    color = board[r][c]
    q = deque([(r, c)])
    seen = {(r, c)}
    group = []
    liberties = set()

    while q:
        cr, cc = q.popleft()
        group.append((cr, cc))
        for nr, nc in neighbors(cr, cc):
            v = board[nr][nc]
            if v == EMPTY:
                liberties.add((nr, nc))
            elif v == color and (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc))
    return group, liberties

def remove_group(board, group):
    for r, c in group:
        board[r][c] = EMPTY

def simulate_move(board, move, my_color=ME):
    r, c = move
    if not inside(r, c) or board[r][c] != EMPTY:
        return None

    opp_color = OPP if my_color == ME else ME
    b = copy_board(board)
    b[r][c] = my_color

    captured = 0
    checked = set()
    for nr, nc in neighbors(r, c):
        if b[nr][nc] == opp_color and (nr, nc) not in checked:
            group, libs = get_group_and_liberties(b, nr, nc)
            for stone in group:
                checked.add(stone)
            if len(libs) == 0:
                captured += len(group)
                remove_group(b, group)

    my_group, my_libs = get_group_and_liberties(b, r, c)
    if len(my_libs) == 0:
        return None

    return b, captured, len(my_group), len(my_libs)

def legal_moves(board):
    moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == EMPTY and simulate_move(board, (r, c), ME) is not None:
                moves.append((r, c))
    return moves

def count_groups_in_atari(board, color):
    seen = set()
    count = 0
    stones = 0
    liberties_map = {}
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == color and (r, c) not in seen:
                group, libs = get_group_and_liberties(board, r, c)
                for s in group:
                    seen.add(s)
                for s in group:
                    liberties_map[s] = libs
                if len(libs) == 1:
                    count += 1
                    stones += len(group)
    return count, stones, liberties_map

def manhattan(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def nearest_distance(move, stones):
    if not stones:
        return 10
    return min(manhattan(move, s) for s in stones)

def opening_move(board, me, opponent):
    occupied = set(me) | set(opponent)
    empties = 361 - len(occupied)
    if empties < 330:
        return None

    candidates = []
    for p in OPENING_POINTS:
        if p in occupied:
            continue
        if simulate_move(board, p, ME) is None:
            continue

        dist_opp = nearest_distance(p, opponent)
        dist_me = nearest_distance(p, me)
        center_bias = -manhattan(p, (10, 10))
        score = 4 * dist_opp + 2 * dist_me + center_bias
        candidates.append((score, p))

    if candidates:
        candidates.sort(reverse=True)
        return candidates[0][1]
    return None

def local_features(board, move, me_set, opp_set):
    r, c = move
    adj_me = 0
    adj_opp = 0
    diag_me = 0
    diag_opp = 0
    edge_penalty = 0

    for nr, nc in neighbors(r, c):
        if (nr, nc) in me_set:
            adj_me += 1
        elif (nr, nc) in opp_set:
            adj_opp += 1

    for dr in (-1, 1):
        for dc in (-1, 1):
            nr, nc = r + dr, c + dc
            if inside(nr, nc):
                if (nr, nc) in me_set:
                    diag_me += 1
                elif (nr, nc) in opp_set:
                    diag_opp += 1

    if r in (1, 19):
        edge_penalty += 1
    if c in (1, 19):
        edge_penalty += 1

    dist_center = abs(r - 10) + abs(c - 10)
    return adj_me, adj_opp, diag_me, diag_opp, edge_penalty, dist_center

def policy(me, opponent):
    board = build_board(me, opponent)
    me_set = set(me)
    opp_set = set(opponent)

    # Good early-board structure.
    op = opening_move(board, me, opponent)
    if op is not None:
        return op

    legal = legal_moves(board)
    if not legal:
        return (0, 0)

    # Precompute tactical info from current board.
    my_atari_count, my_atari_stones, my_lib_map = count_groups_in_atari(board, ME)
    opp_atari_count, opp_atari_stones, opp_lib_map = count_groups_in_atari(board, OPP)

    best_move = None
    best_score = -10**18

    for mv in legal:
        sim = simulate_move(board, mv, ME)
        if sim is None:
            continue
        new_board, captured, my_group_size, my_libs = sim

        score = 0
        r, c = mv

        # Tactical priority: capturing is huge.
        score += captured * 100000

        # If this move fills the liberty of opponent atari groups, reward more.
        pressure_bonus = 0
        touched_opp_groups = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in opp_set and (nr, nc) not in touched_opp_groups:
                group, libs = get_group_and_liberties(board, nr, nc)
                for s in group:
                    touched_opp_groups.add(s)
                if len(libs) == 1 and mv in libs:
                    pressure_bonus += 5000 + 100 * len(group)
                elif len(libs) == 2 and mv in libs:
                    pressure_bonus += 300 + 20 * len(group)
        score += pressure_bonus

        # Saving own atari groups.
        save_bonus = 0
        touched_my_groups = set()
        for nr, nc in neighbors(r, c):
            if (nr, nc) in me_set and (nr, nc) not in touched_my_groups:
                group, libs = get_group_and_liberties(board, nr, nc)
                for s in group:
                    touched_my_groups.add(s)
                if len(libs) == 1 and mv in libs:
                    save_bonus += 7000 + 150 * len(group)
                elif len(libs) == 2 and mv in libs:
                    save_bonus += 400 + 20 * len(group)
        score += save_bonus

        # Healthy shape and connectivity.
        adj_me, adj_opp, diag_me, diag_opp, edge_penalty, dist_center = local_features(board, mv, me_set, opp_set)
        score += adj_me * 180
        score += diag_me * 40
        score += adj_opp * 110
        score += diag_opp * 20

        # Prefer moves that result in decent liberties.
        score += my_libs * 140
        score += min(my_group_size, 12) * 15

        # Strongly avoid self-atari unless capturing.
        if my_libs == 1 and captured == 0:
            score -= 9000
        elif my_libs == 2 and captured == 0:
            score -= 400

        # Mild opening/middlegame positional taste.
        empties = 361 - len(me_set) - len(opp_set)
        if empties > 250:
            score -= edge_penalty * 140
            score -= dist_center * 8
        else:
            score -= edge_penalty * 25
            score -= dist_center * 2

        # Prefer moves near existing action over isolated nonsense.
        d_me = nearest_distance(mv, me)
        d_opp = nearest_distance(mv, opponent)
        if me or opponent:
            score -= max(0, d_me - 3) * 25
            score -= max(0, d_opp - 4) * 10

        # Tiny deterministic tiebreak.
        score += (20 - r) * 0.001 + (20 - c) * 0.0001

        if score > best_score:
            best_score = score
            best_move = mv

    if best_move is not None:
        return best_move

    # Failsafe: return first legal move.
    return legal[0] if legal else (0, 0)
