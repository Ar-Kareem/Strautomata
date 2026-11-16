
import numpy as np
import time

class Connect4AI:
    def __init__(self):
        self.rows = 6
        self.columns = 7
        self.window_length = 4
        
        # Scoring weights
        self.weights = {
            'three_in_a_row': 50,
            'two_in_a_row': 10,
            'one_in_a_row': 1,
            'center_column': 4,
            'block_three': 80,
            'win': 1000000,
        }
        
    def is_valid_location(self, board, col):
        return board[0][col] == 0
    
    def get_valid_locations(self, board):
        return [col for col in range(self.columns) if self.is_valid_location(board, col)]
    
    def get_next_open_row(self, board, col):
        for row in range(self.rows-1, -1, -1):
            if board[row][col] == 0:
                return row
        return None
    
    def drop_piece(self, board, row, col, piece):
        board[row][col] = piece
    
    def evaluate_window(self, window, piece):
        score = 0
        opp_piece = -piece
        
        if window.count(piece) == 4:
            score += self.weights['win']
        elif window.count(piece) == 3 and window.count(0) == 1:
            score += self.weights['three_in_a_row']
        elif window.count(piece) == 2 and window.count(0) == 2:
            score += self.weights['two_in_a_row']
        elif window.count(piece) == 1 and window.count(0) == 3:
            score += self.weights['one_in_a_row']
            
        if window.count(opp_piece) == 3 and window.count(0) == 1:
            score -= self.weights['block_three']
            
        return score
    
    def score_position(self, board, piece):
        score = 0
        
        # Score center column preference
        center_array = [row[3] for row in board]
        center_count = center_array.count(piece)
        score += center_count * self.weights['center_column']
        
        # Horizontal windows
        for row in range(self.rows):
            row_array = board[row]
            for col in range(self.columns - 3):
                window = row_array[col:col+self.window_length]
                score += self.evaluate_window(list(window), piece)
        
        # Vertical windows
        for col in range(self.columns):
            col_array = [board[row][col] for row in range(self.rows)]
            for row in range(self.rows - 3):
                window = col_array[row:row+self.window_length]
                score += self.evaluate_window(window, piece)
        
        # Positive diagonals
        for row in range(self.rows - 3):
            for col in range(self.columns - 3):
                window = [board[row+i][col+i] for i in range(self.window_length)]
                score += self.evaluate_window(window, piece)
        
        # Negative diagonals
        for row in range(self.rows - 3):
            for col in range(self.columns - 3):
                window = [board[row+3-i][col+i] for i in range(self.window_length)]
                score += self.evaluate_window(window, piece)
        
        return score
    
    def is_terminal_node(self, board):
        return self.winning_move(board, 1) or self.winning_move(board, -1) or len(self.get_valid_locations(board)) == 0
    
    def winning_move(self, board, piece):
        # Horizontal check
        for row in range(self.rows):
            for col in range(self.columns - 3):
                if board[row][col] == piece and board[row][col+1] == piece and board[row][col+2] == piece and board[row][col+3] == piece:
                    return True
        
        # Vertical check
        for row in range(self.rows - 3):
            for col in range(self.columns):
                if board[row][col] == piece and board[row+1][col] == piece and board[row+2][col] == piece and board[row+3][col] == piece:
                    return True
        
        # Positive diagonal
        for row in range(self.rows - 3):
            for col in range(self.columns - 3):
                if board[row][col] == piece and board[row+1][col+1] == piece and board[row+2][col+2] == piece and board[row+3][col+3] == piece:
                    return True
        
        # Negative diagonal
        for row in range(3, self.rows):
            for col in range(self.columns - 3):
                if board[row][col] == piece and board[row-1][col+1] == piece and board[row-2][col+2] == piece and board[row-3][col+3] == piece:
                    return True
        
        return False
    
    def minimax(self, board, depth, alpha, beta, maximizing_player):
        valid_locations = self.get_valid_locations(board)
        is_terminal = self.is_terminal_node(board)
        
        if depth == 0 or is_terminal:
            if is_terminal:
                if self.winning_move(board, 1):
                    return (None, self.weights['win'] + depth)
                elif self.winning_move(board, -1):
                    return (None, -self.weights['win'] - depth)
                else:
                    return (None, 0)
            else:
                return (None, self.score_position(board, 1))
        
        if maximizing_player:
            value = float('-inf')
            best_col = valid_locations[0] if valid_locations else None
            
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                temp_board = [row[:] for row in board]
                self.drop_piece(temp_board, row, col, 1)
                new_score = self.minimax(temp_board, depth-1, alpha, beta, False)[1]
                
                if new_score > value:
                    value = new_score
                    best_col = col
                
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            
            return best_col, value
        else:
            value = float('inf')
            best_col = valid_locations[0] if valid_locations else None
            
            for col in valid_locations:
                row = self.get_next_open_row(board, col)
                temp_board = [row[:] for row in board]
                self.drop_piece(temp_board, row, col, -1)
                new_score = self.minimax(temp_board, depth-1, alpha, beta, True)[1]
                
                if new_score < value:
                    value = new_score
                    best_col = col
                
                beta = min(beta, value)
                if alpha >= beta:
                    break
            
            return best_col, value
    
    def get_move(self, board, time_limit=0.95):
        start_time = time.time()
        
        # First, check for immediate winning moves
        valid_locations = self.get_valid_locations(board)
        for col in valid_locations:
            row = self.get_next_open_row(board, col)
            temp_board = [row[:] for row in board]
            self.drop_piece(temp_board, row, col, 1)
            if self.winning_move(temp_board, 1):
                return col
        
        # Check for opponent's immediate winning moves to block
        for col in valid_locations:
            row = self.get_next_open_row(board, col)
            temp_board = [row[:] for row in board]
            self.drop_piece(temp_board, row, col, -1)
            if self.winning_move(temp_board, -1):
                return col
        
        # Iterative deepening
        best_move = valid_locations[3] if 3 in valid_locations else valid_locations[len(valid_locations)//2]
        
        for depth in range(2, 10):
            if time.time() - start_time > time_limit * 0.7:
                break
            
            try:
                move, _ = self.minimax(board, depth, float('-inf'), float('inf'), True)
                if move is not None:
                    best_move = move
            except:
                pass
            
            if time.time() - start_time > time_limit * 0.7:
                break
        
        return best_move

# Global AI instance
_ai = Connect4AI()

def policy(board: list[list[int]]) -> int:
    """
    Returns the best column for the next move.
    """
    # Convert board to mutable list if needed
    board_copy = [list(row) for row in board]
    
    move = _ai.get_move(board_copy)
    
    # Fallback to center or first valid column
    if move is None or not _ai.is_valid_location(board_copy, move):
        valid_locations = _ai.get_valid_locations(board_copy)
        if valid_locations:
            if 3 in valid_locations:
                move = 3
            else:
                move = valid_locations[len(valid_locations)//2]
        else:
            move = 0
    
    return move
