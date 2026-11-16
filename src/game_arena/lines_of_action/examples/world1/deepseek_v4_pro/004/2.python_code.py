
import numpy as np
import time

class TimeoutError(Exception):
    pass

def check_time(start, limit):
    if time.time() - start > limit:
        raise TimeoutError

def count_line(board, r, c, dr, dc):
    if dr == 0 and dc != 0:
        return np.count_nonzero(board[r, :])
    elif dc == 0 and dr != 0:
        return np.count_nonzero(board[:, c])
    elif dr == dc:
        count = 0
        for i in range(8):
            j = i - (r - c)
            if 0 <= j < 8:
                if board[i, j] != 0:
                    count += 1
        return count
    elif dr == -dc:
        count = 0
        for i in range(8):
            j = (r + c) - i
            if 0 <= j < 8:
                if board[i, j] != 0:
                    count += 1
        return count
    else:
        return 0

def get_legal_moves(board, player):
    moves = []
    pieces = np.argwhere(board == player)
    for r, c in pieces:
        for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
            count = count_line(board, r, c, dr, dc)
            if count == 0:
                continue
            nr = r + count * dr
            nc = c + count * dc
            if nr < 0 or nr >= 8 or nc < 0 or nc >= 8:
                continue
            if board[nr, nc] == player:
                continue
            blocked = False
            for step in range(1, count):
                rr = r + step * dr
                cc = c + step * dc
                if board[rr, cc] == -player:
                    blocked = True
                    break
            if blocked:
                continue
            moves.append((r, c, nr, nc))
    return moves

def bfs(board, player, start_r, start_c, visited):
    stack = [(start_r, start_c)]
    size = 0
    while stack:
        r, c = stack.pop()
        if (r, c) in visited:
            continue
        visited.add((r, c))
        size += 1
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == player and (nr, nc) not in visited:
                    stack.append((nr, nc))
    return size

def is_connected(board, player):
    pieces = np.argwhere(board == player)
    if len(pieces) <= 1:
        return True
    visited = set()
    bfs(board, player, pieces[0][0], pieces[0][1], visited)
    return len(visited) == len(pieces)

def unconnected_pieces(board, player):
    pieces = np.argwhere(board == player)
    if len(pieces) == 0:
        return 0
    if len(pieces) == 1:
        return 0
    visited = set()
    max_size = 0
    for (r, c) in pieces:
        if (r, c) not in visited:
            comp_size = bfs(board, player, r, c, visited)
            if comp_size > max_size:
                max_size = comp_size
    return len(pieces) - max_size

def evaluate(board):
    if is_connected(board, 1):
        return 10000
    if is_connected(board, -1):
        return -10000
    if np.count_nonzero(board == -1) == 0:
        return 10000
    if np.count_nonzero(board == 1) == 0:
        return -10000
    my_unconn = unconnected_pieces(board, 1)
    opp_unconn = unconnected_pieces(board, -1)
    return opp_unconn - my_unconn

def sort_moves(board, moves, player):
    def score(move):
        r1, c1, r2, c2 = move
        cap = 1 if board[r2, c2] == -player else 0
        return -cap
    return sorted(moves, key=score)

def alpha_beta(board, depth, alpha, beta, maximizing, start, limit):
    check_time(start, limit)
    if depth == 0:
        return evaluate(board)
    player = 1 if maximizing else -1
    moves = get_legal_moves(board, player)
    if not moves:
        return -10000 if maximizing else 10000
    if maximizing:
        if is_connected(board, 1):
            return 10000
        if is_connected(board, -1):
            return -10000
    else:
        if is_connected(board, -1):
            return -10000
        if is_connected(board, 1):
            return 10000
    moves = sort_moves(board, moves, player)
    if maximizing:
        value = -np.inf
        for move in moves:
            check_time(start, limit)
            new_board = board.copy()
            r1, c1, r2, c2 = move
            new_board[r1, c1] = 0
            new_board[r2, c2] = player
            val = alpha_beta(new_board, depth-1, alpha, beta, False, start, limit)
            value = max(value, val)
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        return value
    else:
        value = np.inf
        for move in moves:
            check_time(start, limit)
            new_board = board.copy()
            r1, c1, r2, c2 = move
            new_board[r1, c1] = 0
            new_board[r2, c2] = player
            val = alpha_beta(new_board, depth-1, alpha, beta, True, start, limit)
            value = min(value, val)
            beta = min(beta, val)
            if alpha >= beta:
                break
        return value

def alpha_beta_search(board, depth, start, limit):
    best_move = None
    best_val = -np.inf
    alpha = -np.inf
    beta = np.inf
    moves = get_legal_moves(board, 1)
    if not moves:
        return evaluate(board), None
    moves = sort_moves(board, moves, 1)
    for move in moves:
        check_time(start, limit)
        new_board = board.copy()
        r1, c1, r2, c2 = move
        new_board[r1, c1] = 0
        new_board[r2, c2] = 1
        if is_connected(new_board, 1):
            val = 10000 + depth
        else:
            val = alpha_beta(new_board, depth-1, alpha, beta, False, start, limit)
        if val > best_val:
            best_val = val
            best_move = move
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best_val, best_move

def policy(board):
    board_np = np.array(board, dtype=np.int8)
    legal_moves = get_legal_moves(board_np, 1)
    if not legal_moves:
        # fallback (should not happen in a legal position)
        return "0,0:0,0"
    if len(legal_moves) == 1:
        move = legal_moves[0]
        return f"{move[0]},{move[1]}:{move[2]},{move[3]}"
    start = time.time()
    time_limit = 0.95
    best_move = legal_moves[0]
    for depth in range(1, 20):
        try:
            val, move = alpha_beta_search(board_np, depth, start, time_limit)
            if move is not None:
                best_move = move
        except TimeoutError:
            break
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
