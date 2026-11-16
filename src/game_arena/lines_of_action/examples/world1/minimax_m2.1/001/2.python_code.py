
import numpy as np
from collections import deque

def policy(board) -> str:
    """
    Lines of Action policy that returns the best move for the current player.
    Uses heuristics focusing on connectivity, center control, and strategic positioning.
    """
    board = np.array(board)
    player = 1
    opponent = -1
    
    # Generate all legal moves
    legal_moves = generate_legal_moves(board, player)
    
    if not legal_moves:
        # No legal moves available - return empty string or try to find any move
        return ""
    
    # Evaluate each move and select the best one
    best_move = None
    best_score = float('-inf')
    
    for move in legal_moves:
        score = evaluate_move(board, move, player, opponent)
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move

def generate_legal_moves(board, player):
    """
    Generate all legal moves for the given player.
    Returns list of tuples: ((from_row, from_col), (to_row, to_col))
    """
    legal_moves = []
    rows, cols = board.shape
    
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == player:
                # Check all 8 directions
                for direction in [(-1, -1), (-1, 0), (-1, 1), 
                                 (0, -1),           (0, 1),
                                 (1, -1),  (1, 0),  (1, 1)]:
                    moves = get_moves_in_direction(board, r, c, direction, player)
                    legal_moves.extend(moves)
    
    return legal_moves

def get_moves_in_direction(board, row, col, direction, player):
    """
    Get all legal moves in a specific direction from (row, col).
    """
    moves = []
    dr, dc = direction
    rows, cols = board.shape
    
    # Count pieces in the line of movement
    count = count_line_pieces(board, row, col, direction)
    
    if count == 0:
        return moves
    
    # Try to move exactly 'count' squares in the direction
    new_row, new_col = row + dr * count, col + dc * count
    
    # Check if the destination is within bounds
    if not (0 <= new_row < rows and 0 <= new_col < cols):
        return moves
    
    # Check if destination is empty or contains opponent piece
    if board[new_row, new_col] == player:
        return moves
    
    # Check if the path is clear (can jump over friendly pieces but not enemy pieces)
    if is_path_clear(board, row, col, new_row, new_col, direction, player):
        moves.append(((row, col), (new_row, new_col)))
    
    return moves

def count_line_pieces(board, row, col, direction):
    """
    Count the number of pieces in the line of movement (including the moving piece).
    """
    dr, dc = direction
    rows, cols = board.shape
    count = 0
    
    # Go backwards first to count pieces in the line
    r, c = row - dr, col - dc
    while 0 <= r < rows and 0 <= c < cols:
        if board[r, c] != 0:
            count += 1
        r -= dr
        c -= dc
    
    # Add the current piece
    count += 1
    
    # Go forwards to count remaining pieces in the line
    r, c = row + dr, col + dc
    while 0 <= r < rows and 0 <= c < cols:
        if board[r, c] != 0:
            count += 1
        r += dr
        c += dc
    
    return count

def is_path_clear(board, from_row, from_col, to_row, to_col, direction, player):
    """
    Check if the path between from and to is clear.
    Can jump over friendly pieces but not enemy pieces.
    """
    dr, dc = direction
    rows, cols = board.shape
    
    # Start from the next cell after the starting position
    r, c = from_row + dr, from_col + dc
    
    while (r, c) != (to_row, to_col):
        if not (0 <= r < rows and 0 <= c < cols):
            return False
        
        cell_value = board[r, c]
        if cell_value == -player:  # Enemy piece - cannot jump over
            return False
        
        r += dr
        c += dc
    
    return True

