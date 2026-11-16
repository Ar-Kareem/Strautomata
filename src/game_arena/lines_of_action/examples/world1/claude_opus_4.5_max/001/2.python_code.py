
import numpy as np
from collections import deque
import time

def policy(board) -> str:
    start_time = time.time()
    board = np.array(board)
    moves = get_legal_moves(board, 1)
    
    if not moves:
        return "0,0:0,0"
    
    for move in moves:
        new_board = make_move(board, move)
        if count_groups(new_board, 1) == 1:
            return format_move(move)
    
    best_move = moves[0]
    best_score = float('-inf')
    
    for move in moves:
        if time.time() - start_time > 0.8:
            break
        new_board = make_move(board, move)
        if count_groups(new_board, -1) == 1:
            continue
        
        opp_moves = get_legal_moves(new_board, -1)
        if not opp_moves:
            score = evaluate_position(new_board)
        else:
            worst_score = float('inf')
            for opp_move in opp_moves:
                if time.time() - start_time > 0.8:
                    worst_score = evaluate_position(new_board)
                    break
                opp_board = make_move(new_board, opp_move)
                if count_groups(opp_board, -1) == 1:
                    worst_score = float('-inf')
                    break
                worst_score = min(worst_score, evaluate_position(opp_board))
            score = worst_score
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move)

def format_move(move):
    return f"{move[0]},{move[1]}:{move[2]},{move[3]}"

def get_legal_moves(board, player):
    moves = []
    opponent = -player
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    for r in range(8):
        for c in range(8):
            if board[r,c] != player:
                continue
            for dr,dc in directions:
                count = count_pieces_in_line(board, r, c, dr, dc)
                nr, nc = r + dr*count, c + dc*count
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr,nc] != player:
                    if is_path_clear(board, r, c, nr, nc, dr, dc, opponent):
                        moves.append((r, c, nr, nc))
    return moves

def count_pieces_in_line(board, r, c, dr, dc):
    count = 0
    nr, nc = r, c
    while 0 <= nr < 8 and 0 <= nc < 8:
        if board[nr,nc] != 0:
            count += 1
        nr += dr
        nc += dc
    nr, nc = r - dr, c - dc
    while 0 <= nr < 8 and 0 <= nc < 8:
        if board[nr,nc] != 0:
            count += 1
        nr -= dr
        nc -= dc
    return count

def is_path_clear(board, r, c, nr, nc, dr, dc, blocking_player):
    cr, cc = r + dr, c + dc
    while (cr, cc) != (nr, nc):
        if board[cr,cc] == blocking_player:
            return False
        cr += dr
        cc += dc
    return True

def make_move(board, move):
    new_board = board.copy()
    r1, c1, r2, c2 = move
    new_board[r2,c2] = new_board[r1,c1]
    new_board[r1,c1] = 0
    return new_board

def count_groups(board, player):
    pieces = [(r,c) for r in range(8) for c in range(8) if board[r,c] == player]
    if len(pieces) <= 1:
        return len(pieces)
    visited = set()
    groups = 0
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    for start in pieces:
        if start in visited:
            continue
        groups += 1
        queue = deque([start])
        visited.add(start)
        while queue:
            pr, pc = queue.popleft()
            for dr,dc in directions:
                npr, npc = pr+dr, pc+dc
                if (npr,npc) not in visited and 0<=npr<8 and 0<=npc<8 and board[npr,npc]==player:
                    visited.add((npr,npc))
                    queue.append((npr,npc))
    return groups

def evaluate_position(board):
    my_pieces = [(r,c) for r in range(8) for c in range(8) if board[r,c] == 1]
    opp_pieces = [(r,c) for r in range(8) for c in range(8) if board[r,c] == -1]
    if not my_pieces:
        return float('-inf')
    
    my_groups = count_groups(board, 1)
    opp_groups = count_groups(board, -1)
    
    my_cr = sum(p[0] for p in my_pieces) / len(my_pieces)
    my_cc = sum(p[1] for p in my_pieces) / len(my_pieces)
    my_spread = sum((p[0]-my_cr)**2 + (p[1]-my_cc)**2 for p in my_pieces)
    
    opp_spread = 0
    if opp_pieces:
        opp_cr = sum(p[0] for p in opp_pieces) / len(opp_pieces)
        opp_cc = sum(p[1] for p in opp_pieces) / len(opp_pieces)
        opp_spread = sum((p[0]-opp_cr)**2 + (p[1]-opp_cc)**2 for p in opp_pieces)
    
    directions = [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]
    my_adj = sum(1 for r,c in my_pieces for dr,dc in directions 
                 if 0<=r+dr<8 and 0<=c+dc<8 and board[r+dr,c+dc]==1)
    opp_adj = sum(1 for r,c in opp_pieces for dr,dc in directions 
                  if 0<=r+dr<8 and 0<=c+dc<8 and board[r+dr,c+dc]==-1)
    
    return -10000*my_groups + 10000*opp_groups - 100*my_spread + 100*opp_spread + 500*my_adj - 500*opp_adj
