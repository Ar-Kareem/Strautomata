
import math
import random
from typing import List, Tuple, Optional

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """
    Implements a minimax-based policy for 3D Tic Tac Toe.
    Returns the best move as a tuple of indices (i, j, k).
    """
    
    # Helper functions
    def get_empty_cells(board: List[List[List[int]]]) -> List[Tuple[int, int, int]]:
        """Returns a list of all empty cells on the board."""
        empty_cells = []
        for i in range(3):
            for j in range(3):
                for k in range(3):
                    if board[i][j][k] == 0:
                        empty_cells.append((i, j, k))
        return empty_cells
    
    def check_winner(board: List[List[List[int]]]) -> int:
        """
        Checks if there is a winner on the board.
        Returns 1 if player 1 wins, -1 if player -1 wins, 0 if no winner.
        """
        # Check all possible lines in 3D
        lines = []
        
        # Rows, columns, depths
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, k) for k in range(3)])
                lines.append([(i, k, j) for k in range(3)])
                lines.append([(k, i, j) for k in range(3)])
        
        # Face diagonals
        for i in range(3):
            lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
            lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
            lines.append([(0, i, 0), (1, i, 1), (2, i, 2)])
            lines.append([(0, i, 2), (1, i, 1), (2, i, 0)])
            lines.append([(0, 0, i), (1, 1, i), (2, 2, i)])
            lines.append([(0, 2, i), (1, 1, i), (2, 0, i)])
        
        # Space diagonals
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        for line in lines:
            values = [board[i][j][k] for i, j, k in line]
            if all(v == 1 for v in values):
                return 1
            elif all(v == -1 for v in values):
                return -1
        return 0
    
    def evaluate(board: List[List[List[int]]]) -> int:
        """
        Evaluates the board state.
        Returns a score: positive for player 1 advantage, negative for player -1.
        """
        score = 0
        
        # Check all possible lines
        lines = []
        
        # Rows, columns, depths
        for i in range(3):
            for j in range(3):
                lines.append([(i, j, k) for k in range(3)])
                lines.append([(i, k, j) for k in range(3)])
                lines.append([(k, i, j) for k in range(3)])
        
        # Face diagonals
        for i in range(3):
            lines.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
            lines.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
            lines.append([(0, i, 0), (1, i, 1), (2, i, 2)])
            lines.append([(0, i, 2), (1, i, 1), (2, i, 0)])
            lines.append([(0, 0, i), (1, 1, i), (2, 2, i)])
            lines.append([(0, 2, i), (1, 1, i), (2, 0, i)])
        
        # Space diagonals
        lines.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
        lines.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
        lines.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
        lines.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])
        
        for line in lines:
            values = [board[i][j][k] for i, j, k in line]
            player1_count = sum(1 for v in values if v == 1)
            player_minus1_count = sum(1 for v in values if v == -1)
            empty_count = sum(1 for v in values if v == 0)
            
            if player_minus1_count == 0:
                # Player 1 can potentially win this line
                if player1_count == 3:
                    score += 1000  # Win
                elif player1_count == 2:
                    score += 100   # One move to win
                elif player1_count == 1:
                    score += 10
            elif player1_count == 0:
                # Player -1 can potentially win this line
                if player_minus1_count == 3:
                    score -= 1000  # Lose
                elif player_minus1_count == 2:
                    score -= 100   # Block opponent's win
                elif player_minus1_count == 1:
                    score -= 10
        
        return score
    
    def minimax(board: List[List[List[int]]], depth: int, alpha: float, beta: float, is_maximizing: bool) -> Tuple[int, Optional[Tuple[int, int, int]]]:
        """
        Minimax algorithm with alpha-beta pruning.
        Returns (score, best_move).
        """
        winner = check_winner(board)
        if winner != 0:
            return winner * 1000, None
        
        empty_cells = get_empty_cells(board)
        if not empty_cells:
            return 0, None
        
        if depth == 0:
            return evaluate(board), None
        
        if is_maximizing:
            max_score = -math.inf
            best_move = None
            for i, j, k in empty_cells:
                board[i][j][k] = 1  # Player 1's move
                score, _ = minimax(board, depth - 1, alpha, beta, False)
                board[i][j][k] = 0  # Undo move
                if score > max_score:
                    max_score = score
                    best_move = (i, j, k)
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            return max_score, best_move
        else:
            min_score = math.inf
            best_move = None
            for i, j, k in empty_cells:
                board[i][j][k] = -1  # Player -1's move
                score, _ = minimax(board, depth - 1, alpha, beta, True)
                board[i][j][k] = 0  # Undo move
                if score < min_score:
                    min_score = score
                    best_move = (i, j, k)
                beta = min(beta, score)
                if beta <= alpha:
                    break
            return min_score, best_move
    
    # Get all empty cells
    empty_cells = get_empty_cells(board)
    
    if not empty_cells:
        # No moves available, return a random cell (should not happen in normal play)
        return (0, 0, 0)
    
    # If this is the first move, make a strategic choice
    if all(board[i][j][k] == 0 for i in range(3) for j in range(3) for k in range(3)):
        # First move: prefer center, then corners, then edges
        center = (1, 1, 1)
        corners = [(0, 0, 0), (0, 0, 2), (0, 2, 0), (0, 2, 2), 
                   (2, 0, 0), (2, 0, 2), (2, 2, 0), (2, 2, 2)]
        edges = [(0, 1, 1), (1, 0, 1), (1, 1, 0), (1, 1, 2), (1, 2, 1), (2, 1, 1)]
        
        if center in empty_cells:
            return center
        elif corners[0] in empty_cells:
            return corners[0]
        else:
            return random.choice(empty_cells)
    
    # Use minimax to find the best move
    # Depth can be adjusted based on performance requirements
    depth = 4  # Adjust depth as needed
    _, best_move = minimax(board, depth, -math.inf, math.inf, True)
    
    if best_move is not None:
        return best_move
    else:
        # Fallback to random move if minimax fails
        return random.choice(empty_cells)
