
import numpy as np

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # Get empty cells
    empty_cells = np.argwhere(board == 0)
    
    # If no empty cells, return (0,0,0) - should not happen in valid games
    if len(empty_cells) == 0:
        return (0, 0, 0)
    
    # Helper function to check if a move wins the game
    def is_winning_move(board, pos, player):
        i, j, k = pos
        # Create a copy and make the move
        test_board = board.copy()
        test_board[i, j, k] = player
        
        # Check all possible winning lines through this position
        # 1D lines (along each axis)
        if np.all(test_board[i, :, k] == player) or \
           np.all(test_board[i, j, :] == player) or \
           np.all(test_board[:, j, k] == player):
            return True
        
        # 2D diagonals in each plane
        # xy plane
        if i == j and np.all(np.diag(test_board[:, :, k]) == player):
            return True
        if i + j == 2 and np.all(np.diag(np.fliplr(test_board[:, :, k])) == player):
            return True
        
        # xz plane
        if i == k and np.all(np.diag(test_board[:, j, :]) == player):
            return True
        if i + k == 2 and np.all(np.diag(np.fliplr(test_board[:, j, :])) == player):
            return True
        
        # yz plane
        if j == k and np.all(np.diag(test_board[i, :, :]) == player):
            return True
        if j + k == 2 and np.all(np.diag(np.fliplr(test_board[i, :, :])) == player):
            return True
        
        # 3D diagonals
        if i == j == k and np.all(np.diag(test_board) == player):
            return True
        if i == j and j + k == 2 and np.all(np.diag(np.flip(test_board, axis=2)) == player):
            return True
        if i == k and i + j == 2 and np.all(np.diag(np.flip(test_board, axis=1)) == player):
            return True
        if j == k and i + j == 2 and np.all(np.diag(np.flip(test_board, axis=0)) == player):
            return True
        if i + j == 2 and j + k == 2 and i + k == 2:
            # Check the other 3D diagonal
            diag = [test_board[0, 2, 2], test_board[1, 1, 1], test_board[2, 0, 0]]
            if all(x == player for x in diag):
                return True
        
        return False
    
    # Check for immediate winning moves
    for pos in empty_cells:
        if is_winning_move(board, pos, 1):
            return tuple(pos)
    
    # Check for blocking opponent's winning moves
    for pos in empty_cells:
        if is_winning_move(board, pos, -1):
            return tuple(pos)
    
    # If no immediate threats or wins, evaluate positions
    best_score = -1
    best_pos = tuple(empty_cells[0])
    
    for pos in empty_cells:
        i, j, k = pos
        score = 0
        
        # Center priority
        if (i, j, k) == (1, 1, 1):
            score += 10
        # Corner priority
        elif (i in [0, 2] and j in [0, 2] and k in [0, 2]):
            score += 5
        # Edge but not corner
        elif sum([x in [0, 2] for x in [i, j, k]]) == 2:
            score += 3
        # Face center but not edge
        elif sum([x in [0, 2] for x in [i, j, k]]) == 1:
            score += 2
        
        # Evaluate potential winning lines
        # Check lines through this position
        lines = []
        
        # 1D lines
        lines.append(board[i, :, k])  # y-axis line
        lines.append(board[i, j, :])  # z-axis line
        lines.append(board[:, j, k])  # x-axis line
        
        # 2D diagonals
        if i == j:
            lines.append(np.diag(board[:, :, k]))
        if i + j == 2:
            lines.append(np.diag(np.fliplr(board[:, :, k])))
        
        if i == k:
            lines.append(np.diag(board[:, j, :]))
        if i + k == 2:
            lines.append(np.diag(np.fliplr(board[:, j, :])))
        
        if j == k:
            lines.append(np.diag(board[i, :, :]))
        if j + k == 2:
            lines.append(np.diag(np.fliplr(board[i, :, :])))
        
        # 3D diagonals
        if i == j == k:
            lines.append(np.diag(board))
        if i == j and j + k == 2:
            lines.append(np.diag(np.flip(board, axis=2)))
        if i == k and i + j == 2:
            lines.append(np.diag(np.flip(board, axis=1)))
        if j == k and i + j == 2:
            lines.append(np.diag(np.flip(board, axis=0)))
        if i + j == 2 and j + k == 2 and i + k == 2:
            diag = [board[0, 2, 2], board[1, 1, 1], board[2, 0, 0]]
            lines.append(np.array(diag))
        
        # Score based on potential
        for line in lines:
            if -1 not in line:  # No opponent pieces
                score += np.sum(line) * 2  # More of our pieces = better
            elif 1 not in line:  # Only opponent pieces
                score += 1  # Block potential threats
        
        if score > best_score:
            best_score = score
            best_pos = tuple(pos)
    
    return best_pos
