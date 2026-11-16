
import numpy as np
from collections import deque

def policy(board):
    """Main policy function that selects a move for Lines of Action"""
    
    def get_all_pieces(board, player):
        """Get all pieces of a specified player"""
        pieces = []
        for i in range(8):
            for j in range(8):
                if board[i][j] == player:
                    pieces.append((i, j))
        return pieces
    
    def is_valid_position(row, col):
        """Check if position is within board"""
        return 0 <= row < 8 and 0 <= col < 8
    
    def get_line_info(board, from_row, from_col, to_row, to_col):
        """Get information about the line of movement"""
        # Determine direction
        dr = to_row - from_row
        dc = to_col - from_col
        
        # Normalize direction
        if dr != 0:
            dr = dr // abs(dr)
        if dc != 0:
            dc = dc // abs(dc)
            
        # Count pieces in the line (including both players)
        pieces_in_line = 0
        current_row, current_col = from_row, from_col
        
        # We need to check if the move is valid and count pieces
        # First check if move is diagonal/horizontal/vertical
        if dr == 0 and dc != 0:  # horizontal
            # Check line of pieces in the horizontal direction
            line_positions = []
            check_row = from_row
            range_start = min(from_col, to_col)
            range_end = max(from_col, to_col) + 1
            for col in range(range_start, range_end):
                line_positions.append((check_row, col))
                if board[check_row][col] != 0:
                    pieces_in_line += 1
                    
        elif dr != 0 and dc == 0:  # vertical
            # Check line of pieces in the vertical direction
            line_positions = []
            check_col = from_col
            range_start = min(from_row, to_row)
            range_end = max(from_row, to_row) + 1
            for row in range(range_start, range_end):
                line_positions.append((row, check_col))
                if board[row][check_col] != 0:
                    pieces_in_line += 1
                    
        elif dr != 0 and dc != 0:  # diagonal
            line_positions = []
            # Determine direction
            dr = 1 if to_row > from_row else -1
            dc = 1 if to_col > from_col else -1
            
            # Collect all positions in the diagonal line
            current_row, current_col = from_row, from_col
            line_positions = []
            while current_row != to_row:
                line_positions.append((current_row, current_col))
                current_row += dr
                current_col += dc
            line_positions.append((to_row, to_col))
            
            # Count pieces
            pieces_in_line = 0
            for row, col in line_positions:
                if board[row][col] != 0:
                    pieces_in_line += 1
                    
        else:  # not diagonal, horizontal, or vertical
            return False, 0, []
            
        # Check if move length matches piece count
        move_length = abs(to_row - from_row) + abs(to_col - from_col)
        
        # If move is diagonal, check that it's diagonal
        if abs(to_row - from_row) != abs(to_col - from_col) and to_row != from_row and to_col != from_col:
            return False, 0, []
            
        if dr != 0 and dc != 0:  # diagonal
            if abs(to_row - from_row) != abs(to_col - from_col):
                return False, 0, []
            if abs(to_row - from_row) != pieces_in_line - 1:  # -1 because piece at from position counts as one of them
                return False, 0, []
                
        elif dr != 0 and dc == 0:  # vertical
            if abs(to_row - from_row) != pieces_in_line - 1:
                return False, 0, []
        elif dr == 0 and dc != 0:  # horizontal
            if abs(to_col - from_col) != pieces_in_line - 1:
                return False, 0, []
                
        return True, pieces_in_line, line_positions
    
    def is_move_legal(board, from_row, from_col, to_row, to_col):
        """Check if move is legal"""
        # Check if starting position has player's piece
        if board[from_row][from_col] != 1:
            return False
            
        # Check if ending position is valid
        if not is_valid_position(to_row, to_col):
            return False
            
        # Check if ending position is empty or has opponent's piece
        if board[to_row][to_col] == 1:  # Can't capture our own piece
            return False
            
        # Determine the line and check validity
        is_valid, piece_count, line_positions = get_line_info(board, from_row, from_col, to_row, to_col)
        if not is_valid:
            return False
            
        # Verify move length equals piece count
        # Must equal piece_count - 1 because we're counting the piece we're moving
        move_length = abs(to_row - from_row) + abs(to_col - from_col)
        if dr == 0 and dc == 0:
            return False
        if dr != 0 and dc != 0:
            if abs(to_row - from_row) != piece_count - 1:
                return False
        elif dr != 0 and dc == 0:
            if abs(to_row - from_row) != piece_count - 1:
                return False
        elif dr == 0 and dc != 0:
            if abs(to_col - from_col) != piece_count - 1:
                return False
                
        # Check for obstacles (we can jump over friendly pieces but not enemies)
        dr = to_row - from_row
        dc = to_col - from_col
        
        if dr != 0:
            dr = dr // abs(dr)
        if dc != 0:
            dc = dc // abs(dc)
            
        # Check if path is blocked by enemy pieces
        if dr != 0 or dc != 0:
            current_row, current_col = from_row + dr, from_col + dc
            while current_row != to_row or current_col != to_col:
                if board[current_row][current_col] == -1:  # Enemy piece blocks the path
                    return False
                current_row += dr
                current_col += dc
                
        return True
        
    def get_legal_moves(board):
        """Generate all legal moves for current player"""
        moves = []
        player_pieces = get_all_pieces(board, 1)
        
        # For simplicity, we will make a more efficient approach - 
        # try all possible moves from each piece
        for from_row, from_col in player_pieces:
            # Try moving in all 8 directions
            directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
            
            # Try all moves of different distances  
            for dr, dc in directions:
                for distance in range(1, 8):  # up to 8 units in any direction
                    to_row, to_col = from_row + dr * distance, from_col + dc * distance
                    
                    # Check if to position is valid
                    if not is_valid_position(to_row, to_col):
                        break
                        
                    # Check if move is legal
                    if is_move_legal(board, from_row, from_col, to_row, to_col):
                        moves.append((from_row, from_col, to_row, to_col))
                        
        return moves
    
    def evaluate_board(board):
        """Evaluate the current board position for the current player"""
        player_pieces = get_all_pieces(board, 1)
        
        # Basic heuristic scores
        score = 0
        
        # Score based on number of pieces
        score += len(player_pieces) * 10
        
        # Evaluate connectivity - check if low connectivity
        # We will use a simple connectivity measure
        connected_components = compute_connected_components(board, 1)
        if len(connected_components) > 1:
            # Multiple components, penetrate score
            score -= len(connected_components) * 50
        else:
            # Single component, reward
            score += 100
            
        # Additional heuristics
        # Center control, piece mobility, etc.
        for r, c in player_pieces:
            # Prefer center positions
            center_distance = abs(r - 3.5) + abs(c - 3.5)
            score += 5.0 / (center_distance + 1)
            
        return score
        
    def compute_connected_components(board, player):
        """Compute connected components for a given player"""
        visited = [[False] * 8 for _ in range(8)]
        components = []
        
        def bfs(start_r, start_c):
            component = []
            queue = deque([(start_r, start_c)])
            visited[start_r][start_c] = True
            directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
            
            while queue:
                r, c = queue.popleft()
                component.append((r, c))
                
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < 8 and 0 <= nc < 8 and 
                        not visited[nr][nc] and board[nr][nc] == player):
                        visited[nr][nc] = True
                        queue.append((nr, nc))
                        
            return component
        
        for r in range(8):
            for c in range(8):
                if board[r][c] == player and not visited[r][c]:
                    components.append(bfs(r, c))
                    
        return components
    
    def score_move(board, from_row, from_col, to_row, to_col):
        """Score a move based on various criteria"""
        # Make a copy of the board
        new_board = [row[:] for row in board]
        
        # Make the move on the temporary board
        new_board[to_row][to_col] = 1
        new_board[from_row][from_col] = 0
        
        score = 0
        
        # Capture bonus (attack opponent pieces)
        if board[to_row][to_col] == -1:
            score += 100
            
        # Connect bonus (if we're connecting pieces)
        # This check is a bit complex to do here without full board analysis,
        # but we'll go for a simple approximation
        
        # Mobility bonus (if we're creating more potential moves)
        # Just a simplified assessment
        
        # Simple center positioning bonus
        center_distance = abs(to_row - 3.5) + abs(to_col - 3.5)
        score += 5.0 / (center_distance + 1)
        
        # Connect better if we move towards grouping
        # Simple method: see if it connects to existing group
        player_pieces = get_all_pieces(board, 1)
        to_pos = (to_row, to_col)
        from_pos = (from_row, from_col)
        
        # Are we getting closer to other pieces?
        min_distance = float('inf')
        for r, c in player_pieces:
            if (r, c) != from_pos:
                dist = abs(r - to_row) + abs(c - to_col)
                min_distance = min(min_distance, dist)
        
        # Reward moves that reduce distance to others
        score += 10.0 / (min_distance + 1)
        
        return score

    # Get all legal moves
    legal_moves = get_legal_moves(board)
    
    if not legal_moves:
        # If no legal moves, try to find any move
        # This shouldn't happen in normal gameplay
        return "0,0:0,0"  # dummy
    
    # Choose the best move by scoring them
    best_move = None
    best_score = float('-inf')
    
    for from_row, from_col, to_row, to_col in legal_moves:
        # Each move is scored by how good it is from a strategic perspective
        score = score_move(board, from_row, from_col, to_row, to_col)
        
        # Add some randomness to avoid getting stuck in local minima for tie-breaks
        import random
        score += random.uniform(0, 0.1)
        
        if score > best_score:
            best_score = score
            best_move = (from_row, from_col, to_row, to_col)
    
    # Convert best move to required string format
    if best_move:
        return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
    else:
        # Fallback, should not happen if we have legal moves
        return "0,0:0,0"
