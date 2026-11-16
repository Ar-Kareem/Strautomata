
import math
from functools import lru_cache

# Precompute all 3-in-a-row lines in 3x3x3
def generate_lines():
    lines = []
    directions = []
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for dz in (-1, 0, 1):
                if dx == dy == dz == 0:
                    continue
                # avoid opposite duplicates: keep only "positive" dirs
                if (dx > 0) or (dx == 0 and dy > 0) or (dx == 0 and dy == 0 and dz > 0):
                    directions.append((dx, dy, dz))
    for x in range(3):
        for y in range(3):
            for z in range(3):
                for dx, dy, dz in directions:
                    x2, y2, z2 = x + 2*dx, y + 2*dy, z + 2*dz
                    if 0 <= x2 < 3 and 0 <= y2 < 3 and 0 <= z2 < 3:
                        line = [(x + t*dx, y + t*dy, z + t*dz) for t in range(3)]
                        lines.append(line)
    return lines

LINES = generate_lines()

# Move ordering: center, corners, edges
def ordered_moves(board):
    empties = [(i,j,k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    def priority(move):
        i,j,k = move
        # center highest
        if (i,j,k) == (1,1,1):
            return 0
        # corners
        if (i in (0,2) and j in (0,2) and k in (0,2)):
            return 1
        # edges
        return 2
    return sorted(empties, key=priority)

def check_win(board, player):
    for line in LINES:
        if sum(board[i][j][k] for i,j,k in line) == 3*player:
            return True
    return False

def evaluate(board):
    # Heuristic evaluation: count open lines
    score = 0
    for line in LINES:
        vals = [board[i][j][k] for i,j,k in line]
        if 1 in vals and -1 in vals:
            continue
        s = sum(vals)
        if s == 3:
            return 10000
        if s == -3:
            return -10000
        if s == 2:
            score += 50
        elif s == 1:
            score += 5
        elif s == -2:
            score -= 50
        elif s == -1:
            score -= 5
    return score

def board_to_tuple(board):
    return tuple(board[i][j][k] for i in range(3) for j in range(3) for k in range(3))

@lru_cache(maxsize=None)
def negamax(state, depth, alpha, beta, player):
    # state is tuple representation
    board = [[[0]*3 for _ in range(3)] for _ in range(3)]
    idx = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                board[i][j][k] = state[idx]
                idx += 1

    if check_win(board, 1):
        return 10000 * player
    if check_win(board, -1):
        return -10000 * player

    empties = [(i,j,k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    if depth == 0 or not empties:
        return evaluate(board) * player

    best = -math.inf
    for move in ordered_moves(board):
        i,j,k = move
        board[i][j][k] = player
        val = -negamax(board_to_tuple(board), depth-1, -beta, -alpha, -player)
        board[i][j][k] = 0
        if val > best:
            best = val
        alpha = max(alpha, val)
        if alpha >= beta:
            break
    return best

def policy(board):
    # 1. Immediate win
    for i,j,k in ordered_moves(board):
        board[i][j][k] = 1
        if check_win(board, 1):
            board[i][j][k] = 0
            return (i,j,k)
        board[i][j][k] = 0

    # 2. Block opponent's win
    for i,j,k in ordered_moves(board):
        board[i][j][k] = -1
        if check_win(board, -1):
            board[i][j][k] = 0
            return (i,j,k)
        board[i][j][k] = 0

    # 3. Minimax search
    empties = [(i,j,k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    n_empty = len(empties)
    if n_empty > 20:
        depth = 2
    elif n_empty > 14:
        depth = 3
    elif n_empty > 8:
        depth = 4
    else:
        depth = n_empty

    best_move = None
    best_val = -math.inf
    for move in ordered_moves(board):
        i,j,k = move
        board[i][j][k] = 1
        val = -negamax(board_to_tuple(board), depth-1, -math.inf, math.inf, -1)
        board[i][j][k] = 0
        if val > best_val:
            best_val = val
            best_move = move

    if best_move is None:
        # fallback: return first empty
        return empties[0] if empties else (0,0,0)
    return best_move
