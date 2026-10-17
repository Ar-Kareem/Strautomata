
import numpy as np

def get_queen_moves(board, row, col, ignore_pos=None):
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 6:
            if board[r, c] == 0 or (ignore_pos and (r, c) == ignore_pos):
                moves.append((r, c))
            else:
                break
            r += dr
            c += dc
    return moves

def get_all_legal_moves(board, player):
    legal_moves = []
    amazon_positions = np.argwhere(board == player)
    for r_from, c_from in amazon_positions:
        to_positions = get_queen_moves(board, r_from, c_from)
        for r_to, c_to in to_positions:
            # Temporarily move amazon
            orig_val = board[r_from, c_from]
            board[r_from, c_from] = 0
            
            # Arrows can be shot from r_to, c_to
            # Note: the original square (r_from, c_from) is now empty and accessible
            arrow_positions = get_queen_moves(board, r_to, c_to)
            for r_arr, c_arr in arrow_positions:
                legal_moves.append(((r_from, c_from), (r_to, c_to), (r_arr, c_arr)))
            
            # Restore board
            board[r_from, c_from] = orig_val
    return legal_moves

def evaluate_mobility(board, player):
    opp = 3 - player
    my_moves = len(get_all_legal_moves(board, player))
    opp_moves = len(get_all_legal_moves(board, opp))
    return my_moves - opp_moves

def policy(board) -> str:
    # Ensure board is numpy array
    board = np.array(board)
    my_id = 1
    opp_id = 2
    
    legal_moves = get_all_legal_moves(board, my_id)
    if not legal_moves:
        return "" # Should not happen per rules

    best_score = -float('inf')
    best_move = legal_moves[0]
    
    # Simple heuristic: Maximize my moves while minimizing opponent moves
    # To save time, we sample a subset if there are too many moves, 
    # but on 6x6, we can usually check most.
    limit = 150 
    checked = 0
    
    for move in legal_moves:
        (f_r, f_c), (t_r, t_c), (a_r, a_c) = move
        
        # Apply move
        board[f_r, f_c] = 0
        board[t_r, t_c] = my_id
        board[a_r, a_c] = -1
        
        # Simple score: Mobility difference
        # We only look at local mobility around the change to speed up
        score = evaluate_mobility(board, my_id)
        
        if score > best_score:
            best_score = score
            best_move = move
            
        # Undo move
        board[a_r, a_c] = 0
        board[t_r, t_c] = 0
        board[f_r, f_c] = my_id
        
        checked += 1
        if checked > limit:
            break

    f, t, a = best_move
    return f"{f[0]},{f[1]}:{t[0]},{t[1]}:{a[0]},{a[1]}"
