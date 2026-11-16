
import numpy as np
from typing import List, Tuple

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Implements a smart Dots and Boxes policy for a 4x4 grid using minimax with alpha-beta pruning.
    Avoids creating 3-sided boxes for opponent, prioritizes capturing, and seeks chain opportunities.
    """
    # Extract current state and find all legal moves
    legal_moves = []
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0:
                legal_moves.append((r, c, 'H'))
            if vertical[r, c] == 0:
                legal_moves.append((r, c, 'V'))
    
    if not legal_moves:
        # Shouldn't happen in valid games, but safety fallback
        return "0,0,H"
    
    # First, try to find any move that captures a box immediately
    capture_moves = []
    for move in legal_moves:
        r, c, d = move
        if _would_capture_box(r, c, d, horizontal, vertical, capture):
            capture_moves.append(move)
    
    if capture_moves:
        # Prefer moves that capture more boxes
        best_capture = None
        max_caps = 0
        for move in capture_moves:
            r, c, d = move
            caps = _count_captured_boxes(r, c, d, horizontal, vertical, capture)
            if caps > max_caps:
                max_caps = caps
                best_capture = move
        if best_capture:
            return f"{best_capture[0]},{best_capture[1]},{best_capture[2]}"
    
    # Avoid moves that create a 3-sided box for opponent
    dangerous_moves = []
    for move in legal_moves:
        r, c, d = move
        if _would_create_dangerous_box(r, c, d, horizontal, vertical, capture):
            dangerous_moves.append(move)
    
    # Filter out dangerous moves unless we have no choice
    safe_moves = [m for m in legal_moves if m not in dangerous_moves]
    
    if safe_moves:
        # Use minimax to evaluate safe moves
        best_move = minimax_search(horizontal, vertical, capture, safe_moves, depth=4)
        if best_move:
            return f"{best_move[0]},{best_move[1]},{best_move[2]}"
    
    # If all moves are dangerous, we must play one — pick the one with least damage
    best_danger = None
    min_new_boxes = float('inf')
    for move in dangerous_moves:
        r, c, d = move
        new_boxes = _count_new_opponent_boxes(r, c, d, horizontal, vertical, capture)
        if new_boxes < min_new_boxes:
            min_new_boxes = new_boxes
            best_danger = move
    
    if best_danger:
        return f"{best_danger[0]},{best_danger[1]},{best_danger[2]}"
    
    # Fallback: pick first legal move (shouldn't reach here)
    return f"{legal_moves[0][0]},{legal_moves[0][1]},{legal_moves[0][2]}"

def _would_capture_box(r, c, d, horizontal, vertical, capture) -> bool:
    """Check if playing edge (r,c,d) would complete at least one box."""
    boxes_to_check = []
    if d == 'H':
        # Horizontal edge affects boxes above and below
        if r > 0:
            boxes_to_check.append((r-1, c))   # box above
        if r < 4:
            boxes_to_check.append((r, c))     # box below
    else: # d == 'V'
        # Vertical edge affects boxes left and right
        if c > 0:
            boxes_to_check.append((r, c-1))   # box left
        if c < 4:
            boxes_to_check.append((r, c))     # box right
    
    for br, bc in boxes_to_check:
        if capture[br, bc] == 0:  # Box not captured yet
            # Count filled sides
            sides = 0
            # Top edge
            if br == 0:
                top = horizontal[br, bc]
            else:
                top = horizontal[br, bc]
            # Bottom edge
            bottom = horizontal[br+1, bc]
            # Left edge
            left = vertical[br, bc]
            # Right edge
            right = vertical[br, bc+1]
            
            if top != 0: sides += 1
            if bottom != 0: sides += 1
            if left != 0: sides += 1
            if right != 0: sides += 1
            
            # If this move makes the 4th side, we capture it
            if sides == 3:
                # Check if this move is the missing side
                if d == 'H' and (br == r-1 or br == r):
                    if r-1 == br and c == bc:
                        return True
                    if r == br and c == bc:
                        return True
                if d == 'V' and (bc == c-1 or bc == c):
                    if c-1 == bc and r == br:
                        return True
                    if c == bc and r == br:
                        return True
    return False

def _would_create_dangerous_box(r, c, d, horizontal, vertical, capture) -> bool:
    """Check if this move creates a 3-sided box for the opponent."""
    boxes_to_check = []
    if d == 'H':
        if r > 0:
            boxes_to_check.append((r-1, c))   # box above
        if r < 4:
            boxes_to_check.append((r, c))     # box below
    else: # d == 'V'
        if c > 0:
            boxes_to_check.append((r, c-1))   # box left
        if c < 4:
            boxes_to_check.append((r, c))     # box right

    for br, bc in boxes_to_check:
        if capture[br, bc] == 0:  # Box not captured yet
            sides = 0
            top = horizontal[br, bc]
            bottom = horizontal[br+1, bc]
            left = vertical[br, bc]
            right = vertical[br, bc+1]
            
            if top != 0: sides += 1
            if bottom != 0: sides += 1
            if left != 0: sides += 1
            if right != 0: sides += 1
            
            # If 3 sides already filled, this move makes 4 → opponent gets it
            if sides == 3:
                # Check if this move is the last side (dangerous)
                if d == 'H': 
                    if (r-1 == br and c == bc) or (r == br and c == bc):
                        return True
                if d == 'V':
                    if (c-1 == bc and r == br) or (c == bc and r == br):
                        return True
    return False

def _count_captured_boxes(r, c, d, horizontal, vertical, capture) -> int:
    """Count how many boxes this move would capture."""
    count = 0
    boxes_to_check = []
    if d == 'H':
        if r > 0:
            boxes_to_check.append((r-1, c))
        if r < 4:
            boxes_to_check.append((r, c))
    else: # d == 'V'
        if c > 0:
            boxes_to_check.append((r, c-1))
        if c < 4:
            boxes_to_check.append((r, c))
    
    for br, bc in boxes_to_check:
        if capture[br, bc] == 0:
            top = horizontal[br, bc]
            bottom = horizontal[br+1, bc]
            left = vertical[br, bc]
            right = vertical[br, bc+1]
            sides = sum(1 for e in [top, bottom, left, right] if e != 0)
            if sides == 3:
                # This move completes the box
                if d == 'H' and (r-1 == br or r == br):
                    count += 1
                if d == 'V' and (c-1 == bc or c == bc):
                    count += 1
    return count

def _count_new_opponent_boxes(r, c, d, horizontal, vertical, capture) -> int:
    """Count how many boxes the opponent would get if we make this move."""
    # Same logic as _count_captured_boxes, but we're the one playing, so any box captured is the opponent's if 3 sides were already filled?
    # Actually in our evaluation, if 3 sides are filled and we complete it, that box goes to us (since we just played) — so dangerous moves are those where opponent already has 3 sides, and we complete it → but that doesn't happen!
    # Correction: we are the player. If the box has 3 sides already and we place the fourth, WE capture it.
    # So dangerous moves are those that complete a box that had 3 sides — meaning it's great for us.
    # But "dangerous" for us means we created a 3-sided box for opponent, then they can complete it next turn.
    
    # Actually: we define dangerous as "if we make this move, then THE NEXT PLAYER can capture a box" after our move.
    # So we simulate: we place the edge. Then check if any box now has exactly 3 sides filled. But we just played, so if any box got its 4th side, we captured it. But we already looked at that above.
    
    # The real danger is creating a box with 3 sides that we didn't complete. So we need to check if the move we're making creates a new 3-sided box (not yet complete) for the opponent.
    # But note: we only place one edge. So if we place an edge and that makes a box 3-sided (but not 4th), then opponent can complete it next turn.
    
    count = 0
    boxes_to_check = []
    if d == 'H':
        if r > 0:
            boxes_to_check.append((r-1, c))
        if r < 4:
            boxes_to_check.append((r, c))
    else: # d == 'V'
        if c > 0:
            boxes_to_check.append((r, c-1))
        if c < 4:
            boxes_to_check.append((r, c))
    
    for br, bc in boxes_to_check:
        if capture[br, bc] == 0:
            top = horizontal[br, bc]
            bottom = horizontal[br+1, bc]
            left = vertical[br, bc]
            right = vertical[br, bc+1]
            sides = sum(1 for e in [top, bottom, left, right] if e != 0)
            
            # After we play our edge, count again
            if d == 'H':
                if r-1 == br and c == bc:
                    # This is top edge of box (br,bc)
                    sides += 1
                elif r == br and c == bc:
                    # This is bottom edge of box (br,bc)
                    sides += 1
            else: # 'V'
                if c-1 == bc and r == br:
                    # Left edge
                    sides += 1
                elif c == bc and r == br:
                    # Right edge
                    sides += 1
            
            if sides == 3:
                # This move makes a 3-sided box → opponent can complete it next turn → dangerous
                count += 1
    return count

def minimax_search(h, v, c, legal_moves, depth=4, alpha=-float('inf'), beta=float('inf'), maximizing=True):
    """Minimax search with alpha-beta pruning."""
    if depth == 0 or not legal_moves:
        return None
    
    # Evaluation function
    def evaluate_board(h, v, c):
        my_boxes = np.sum(c == 1)
        opp_boxes = np.sum(c == -1)
        # Prioritize central edges (they control more boxes)
        center_control = 0
        # Central horizontal edges: rows 2,3 cols 1-3
        for c in range(1,4):
            if h[2, c] != 0:
                center_control += 1
            if h[3, c] != 0:
                center_control += 1
        # Central vertical edges: cols 2,3 rows 1-3
        for r in range(1,4):
            if v[r, 2] != 0:
                center_control += 1
            if v[r, 3] != 0:
                center_control += 1
        return my_boxes - opp_boxes + center_control * 0.1
    
    best_move = None
    
    # Sort moves for better pruning: capture moves first, then others
    def move_priority(move):
        r, c, d = move
        caps = _count_captured_boxes(r, c, d, h, v, c)
        dangerous = _would_create_dangerous_box(r, c, d, h, v, c)
        # Prefer capture moves, then avoid dangerous, then priority to center
        center_priority = 0
        if d == 'H' and r in [2,3] and c in [1,2,3]:
            center_priority = 1
        elif d == 'V' and c in [2,3] and r in [1,2,3]:
            center_priority = 1
        return (-caps, dangerous, -center_priority)
    
    # Try to sort moves
    legal_moves_sorted = sorted(legal_moves, key=move_priority)
    
    for move in legal_moves_sorted:
        r, c, d = move
        # Make move
        if d == 'H':
            h[r, c] = 1
        else:
            v[r, c] = 1
            
        # Check how many boxes we capture
        new_captures = 0
        boxes_to_check = []
        if d == 'H':
            if r > 0:
                boxes_to_check.append((r-1, c))
            if r < 4:
                boxes_to_check.append((r, c))
        else:
            if c > 0:
                boxes_to_check.append((r, c-1))
            if c < 4:
                boxes_to_check.append((r, c))
        
        for br, bc in boxes_to_check:
            if c[br, bc] == 0:
                top = h[br, bc]
                bottom = h[br+1, bc]
                left = v[br, bc]
                right = v[br, bc+1]
                sides = sum(1 for e in [top, bottom, left, right] if e != 0)
                if sides == 4:
                    new_captures += 1
                    c[br, bc] = 1  # We capture it
        
        # Recurse only if we didn't capture any box (turn passes)
        # If we captured, we get another turn (maximizing again)
        next_maximizing = True if new_captures > 0 else not maximizing
        
        # Remove current move from legal moves for next state
        next_legal = [m for m in legal_moves if m != move]
        
        # Recursively evaluate
        eval_score = minimax_search(h.copy(), v.copy(), c.copy(), next_legal, depth - 1, alpha, beta, next_maximizing)
        if eval_score is None:
            score = evaluate_board(h, v, c)
        else:
            # We expect eval_score to be the best move from subtree, but we want the score
            # Actually, we'll change our minimax to return a score, not a move
            # Let's restructure: we'll have a helper function that returns score
            score = evaluate_board(h, v, c)
        
        # Undo move
        if d == 'H':
            h[r, c] = 0
        else:
            v[r, c] = 0
        # Undo any captures (we only added)
        for br, bc in boxes_to_check:
            if c[br, bc] == 1:
                c[br, bc] = 0
        
        if maximizing:
            if score > alpha:
                alpha = score
                best_move = move
            if alpha >= beta:
                break
        else:
            if score < beta:
                beta = score
            if alpha >= beta:
                break
    
    return best_move
