
import math
import time
import random
from typing import List, Tuple, Optional

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Returns the best move for the given position using alpha-beta search with iterative deepening.
    """
    # Convert to sets for faster lookups
    me_set = set(me)
    opp_set = set(opp)
    
    # Determine move direction based on color
    forward_dir = -1 if color == 'b' else 1  # Black moves down (decreasing row), White moves up (increasing row)
    home_row = 7 if color == 'b' else 0  # Starting row
    prom_row = 0 if color == 'b' else 7  # Promotion row
    
    # Create game state
    state = BreakthroughState(me_set, opp_set, forward_dir, home_row, prom_row)
    
    # Use iterative deepening with time limit
    start_time = time.time()
    time_limit = 0.95  # Use 95% of available time
    
    best_move = None
    best_score = -float('inf')
    
    # Get all legal moves
    all_moves = state.get_all_moves()
    if not all_moves:
        # Should never happen, but fallback
        return random.choice(list(all_moves)) if all_moves else ((0,0), (0,0))
    
    # Check for immediate winning moves first
    for move in all_moves:
        to_pos = move[1]
        if to_pos[0] == prom_row:  # Promotion move
            # Verify it's legal (not a forward capture attempt)
            from_pos = move[0]
            row_diff = to_pos[0] - from_pos[0]
            col_diff = abs(to_pos[1] - from_pos[1])
            
            # Forward move (col_diff = 0) must be to empty square
            if col_diff == 0 and to_pos not in opp_set:
                return move
            # Diagonal move: either empty or opponent piece
            elif col_diff == 1:
                return move
    
    # Start with depth 1 and increase
    depth = 1
    while time.time() - start_time < time_limit and depth <= 6:
        alpha = -float('inf')
        beta = float('inf')
        
        current_best = None
        current_score = -float('inf')
        
        # Order moves: captures first, then forward moves, then others
        ordered_moves = order_moves(all_moves, state)
        
        for move in ordered_moves:
            # Make move
            new_state = state.make_move(move)
            
            # Search
            score = -alpha_beta(new_state, depth-1, -beta, -alpha, start_time, time_limit)
            
            if score > current_score:
                current_score = score
                current_best = move
            
            alpha = max(alpha, score)
            
            # Check time
            if time.time() - start_time >= time_limit:
                break
        
        if current_best is not None and time.time() - start_time < time_limit:
            best_move = current_best
            best_score = current_score
        
        depth += 1
    
    # If we didn't find a move (shouldn't happen), return random legal move
    if best_move is None:
        best_move = random.choice(list(all_moves))
    
    return best_move

def order_moves(moves, state):
    """Order moves for better alpha-beta performance."""
    captures = []
    promotions = []
    forward_moves = []
    other_moves = []
    
    for move in moves:
        to_pos = move[1]
        from_pos = move[0]
        
        # Check if capture
        if to_pos in state.opp:
            captures.append(move)
        # Check if promotion
        elif to_pos[0] == state.prom_row:
            promotions.append(move)
        # Check if forward move (straight ahead)
        elif to_pos[1] == from_pos[1]:
            forward_moves.append(move)
        else:
            other_moves.append(move)
    
    # Return in order: captures, promotions, forward moves, others
    return captures + promotions + forward_moves + other_moves

def alpha_beta(state, depth, alpha, beta, start_time, time_limit):
    """Alpha-beta search with quiescence."""
    # Check time
    if time.time() - start_time >= time_limit:
        return evaluate(state)
    
    # Terminal node or depth limit
    if depth == 0 or state.is_terminal():
        return quiescence(state, alpha, beta, start_time, time_limit)
    
    # Get moves
    moves = state.get_all_moves()
    if not moves:
        return evaluate(state)  # No moves available
    
    # Order moves
    ordered_moves = order_moves(moves, state)
    
    value = -float('inf')
    for move in ordered_moves:
        new_state = state.make_move(move)
        score = -alpha_beta(new_state, depth-1, -beta, -alpha, start_time, time_limit)
        value = max(value, score)
        alpha = max(alpha, value)
        
        if alpha >= beta:
            break  # Beta cutoff
        
        # Check time
        if time.time() - start_time >= time_limit:
            break
    
    return value

def quiescence(state, alpha, beta, start_time, time_limit):
    """Quiescence search to evaluate captures only at leaf nodes."""
    stand_pat = evaluate(state)
    
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
    
    # Only consider capture moves
    capture_moves = []
    for move in state.get_all_moves():
        if move[1] in state.opp:  # Capture move
            capture_moves.append(move)
    
    if not capture_moves:
        return stand_pat
    
    for move in capture_moves:
        # Check time
        if time.time() - start_time >= time_limit:
            break
            
        new_state = state.make_move(move)
        score = -quiescence(new_state, -beta, -alpha, start_time, time_limit)
        
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    
    return alpha

def evaluate(state):
    """Evaluate the position from the perspective of the player to move."""
    # Material score
    material = len(state.me) * 100 - len(state.opp) * 100
    
    # Advancement score
    advancement = 0
    for piece in state.me:
        if state.forward_dir == -1:  # Black moving down
            rows_advanced = 7 - piece[0]  # From row 7 to 0
        else:  # White moving up
            rows_advanced = piece[0]  # From row 0 to 7
        advancement += rows_advanced * 15
    
    for piece in state.opp:
        if state.forward_dir == -1:  # Black's perspective, opponent is White
            rows_advanced = piece[0]  # White advances upward
        else:  # White's perspective, opponent is Black
            rows_advanced = 7 - piece[0]  # Black advances downward
        advancement -= rows_advanced * 15
    
    # Center control
    center = 0
    for piece in state.me:
        if 3 <= piece[1] <= 4:  # Center columns
            center += 10
    
    for piece in state.opp:
        if 3 <= piece[1] <= 4:
            center -= 10
    
    # Promotion threat
    promotion = 0
    for piece in state.me:
        if abs(piece[0] - state.prom_row) == 1:  # One row from promotion
            # Check if path is clear
            target_row = state.prom_row
            target_col = piece[1]
            
            # Can move straight forward if empty
            if (target_row, target_col) not in state.me and (target_row, target_col) not in state.opp:
                promotion += 500
            # Can capture diagonally to promote
            else:
                for dc in [-1, 1]:
                    if 0 <= target_col + dc <= 7:
                        if (target_row, target_col + dc) in state.opp:
                            promotion += 500
                            break
    
    # Safety (penalize pieces that can be captured)
    safety = 0
    for piece in state.me:
        # Check if opponent can capture this piece
        for dc in [-1, 1]:
            opp_row = piece[0] - state.forward_dir  # Opposite direction
            opp_col = piece[1] + dc
            if 0 <= opp_row <= 7 and 0 <= opp_col <= 7:
                if (opp_row, opp_col) in state.opp:
                    safety -= 30  # Piece is under attack
    
    # Pawn structure (connected pieces)
    structure = 0
    for piece in state.me:
        # Check for adjacent friendly pieces in same or adjacent rows
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                adj_row = piece[0] + dr
                adj_col = piece[1] + dc
                if (adj_row, adj_col) in state.me:
                    structure += 5
    
    # Mobility
    mobility = len(state.get_all_moves()) * 2
    
    # King of the Hill (control of center rows)
    hill = 0
    for piece in state.me:
        if 3 <= piece[0] <= 4:  # Center rows
            hill += 5
    
    # Total score
    total = (material + advancement + center + promotion + safety + 
             structure + mobility + hill)
    
    return total

class BreakthroughState:
    """Represents a Breakthrough game state."""
    
    def __init__(self, me, opp, forward_dir, home_row, prom_row):
        self.me = me
        self.opp = opp
        self.forward_dir = forward_dir
        self.home_row = home_row
        self.prom_row = prom_row
    
    def get_all_moves(self):
        """Generate all legal moves for the current player."""
        moves = set()
        
        for piece in self.me:
            from_row, from_col = piece
            
            # Forward move (straight ahead)
            to_row = from_row + self.forward_dir
            if 0 <= to_row <= 7:
                # Straight forward
                if (to_row, from_col) not in self.me and (to_row, from_col) not in self.opp:
                    moves.add(((from_row, from_col), (to_row, from_col)))
                
                # Diagonal moves (left and right)
                for dc in [-1, 1]:
                    to_col = from_col + dc
                    if 0 <= to_col <= 7:
                        to_pos = (to_row, to_col)
                        # Diagonal can be to empty square or opponent piece (capture)
                        if to_pos not in self.me:  # Can't capture own piece
                            moves.add(((from_row, from_col), to_pos))
        
        return moves
    
    def make_move(self, move):
        """Return a new state after making the move."""
        from_pos, to_pos = move
        new_me = set(self.me)
        new_opp = set(self.opp)
        
        # Remove piece from old position
        new_me.remove(from_pos)
        
        # Add piece to new position
        new_me.add(to_pos)
        
        # If capture, remove opponent piece
        if to_pos in self.opp:
            new_opp.remove(to_pos)
        
        return BreakthroughState(new_me, new_opp, self.forward_dir, self.home_row, self.prom_row)
    
    def is_terminal(self):
        """Check if the game is over."""
        # Check for promotion
        for piece in self.me:
            if piece[0] == self.prom_row:
                return True
        
        # Check if opponent has no pieces
        if not self.opp:
            return True
        
        # Check if current player has no moves (shouldn't happen in Breakthrough but check anyway)
        if not self.get_all_moves():
            return True
        
        return False
    
    def __hash__(self):
        return hash((frozenset(self.me), frozenset(self.opp)))
    
    def __eq__(self, other):
        return (self.me == other.me and self.opp == other.opp)

# Test function (not used in production)
if __name__ == "__main__":
    # Example initial position
    me = [(6, i) for i in range(8)] + [(7, i) for i in range(8)]
    opp = [(0, i) for i in range(8)] + [(1, i) for i in range(8)]
    
    result = policy(me, opp, 'b')
    print(f"Best move: {result}")
