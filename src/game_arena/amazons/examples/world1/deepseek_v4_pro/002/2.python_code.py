
import numpy as np
import time

class Timeout(Exception):
    pass

def policy(board):
    # Convert numpy array to list of lists for faster access
    if isinstance(board, np.ndarray):
        state = board.tolist()
    else:
        state = board
    player = 1  # Our amazons are 1
    moves = get_legal_moves(state, player)
    if not moves:
        return ""  # No moves, shouldn't happen
    best_move_tuple = moves[0]
    start_time = time.time()
    try:
        for depth in range(1, 10):  # Max depth 10, but will break on time
            val, move_tuple = alpha_beta_search(state, player, depth, start_time, 0.95)
            if move_tuple is not None:
                best_move_tuple = move_tuple
            if time.time() - start_time > 0.95:
                break
    except Timeout:
        pass
    return move_to_str(best_move_tuple)

def move_to_str(move):
    sr, sc, tr, tc, ar, ac = move
    return f"{sr},{sc}:{tr},{tc}:{ar},{ac}"

def get_legal_moves(board, player):
    moves = []
    amazons = [(r, c) for r in range(6) for c in range(6) if board[r][c] == player]
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    for sr, sc in amazons:
        for dr, dc in directions:
            r, c = sr + dr, sc + dc
            while 0 <= r < 6 and 0 <= c < 6 and board[r][c] == 0:
                arrow_moves = get_arrow_moves(board, sr, sc, r, c, player)
                for ar, ac in arrow_moves:
                    moves.append((sr, sc, r, c, ar, ac))
                r += dr
                c += dc
    return moves

def get_arrow_moves(board, sr, sc, tr, tc, player):
    arrows = []
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    for dr, dc in directions:
        r, c = tr + dr, tc + dc
        while 0 <= r < 6 and 0 <= c < 6:
            if (r, c) == (sr, sc):
                # vacated square is now empty
                arrows.append((r, c))
            elif (r, c) == (tr, tc):
                break
            elif board[r][c] != 0:
                break
            else:
                arrows.append((r, c))
            r += dr
            c += dc
    return arrows

def apply_move(board, move, player):
    sr, sc, tr, tc, ar, ac = move
    new_board = [row[:] for row in board]
    new_board[sr][sc] = 0
    new_board[tr][tc] = player
    new_board[ar][ac] = -1
    return new_board

def alpha_beta_search(board, player, depth, start_time, time_limit):
    best_move = None
    alpha = -float('inf')
    beta = float('inf')
    moves = get_legal_moves(board, player)
    if not moves:
        # Should not happen at root, but handle gracefully
        return (-float('inf') if player == 1 else float('inf')), None
    
    # Move ordering
    move_scores = []
    for move in moves:
        new_board = apply_move(board, move, player)
        score = evaluate(new_board)
        move_scores.append((score, move))
    if player == 1:
        move_scores.sort(key=lambda x: x[0], reverse=True)
    else:
        move_scores.sort(key=lambda x: x[0])
    ordered_moves = [m for _, m in move_scores]
    
    if player == 1:
        value = -float('inf')
        for move in ordered_moves:
            if time.time() - start_time > time_limit:
                raise Timeout()
            new_board = apply_move(board, move, player)
            v, _ = alpha_beta_recursive(new_board, 2, depth - 1, alpha, beta, start_time, time_limit)
            if v > value:
                value = v
                best_move = move
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, best_move
    else:
        value = float('inf')
        for move in ordered_moves:
            if time.time() - start_time > time_limit:
                raise Timeout()
            new_board = apply_move(board, move, player)
            v, _ = alpha_beta_recursive(new_board, 1, depth - 1, alpha, beta, start_time, time_limit)
            if v < value:
                value = v
                best_move = move
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, best_move

def alpha_beta_recursive(board, player, depth, alpha, beta, start_time, time_limit):
    if time.time() - start_time > time_limit:
        raise Timeout()
    moves = get_legal_moves(board, player)
    if not moves:
        if player == 1:
            return -float('inf'), None
        else:
            return float('inf'), None
    if depth == 0:
        return evaluate(board), None

    # Move ordering
    move_scores = []
    for move in moves:
        new_board = apply_move(board, move, player)
        score = evaluate(new_board)
        move_scores.append((score, move))
    if player == 1:
        move_scores.sort(key=lambda x: x[0], reverse=True)
    else:
        move_scores.sort(key=lambda x: x[0])
    ordered_moves = [m for _, m in move_scores]

    if player == 1:
        value = -float('inf')
        for move in ordered_moves:
            if time.time() - start_time > time_limit:
                raise Timeout()
            new_board = apply_move(board, move, player)
            v, _ = alpha_beta_recursive(new_board, 2, depth - 1, alpha, beta, start_time, time_limit)
            value = max(value, v)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value, None
    else:
        value = float('inf')
        for move in ordered_moves:
            if time.time() - start_time > time_limit:
                raise Timeout()
            new_board = apply_move(board, move, player)
            v, _ = alpha_beta_recursive(new_board, 1, depth - 1, alpha, beta, start_time, time_limit)
            value = min(value, v)
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value, None

def evaluate(board):
    p1_reach = count_reachable(board, 1)
    p2_reach = count_reachable(board, 2)
    if p1_reach == 0 and p2_reach == 0:
        return 0
    if p1_reach == 0:
        return -1000
    if p2_reach == 0:
        return 1000
    return p1_reach - p2_reach

def count_reachable(board, player):
    visited = [[False]*6 for _ in range(6)]
    count = 0
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    amazons = [(r, c) for r in range(6) for c in range(6) if board[r][c] == player]
    for r, c in amazons:
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == 0:
                if not visited[nr][nc]:
                    visited[nr][nc] = True
                    count += 1
                nr += dr
                nc += dc
    return count
