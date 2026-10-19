
import numpy as np
from typing import List, Tuple, Optional

def policy(board: List[List[int]]) -> Tuple[int, int]:
    def evaluate_board(board_state: List[List[int]]) -> int:
        """Evaluate the board state. Positive for player 1 win, negative for player -1 win."""
        score = 0
        
        # Check rows
        for row in board_state:
            counts = [0, 0, 0]  # [empty, player1, player2]
            for cell in row:
                counts[cell + 1] += 1
            if counts[2] == 4:
                return 1000  # Player 1 wins
            elif counts[1] == 4:
                return -1000  # Player -1 wins
            elif counts[2] == 3 and counts[0] == 1:
                score += 10  # Player 1 can win
            elif counts[1] == 3 and counts[0] == 1:
                score -= 10  # Player -1 can win
        
        # Check columns
        for col in range(4):
            counts = [0, 0, 0]
            for row in range(4):
                cell = board_state[row][col]
                counts[cell + 1] += 1
            if counts[2] == 4:
                return 1000
            elif counts[1] == 4:
                return -1000
            elif counts[2] == 3 and counts[0] == 1:
                score += 10
            elif counts[1] == 3 and counts[0] == 1:
                score -= 10
        
        # Check main diagonals
        main_diag = [board_state[i][i] for i in range(4)]
        counts = [0, 0, 0]
        for cell in main_diag:
            counts[cell + 1] += 1
        if counts[2] == 4:
            return 1000
        elif counts[1] == 4:
            return -1000
        elif counts[2] == 3 and counts[0] == 1:
            score += 10
        elif counts[1] == 3 and counts[0] == 1:
            score -= 10
            
        anti_diag = [board_state[i][3-i] for i in range(4)]
        counts = [0, 0, 0]
        for cell in anti_diag:
            counts[cell + 1] += 1
        if counts[2] == 4:
            return 1000
        elif counts[1] == 4:
            return -1000
        elif counts[2] == 3 and counts[0] == 1:
            score += 10
        elif counts[1] == 3 and counts[0] == 1:
            score -= 10
            
        return score
    
    def minimax(board_state: List[List[int]], depth: int, alpha: float, beta: float, is_maximizing: bool) -> int:
        """Minimax algorithm with alpha-beta pruning."""
        # Check if terminal state
        eval_score = evaluate_board(board_state)
        if eval_score == 1000 or eval_score == -1000 or depth == 0:
            return eval_score
        
        if is_maximizing:
            max_eval = float('-inf')
            for i in range(4):
                for j in range(4):
                    if board_state[i][j] == 0:
                        board_state[i][j] = 1  # Make move
                        eval_score = minimax(board_state, depth - 1, alpha, beta, False)
                        board_state[i][j] = 0  # Undo move
                        max_eval = max(max_eval, eval_score)
                        alpha = max(alpha, eval_score)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
            return max_eval
        else:
            min_eval = float('inf')
            for i in range(4):
                for j in range(4):
                    if board_state[i][j] == 0:
                        board_state[i][j] = -1  # Make move
                        eval_score = minimax(board_state, depth - 1, alpha, beta, True)
                        board_state[i][j] = 0  # Undo move
                        min_eval = min(min_eval, eval_score)
                        beta = min(beta, eval_score)
                        if beta <= alpha:
                            break  # Alpha-beta pruning
            return min_eval
    
    # Find all empty positions
    empty_positions = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty_positions.append((i, j))
    
    if not empty_positions:
        return (0, 0)
    
    # Try all moves and find the best one
    best_score = float('-inf')
    best_move = empty_positions[0]
    
    for i, j in empty_positions:
        board[i][j] = 1  # Make the move
        score = minimax(board, 4, float('-inf'), float('inf'), False)  # Minimize opponent
        board[i][j] = 0  # Undo the move
        
        if score > best_score:
            best_score = score
            best_move = (i, j)
    
    return best_move
