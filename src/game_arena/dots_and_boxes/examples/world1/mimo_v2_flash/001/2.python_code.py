
import numpy as np
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Dots and Boxes Policy for 4x4 Grid.
    
    Strategy:
    1. Prioritize capturing boxes (if immediate points are available).
    2. Avoid creating moves for the opponent. Specifically, avoid filling the 3rd side of a box
       unless forced to.
    3. If no boxes can be captured, play a 'safe' move (one that does not complete a box).
    4. If no safe moves exist, we are forced to break a chain (play the dangerous move).
    """
    
    # Helper to count how many lines a move would add to a box
    def get_box_delta(r, c, direction):
        # A move at (r, c) affects specific boxes depending on direction.
        # The board has 4x4 boxes. Box (i, j) corresponds to top-left dot (i, j).
        # Horizontal edge (r, c) is between dots (r, c) and (r, c+1). 
        # It is the top edge of box (r, c) and bottom edge of box (r-1, c).
        # Vertical edge (r, c) is between dots (r, c) and (r+1, c).
        # It is the left edge of box (r, c) and right edge of box (r, c-1).
        
        affected_boxes = []
        if direction == 'H':
            # Top edge of box (r, c)
            if r < 4: affected_boxes.append((r, c))
            # Bottom edge of box (r-1, c)
            if r > 0: affected_boxes.append((r-1, c))
        else: # 'V'
            # Left edge of box (r, c)
            if c < 4: affected_boxes.append((r, c))
            # Right edge of box (r, c-1)
            if c > 0: affected_boxes.append((r, c-1))
            
        return affected_boxes

    def count_edges(box_r, box_c):
        if not (0 <= box_r < 4 and 0 <= box_c < 4):
            return 0
        h1 = horizontal[box_r, box_c]
        h2 = horizontal[box_r + 1, box_c]
        v1 = vertical[box_r, box_c]
        v2 = vertical[box_r, box_c + 1]
        return (1 if h1 != 0 else 0) + (1 if h2 != 0 else 0) + (1 if v1 != 0 else 0) + (1 if v2 != 0 else 0)

    # 1. Gather all legal moves and classify them
    safe_moves = []      # Moves that don't complete a box
    scoring_moves = []   # Moves that complete at least one box
    losing_moves = []    # Moves that give opponent a 3-side box (we want to avoid these)

    # Iterate over all potential edges
    for r in range(5):
        for c in range(5):
            # Check Horizontal
            if horizontal[r, c] == 0:
                boxes = get_box_delta(r, c, 'H')
                new_captures = 0
                creates_danger = False
                
                for br, bc in boxes:
                    current_edges = count_edges(br, bc)
                    # If currently 2 edges, adding 1 makes 3. This creates a danger for opponent unless it also completes another box.
                    if current_edges == 2:
                        # This move creates a 3-side box. Unless this move also completes another box (which we check later),
                        # this is generally a bad move. We will mark it as dangerous.
                        creates_danger = True
                    if current_edges == 3:
                        new_captures += 1
                
                if new_captures > 0:
                    scoring_moves.append((r, c, 'H', new_captures))
                elif creates_danger:
                    losing_moves.append((r, c, 'H'))
                else:
                    safe_moves.append((r, c, 'H'))

            # Check Vertical
            if vertical[r, c] == 0:
                boxes = get_box_delta(r, c, 'V')
                new_captures = 0
                creates_danger = False
                
                for br, bc in boxes:
                    current_edges = count_edges(br, bc)
                    if current_edges == 2:
                        creates_danger = True
                    if current_edges == 3:
                        new_captures += 1
                        
                if new_captures > 0:
                    scoring_moves.append((r, c, 'V', new_captures))
                elif creates_danger:
                    losing_moves.append((r, c, 'V'))
                else:
                    safe_moves.append((r, c, 'V'))

    # 2. Decision Logic
    
    # A. If we can capture boxes, we generally should.
    # Exception: If we have exactly one move, and that move captures 1 box but leaves 3 boxes for the opponent (long chain rule),
    # we might avoid it. But on a 4x4 grid, taking points is usually robust. 
    # Let's stick to: If there are scoring moves, take the one with the highest capture count.
    if scoring_moves:
        # Sort by number of captures descending
        scoring_moves.sort(key=lambda x: x[3], reverse=True)
        best_move = scoring_moves[0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # B. If no scoring moves, look for safe moves.
    if safe_moves:
        # Pick a random safe move to distribute lines or pick one that looks useful.
        # Pure random is often strong enough to avoid predictability.
        move = random.choice(safe_moves)
        return f"{move[0]},{move[1]},{move[2]}"

    # C. If no safe moves and no immediate scoring, we are forced to open the chain.
    # This implies losing_moves exist. We must pick one.
    # We should pick the one that minimizes damage. However, in a forced situation,
    # any 3rd line creates a 4th line for the opponent.
    if losing_moves:
        move = random.choice(losing_moves)
        return f"{move[0]},{move[1]},{move[2]}"

    # Fallback (should not be reached if there are legal moves)
    return "0,0,H"
