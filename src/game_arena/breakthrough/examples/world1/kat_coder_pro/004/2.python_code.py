
import random
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    # Convert lists to sets for faster lookups
    my_pieces = set(me)
    opp_pieces = set(opp)
    
    # Determine direction of movement
    direction = -1 if color == 'w' else 1
    
    # Get all legal moves
    legal_moves = get_legal_moves(my_pieces, opp_pieces, direction)
    
    if not legal_moves:
        # Fallback if no legal moves (shouldn't happen in Breakthrough)
        return random.choice(get_all_possible_moves(my_pieces, opp_pieces, direction))
    
    # Use minimax with alpha-beta pruning to find the best move
    best_move = None
    best_value = float('-inf') if color == 'w' else float('inf')
    
    # Sort moves to improve alpha-beta pruning efficiency
    legal_moves.sort(key=lambda move: evaluate_move(move, my_pieces, opp_pieces, direction), reverse=color == 'w')
    
    for move in legal_moves:
        new_me, new_opp = apply_move(move, my_pieces.copy(), opp_pieces.copy())
        value = minimax(new_me, new_opp, 2, float('-inf'), float('inf'), False if color == 'w' else True, direction)
        
        if (color == 'w' and value > best_value) or (color == 'b' and value < best_value):
            best_value = value
            best_move = move
    
    return best_move

def get_legal_moves(me: set, opp: set, direction: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Get all legal moves for the current player."""
    moves = []
    
    for piece in me:
        row, col = piece
        
        # Forward move
        forward_pos = (row + direction, col)
        if 0 <= forward_pos[0] <= 7 and forward_pos not in me and forward_pos not in opp:
            moves.append((piece, forward_pos))
        
        # Diagonal captures
        for dc in [-1, 1]:
            diag_pos = (row + direction, col + dc)
            if 0 <= diag_pos[0] <= 7 and 0 <= diag_pos[1] <= 7:
                if diag_pos in opp:
                    moves.append((piece, diag_pos))
                elif diag_pos not in me:
                    # Diagonal non-capture move (only allowed if forward is blocked)
                    forward_pos = (row + direction, col)
                    if forward_pos[0] <= 7 and forward_pos[0] >= 0 and forward_pos in opp:
                        moves.append((piece, diag_pos))
    
    return moves

def get_all_possible_moves(me: set, opp: set, direction: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Get all possible moves without checking if they're legal."""
    moves = []
    
    for piece in me:
        row, col = piece
        
        # All possible target positions
        targets = [
            (row + direction, col),      # Forward
            (row + direction, col - 1),  # Diagonal left
            (row + direction, col + 1),  # Diagonal right
        ]
        
        for target in targets:
            if 0 <= target[0] <= 7 and 0 <= target[1] <= 7:
                moves.append((piece, target))
    
    return moves

def apply_move(move: Tuple[Tuple[int, int], Tuple[int, int]], me: set, opp: set) -> Tuple[set, set]:
    """Apply a move and return new board states."""
    from_pos, to_pos = move
    
    # Remove from old position
    me.remove(from_pos)
    
    # Check if capturing
    if to_pos in opp:
        opp.remove(to_pos)
    
    # Add to new position
    me.add(to_pos)
    
    return me, opp

def evaluate_move(move: Tuple[Tuple[int, int], Tuple[int, int]], me: set, opp: set, direction: int) -> float:
    """Evaluate a move for sorting purposes."""
    from_pos, to_pos = move
    
    # Prefer moves that promote
    if (direction == 1 and to_pos[0] == 0) or (direction == -1 and to_pos[0] == 7):
        return 1000
    
    # Prefer captures
    if to_pos in opp:
        return 100
    
    # Prefer forward moves
    return abs(to_pos[0] - from_pos[0])

def evaluate_board(me: set, opp: set, direction: int) -> float:
    """Evaluate the current board state."""
    score = 0
    
    # Piece count
    score += len(me) * 10
    score -= len(opp) * 10
    
    # Position values
    for piece in me:
        row, col = piece
        # Closer to opponent's home row is better
        dist = abs(row - (7 if direction == 1 else 0))
        score += (7 - dist) * 0.5
    
    for piece in opp:
        row, col = piece
        dist = abs(row - (0 if direction == 1 else 7))
        score -= (7 - dist) * 0.5
    
    # Check for promotion threat
    for piece in me:
        row, col = piece
        if (direction == 1 and row <= 1) or (direction == -1 and row >= 6):
            score += 5
    
    return score

def check_win(me: set, opp: set, direction: int) -> int:
    """Check if the game is over. Returns 1 if me wins, -1 if opp wins, 0 if ongoing."""
    # Check if any piece reached opponent's home row
    for piece in me:
        row = piece[0]
        if (direction == 1 and row == 0) or (direction == -1 and row == 7):
            return 1
    
    for piece in opp:
        row = piece[0]
        if (direction == -1 and row == 0) or (direction == 1 and row == 7):
            return -1
    
    # Check if all opponent pieces are captured
    if not opp:
        return 1
    if not me:
        return -1
    
    return 0

def minimax(me: set, opp: set, depth: int, alpha: float, beta: float, maximizing: bool, direction: int) -> float:
    """Minimax algorithm with alpha-beta pruning."""
    # Check for terminal state
    result = check_win(me, opp, direction)
    if result != 0:
        return result * 1000  # Large value for winning
    
    if depth == 0:
        return evaluate_board(me, opp, -direction if maximizing else direction)
    
    if maximizing:
        max_eval = float('-inf')
        moves = get_legal_moves(me, opp, direction)
        
        for move in moves:
            new_me, new_opp = apply_move(move, me.copy(), opp.copy())
            eval_val = minimax(new_me, new_opp, depth - 1, alpha, beta, False, -direction)
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        moves = get_legal_moves(opp, me, -direction)
        
        for move in moves:
            new_opp, new_me = apply_move(move, opp.copy(), me.copy())
            eval_val = minimax(new_me, new_opp, depth - 1, alpha, beta, True, direction)
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval
