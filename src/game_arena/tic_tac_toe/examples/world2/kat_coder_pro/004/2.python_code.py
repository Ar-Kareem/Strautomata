
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Smart 4x4 Tic Tac Toe policy using minimax with alpha-beta pruning.
    
    Strategy:
    1. First check for immediate win opportunities
    2. Then check for blocking opponent's winning moves
    3. Use minimax with alpha-beta pruning for deeper lookahead
    4. Evaluate board positions using a heuristic that considers:
       - Lines of 3 with an empty spot (threats)
       - Lines of 2 with 2 empty spots (potential)
       - Center control preference
       - Mobility (number of available moves)
    """
    
    def get_empty_cells(board):
        """Get all empty cell positions."""
        empty_cells = []
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    empty_cells.append((i, j))
        return empty_cells
    
    def check_winner(board):
        """Check if there's a winner or if the game is a draw."""
        # Check rows, columns, and diagonals for 4 in a row
        for i in range(4):
            # Check rows
            if abs(sum(board[i])) == 4:
                return board[i][0]
            # Check columns
            if abs(sum(board[j][i] for j in range(4))) == 4:
                return board[0][i]
        
        # Check diagonals
        if abs(sum(board[i][i] for i in range(4))) == 4:
            return board[0][0]
        if abs(sum(board[i][3-i] for i in range(4))) == 4:
            return board[0][3]
        
        # Check for draw
        if not get_empty_cells(board):
            return 0
        
        return None
    
    def evaluate_board(board, depth):
        """Evaluate the board position."""
        score = 0
        
        # Check for immediate wins/losses
        winner = check_winner(board)
        if winner == 1:  # AI wins
            return 1000 + depth  # Prefer faster wins
        elif winner == -1:  # Opponent wins
            return -1000 - depth  # Prefer slower losses
        
        # Evaluate potential winning lines
        lines = []
        
        # Rows
        for i in range(4):
            lines.append([board[i][j] for j in range(4)])
        
        # Columns
        for j in range(4):
            lines.append([board[i][j] for i in range(4)])
        
        # Diagonals
        lines.append([board[i][i] for i in range(4)])
        lines.append([board[i][3-i] for i in range(4)])
        
        for line in lines:
            ai_count = sum(1 for x in line if x == 1)
            opp_count = sum(1 for x in line if x == -1)
            empty_count = sum(1 for x in line if x == 0)
            
            if opp_count == 0:  # No opponent pieces in this line
                if ai_count == 3:
                    score += 100  # Almost winning
                elif ai_count == 2:
                    score += 10   # Good potential
                elif ai_count == 1:
                    score += 1    # Some presence
            elif ai_count == 0:   # No AI pieces in this line
                if opp_count == 3:
                    score -= 50   # Block opponent's almost-win
                elif opp_count == 2:
                    score -= 5    # Opponent has potential
        
        # Center control bonus
        center_cells = [(1,1), (1,2), (2,1), (2,2)]
        for i, j in center_cells:
            if board[i][j] == 1:
                score += 2
            elif board[i][j] == -1:
                score -= 1
        
        # Mobility bonus (more empty cells nearby is better)
        ai_mobility = 0
        opp_mobility = 0
        for i in range(4):
            for j in range(4):
                if board[i][j] == 1:
                    for di, dj in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < 4 and 0 <= nj < 4 and board[ni][nj] == 0:
                            ai_mobility += 1
                elif board[i][j] == -1:
                    for di, dj in [(0,1), (1,0), (0,-1), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]:
                        ni, nj = i + di, j + dj
                        if 0 <= ni < 4 and 0 <= nj < 4 and board[ni][nj] == 0:
                            opp_mobility += 1
        
        score += (ai_mobility - opp_mobility) * 0.1
        
        return score
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        """Minimax algorithm with alpha-beta pruning."""
        winner = check_winner(board)
        if winner is not None:
            return evaluate_board(board, depth)
        
        if depth == 0:
            return evaluate_board(board, 0)
        
        empty_cells = get_empty_cells(board)
        
        if is_maximizing:
            max_eval = float('-inf')
            for i, j in empty_cells:
                board[i][j] = 1  # AI's move
                eval_score = minimax(board, depth - 1, alpha, beta, False)
                board[i][j] = 0  # Undo move
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for i, j in empty_cells:
                board[i][j] = -1  # Opponent's move
                eval_score = minimax(board, depth - 1, alpha, beta, True)
                board[i][j] = 0  # Undo move
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha-beta pruning
            return min_eval
    
    # First, check for immediate winning moves
    empty_cells = get_empty_cells(board)
    for i, j in empty_cells:
        board[i][j] = 1
        if check_winner(board) == 1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Then, check for blocking opponent's winning moves
    for i, j in empty_cells:
        board[i][j] = -1
        if check_winner(board) == -1:
            board[i][j] = 0
            return (i, j)
        board[i][j] = 0
    
    # Use minimax to find the best move
    # Limit depth based on remaining empty cells to stay within time constraints
    remaining_moves = len(empty_cells)
    if remaining_moves > 12:
        depth = 3
    elif remaining_moves > 8:
        depth = 4
    elif remaining_moves > 4:
        depth = 5
    else:
        depth = 6
    
    best_score = float('-inf')
    best_move = empty_cells[0]  # Default to first empty cell
    
    for i, j in empty_cells:
        board[i][j] = 1
        score = minimax(board, depth - 1, float('-inf'), float('inf'), False)
        board[i][j] = 0
        
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
