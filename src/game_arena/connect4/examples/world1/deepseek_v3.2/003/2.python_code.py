
import numpy as np
import math
import random

def policy(board: list[list[int]]) -> int:
    """
    Connect 4 policy using minimax with alpha-beta pruning.
    Returns the column (0-6) to play in.
    """
    
    # Convert board to numpy array for easier manipulation
    board_arr = np.array(board)
    
    # Get player and opponent
    PLAYER = 1
    OPPONENT = -1
    
    # Precompute all possible winning lines (4 in a row)
    def get_winning_lines():
        lines = []
        # Horizontal
        for r in range(6):
            for c in range(4):
                lines.append([(r, c+i) for i in range(4)])
        # Vertical
        for c in range(7):
            for r in range(3):
                lines.append([(r+i, c) for i in range(4)])
        # Diagonal (down-right)
        for r in range(3):
            for c in range(4):
                lines.append([(r+i, c+i) for i in range(4)])
        # Diagonal (down-left)
        for r in range(3):
            for c in range(3, 7):
                lines.append([(r+i, c-i) for i in range(4)])
        return lines
    
    WINNING_LINES = get_winning_lines()
    
    def check_win(board_state, player):
        """Check if player has won"""
        for line in WINNING_LINES:
            if all(board_state[r][c] == player for r, c in line):
                return True
        return False
    
    def get_valid_moves(board_state):
        """Return list of non-full columns"""
        return [c for c in range(7) if board_state[0][c] == 0]
    
    def make_move(board_state, col, player):
        """Return new board after making move in column"""
        # Create copy
        new_board = board_state.copy()
        # Find first empty row from bottom
        for row in range(5, -1, -1):
            if new_board[row][col] == 0:
                new_board[row][col] = player
                return new_board
        return None  # Column full (shouldn't happen if valid move)
    
    def evaluate_position(board_state):
        """
        Evaluate the board position from player's perspective.
        Higher score is better for player.
        """
        score = 0
        
        # Center column preference
        center_col = 3
        center_count = sum(1 for r in range(6) if board_state[r][center_col] == PLAYER)
        score += center_count * 3
        
        # Check all winning lines
        for line in WINNING_LINES:
            player_count = sum(1 for r, c in line if board_state[r][c] == PLAYER)
            opponent_count = sum(1 for r, c in line if board_state[r][c] == OPPONENT)
            
            if opponent_count == 0:
                # Only player pieces or empty
                if player_count == 3:
                    score += 100  # Almost winning
                elif player_count == 2:
                    score += 10   # Two in a row
                elif player_count == 1:
                    score += 1    # Single piece
            elif player_count == 0:
                # Only opponent pieces or empty
                if opponent_count == 3:
                    score -= 80   # Block opponent's almost win
                elif opponent_count == 2:
                    score -= 8    # Opponent has two
                elif opponent_count == 1:
                    score -= 1    # Opponent single
        
        return score
    
    def minimax(board_state, depth, alpha, beta, maximizing_player):
        """
        Minimax with alpha-beta pruning.
        Returns evaluation score.
        """
        # Terminal state checks
        if check_win(board_state, PLAYER):
            return 10000
        if check_win(board_state, OPPONENT):
            return -10000
        
        valid_moves = get_valid_moves(board_state)
        if not valid_moves or depth == 0:
            return evaluate_position(board_state)
        
        if maximizing_player:
            max_eval = -math.inf
            for col in valid_moves:
                new_board = make_move(board_state, col, PLAYER)
                eval_score = minimax(new_board, depth-1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = math.inf
            for col in valid_moves:
                new_board = make_move(board_state, col, OPPONENT)
                eval_score = minimax(new_board, depth-1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    # First, check for immediate winning move
    valid_moves = get_valid_moves(board_arr)
    for col in valid_moves:
        new_board = make_move(board_arr, col, PLAYER)
        if check_win(new_board, PLAYER):
            return col
    
    # Then, check for immediate blocking move (opponent about to win)
    for col in valid_moves:
        new_board = make_move(board_arr, col, OPPONENT)
        if check_win(new_board, OPPONENT):
            return col
    
    # Use minimax with iterative deepening to use time efficiently
    best_move = None
    best_score = -math.inf
    
    # Try increasing depths until we run out of time (simplified)
    # We'll just use depth 5 which should complete in <1s
    depth = 5
    
    # Order moves by center preference for better pruning
    valid_moves.sort(key=lambda x: abs(x - 3))  # Center columns first
    
    for col in valid_moves:
        new_board = make_move(board_arr, col, PLAYER)
        score = minimax(new_board, depth-1, -math.inf, math.inf, False)
        
        if score > best_score:
            best_score = score
            best_move = col
    
    # If no move found (shouldn't happen), pick first valid move
    if best_move is None and valid_moves:
        best_move = valid_moves[0]
    
    return best_move
