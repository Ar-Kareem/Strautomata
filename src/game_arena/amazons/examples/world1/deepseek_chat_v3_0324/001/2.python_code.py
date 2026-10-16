
import numpy as np

def policy(board):
    # Find all our amazons
    amazon_positions = np.argwhere(board == 1)
    
    best_move = None
    best_score = -float('inf')
    
    for amazon in amazon_positions:
        from_row, from_col = amazon
        # Generate all possible moves for this amazon
        for to_row, to_col in get_valid_moves(board, from_row, from_col):
            # Temporarily move the amazon to calculate arrow shots
            board[from_row, from_col] = 0
            board[to_row, to_col] = 1
            
            # Generate all possible arrow shots from new position
            for arrow_row, arrow_col in get_valid_moves(board, to_row, to_col):
                move_str = f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
                score = evaluate_move(board, from_row, from_col, to_row, to_col, arrow_row, arrow_col)
                
                if score > best_score or best_move is None:
                    best_score = score
                    best_move = move_str
            
            # Revert the board
            board[from_row, from_col] = 1
            board[to_row, to_col] = 0
    
    return best_move

def get_valid_moves(board, row, col):
    moves = []
    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1),          (0,1),
                  (1,-1),  (1,0), (1,1)]
    
    for dr, dc in directions:
        r, c = row + dr, col + dc
        while 0 <= r < 6 and 0 <= c < 6:
            if board[r, c] != 0:
                break
            moves.append((r, c))
            r += dr
            c += dc
    return moves

def evaluate_move(board, from_row, from_col, to_row, to_col, arrow_row, arrow_col):
    # Mobility score - how many squares does this move open/close
    mobility = 0
    
    # Central position bonus
    center_dist = abs(to_row - 2.5) + abs(to_col - 2.5)
    center_bonus = (5 - center_dist) * 0.5
    
    # Arrow impact - count how many opponent moves this blocks
    arrow_block = 0
    opponent_positions = np.argwhere(board == 2)
    for opp_row, opp_col in opponent_positions:
        # Check if arrow is between opponent and potential moves
        if (opp_row == arrow_row or opp_col == arrow_col or 
            abs(opp_row - arrow_row) == abs(opp_col - arrow_col)):
            arrow_block += 1
    
    # Total score
    return center_bonus + arrow_block * 0.3 + mobility * 0.1
