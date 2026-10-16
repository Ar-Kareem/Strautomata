
import numpy as np

def valid_moves(board, row, col):
    moves = []
    piece_count = np.count_nonzero(board)
    
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    for d_row, d_col in directions:
        distance = 1
        while True:
            new_row = row + d_row * distance
            new_col = col + d_col * distance
            if new_row < 0 or new_row > 7 or new_col < 0 or new_col > 7:
                break
            
            if board[new_row][new_col] == 0:
                if distance == piece_count:
                    moves.append((new_row, new_col))
            elif board[new_row][new_col] == -1:
                if distance == piece_count:
                    moves.append((new_row, new_col))
                break
            else:
                break
            distance += 1
            
    return moves

def policy(board) -> str:
    best_move = None
    max_connection = -1
    
    my_pieces = np.argwhere(board == 1)
    
    for row, col in my_pieces:
        for new_row, new_col in valid_moves(board, row, col):
            # Create a copy of the board to simulate this move
            new_board = board.copy()
            new_board[new_row][new_col] = 1
            new_board[row][col] = 0
            
            # Calculate new connectivity
            connection_count = np.sum(new_board == 1)
            if connection_count > max_connection:
                max_connection = connection_count
                best_move = f"{row},{col}:{new_row},{new_col}"
                
    return best_move if best_move else "0,0:0,1"  # Fallback to a legal default move
