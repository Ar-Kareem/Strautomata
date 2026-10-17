
import numpy as np
from itertools import product

def policy(board):
    my_amazons = [(r,c) for r,c in product(range(6), range(6)) if board[r,c] == 1]
    best_move = None
    best_score = -float('inf')
    
    for amazon in my_amazons:
        moves = get_legal_moves(board, amazon)
        for move in moves:
            score = evaluate_move(board, amazon, move)
            if score > best_score:
                best_score = score
                best_move = move
    
    return format_move(best_move)

def get_legal_moves(board, amazon):
    moves = []
    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1),          (0,1),
                  (1,-1),  (1,0), (1,1)]
    
    # Get all possible amazon moves
    for dr, dc in directions:
        r, c = amazon[0] + dr, amazon[1] + dc
        while 0 <= r < 6 and 0 <= c < 6:
            if board[r,c] != 0:
                break
            # For each landing position, get possible arrow shots
            temp_board = board.copy()
            temp_board[amazon] = 0
            temp_board[r,c] = 1
            
            arrow_directions = directions.copy()
            for adr, adc in arrow_directions:
                ar, ac = r + adr, c + adc
                while 0 <= ar < 6 and 0 <= ac < 6:
                    if temp_board[ar,ac] != 0:
                        break
                    moves.append((amazon[0], amazon[1], r, c, ar, ac))
                    ar += adr
                    ac += adc
            r += dr
            c += dc
    
    return moves

def evaluate_move(board, amazon, move):
    from_r, from_c, to_r, to_c, arrow_r, arrow_c = move
    
    # Simulate the move
    new_board = board.copy()
    new_board[from_r, from_c] = 0
    new_board[to_r, to_c] = 1
    new_board[arrow_r, arrow_c] = -1
    
    # Mobility score
    my_mobility = sum(len(get_legal_moves(new_board, (r,c))) 
                     for r,c in product(range(6), range(6)) if new_board[r,c] == 1)
    
    # Opponent mobility
    opponent_amazons = [(r,c) for r,c in product(range(6), range(6)) if new_board[r,c] == 2]
    opponent_mobility = sum(len(get_legal_moves(new_board, (r,c))) 
                          for r,c in opponent_amazons)
    
    # Centrality
    centrality = (5 - abs(to_r - 2.5) - abs(to_c - 2.5)) * 2  # Max 5, min 1
    
    # Arrow effectiveness
    arrow_score = 0
    for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
        r, c = arrow_r + dr, arrow_c + dc
        while 0 <= r < 6 and 0 <= c < 6:
            if new_board[r,c] == 2:
                arrow_score += 3  # Threatening opponent amazon
                break
            if new_board[r,c] != 0:
                break
            r += dr
            c += dc
    
    # Combine scores with weights
    score = (my_mobility * 0.4 - opponent_mobility * 0.4 + 
             centrality * 0.1 + arrow_score * 0.1)
    
    return score

def format_move(move):
    from_r, from_c, to_r, to_c, arrow_r, arrow_c = move
    return f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
