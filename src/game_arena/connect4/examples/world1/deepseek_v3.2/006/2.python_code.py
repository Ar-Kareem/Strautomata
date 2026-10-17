
import numpy as np
from typing import Optional, List

def policy(board: List[List[int]]) -> int:
    """
    Returns the best column to play in Connect 4.
    Uses minimax with alpha-beta pruning to depth 6.
    """
    
    # Convert to numpy array for easier manipulation
    board_array = np.array(board)
    
    # Define the Player class to track game state
    class Connect4:
        ROWS = 6
        COLS = 7
        WIN_LENGTH = 4
        
        def __init__(self, board):
            self.board = np.array(board)
            self.current_player = 1  # We're always player 1
        
        def get_valid_moves(self):
            """Return list of columns that are not full."""
            return [c for c in range(self.COLS) if self.board[0, c] == 0]
        
        def make_move(self, col, player):
            """Make a move in the given column for the given player.
            Returns new board state."""
            new_board = self.board.copy()
            # Find the lowest empty row in the column
            for row in range(self.ROWS-1, -1, -1):
                if new_board[row, col] == 0:
                    new_board[row, col] = player
                    break
            return new_board
        
        def is_terminal(self, board_state=None):
            """Check if game is over (win or board full)."""
            if board_state is None:
                board_state = self.board
            
            # Check for win
            if self.get_winner(board_state) != 0:
                return True
            
            # Check if board is full
            return np.all(board_state[0, :] != 0)
        
        def get_winner(self, board_state=None):
            """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
            if board_state is None:
                board_state = self.board
            
            # Check horizontal
            for r in range(self.ROWS):
                for c in range(self.COLS - self.WIN_LENGTH + 1):
                    segment = board_state[r, c:c+self.WIN_LENGTH]
                    if np.all(segment == 1):
                        return 1
                    if np.all(segment == -1):
                        return -1
            
            # Check vertical
            for r in range(self.ROWS - self.WIN_LENGTH + 1):
                for c in range(self.COLS):
                    segment = board_state[r:r+self.WIN_LENGTH, c]
                    if np.all(segment == 1):
                        return 1
                    if np.all(segment == -1):
                        return -1
            
            # Check diagonal (down-right)
            for r in range(self.ROWS - self.WIN_LENGTH + 1):
                for c in range(self.COLS - self.WIN_LENGTH + 1):
                    segment = [board_state[r+i, c+i] for i in range(self.WIN_LENGTH)]
                    if all(cell == 1 for cell in segment):
                        return 1
                    if all(cell == -1 for cell in segment):
                        return -1
            
            # Check diagonal (down-left)
            for r in range(self.ROWS - self.WIN_LENGTH + 1):
                for c in range(self.WIN_LENGTH - 1, self.COLS):
                    segment = [board_state[r+i, c-i] for i in range(self.WIN_LENGTH)]
                    if all(cell == 1 for cell in segment):
                        return 1
                    if all(cell == -1 for cell in segment):
                        return -1
            
            return 0
        
        def evaluate(self, board_state=None):
            """Heuristic evaluation of the board position.
            Positive is good for player 1, negative for player -1."""
            if board_state is None:
                board_state = self.board
            
            score = 0
            
            # Score all possible 4-in-a-row segments
            # Horizontal segments
            for r in range(self.ROWS):
                for c in range(self.COLS - self.WIN_LENGTH + 1):
                    segment = board_state[r, c:c+self.WIN_LENGTH]
                    score += self._score_segment(segment)
            
            # Vertical segments
            for r in range(self.ROWS - self.WIN_LENGTH + 1):
                for c in range(self.COLS):
                    segment = board_state[r:r+self.WIN_LENGTH, c]
                    score += self._score_segment(segment)
            
            # Diagonal (down-right)
            for r in range(self.ROWS - self.WIN_LENGTH + 1):
                for c in range(self.COLS - self.WIN_LENGTH + 1):
                    segment = [board_state[r+i, c+i] for i in range(self.WIN_LENGTH)]
                    score += self._score_segment(segment)
            
            # Diagonal (down-left)
            for r in range(self.ROWS - self.WIN_LENGTH + 1):
                for c in range(self.WIN_LENGTH - 1, self.COLS):
                    segment = [board_state[r+i, c-i] for i in range(self.WIN_LENGTH)]
                    score += self._score_segment(segment)
            
            # Center column preference
            center_col = self.COLS // 2
            for r in range(self.ROWS):
                if board_state[r, center_col] == 1:
                    score += 3
                elif board_state[r, center_col] == -1:
                    score -= 3
            
            return score
        
        def _score_segment(self, segment):
            """Score a single 4-cell segment."""
            player_count = np.sum(segment == 1)
            opponent_count = np.sum(segment == -1)
            
            # If segment contains both players' discs, it's worthless
            if player_count > 0 and opponent_count > 0:
                return 0
            
            # Exponential scoring for potential lines
            if player_count > 0:
                return player_count ** 3
            elif opponent_count > 0:
                return -(opponent_count ** 3)
            return 0
    
    # Create game instance
    game = Connect4(board_array)
    
    # First, check for immediate winning moves
    valid_moves = game.get_valid_moves()
    for col in valid_moves:
        new_board = game.make_move(col, 1)  # Try our move
        if game.get_winner(new_board) == 1:
            return col
    
    # Then, check for opponent's immediate winning moves (block them)
    for col in valid_moves:
        new_board = game.make_move(col, -1)  # Try opponent's move
        if game.get_winner(new_board) == -1:
            return col
    
    # Use minimax with alpha-beta pruning to find best move
    depth = 6  # Adjust based on time constraints
    
    def minimax(board_state, depth, alpha, beta, maximizing_player):
        """Minimax with alpha-beta pruning."""
        winner = game.get_winner(board_state)
        if winner != 0:
            return float('inf') if winner == 1 else float('-inf')
        
        if depth == 0 or game.is_terminal(board_state):
            # Create temporary game instance for evaluation
            temp_game = Connect4(board_state)
            return temp_game.evaluate(board_state)
        
        if maximizing_player:
            max_eval = float('-inf')
            for col in range(game.COLS):
                # Check if column is valid
                if board_state[0, col] == 0:
                    new_board = game.make_move(col, 1)
                    eval_score = minimax(new_board, depth-1, alpha, beta, False)
                    max_eval = max(max_eval, eval_score)
                    alpha = max(alpha, eval_score)
                    if beta <= alpha:
                        break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for col in range(game.COLS):
                # Check if column is valid
                if board_state[0, col] == 0:
                    new_board = game.make_move(col, -1)
                    eval_score = minimax(new_board, depth-1, alpha, beta, True)
                    min_eval = min(min_eval, eval_score)
                    beta = min(beta, eval_score)
                    if beta <= alpha:
                        break  # Alpha cutoff
            return min_eval
    
    # Find best move using minimax
    best_score = float('-inf')
    best_col = valid_moves[0]  # Default to first valid move
    
    for col in valid_moves:
        new_board = game.make_move(col, 1)
        move_score = minimax(new_board, depth-1, float('-inf'), float('inf'), False)
        
        if move_score > best_score:
            best_score = move_score
            best_col = col
    
    return best_col
