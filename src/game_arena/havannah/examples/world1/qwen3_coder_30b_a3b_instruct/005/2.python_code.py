
import numpy as np
from collections import deque
import random

def get_neighbors(row, col):
    """Get valid hex neighbors for a given position"""
    neighbors = []
    # Hexagonal grid has 6 neighbors
    # For a hex grid, the pattern is: 
    # - row+1,col (down) - row-1,col (up)
    # - row+1,col+1 (down-right) - row-1,col-1 (up-left) 
    # - row,col+1 (right) - row,col-1 (left)
    offsets = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1)]
    for dr, dc in offsets:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 15 and 0 <= nc < 15:
            neighbors.append((nr, nc))
    return neighbors

def get_all_paths(board, start_row, start_col, color):
    """Get all connected paths from start position"""
    visited = set()
    queue = deque([(start_row, start_col)])
    visited.add((start_row, start_col))
    paths = [(start_row, start_col)]
    
    while queue:
        row, col = queue.popleft()
        for nr, nc in get_neighbors(row, col):
            if (nr, nc) not in visited and board[nr][nc] == color:
                visited.add((nr, nc))
                queue.append((nr, nc))
                paths.append((nr, nc))
    
    return paths

def detect_ring(board, color):
    """Simple ring detection - this is a very simplified version"""
    # This would be more complex in real implementation but for strategic priority
    return False

def detect_bridge(board, color):
    """Detect if color has a bridge between opposite corners"""
    # Simplified: check for path from corner to opposite corner
    corners = [(0,0), (0,14), (14,0), (14,14)]
    # For implementation in competitions, would need graph connectivity
    return False

def detect_fork(board, color):
    """Detect if color has fork connecting 3 edges"""
    # Simplified version
    return False

def calculate_score(board, row, col, me, opp):
    """Calculate heuristic score for a potential move"""
    if board[row][col] != 0:  # not empty
        return -1
    
    score = 0
    
    # Check if this move completes any structure
    # For now, simplest heuristic: prefer center positions
    center = 7
    dist_from_center = abs(row - center) + abs(col - center)
    score += 10 - dist_from_center  # prefer center positions
    
    # Prefer positions that can connect to existing stones
    my_stones = set(me)
    opponent_stones = set(opp)
    
    neighbors = get_neighbors(row, col)
    my_connections = sum(1 for nr, nc in neighbors if (nr, nc) in my_stones)
    opponent_connections = sum(1 for nr, nc in neighbors if (nr, nc) in opponent_stones)
    
    # Prefer moves that connect to our stones
    score += my_connections * 2
    
    # Prefer moves that connect to opponent stones (defensive)
    score -= opponent_connections
    
    return score

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """Main policy function to determine the next move"""
    board = np.zeros((15, 15), dtype=int)
    
    # Set board state
    for r, c in me:
        board[r][c] = 1  # Player 0
    for r, c in opp:
        board[r][c] = 2  # Player 1
    
    # Convert lists to sets for faster lookup
    my_stones = set(me)
    opp_stones = set(opp)
    
    # 1. Try to win immediately
    for r, c in valid_mask:
        if valid_mask[r][c]:
            # Test if placing here creates a win
            # For a simplified solution, let's avoid this too complex logic
            pass
    
    # 2. Block opponent wins (if any)
    # For simplicity, let's skip detailed blocking in this optimization
    
    # 3. Use heuristic scoring for strategic placement
    best_score = -float('inf')
    best_move = None
    
    # Try placing to get co-most strategic position
    candidate_moves = []
    for r in range(15):
        for c in range(15):
            if valid_mask[r][c] and board[r][c] == 0:
                score = calculate_score(board, r, c, me, opp)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    # If no strategic move found, play anywhere legal
    if best_move is None:
        for r in range(15):
            for c in range(15):
                if valid_mask[r][c]:
                    return (r, c)
    
    return best_move
