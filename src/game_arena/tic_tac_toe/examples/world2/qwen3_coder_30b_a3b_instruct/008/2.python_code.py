
import numpy as np
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    """
    Returns the best move for player 1 (me) in a 4x4 Tic Tac Toe game.
    Uses minimax with alpha-beta pruning for optimal play.
    """
    def get_all_lines():
        """Get all possible winning lines (rows, columns, diagonals)"""
        lines = []
        
        # Rows
        for i in range(4):
            lines.append([(i, j) for j in range(4)])
        
        # Columns
        for j in range(4):
            lines.append([(i, j) for i in range(4)])
        
        # Main diagonal
        lines.append([(i, i) for i in range(4)])
        
        # Anti-diagonal
        lines.append([(i, 3-i) for i in range(4)])
        
        return lines
    
    def evaluate_position(board_state):
        """Evaluate the board state for player 1 (maximizing player)"""
        lines = get_all_lines()
        score = 0
        
        # Count potential winning lines
        for line in lines:
            values = [board_state[i][j] for i, j in line]
            player_count = values.count(1)
            opponent_count = values.count(-1)
            empty_count = values.count(0)
            
            # If I can win in this line
            if player_count == 3 and empty_count == 1:
                score += 1000
            # If opponent can win in this line
            elif opponent_count == 3 and empty_count == 1:
                score -= 1000
            
            # Prefer positions that create more winning opportunities
            elif player_count == 2 and empty_count == 2:
                score += 100
            elif player_count == 1 and empty_count == 3:
                score += 10
            
            # Opponent threats
            elif opponent_count == 2 and empty_count == 2:
                score -= 100
            elif opponent_count == 1 and empty_count == 3:
                score -= 10
                
        return score
    
    def minimax(board_state, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning"""
        
        # Check if game is over
        winner = check_winner(board_state)
        if winner == 1:
            return 10000 - depth
        elif winner == -1:
            return -10000 + depth
        elif is_board_full(board_state):
            return 0
        
        # If depth limit reached, use heuristic evaluation
        if depth == 0:
            return evaluate_position(board_state)
        
        if maximizing_player:
            max_eval = float('-inf')
            for i in range(4):
                for j in range(4):
                    if board_state[i][j] == 0:
                        board_state[i][j] = 1
                        eval_score = minimax(board_state, depth - 1, alpha, beta, False)
                        board_state[i][j] = 0
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(4):
                for j in range(4):
                    if board_state[i][j] == 0:
                        board_state[i][j] = -1
                        eval_score = minimax(board_state, depth - 1, alpha, beta, True)
                        board_state[i][j] = 0
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break
            return min_eval
    
    def check_winner(board_state):
        """Check if there's a winner"""
        lines = get_all_lines()
        
        for line in lines:
            values = [board_state[i][j] for i, j in line]
            if values == [1, 1, 1, 1]:
                return 1
            elif values == [-1, -1, -1, -1]:
                return -1
        return 0
    
    def is_board_full(board_state):
        """Check if the board is full"""
        for i in range(4):
            for j in range(4):
                if board_state[i][j] == 0:
                    return False
        return True
    
    # Strategy: prioritize center positions and look for winning/losing moves first
    # Try to find if there's a winning move for player 1
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = 1
                if check_winner(board) == 1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Try to block opponent winning moves
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                board[i][j] = -1
                if check_winner(board) == -1:
                    board[i][j] = 0
                    return (i, j)
                board[i][j] = 0
    
    # Find the best move using minimax with limited depth
    best_score = float('-inf')
    best_move = None
    
    # Try different depths to trade off between speed and accuracy
    for depth in [3, 2, 1]:
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    board[i][j] = 1
                    score = minimax(board, depth, float('-inf'), float('inf'), False)
                    board[i][j] = 0
                    
                    if score > best_score:
                        best_score = score
                        best_move = (i, j)
    
    # If no best move was found, just choose the first empty spot
    if best_move is None:
        for i in range(4):
            for j in range(4):
                if board[i][j] == 0:
                    return (i, j)
    
    return best_move
