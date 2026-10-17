
import numpy as np
import itertools

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes policy for 4x4 grid.
    Returns move string in format 'row,col,dir'
    """
    
    def get_possible_moves():
        """Get all legal moves"""
        moves = []
        # Horizontal edges: rows 0-4, cols 0-3
        for r in range(5):
            for c in range(4):
                if horizontal[r, c] == 0:
                    moves.append((r, c, 'H'))
        
        # Vertical edges: rows 0-3, cols 0-4
        for r in range(4):
            for c in range(5):
                if vertical[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves
    
    def boxes_completed_by_move(row, col, dir):
        """Count boxes that would be completed by this move"""
        completed = 0
        
        if dir == 'H':
            # Check box above (if exists)
            if row > 0:
                # Check box at (row-1, col)
                top = horizontal[row-1, col] != 0
                bottom = True  # This move
                left = vertical[row-1, col] != 0
                right = vertical[row-1, col+1] != 0
                if top and bottom and left and right:
                    completed += 1
            
            # Check box below (if exists)
            if row < 4:
                # Check box at (row, col)
                top = True  # This move
                bottom = horizontal[row+1, col] != 0
                left = vertical[row, col] != 0
                right = vertical[row, col+1] != 0
                if top and bottom and left and right:
                    completed += 1
                    
        else:  # dir == 'V'
            # Check box to left (if exists)
            if col > 0:
                # Check box at (row, col-1)
                top = horizontal[row, col-1] != 0
                bottom = horizontal[row+1, col-1] != 0
                left = vertical[row, col-1] != 0
                right = True  # This move
                if top and bottom and left and right:
                    completed += 1
            
            # Check box to right (if exists)
            if col < 4:
                # Check box at (row, col)
                top = horizontal[row, col] != 0
                bottom = horizontal[row+1, col] != 0
                left = True  # This move
                right = vertical[row, col+1] != 0
                if top and bottom and left and right:
                    completed += 1
        
        return completed
    
    def boxes_that_become_three_sided(row, col, dir):
        """Count boxes that would have exactly 3 sides after this move"""
        three_sided = 0
        
        if dir == 'H':
            # Check box above
            if row > 0:
                sides = 0
                if horizontal[row-1, col] != 0: sides += 1
                if True: sides += 1  # This move
                if vertical[row-1, col] != 0: sides += 1
                if vertical[row-1, col+1] != 0: sides += 1
                if sides == 3:
                    three_sided += 1
            
            # Check box below
            if row < 4:
                sides = 0
                if True: sides += 1  # This move
                if horizontal[row+1, col] != 0: sides += 1
                if vertical[row, col] != 0: sides += 1
                if vertical[row, col+1] != 0: sides += 1
                if sides == 3:
                    three_sided += 1
                    
        else:  # dir == 'V'
            # Check box to left
            if col > 0:
                sides = 0
                if horizontal[row, col-1] != 0: sides += 1
                if horizontal[row+1, col-1] != 0: sides += 1
                if vertical[row, col-1] != 0: sides += 1
                if True: sides += 1  # This move
                if sides == 3:
                    three_sided += 1
            
            # Check box to right
            if col < 4:
                sides = 0
                if horizontal[row, col] != 0: sides += 1
                if horizontal[row+1, col] != 0: sides += 1
                if True: sides += 1  # This move
                if vertical[row, col+1] != 0: sides += 1
                if sides == 3:
                    three_sided += 1
        
        return three_sided
    
    def get_chain_length(row, col, dir):
        """
        If this move completes a box, check how many more boxes would be forced
        to complete in a chain reaction
        """
        chain_len = 0
        
        # Create copies to simulate
        h_temp = horizontal.copy()
        v_temp = vertical.copy()
        cap_temp = capture.copy()
        
        if dir == 'H':
            h_temp[row, col] = 1
        else:
            v_temp[row, col] = 1
        
        # Check for chains (simplified - check for immediate forced moves)
        # This is a heuristic approach
        checked_boxes = []
        
        if dir == 'H':
            boxes_to_check = []
            if row > 0:
                boxes_to_check.append((row-1, col))
            if row < 4:
                boxes_to_check.append((row, col))
            
            for br, bc in boxes_to_check:
                # Count sides
                sides = 0
                top = h_temp[br, bc] != 0
                bottom = h_temp[br+1, bc] != 0
                left = v_temp[br, bc] != 0
                right = v_temp[br, bc+1] != 0
                
                if top: sides += 1
                if bottom: sides += 1
                if left: sides += 1
                if right: sides += 1
                
                if sides == 3:
                    # Find the missing edge
                    if not top:
                        # Check what box would be affected
                        if br > 0:
                            # Box above at (br-1, bc)
                            chain_len += 1
                    elif not bottom:
                        if br < 3:
                            # Box below at (br+1, bc)
                            chain_len += 1
                    elif not left:
                        if bc > 0:
                            # Box to left at (br, bc-1)
                            chain_len += 1
                    elif not right:
                        if bc < 3:
                            # Box to right at (br, bc+1)
                            chain_len += 1
        
        return chain_len
    
    def move_score(row, col, dir):
        """Score a move based on strategic value"""
        score = 0
        
        # Priority 1: Capturing boxes (highest score)
        boxes_captured = boxes_completed_by_move(row, col, dir)
        if boxes_captured > 0:
            score += 1000 * boxes_captured
            
            # Bonus for chains
            chain_bonus = get_chain_length(row, col, dir)
            score += 200 * chain_bonus
            
            return score  # Immediate capture moves dominate
        
        # Priority 2: Avoid creating 3-sided boxes for opponent
        three_sided = boxes_that_become_three_sided(row, col, dir)
        score -= 100 * three_sided
        
        # Priority 3: Control center of board
        # Center edges are more valuable as they affect more boxes
        center_value = 0
        
        if dir == 'H':
            # Center horizontal edges (rows 1-3, cols 1-2)
            if 1 <= row <= 3 and 1 <= col <= 2:
                center_value = 3
            # Next best (edges near center)
            elif (row == 0 or row == 4) and 1 <= col <= 2:
                center_value = 1
            elif 1 <= row <= 3 and (col == 0 or col == 3):
                center_value = 2
        else:  # dir == 'V'
            # Center vertical edges (rows 1-2, cols 1-3)
            if 1 <= row <= 2 and 1 <= col <= 3:
                center_value = 3
            # Next best (edges near center)
            elif (row == 0 or row == 3) and 1 <= col <= 3:
                center_value = 1
            elif 1 <= row <= 2 and (col == 0 or col == 4):
                center_value = 2
        
        score += center_value
        
        # Priority 4: Connect to existing edges (build structures)
        # Check if this edge connects to other edges
        connections = 0
        
        if dir == 'H':
            # Check left neighbor
            if col > 0 and horizontal[row, col-1] != 0:
                connections += 1
            # Check right neighbor
            if col < 3 and horizontal[row, col+1] != 0:
                connections += 1
            # Check vertical connections at ends
            if vertical[max(0, row-1), col] != 0:
                connections += 1
            if row < 4 and vertical[row, col] != 0:
                connections += 1
            if vertical[max(0, row-1), col+1] != 0:
                connections += 1
            if row < 4 and vertical[row, col+1] != 0:
                connections += 1
        else:  # dir == 'V'
            # Check top neighbor
            if row > 0 and vertical[row-1, col] != 0:
                connections += 1
            # Check bottom neighbor
            if row < 3 and vertical[row+1, col] != 0:
                connections += 1
            # Check horizontal connections
            if horizontal[row, max(0, col-1)] != 0:
                connections += 1
            if col < 4 and horizontal[row, col] != 0:
                connections += 1
            if horizontal[row+1, max(0, col-1)] != 0:
                connections += 1
            if col < 4 and horizontal[row+1, col] != 0:
                connections += 1
        
        score += connections
        
        # Priority 5: Early game vs late game strategy
        total_edges_played = np.sum(horizontal != 0) + np.sum(vertical != 0)
        total_edges = 40  # 4x4 grid has 40 edges total
        
        if total_edges_played < 20:  # Early game
            # Avoid edges that create 3-sided boxes
            if three_sided == 0:
                score += 5
        else:  # Late game
            # More aggressive - if we're behind, take more risks
            my_boxes = np.sum(capture == 1)
            opp_boxes = np.sum(capture == -1)
            
            if my_boxes < opp_boxes:
                # We're behind - be more aggressive
                if three_sided == 1:  # Controlled risk
                    score += 10
        
        return score
    
    # Get all possible moves
    moves = get_possible_moves()
    
    if not moves:
        return ""  # Shouldn't happen in valid game state
    
    # Score all moves
    scored_moves = []
    for row, col, dir in moves:
        score = move_score(row, col, dir)
        scored_moves.append((score, row, col, dir))
    
    # Sort by score (descending)
    scored_moves.sort(reverse=True, key=lambda x: x[0])
    
    # Return the best move
    _, best_row, best_col, best_dir = scored_moves[0]
    
    return f"{best_row},{best_col},{best_dir}"

