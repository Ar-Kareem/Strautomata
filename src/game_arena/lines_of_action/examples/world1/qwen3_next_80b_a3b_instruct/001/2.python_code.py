
import numpy as np
from collections import deque

def policy(board):
    # Find all legal moves
    legal_moves = generate_legal_moves(board)
    
    if not legal_moves:
        # Should not happen in valid games, but return arbitrary move if forced
        return "0,0:0,1"
    
    # Evaluate each legal move using a heuristic function
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        # Parse move
        from_pos, to_pos = parse_move(move)
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Simulate the move
        new_board = simulate_move(board, from_row, from_col, to_row, to_col)
        
        # Evaluate the new board state
        score = evaluate_board(new_board, board, from_row, from_col, to_row, to_col)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move if best_move is not None else legal_moves[0]

def parse_move(move_str):
    parts = move_str.split(':')
    from_part = parts[0].split(',')
    to_part = parts[1].split(',')
    from_row, from_col = int(from_part[0]), int(from_part[1])
    to_row, to_col = int(to_part[0]), int(to_part[1])
    return (from_row, from_col), (to_row, to_col)

def simulate_move(board, from_row, from_col, to_row, to_col):
    # Create a deep copy of the board
    new_board = np.copy(board)
    # Remove piece from original position
    new_board[from_row, from_col] = 0
    # Place piece at new position
    new_board[to_row, to_col] = 1
    return new_board

def evaluate_board(board, old_board, from_row, from_col, to_row, to_col):
    # Heuristic evaluation function
    
    # Count total pieces (constant per turn, but changes after capture)
    total_pieces = np.sum(np.abs(board))
    
    # Calculate connectivity of our pieces (number of connected components)
    our_pieces = (board == 1)
    num_components = count_connected_components(our_pieces)
    
    # Calculate how many opponent pieces we captured
    old_total_ours = np.sum(old_board == 1)
    new_total_ours = np.sum(board == 1)
    # If our piece count didn't change, we didn't capture (or just moved)
    # But opponent piece count decreased? We captured!
    old_total_opponent = np.sum(old_board == -1)
    new_total_opponent = np.sum(board == -1)
    captures = old_total_opponent - new_total_opponent
    
    # Center control: reward pieces near center (indices 3,4)
    center_score = 0
    for r in range(8):
        for c in range(8):
            if board[r, c] == 1:
                # Distance to center (3.5, 3.5)
                dist = abs(r - 3.5) + abs(c - 3.5)  # Manhattan to center
                center_score += max(0, 4 - dist)  # Higher near center
    
    # Mobility: count our legal moves after this move
    our_mobility = len(generate_legal_moves(board))
    
    # Opponent mobility: simulate opponent's turn
    opponent_board = -board  # flip roles
    opponent_moves = generate_legal_moves(opponent_board)
    opponent_mobility = len(opponent_moves)
    
    # Evaluate improvement in connectivity (simpler: compare total connected components)
    # Lower is better for us
    connectivity_score = -num_components * 10  # negative because we want fewer components
    
    # Bonus for captures
    capture_score = captures * 50
    
    # Bonus for mobility advantage
    mobility_score = our_mobility - opponent_mobility  # we want higher than opponent
    
    # Combined score
    score = (
        capture_score +
        connectivity_score +
        center_score * 2 +
        mobility_score * 3
    )
    
    return score

def count_connected_components(piece_mask):
    """Count the number of connected components of True values in piece_mask (8-directional)"""
    if not np.any(piece_mask):
        return 0
    
    visited = np.zeros_like(piece_mask, dtype=bool)
    components = 0
    rows, cols = piece_mask.shape
    
    def bfs(start_r, start_c):
        queue = deque([(start_r, start_c)])
        visited[start_r, start_c] = True
        directions = [(dr, dc) for dr in (-1,0,1) for dc in (-1,0,1) if not (dr==0 and dc==0)]
        
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if (0 <= nr < rows and 0 <= nc < cols and 
                    piece_mask[nr, nc] and not visited[nr, nc]):
                    visited[nr, nc] = True
                    queue.append((nr, nc))
    
    for r in range(rows):
        for c in range(cols):
            if piece_mask[r, c] and not visited[r, c]:
                components += 1
                bfs(r, c)
    
    return components

def generate_legal_moves(board):
    moves = []
    rows, cols = board.shape
    total_pieces = np.sum(np.abs(board))
    
    for from_row in range(rows):
        for from_col in range(cols):
            if board[from_row, from_col] == 1:  # Our piece
                # Check all 8 directions
                directions = [(dr, dc) for dr in (-1,0,1) for dc in (-1,0,1) if not (dr==0 and dc==0)]
                
                for dr, dc in directions:
                    # Try to move exactly 'total_pieces' squares in this direction
                    to_row = from_row + dr * total_pieces
                    to_col = from_col + dc * total_pieces
                    
                    # Check bounds
                    if to_row < 0 or to_row >= rows or to_col < 0 or to_col >= cols:
                        continue
                    
                    # Check if we can move along the path: can jump over friendly, not enemy
                    blocked = False
                    # Check the intermediate squares (we hop over pieces)
                    # We move exactly total_pieces steps
                    # We need to verify that we don't jump over an enemy piece in between
                    for step in range(1, total_pieces + 1):
                        intermediate_row = from_row + dr * step
                        intermediate_col = from_col + dc * step
                        
                        # If we step on an enemy piece before the end, we can land on it (capture), but not jump over
                        # So we must check all intermediate squares until the last
                        if step < total_pieces:
                            # If we meet an enemy piece before destination, we can't jump over
                            if board[intermediate_row, intermediate_col] == -1:
                                blocked = True
                                break
                            # If we meet a friendly piece, that's fine
                        else:
                            # Last step: destination
                            if board[intermediate_row, intermediate_col] == 1:
                                # Cannot land on your own piece
                                blocked = True
                                break
                            # If it's -1 or 0, we can land (capture or move)
                    
                    if not blocked and (board[to_row, to_col] == 0 or board[to_row, to_col] == -1):
                        # Valid move
                        moves.append(f"{from_row},{from_col}:{to_row},{to_col}")
    
    return moves
