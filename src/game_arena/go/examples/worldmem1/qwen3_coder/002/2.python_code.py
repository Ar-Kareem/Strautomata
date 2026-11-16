
import numpy as np
from typing import List, Tuple, Dict

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # Initialize the board
    board = np.zeros((21, 21))  # 19x19 with padding
    for r, c in me:
        board[r, c] = 1
    for r, c in opponent:
        board[r, c] = 2
    
    def is_legal_move(row, col, player=1):
        # Check if position is empty
        if board[row, col] != 0:
            return False
            
        # Temporarily place the stone
        board[row, col] = player
        opponent_color = 3 - player
        
        # Check if any adjacent opponent group is captured
        captured = False
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = row + dr, col + dc
            if board[nr, nc] == opponent_color:
                # Check if this group has liberties
                if not has_liberty(nr, nc, opponent_color):
                    captured = True
                    break
        
        # Check if the placed stone has liberties
        has_libs = has_liberty(row, col, player)
        board[row, col] = 0  # Remove the temporary stone
        
        # Move is legal if the stone has liberties or captures opponent stones
        return has_libs or captured
    
    def has_liberty(row, col, color):
        visited = set()
        stack = [(row, col)]
        
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if board[nr, nc] == 0:  # Liberty found
                    return True
                elif board[nr, nc] == color and (nr, nc) not in visited:
                    stack.append((nr, nc))
        
        return False
    
    def evaluate_move(row, col):
        score = 0
        
        # Prefer moves closer to existing stones
        for r, c in me:
            distance = abs(row - r) + abs(col - c)
            if distance == 1:  # Adjacent
                score += 10
            elif distance == 2:  # Two spaces away
                score += 5
        
        # Prefer moves that put pressure on opponent
        for r, c in opponent:
            distance = abs(row - r) + abs(col - c)
            if distance == 1:
                score += 8
            elif distance == 2:
                score += 3
                
        # Avoid edges slightly
        if row <= 2 or row >= 18 or col <= 2 or col >= 18:
            score -= 2
            
        # Prefer center positions
        center_r, center_c = 10, 10
        dist_to_center = abs(row - center_r) + abs(col - center_c)
        score += max(0, 10 - dist_to_center)
        
        return score
    
    # Generate candidate moves in a spiral pattern from center outward
    candidates = []
    center_r, center_c = 10, 10
    
    # Try positions in a diamond pattern around the center
    for dist in range(1, 10):
        for dr in range(-dist, dist+1):
            for dc in [dist-abs(dr), -(dist-abs(dr))]:
                if dc == 0 and dr == 0:
                    continue
                r, c = center_r + dr, center_c + dc
                if 1 <= r <= 19 and 1 <= c <= 19:
                    candidates.append((r, c))
    
    # Evaluate candidate moves
    best_move = (0, 0)  # Default to pass
    best_score = -1
    
    for r, c in candidates:
        if is_legal_move(r, c):
            score = evaluate_move(r, c)
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    # If no good move found, try all positions on board
    if best_score < 5:  # Threshold for a "good" move
        for r in range(1, 20):
            for c in range(1, 20):
                if is_legal_move(r, c):
                    score = evaluate_move(r, c)
                    if score > best_score:
                        best_score = score
                        best_move = (r, c)
    
    return (best_move, memory)
