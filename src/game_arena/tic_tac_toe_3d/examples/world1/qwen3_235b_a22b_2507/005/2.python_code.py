
import numpy as np
from typing import List, Tuple

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Convert to numpy array for easier manipulation
    board_np = np.array(board, dtype=int)
    
    # Get all possible moves (empty cells)
    empty_cells = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board_np[i, j, k] == 0:
                    empty_cells.append((i, j, k))
    
    # If only one move available, take it
    if len(empty_cells) == 1:
        return empty_cells[0]
    
    # Define a function to check if a player has won
    def check_win(b, player):
        # Check all possible winning lines in 3D
        for i in range(3):
            for j in range(3):
                # Check lines along the third dimension
                if np.all(b[i, j, :] == player):
                    return True
                # Check lines along the second dimension
                if np.all(b[i, :, j] == player):
                    return True
                # Check lines along the first dimension
                if np.all(b[:, i, j] == player):
                    return True
        
        # Check face diagonals
        for i in range(3):
            # Diagonals on each face perpendicular to first axis
            if b[i, 0, 0] == b[i, 1, 1] == b[i, 2, 2] == player:
                return True
            if b[i, 0, 2] == b[i, 1, 1] == b[i, 2, 0] == player:
                return True
            # Diagonals on each face perpendicular to second axis
            if b[0, i, 0] == b[1, i, 1] == b[2, i, 2] == player:
                return True
            if b[2, i, 0] == b[1, i, 1] == b[0, i, 2] == player:
                return True
            # Diagonals on each face perpendicular to third axis
            if b[0, 0, i] == b[1, 1, i] == b[2, 2, i] == player:
                return True
            if b[2, 0, i] == b[1, 1, i] == b[0, 2, i] == player:
                return True
        
        # Check space diagonals
        if b[0, 0, 0] == b[1, 1, 1] == b[2, 2, 2] == player:
            return True
        if b[0, 0, 2] == b[1, 1, 1] == b[2, 2, 0] == player:
            return True
        if b[0, 2, 0] == b[1, 1, 1] == b[2, 0, 2] == player:
            return True
        if b[0, 2, 2] == b[1, 1, 1] == b[2, 0, 0] == player:
            return True
        
        return False
    
    # Evaluate the board position
    def evaluate(b):
        if check_win(b, 1):  # AI wins
            return 1000
        if check_win(b, -1):  # Opponent wins
            return -1000
        
        score = 0
        
        # Count all lines (rows, columns, diagonals) and score based on potential
        lines = []
        
        # Add all lines along the three main axes
        for i in range(3):
            for j in range(3):
                lines.append(b[i, j, :])  # along k-axis
                lines.append(b[i, :, j])  # along j-axis
                lines.append(b[:, i, j])  # along i-axis
        
        # Add face diagonals
        for i in range(3):
            lines.append(np.array([b[i, 0, 0], b[i, 1, 1], b[i, 2, 2]]))
            lines.append(np.array([b[i, 0, 2], b[i, 1, 1], b[i, 2, 0]]))
            lines.append(np.array([b[0, i, 0], b[1, i, 1], b[2, i, 2]]))
            lines.append(np.array([b[2, i, 0], b[1, i, 1], b[0, i, 2]]))
            lines.append(np.array([b[0, 0, i], b[1, 1, i], b[2, 2, i]]))
            lines.append(np.array([b[2, 0, i], b[1, 1, i], b[0, 2, i]]))
        
        # Add space diagonals
        lines.append(np.array([b[0, 0, 0], b[1, 1, 1], b[2, 2, 2]]))
        lines.append(np.array([b[0, 0, 2], b[1, 1, 1], b[2, 2, 0]]))
        lines.append(np.array([b[0, 2, 0], b[1, 1, 1], b[2, 0, 2]]))
        lines.append(np.array([b[0, 2, 2], b[1, 1, 1], b[2, 0, 0]]))
        
        for line in lines:
            ai_count = np.sum(line == 1)
            opp_count = np.sum(line == -1)
            empty_count = np.sum(line == 0)
            
            if ai_count > 0 and opp_count == 0:
                # Potential for AI to win this line
                if ai_count == 2:
                    score += 10  # Very valuable - one move from winning
                else:
                    score += 1
            elif opp_count > 0 and ai_count == 0:
                # Opponent could win this line
                if opp_count == 2:
                    score -= 10  # Must block this
                else:
                    score -= 1
        
        return score
    
    # Minimax with alpha-beta pruning
    def minimax(b, depth, alpha, beta, maximizing_player):
        # Check for terminal states
        if check_win(b, 1):
            return 1000 - depth  # Win (prefer faster wins)
        if check_win(b, -1):
            return -1000 + depth  # Loss (prefer slower losses)
        if depth == 0 or len(np.where(b == 0)[0]) == 0:
            return evaluate(b)
        
        if maximizing_player:
            max_eval = float('-inf')
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if b[i, j, k] == 0:
                            b[i, j, k] = 1  # Place AI piece
                            eval_score = minimax(b, depth - 1, alpha, beta, False)
                            b[i, j, k] = 0  # Undo move
                            max_eval = max(max_eval, eval_score)
                            alpha = max(alpha, eval_score)
                            if beta <= alpha:
                                break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(3):
                for j in range(3):
                    for k in range(3):
                        if b[i, j, k] == 0:
                            b[i, j, k] = -1  # Place opponent piece
                            eval_score = minimax(b, depth - 1, alpha, beta, True)
                            b[i, j, k] = 0  # Undo move
                            min_eval = min(min_eval, eval_score)
                            beta = min(beta, eval_score)
                            if beta <= alpha:
                                break
            return min_eval
    
    # Find the best move using minimax
    best_score = float('-inf')
    best_move = empty_cells[0]  # Default to first available move
    
    # Depth limit based on number of empty cells
    empty_count = len(empty_cells)
    if empty_count >= 15:
        depth = 4  # Early game - shallower search
    elif empty_count >= 10:
        depth = 6  # Mid game - deeper search
    else:
        depth = 8  # End game - search as deep as possible
    
    for move in empty_cells:
        i, j, k = move
        board_np[i, j, k] = 1  # Place AI piece
        score = minimax(board_np, depth, float('-inf'), float('inf'), False)
        board_np[i, j, k] = 0  # Undo move
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move
