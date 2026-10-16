
import numpy as np
import copy
from collections import deque

def policy(board) -> str:
    """Main policy function using minimax with alpha-beta pruning"""
    
    def get_all_amazon_positions(board, player):
        """Get all positions of player's amazons"""
        positions = []
        for i in range(6):
            for j in range(6):
                if board[i][j] == player:
                    positions.append((i, j))
        return positions
    
    def is_valid_position(row, col):
        """Check if position is within board bounds"""
        return 0 <= row < 6 and 0 <= col < 6
    
    def is_empty(board, row, col):
        """Check if square is empty (not blocked)"""
        if not is_valid_position(row, col):
            return False
        return board[row][col] == 0
    
    def is_blocked(board, row, col):
        """Check if square is blocked (amazon or arrow)"""
        if not is_valid_position(row, col):
            return True
        return board[row][col] != 0
    
    def get_path_points(from_row, from_col, to_row, to_col):
        """Get all squares on the path from (from_row, from_col) to (to_row, to_col)"""
        points = []
        row_diff = to_row - from_row
        col_diff = to_col - from_col
        
        # Determine direction
        row_dir = 0
        col_dir = 0
        if row_diff > 0:
            row_dir = 1
        elif row_diff < 0:
            row_dir = -1
        if col_diff > 0:
            col_dir = 1
        elif col_diff < 0:
            col_dir = -1
            
        # Walk along the path
        current_row, current_col = from_row + row_dir, from_col + col_dir
        while (current_row != to_row or current_col != to_col):
            points.append((current_row, current_col))
            current_row += row_dir
            current_col += col_dir
            
        return points
    
    def is_path_clear(board, from_row, from_col, to_row, to_col):
        """Check if path is clear for movement"""
        if from_row == to_row and from_col == to_col:
            return True
            
        path_points = get_path_points(from_row, from_col, to_row, to_col)
        for point in path_points:
            if is_blocked(board, point[0], point[1]):
                return False
        return True
    
    def get_reachable_squares(board, row, col):
        """Get all reachable squares for an amazon at (row, col)"""
        reachable = set()
        # Check all 8 directions
        directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
        
        for dr, dc in directions:
            # Move along direction until blocked
            r, c = row + dr, col + dc
            while is_valid_position(r, c) and not is_blocked(board, r, c):
                reachable.add((r, c))
                r += dr
                c += dc
                
        return reachable
    
    def get_all_legal_moves(board):
        """Get all legal moves for current player (1)"""
        legal_moves = []
        amazons = get_all_amazon_positions(board, 1)
        
        # For each amazon
        for amazon_row, amazon_col in amazons:
            # Get all reachable squares
            reachable = get_reachable_squares(board, amazon_row, amazon_col)
            
            # For each reachable square
            for to_row, to_col in reachable:
                # Create a temp board to simulate the move
                temp_board = copy.deepcopy(board)
                temp_board[amazon_row][amazon_col] = 0  # Remove amazon from old position
                temp_board[to_row][to_col] = 1  # Place amazon at new position
                
                # Get all squares reachable from new position
                reachable_from_new = get_reachable_squares(temp_board, to_row, to_col)
                
                # Consider each possible arrow shot
                for arrow_row, arrow_col in reachable_from_new:
                    # Check if arrow position is valid and empty
                    if temp_board[arrow_row][arrow_col] == 0:
                        # Create a final board state
                        final_board = copy.deepcopy(temp_board)
                        final_board[arrow_row][arrow_col] = -1  # Place arrow
                        
                        legal_moves.append({
                            'from': (amazon_row, amazon_col),
                            'to': (to_row, to_col),
                            'arrow': (arrow_row, arrow_col),
                            'board': final_board
                        })
        
        return legal_moves
    
    def evaluate_board(board):
        """Evaluate the board state for player 1 (maximizer)"""
        # Count available moves for each player
        player1_moves = len(get_all_legal_moves(board))
        
        # Get all player 1 positions
        player1_positions = get_all_amazon_positions(board, 1)
        
        # Get all player 2 positions  
        player2_positions = get_all_amazon_positions(board, 2)
        
        # Mobility - for each amazon, count reachable squares
        player1_mobility = 0
        for row, col in player1_positions:
            player1_mobility += len(get_reachable_squares(board, row, col))
            
        player2_mobility = 0
        for row, col in player2_positions:
            player2_mobility += len(get_reachable_squares(board, row, col))
            
        # Central position evaluation (heuristic for good positioning) 
        center_bonus = 0
        for row, col in player1_positions:
            # Bonus for being near center (3,3)
            dist_to_center = abs(row - 3) + abs(col - 3)
            center_bonus += max(0, 3 - dist_to_center)
            
        # Overall evaluation
        # Enemy mobility is negative impact
        # Available moves is positive
        # Center bonus is positive
        # For a balanced evaluation we'll use these components
        score = (player1_moves - player2_moves) * 10 + \
                (player1_mobility - player2_mobility) * 2 + \
                center_bonus * 5
                
        # If no moves left, it's game over
        if player1_moves == 0:
            score = -10000  # Significant penalty for no moves
            
        return score
    
    def minimax(board, depth, alpha, beta, is_maximizing):
        """Minimax with alpha-beta pruning"""
        if depth == 0:
            return evaluate_board(board), None
            
        legal_moves = get_all_legal_moves(board)
        
        if not legal_moves:
            # No moves left
            if is_maximizing:
                return -10000, None  # Player 1 loses
            else:
                return 10000, None   # Player 2 loses
                
        if is_maximizing:
            max_eval = float('-inf')
            best_move = None
            for move in legal_moves:
                eval_score, _ = minimax(move['board'], depth - 1, alpha, beta, False)
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            best_move = None
            for move in legal_moves:
                eval_score, _ = minimax(move['board'], depth - 1, alpha, beta, True)
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move
    
    # Generate and evaluate all moves
    legal_moves = get_all_legal_moves(board)
    if not legal_moves:
        # This shouldn't happen according to the rules, but be safe
        return "0,0:0,0:0,0"
    
    # If we only have a few moves, just return one
    if len(legal_moves) <= 4:
        # Do minimax with depth 2 for fewer moves
        _, best_move = minimax(board, 2, float('-inf'), float('inf'), True)
    else:
        # Do minimax with depth 3 for more moves
        _, best_move = minimax(board, 3, float('-inf'), float('inf'), True)
    
    # If no best move selected, just return first available
    if not best_move:
        best_move = legal_moves[0]
    
    # Format move string
    move_str = f"{best_move['from'][0]},{best_move['from'][1]}:" \
               f"{best_move['to'][0]},{best_move['to'][1]}:" \
               f"{best_move['arrow'][0]},{best_move['arrow'][1]}"
    
    return move_str
