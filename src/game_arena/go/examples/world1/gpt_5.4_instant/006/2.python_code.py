
from collections import deque

BOARD_SIZE = 19
DIRS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def inside(r, c):
    return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE


def build_board(me, opponent):
    board = [[0] * (BOARD_SIZE + 1) for _ in range(BOARD_SIZE + 1)]
    for r, c in me:
        if inside(r, c):
            board[r][c] = 1
    for r, c in opponent:
        if inside(r, c):
            board[r][c] = 2
    return board


def neighbors(r, c):
    for dr, dc in DIRS:
        nr, nc = r + dr, c + dc
        if inside(nr, nc):
            yield nr, nc


def get_group_and_liberties(board, r, c):
    color = board[r][c]
    group = []
    liberties = set()
    q = deque([(r, c)])
    seen = {(r, c)}
    while q:
        x, y = q.popleft()
        group.append((x, y))
        for nx, ny in neighbors(x, y):
            v = board[nx][ny]
            if v == 0:
                liberties.add((nx, ny))
            elif v == color and (nx, ny) not in seen:
                seen.add((nx, ny))
                q.append((nx, ny))
    return group, liberties


def copy_board(board):
    return [row[:] for row in board]


def play_move(board, r, c, color):
    if (r, c) == (0, 0):
        return copy_board(board), 0
    if not inside(r, c) or board[r][c] != 0:
        return None, -1

    b = copy_board(board)
    opp = 3 - color
    b[r][c] = color
    captured = 0

    checked = set()
    for nx, ny in neighbors(r, c):
        if b[nx][ny] == opp and (nx, ny) not in checked:
            group, libs = get_group_and_liberties(b, nx, ny)
            for p in group:
                checked.add(p)
            if len(libs) == 0:
                captured += len(group)
                for gx, gy in group:
                    b[gx][gy] = 0

    group, libs = get_group_and_liberties(b, r, c)
    if len(libs) == 0:
        return None, -1  # suicide illegal

    return b, captured


def legal_moves(board):
    moves = []
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == 0:
                nb, cap = play_move(board, r, c, 1)
                if nb is not None:
                    moves.append((r, c, cap))
    return moves


def count_adjacent(board, r, c, color):
    cnt = 0
    for nr, nc in neighbors(r, c):
        if board[nr][nc] == color:
            cnt += 1
    return cnt


def min_dist_to_stones(r, c, stones):
    if not stones:
        return 0
    best = 10**9
    for sr, sc in stones:
        d = abs(r - sr) + abs(c - sc)
        if d < best:
            best = d
    return best


def opening_preference(r, c):
    # Prefer center / star-point-ish regions early
    center_dist = abs(r - 10) + abs(c - 10)
    star_bonus = 0
    for sr, sc in [(4, 4), (4, 10), (4, 16), (10, 4), (10, 10), (10, 16), (16, 4), (16, 10), (16, 16)]:
        d = abs(r - sr) + abs(c - sc)
        if d == 0:
            star_bonus = max(star_bonus, 6)
        elif d == 1:
            star_bonus = max(star_bonus, 4)
        elif d == 2:
            star_bonus = max(star_bonus, 2)
    return -center_dist + star_bonus


def find_critical_saves(board):
    # Return candidate moves that save our groups in atari
    saves = set()
    seen = set()
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r][c] == 1 and (r, c) not in seen:
                group, libs = get_group_and_liberties(board, r, c)
                for p in group:
                    seen.add(p)
                if len(libs) == 1:
                    lib = next(iter(libs))
                    nb, _ = play_move(board, lib[0], lib[1], 1)
                    if nb is not None:
                        saves.add(lib)
                    # Also consider capturing adjacent attacker stones
                    for gx, gy in group:
                        for nx, ny in neighbors(gx, gy):
                            if board[nx][ny] == 2:
                                og, olib = get_group_and_liberties(board, nx, ny)
                                if len(olib) == 1:
                                    cap_move = next(iter(olib))
                                    nb2, _ = play_move(board, cap_move[0], cap_move[1], 1)
                                    if nb2 is not None:
                                        saves.add(cap_move)
    return saves


def evaluate_move(board, me, opponent, r, c, captured):
    nb, _ = play_move(board, r, c, 1)
    if nb is None:
        return -10**18

    score = 0

    # Big priority: captures
    score += captured * 1000

    # Shape / local fighting
    my_adj = count_adjacent(board, r, c, 1)
    opp_adj = count_adjacent(board, r, c, 2)
    score += my_adj * 18
    score += opp_adj * 10

    # Avoid isolated edge junk unless tactical
    if r in (1, BOARD_SIZE) or c in (1, BOARD_SIZE):
        score -= 8
    if r in (2, BOARD_SIZE - 1) or c in (2, BOARD_SIZE - 1):
        score -= 3

    # Opening preference if board sparse
    total = len(me) + len(opponent)
    if total < 16:
        score += opening_preference(r, c) * 3
    else:
        # Stay relevant to existing stones
        d_me = min_dist_to_stones(r, c, me)
        d_opp = min_dist_to_stones(r, c, opponent)
        score += max(0, 8 - d_me) * 5
        score += max(0, 6 - d_opp) * 3

    # Penalize self-atari / low-liberty result
    group, libs = get_group_and_liberties(nb, r, c)
    l = len(libs)
    if l == 1:
        score -= 120
    elif l == 2:
        score -= 25
    else:
        score += min(l, 4) * 4

    # Bonus if move puts adjacent opponent groups in atari
    seen_opp = set()
    atari_bonus = 0
    for nx, ny in neighbors(r, c):
        if nb[nx][ny] == 2 and (nx, ny) not in seen_opp:
            og, olib = get_group_and_liberties(nb, nx, ny)
            for p in og:
                seen_opp.add(p)
            if len(olib) == 1:
                atari_bonus += len(og) * 25
    score += atari_bonus

    return score


def policy(me, opponent):
    board = build_board(me, opponent)

    # Gather all legal moves and immediate captures
    moves = legal_moves(board)
    if not moves:
        return (0, 0)

    # 1) Immediate best capture
    best_cap = max(cap for _, _, cap in moves)
    if best_cap > 0:
        cap_moves = [(r, c, cap) for r, c, cap in moves if cap == best_cap]
        best_move = None
        best_score = -10**18
        for r, c, cap in cap_moves:
            s = evaluate_move(board, me, opponent, r, c, cap)
            if s > best_score:
                best_score = s
                best_move = (r, c)
        if best_move is not None:
            return best_move

    # 2) Save own groups in atari
    critical = find_critical_saves(board)
    if critical:
        best_move = None
        best_score = -10**18
        move_caps = {(r, c): cap for r, c, cap in moves}
        for r, c in critical:
            if (r, c) in move_caps:
                s = evaluate_move(board, me, opponent, r, c, move_caps[(r, c)]) + 500
                if s > best_score:
                    best_score = s
                    best_move = (r, c)
        if best_move is not None:
            return best_move

    # 3) General evaluation over legal moves
    best_move = None
    best_score = -10**18
    for r, c, cap in moves:
        s = evaluate_move(board, me, opponent, r, c, cap)
        if s > best_score:
            best_score = s
            best_move = (r, c)

    if best_move is not None:
        return best_move

    return (0, 0)
