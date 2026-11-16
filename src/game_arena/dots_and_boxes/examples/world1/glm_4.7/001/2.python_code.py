
import numpy as np
import random
from collections import deque

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Policy for Dots and Boxes on a 4x4 grid.
    
    Strategy:
    1. Take boxes if available (highest priority).
    2. Avoid creating 3-edge boxes if possible.
    3. If all moves create 3-edge boxes, prefer moves with shorter chains.
    """
    
    def count_box_edges(box_row: int, box_col: int) -> int:
        """Count the number of drawn edges of a box."""
        count = 0
        if horizontal[box_row, box_col] != 0:
            count += 1
        if horizontal[box_row + 1, box_col] != 0:
            count += 1
        if vertical[box_row, box_col] != 0:
            count += 1
        if vertical[box_row, box_col + 1] != 0:
            count += 1
        return count
    
    def estimate_chain_length(start_box_row: int, start_box_col: int) -> int:
        """
        Estimate the chain length starting from a box that will become a 3-edge box.
        Uses BFS to count the number of connected 2-edge boxes.
        """
        if capture[start_box_row, start_box_col] != 0:
            return 0
        
        edges = count_box_edges(start_box_row, start_box_col)
        edges_after_move = edges + 1
        
        if edges_after_move != 3:
            return 0
        
        visited = set([(start_box_row, start_box_col)])
        queue = deque([(start_box_row, start_box_col)])
        length = 0
        
        while queue:
            current_row, current_col = queue.popleft()
            length += 1
            
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = current_row + dr, current_col + dc
                if (0 <= nr < 4 and 0 <= nc < 4 and 
                    (nr, nc) not in visited and 
                    capture[nr, nc] == 0 and 
                    count_box_edges(nr, nc) == 2):
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        
        return length
    
    # Find all legal moves
    legal_moves = []
    for i in range(5):
        for j in range(4):
            if horizontal[i, j] == 0:
                legal_moves.append((i, j, 'H'))
    for i in range(4):
        for j in range(5):
            if vertical[i, j] == 0:
                legal_moves.append((i, j, 'V'))
    
    if not legal_moves:
        return ""
    
    best_score = -float('inf')
    best_moves = []
    
    for row, col, dir in legal_moves:
        boxes_captured = 0
        total_chain_length = 0
        
        three_edge_boxes = []
        
        if dir == 'H':
            if row > 0 and capture[row - 1, col] == 0:
                edges = count_box_edges(row - 1, col)
                if edges == 3:
                    boxes_captured += 1
                elif edges == 2:
                    three_edge_boxes.append((row - 1, col))
            if row < 4 and capture[row, col] == 0:
                edges = count_box_edges(row, col)
                if edges == 3:
                    boxes_captured += 1
                elif edges == 2:
                    three_edge_boxes.append((row, col))
        else:
            if col > 0 and capture[row, col - 1] == 0:
                edges = count_box_edges(row, col - 1)
                if edges == 3:
                    boxes_captured += 1
                elif edges == 2:
                    three_edge_boxes.append((row, col - 1))
            if col < 4 and capture[row, col] == 0:
                edges = count_box_edges(row, col)
                if edges == 3:
                    boxes_captured += 1
                elif edges == 2:
                    three_edge_boxes.append((row, col))
        
        for box_row, box_col in three_edge_boxes:
            total_chain_length += estimate_chain_length(box_row, box_col)
        
        score = 1000 * boxes_captured - total_chain_length
        
        if score > best_score:
            best_score = score
            best_moves = [(row, col, dir)]
        elif score == best_score:
            best_moves.append((row, col, dir))
    
    row, col, dir = random.choice(best_moves)
    return f"{row},{col},{dir}"
