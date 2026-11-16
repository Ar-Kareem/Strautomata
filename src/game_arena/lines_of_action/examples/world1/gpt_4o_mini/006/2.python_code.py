
import numpy as np

def policy(board) -> str:
    board = np.array(board)
    my_pieces = np.argwhere(board == 1)
    opponent_pieces = np.argwhere(board == -1)
    best_move = None
    best_score = -float('inf')
    
    def score_move(from_pos, to_pos):
        # Score calculation based on piece connectivity and control
        score = 0

        # Check connectivity after move
        new_board = board.copy()
        new_board[to_pos[0], to_pos[1]] = 1  # Place my piece
        new_board[from_pos[0], from_pos[1]] = 0  # Remove my piece
        
        my_connected = calculate_connected_pieces(new_board, 1)
        opponent_connected = calculate_connected_pieces(new_board, -1)
        
        # Score based on number of connected pieces
        score += my_connected - opponent_connected
        
        return score

    def calculate_connected_pieces(current_board, player):
        connected = 0
        seen = np.zeros((8, 8), dtype=bool)

        def dfs(row, col):
            if row < 0 or row >= 8 or col < 0 or col >= 8 or seen[row, col]:
                return 
            if current_board[row, col] != player:
                return
            
            seen[row, col] = True
            nonlocal connected
            connected += 1
            
            # Explore all 8 directions
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr != 0 or dc != 0:
                        dfs(row + dr, col + dc)

        for r in range(8):
            for c in range(8):
                if current_board[r, c] == player and not seen[r, c]:
                    connected = 0
                    dfs(r, c)

        return connected

    legal_moves = []

    # Generate legal moves for all my pieces
    for (r, c) in my_pieces:
        # Check all directions
        for dr in range(-7, 8):
            for dc in range(-7, 8):
                if abs(dr) == abs(dc) and dr != 0:  # Skip the diagonal terms
                    continue
                if dr == 0 and dc == 0:  # Skip the no move
                    continue

                distance = np.max(np.count_nonzero(board[r, :] == 1), 
                                  np.count_nonzero(board[:, c] == 1),
                                  np.count_nonzero(np.diag(board, c)) + np.count_nonzero(np.diag(np.fliplr(board), c)) )
                
                new_row, new_col = r + dr, c + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    if board[new_row][new_col] == 0 or board[new_row][new_col] == -1:
                        # Check jumping conditions (cannot jump over -1)
                        if can_move(r, c, new_row, new_col, board):
                            legal_moves.append(((r, c), (new_row, new_col)))

    # Evaluate legal moves and pick the best one
    for from_pos, to_pos in legal_moves:
        cur_score = score_move(from_pos, to_pos)
        if cur_score > best_score:
            best_score = cur_score
            best_move = (from_pos, to_pos)

    if best_move is None:
        raise ValueError("No legal moves available.")
    
    from_pos, to_pos = best_move
    return f"{from_pos[0]},{from_pos[1]}:{to_pos[0]},{to_pos[1]}"

def can_move(from_row, from_col, to_row, to_col, board):
    direction_row = np.sign(to_row - from_row)
    direction_col = np.sign(to_col - from_col)
    
    current_row = from_row + direction_row
    current_col = from_col + direction_col
    
    while (current_row != to_row or current_col != to_col):
        if board[current_row, current_col] == -1:
            return False
        current_row += direction_row
        current_col += direction_col
    
    return True
