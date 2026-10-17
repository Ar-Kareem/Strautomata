
import numpy as np
from collections import deque

def policy(board):
    board = np.array(board)
    moves = get_legal_moves(board, 1)
    if not moves:
        return "0,0:0,0"
    
    best_move = moves[0]
    best_score = -float('inf')
    
    for move in moves:
        new_board = apply_move(board, move)
        score = minimax(new_board, 3, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

def get_legal_moves(board, player):
    moves = []
    pieces = list(zip(*np.where(board == player)))
    for r, c in pieces:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                # Count pieces in this line
                count = count_pieces_in_line(board, r, c, dr, dc)
                tr, tc = r + dr * count, c + dc * count
                if 0 <= tr < 8 and 0 <= tc < 8:
                    if board[tr][tc] != player:
                        # Check path for enemy pieces
                        if not blocked(board, r, c, dr, dc, count, player):
                            moves.append((r, c, tr, tc))
    return moves

def count_pieces_in_line(board, r, c, dr, dc):
    count = 0
    for sign in [1, -1]:
        nr, nc = r + sign * dr, c + sign * dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr][nc] != 0:
                count += 1
            nr += sign * dr
            nc += sign * dc
    # count the piece itself
    count += 1
    return count

def blocked(board, r, c, dr, dc, count, player):
    for i in range(1, count):
        nr, nc = r + dr * i, c + dc * i
        if board[nr][nc] == -player:
            return True
    return False

def apply_move(board, move):
    b = board.copy()
    r1, c1, r2, c2 = move
    b[r2][c2] = b[r1][c1]
    b[r1][c1] = 0
    return b

def evaluate(board):
    # Check wins
    if is_connected(board, 1):
        return 10000
    if is_connected(board, -1):
        return -10000
    return connectivity_score(board, 1) - connectivity_score(board, -1)

def connectivity_score(board, player):
    pieces = list(zip(*np.where(board == player)))
    if len(pieces) <= 1:
        return 1000
    # Negative of sum of distances to center of mass
    cr = np.mean([p[0] for p in pieces])
    cc = np.mean([p[1] for p in pieces])
    dist = sum(max(abs(p[0]-cr), abs(p[1]-cc)) for p in pieces)
    # Count adjacent pairs
    adj = 0
    pset = set(pieces)
    for r, c in pieces:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if (dr or dc) and (r+dr, c+dc) in pset:
                    adj += 1
    return -dist * 2 + adj * 3

def is_connected(board, player):
    pieces = list(zip(*np.where(board == player)))
    if len(pieces) <= 1:
        return True
    visited = set()
    q = deque([pieces[0]])
    visited.add(pieces[0])
    pset = set(pieces)
    while q:
        r, c = q.popleft()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr or dc:
                    n = (r+dr, c+dc)
                    if n in pset and n not in visited:
                        visited.add(n)
                        q.append(n)
    return len(visited) == len(pieces)

def minimax(board, depth, alpha, beta, maximizing):
    if depth == 0 or is_connected(board, 1) or is_connected(board, -1):
        return evaluate(board)
    
    player = 1 if maximizing else -1
    moves = get_legal_moves(board, player)
    
    if not moves:
        return evaluate(board)
    
    if maximizing:
        val = -float('inf')
        for move in moves:
            val = max(val, minimax(apply_move(board, move), depth-1, alpha, beta, False))
            alpha = max(alpha, val)
            if val >= beta:
                break
        return val
    else:
        val = float('inf')
        for move in moves:
            val = min(val, minimax(apply_move(board, move), depth-1, alpha, beta, True))
            beta = min(beta, val)
            if val <= alpha:
                break
        return val
