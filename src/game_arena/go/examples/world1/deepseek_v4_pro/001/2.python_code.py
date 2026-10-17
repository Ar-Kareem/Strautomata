
import numpy as np
from collections import deque
import time

def get_group_and_liberties(board, r, c):
    color = board[r, c]
    if color == 0:
        return [], set()
    group = []
    liberties = set()
    visited = np.zeros((19, 19), dtype=bool)
    q = deque([(r, c)])
    visited[r, c] = True
    while q:
        cr, cc = q.popleft()
        group.append((cr, cc))
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr, nc] == 0:
                    liberties.add((nr, nc))
                elif board[nr, nc] == color and not visited[nr, nc]:
                    visited[nr, nc] = True
                    q.append((nr, nc))
    return group, liberties

def is_legal(board, r, c, player):
    if board[r, c] != 0:
        return False
    temp = board.copy()
    temp[r, c] = player
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and temp[nr, nc] == -player:
            group, liberties = get_group_and_liberties(temp, nr, nc)
            if len(liberties) == 0:
                for gr, gc in group:
                    temp[gr, gc] = 0
    group, liberties = get_group_and_liberties(temp, r, c)
    return len(liberties) > 0

def apply_move(board, r, c, player):
    board[r, c] = player
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == -player:
            group, liberties = get_group_and_liberties(board, nr, nc)
            if len(liberties) == 0:
                for gr, gc in group:
                    board[gr, gc] = 0

def evaluate_board(board, player):
    dist = np.full((19, 19), 999, dtype=np.int16)
    color_mask = np.zeros((19, 19), dtype=np.int8)
    q = deque()
    for r in range(19):
        for c in range(19):
            if board[r, c] == player:
                dist[r, c] = 0
                color_mask[r, c] = 1
                q.append((r, c, 1))
            elif board[r, c] == -player:
                dist[r, c] = 0
                color_mask[r, c] = -1
                q.append((r, c, -1))
    while q:
        r, c, col = q.popleft()
        d = dist[r, c] + 1
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr, nc] == 0:
                    if dist[nr, nc] > d:
                        dist[nr, nc] = d
                        color_mask[nr, nc] = col
                        q.append((nr, nc, col))
                    elif dist[nr, nc] == d and color_mask[nr, nc] != col:
                        color_mask[nr, nc] = 0
    my_score = np.count_nonzero(color_mask == 1)
    opp_score = np.count_nonzero(color_mask == -1)
    return my_score - opp_score

def generate_candidates(board, player, start_time):
    candidates = set()
    stones_positions = np.argwhere(board != 0)
    total_stones = len(stones_positions)
    # adjacent moves
    for r, c in stones_positions:
        if time.time() - start_time > 0.9:
            break
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                candidates.add((nr, nc))
    # opening star points
    star_points = [(3, 3), (3, 9), (3, 15),
                   (9, 3), (9, 9), (9, 15),
                   (15, 3), (15, 9), (15, 15)]
    if total_stones < 10:
        for p in star_points:
            if board[p[0], p[1]] == 0:
                candidates.add(p)
    # fallback if no candidates
    if not candidates:
        for r in range(19):
            for c in range(19):
                if board[r, c] == 0:
                    candidates.add((r, c))
                    break
            if candidates:
                break
    legal = []
    for r, c in candidates:
        if time.time() - start_time > 0.9:
            break
        if is_legal(board, r, c, player):
            legal.append((r, c))
    legal.append((0, 0))  # pass
    return legal

def policy(me, opponent):
    start_time = time.time()
    board = np.zeros((19, 19), dtype=np.int8)
    for r, c in me:
        board[r - 1, c - 1] = 1
    for r, c in opponent:
        board[r - 1, c - 1] = -1

    my_candidates = generate_candidates(board, 1, start_time)
    best_score = -9999
    best_move = (0, 0)

    for move in my_candidates:
        if time.time() - start_time > 0.9:
            break
        if move == (0, 0):
            board_after_me = board.copy()
        else:
            board_after_me = board.copy()
            apply_move(board_after_me, move[0], move[1], 1)

        opp_candidates = generate_candidates(board_after_me, -1, start_time)
        if not opp_candidates:
            score = evaluate_board(board_after_me, 1)
        else:
            min_score = 9999
            for opp_move in opp_candidates:
                if time.time() - start_time > 0.9:
                    break
                if opp_move == (0, 0):
                    board_after_opp = board_after_me.copy()
                else:
                    board_after_opp = board_after_me.copy()
                    apply_move(board_after_opp, opp_move[0], opp_move[1], -1)
                score = evaluate_board(board_after_opp, 1)
                if score < min_score:
                    min_score = score
            score = min_score if opp_candidates else evaluate_board(board_after_me, 1)

        if score > best_score:
            best_score = score
            best_move = move

    if best_move == (0, 0):
        return (0, 0)
    return (best_move[0] + 1, best_move[1] + 1)
