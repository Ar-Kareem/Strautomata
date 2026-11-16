
import numpy as np
from typing import Tuple, List, Optional
import random

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Policy for Dots and Boxes game using minimax with alpha-beta pruning.
    """
    # Set a fixed seed for reproducibility in tournaments
    # (removed to allow natural randomness for tie-breaking)
    
    # Define constants
    SIZE = 5  # 5x5 dots grid
    BOX_SIZE = 4  # 4x4 boxes grid
    
    # Determine whose turn it is (we are always player 1)
    PLAYER = 1
    OPPONENT = -1
    
    def evaluate_state(horiz: np.ndarray, vert: np.ndarray, capt: np.ndarray, maximizing_player: bool) -> float:
        """Evaluate the board state heuristically."""
        # Our player is always PLAYER
        our_captures = np.sum(capt == PLAYER)
        opp_captures = np.sum(capt == OPPONENT)
        
        # Base score: difference in captures
        score = our_captures - opp_captures
        
        # Add heuristic for potential captures and dangerous moves
        # Look at each box and check how many sides are filled
        for i in range(BOX_SIZE):
            for j in range(BOX_SIZE):
                # Check if box is already captured
                if capt[i, j] != 0:
                    continue
                
                # Count filled sides of this box
                top = horiz[i, j]
                bottom = horiz[i+1, j]
                left = vert[i, j]
                right = vert[i, j+1]
                
                filled_count = (top != 0) + (bottom != 0) + (left != 0) + (right != 0)
                
                if filled_count == 3:
                    # Box has three sides filled - next player to play here captures it
                    # This is a dangerous box for the player whose turn it is
                    if maximizing_player:
                        score -= 1.5  # Bad for us if it's our turn
                    else:
                        score += 1.5  # Good for us if it's opponent's turn
                elif filled_count == 2:
                    # Two sides filled - moderate opportunity/threat
                    pass  # Neutral for now
        
        # Bonus for having more potential to form chains
        # (simplified: count potential boxes we can capture)
        return score
    
    def is_legal_move(row: int, col: int, direction: str, horiz: np.ndarray, vert: np.ndarray) -> bool:
        """Check if a move is legal."""
        if not (0 <= row < SIZE and 0 <= col < SIZE):
            return False
        if direction == 'H':
            if row >= SIZE or col >= BOX_SIZE:  # H edges are between (row, col) and (row, col+1)
                return False
            return horiz[row, col] == 0
        elif direction == 'V':
            if row >= BOX_SIZE or col >= SIZE:  # V edges are between (row, col) and (row+1, col)
                return False
            return vert[row, col] == 0
        return False
    
    def make_move(row: int, col: int, direction: str, horiz: np.ndarray, vert: np.ndarray, capt: np.ndarray, player: int) -> Tuple[np.ndarray, np.ndarray, np.ndarray, bool]:
        """
        Execute a move and return new state plus whether the player gets another turn.
        """
        new_horiz = horiz.copy()
        new_vert = vert.copy()
        new_capt = capt.copy()
        
        if direction == 'H':
            new_horiz[row, col] = player
        else:  # 'V'
            new_vert[row, col] = player
        
        captured_boxes = False
        
        # Check all boxes that might be completed by this move
        if direction == 'H':
            # A horizontal edge at (row, col) affects box (row-1, col) and box (row, col)
            # Box above the edge
            if row > 0 and col < BOX_SIZE:
                # Check if box (row-1, col) is completed
                if new_capt[row-1, col] == 0:
                    top_edge = new_horiz[row-1, col]
                    bottom_edge = new_horiz[row, col]
                    left_edge = new_vert[row-1, col]
                    right_edge = new_vert[row-1, col+1]
                    if top_edge != 0 and bottom_edge != 0 and left_edge != 0 and right_edge != 0:
                        new_capt[row-1, col] = player
                        captured_boxes = True
            
            # Box below the edge
            if row < BOX_SIZE and col < BOX_SIZE:
                if new_capt[row, col] == 0:
                    top_edge = new_horiz[row, col]
                    bottom_edge = new_horiz[row+1, col]
                    left_edge = new_vert[row, col]
                    right_edge = new_vert[row, col+1]
                    if top_edge != 0 and bottom_edge != 0 and left_edge != 0 and right_edge != 0:
                        new_capt[row, col] = player
                        captured_boxes = True
        
        else:  # 'V'
            # A vertical edge at (row, col) affects box (row, col-1) and box (row, col)
            # Box to the left
            if col > 0 and row < BOX_SIZE:
                if new_capt[row, col-1] == 0:
                    top_edge = new_horiz[row, col-1]
                    bottom_edge = new_horiz[row+1, col-1]
                    left_edge = new_vert[row, col-1]
                    right_edge = new_vert[row, col]
                    if top_edge != 0 and bottom_edge != 0 and left_edge != 0 and right_edge != 0:
                        new_capt[row, col-1] = player
                        captured_boxes = True
            
            # Box to the right
            if col < BOX_SIZE and row < BOX_SIZE:
                if new_capt[row, col] == 0:
                    top_edge = new_horiz[row, col]
                    bottom_edge = new_horiz[row+1, col]
                    left_edge = new_vert[row, col]
                    right_edge = new_vert[row, col+1]
                    if top_edge != 0 and bottom_edge != 0 and left_edge != 0 and right_edge != 0:
                        new_capt[row, col] = player
                        captured_boxes = True
        
        return new_horiz, new_vert, new_capt, captured_boxes
    
    def get_all_moves(horiz: np.ndarray, vert: np.ndarray) -> List[Tuple[int, int, str]]:
        """Get all legal moves."""
        moves = []
        # Horizontal edges: row 0-4, col 0-3
        for r in range(SIZE):
            for c in range(BOX_SIZE):
                if horiz[r, c] == 0:
                    moves.append((r, c, 'H'))
        
        # Vertical edges: row 0-3, col 0-4
        for r in range(BOX_SIZE):
            for c in range(SIZE):
                if vert[r, c] == 0:
                    moves.append((r, c, 'V'))
        
        return moves
    
    def minimax(horiz: np.ndarray, vert: np.ndarray, capt: np.ndarray, 
                depth: int, alpha: float, beta: float, maximizing: bool) -> Tuple[float, Optional[Tuple[int, int, str]]]:
        """
        Minimax with alpha-beta pruning.
        Returns (score, best_move).
        """
        # Terminal condition: game over or depth limit reached
        if depth == 0 or np.all(horiz != 0) and np.all(vert != 0):
            return evaluate_state(horiz, vert, capt, maximizing), None
        
        current_player = PLAYER if maximizing else OPPONENT
        moves = get_all_moves(horiz, vert)
        
        if not moves:
            return evaluate_state(horiz, vert, capt, maximizing), None
        
        # Sort moves heuristically: prefer capturing moves, then safe moves
        def move_priority(move):
            r, c, d = move
            _, _, _, captures = make_move(r, c, d, horiz, vert, capt, current_player)
            if captures:
                return 0  # Capturing moves best
            # Check if this creates a 3-sided box
            new_h, new_v, _, _ = make_move(r, c, d, horiz, vert, capt, current_player)
            dangerous = False
            for i in range(BOX_SIZE):
                for j in range(BOX_SIZE):
                    if new_h[i, j] != 0 and new_h[i+1, j] != 0 and new_v[i, j] != 0 and new_v[i, j+1] != 0:
                        continue  # Already captured
                    filled = (new_h[i, j] != 0) + (new_h[i+1, j] != 0) + (new_v[i, j] != 0) + (new_v[i, j+1] != 0)
                    if filled == 3:
                        dangerous = True
                        break
                if dangerous:
                    break
            return 1 if dangerous else 2  # Avoid dangerous moves
        
        moves.sort(key=move_priority)
        
        if maximizing:
            max_score = float('-inf')
            best_move = moves[0] if moves else None
            
            for move in moves:
                r, c, d = move
                new_h, new_v, new_capt, captured = make_move(r, c, d, horiz, vert, capt, PLAYER)
                
                if captured:
                    # Player gets another turn
                    score, _ = minimax(new_h, new_v, new_capt, depth-1, alpha, beta, True)
                else:
                    score, _ = minimax(new_h, new_v, new_capt, depth-1, alpha, beta, False)
                
                if score > max_score:
                    max_score = score
                    best_move = move
                
                alpha = max(alpha, score)
                if beta <= alpha:
                    break
            
            return max_score, best_move
        else:
            min_score = float('inf')
            best_move = moves[0] if moves else None
            
            for move in moves:
                r, c, d = move
                new_h, new_v, new_capt, captured = make_move(r, c, d, horiz, vert, capt, OPPONENT)
                
                if captured:
                    # Opponent gets another turn
                    score, _ = minimax(new_h, new_v, new_capt, depth-1, alpha, beta, False)
                else:
                    score, _ = minimax(new_h, new_v, new_capt, depth-1, alpha, beta, True)
                
                if score < min_score:
                    min_score = score
                    best_move = move
                
                beta = min(beta, score)
                if beta <= alpha:
                    break
            
            return min_score, best_move
    
    # Determine search depth based on number of moves remaining
    moves_left = np.sum(horizontal == 0) + np.sum(vertical == 0)
    
    if moves_left <= 6:
        depth = moves_left  # Search to end of game
    elif moves_left <= 12:
        depth = 6
    elif moves_left <= 18:
        depth = 4
    else:
        depth = 2
    
    # Run minimax to find best move
    _, best_move = minimax(horizontal, vertical, capture, depth, float('-inf'), float('inf'), True)
    
    if best_move is None:
        # Fallback: just pick any legal move
        moves = get_all_moves(horizontal, vertical)
        if moves:
            best_move = random.choice(moves)
        else:
            # Should never happen
            return "0,0,H"
    
    row, col, direction = best_move
    return f"{row},{col},{direction}"