def evaluate_move(board, move, player, opponent):
    """
    Evaluate the quality of a move using multiple heuristics.
    """
    (from_row, from_col), (to_row, to_col) = move
    
    # Create a copy of the board with the move applied
    new_board = board.copy()
    new_board[to_row, to_col] = player
    new_board[from_row, from_col] = 0
    
    score = 0
    
    # Heuristic 1: Connectivity (most important)
    connectivity_score = evaluate_connectivity(new_board, player)
    score += connectivity_score * 10
    
    # Heuristic 2: Center control
    center_score = evaluate_center_control(new_board, player)
    score += center_score * 2
    
    # Heuristic 3: Piece mobility
    mobility_score = evaluate_mobility(new_board, player)
    score += mobility_score * 1
    
    # Heuristic 4: Block opponent connectivity
    block_score = -evaluate_connectivity(new_board, opponent) * 3
    score += block_score
    
    # Heuristic 5: Capture bonus
    if board[to_row, to_col] == opponent:
        score += 5
    
    # Heuristic 6: Position improvement
    position_score = evaluate_position_change(board, from_row, from_col, to_row, to_col)
    score += position_score * 1
    
    return score

def evaluate_connectivity(board, player):
    """
    Evaluate how well connected the player's pieces are.
    Returns a score based on the largest connected component and total connectivity.
    """
    rows, cols = board.shape
    visited = np.zeros((rows, cols), dtype=bool)
    
    max_component_size = 0
    total_connections = 0
    
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == player and not visited[r, c]:
                component_size, component_connections = bfs_connectivity(
                    board, r, c, player, visited
                )
                max_component_size = max(max_component_size, component_size)
                total_connections += component_connections
    
    # Count total pieces
    total_pieces = np.sum(board == player)
    
    # Score based on how many pieces are in the largest component
    if total_pieces > 0:
        connectivity_ratio = max_component_size / total_pieces
        return connectivity_ratio + total_connections * 0.1
    else:
        return 0

def bfs_connectivity(board, start_row, start_col, player, visited):
    """
    Use BFS to find connected component size and count connections.
    """
    rows, cols = board.shape
    queue = deque([(start_row, start_col)])
    visited[start_row, start_col] = True
    component_size = 0
    connections = 0
    
    # 8 directions for connectivity
    directions = [(-1, -1), (-1, 0), (-1, 1), 
                 (0, -1),           (0, 1),
                 (1, -1),  (1, 0),  (1, 1)]
    
    while queue:
        r, c = queue.popleft()
        component_size += 1
        
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < rows and 0 <= nc < cols:
                if board[nr, nc] == player and not visited[nr, nc]:
                    visited[nr, nc] = True
                    queue.append((nr, nc))
                    connections += 1
                elif board[nr, nc] == player:
                    # Already visited but still counts as a connection
                    connections += 0.5
    
    return component_size, connections

def evaluate_center_control(board, player):
    """
    Evaluate control of the center of the board.
    Center squares are more valuable as they provide more movement options.
    """
    # Define center as the 4x4 middle area (rows 2-5, cols 2-5)
    center_score = 0
    
    # Weight matrix for center control
    weights = [
        [1, 2, 2, 1],
        [2, 3, 3, 2],
        [2, 3, 3, 2],
        [1, 2, 2, 1]
    ]
    
    for r in range(2, 6):
        for c in range(2, 6):
            if board[r, c] == player:
                center_score += weights[r-2][c-2]
            elif board[r, c] == -player:
                center_score -= weights[r-2][c-2] * 0.8
    
    return center_score

def evaluate_mobility(board, player):
    """
    Evaluate how mobile the player's pieces are.
    More mobile pieces can respond to threats and create opportunities.
    """
    legal_moves = generate_legal_moves(board, player)
    return len(legal_moves)

def evaluate_position_change(board, from_row, from_col, to_row, to_col):
    """
    Evaluate if the move improves the piece's position.
    """
    # Distance from center
    board_size = 8
    center = board_size // 2
    
    from_distance = abs(from_row - center) + abs(from_col - center)
    to_distance = abs(to_row - center) + abs(to_col - center)
    
    # Moving closer to center is generally better
    return from_distance - to_distance
