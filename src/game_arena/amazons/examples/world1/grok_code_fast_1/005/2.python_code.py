
import numpy as np
from collections import deque

def is_on_line(r1, c1, r2, c2):
    return r1 == r2 or c1 == c2 or abs(r1 - r2) == abs(c1 - c2)

def get_possible_moves(board, r, c):
    moves = []
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            nr, nc = r, c
            while True:
                nr += dr
                nc += dc
                if not (0 <= nr < 6 and 0 <= nc < 6):
                    break
                if board[nr, nc] != 0:
                    break
                moves.append((nr, nc))
    return moves

def get_reachable(board, r, c):
    reachable = set()
    visited = set()
    queue = deque([(r, c)])
    visited.add((r, c))
    while queue:
        cr, cc = queue.popleft()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < 6 and 0 <= nc < 6 and board[nr, nc] == 0 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    reachable.add((nr, nc))
                    queue.append((nr, nc))
    return reachable

def policy(board):
    my_pos = [(r, c) for r in range(6) for c in range(6) if board[r, c] == 1]
    opp_pos = [(r, c) for r in range(6) for c in range(6) if board[r, c] == 2]
    
    best_move = None
    best_score = float('-inf')
    
    for fr, fc in my_pos:
        for tr, tc in get_possible_moves(board, fr, fc):
            # Simulate move
            temp_board = board.copy()
            temp_board[fr, fc] = 0
            temp_board[tr, tc] = 1
            my_pos_after = [(tr, tc) if (pr, pc) == (fr, fc) else (pr, pc) for pr, pc in my_pos]
            
            for ar, ac in get_possible_moves(temp_board, tr, tc):
                # Simulate arrow
                temp_board[ar, ac] = -1
                
                # Compute scores
                my_score = sum(len(get_reachable(temp_board, r, c)) for r, c in my_pos_after)
                opp_score = sum(len(get_reachable(temp_board, r, c)) for r, c in opp_pos)
                score = my_score - opp_score
                
                if score > best_score:
                    best_score = score
                    best_move = (fr, fc, tr, tc, ar, ac)
                
                # Undo arrow
                temp_board[ar, ac] = 0
    
    if best_move is None:
        # No moves, but shouldn't happen; return arbitrary if forced
        my_arbitrary = my_pos[0]
        return f"{my_arbitrary[0]},{my_arbitrary[1]}:{my_arbitrary[0]},{my_arbitrary[1]}:{my_arbitrary[0]},{my_arbitrary[1]}"
    
    fr, fc, tr, tc, ar, ac = best_move
    return f"{fr},{fc}:{tr},{tc}:{ar},{ac}"
