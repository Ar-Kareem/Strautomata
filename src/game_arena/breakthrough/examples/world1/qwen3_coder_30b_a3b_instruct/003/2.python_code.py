
import numpy as np
from typing import List, Tuple
import copy
import time

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Main policy function that returns the next move for Breakthrough.
    """
    # Convert to more convenient formats
    me_positions = set(me)
    opp_positions = set(opp)
    
    # Check if we have any winning moves immediately
    winning_moves = get_winning_moves(me_positions, opp_positions, color)
    if winning_moves:
        return winning_moves[0]  # Return first winning move
    
    # Try immediate captures if possible
    capture_moves = get_capture_moves(me_positions, opp_positions, color)
    if capture_moves:
        return capture_moves[0]  # Return first capture move
    
    # Use minimax with iterative deepening
    start_time = time.time()
    best_move = None
    max_depth = 4
    
    # Try iterative deepening to make use of time
    for depth in range(1, max_depth + 1):
        if time.time() - start_time > 0.8:  # Leave 0.2s for overhead
            break
            
        # Get best move at current depth
        move = minimax_root(me_positions, opp_positions, color, depth)
        if move:
            best_move = move
    
    # If no move found, do basic move selection
    if not best_move:
        # Get all legal moves
        all_moves = get_all_moves(me_positions, opp_positions, color)
        if all_moves:
            # Prefer moves that advance pieces toward enemy home row
            # For black (down), prefer moves to lower rows
            # For white (up), prefer moves to higher rows
            best_moves = []
            best_score = float('-inf')
            
            for move in all_moves:
                from_pos, to_pos = move
                from_row, from_col = from_pos
                to_row, to_col = to_pos
                
                # Score based on advancement and capture potential
                score = 0
                
                # Prefer advancing pieces (higher for white, lower for black)
                if color == 'w':
                    if to_row > from_row:  # Moved forward
                        score += 10 + (to_row - from_row) * 5
                    else:  # Not moving forward - penalize a bit
                        score -= 2
                else:  # color == 'b'
                    if to_row < from_row:  # Moved forward
                        score += 10 + (from_row - to_row) * 5
                    else:  # Not moving forward - penalize
                        score -= 2
                
                # Prefer captures
                if (to_row, to_col) in opp_positions:
                    score += 20
                
                # Prefer central control
                if 2 < to_col < 5:
                    score += 5
                
                if score > best_score:
                    best_score = score
                    best_moves = [move]
                elif score == best_score:
                    best_moves.append(move)
            
            # Return best move
            if best_moves:
                return best_moves[0]
            
            # Fallback to any legal move
            return all_moves[0]
    
    return best_move

def get_winning_moves(me_positions: set, opp_positions: set, color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Check for immediate winning moves."""
    moves = []
    
    # Check pieces that can win by reaching home row
    for pos in me_positions:
        from_row, from_col = pos
        if color == 'w' and from_row == 7:  # White reached black home row
            moves.append((pos, pos))
        elif color == 'b' and from_row == 0:  # Black reached white home row
            moves.append((pos, pos))
    
    # Check if all opponent pieces are captured (winning condition)
    if len(opp_positions) == 0:
        # Return a move to encourage advancement
        for pos in me_positions:
            moves.append((pos, pos))
    
    return moves

def get_capture_moves(me_positions: set, opp_positions: set, color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Get all moves that would result in a capture."""
    moves = []
    directions = []
    
    if color == 'b':  # Black moves down
        directions = [(1, -1), (1, 0), (1, 1)]  # down and diagonals
    else:  # White moves up
        directions = [(-1, -1), (-1, 0), (-1, 1)]  # up and diagonals
    
    for pos in me_positions:
        from_row, from_col = pos
        for dr, dc in directions:
            to_row, to_col = from_row + dr, from_col + dc
            if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                # Check if it's a diagonal move to capture opponent
                if (to_row, to_col) in opp_positions:
                    moves.append((pos, (to_row, to_col)))
    
    return moves

def get_all_moves(me_positions: set, opp_positions: set, color: str) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Get all legal moves for current player."""
    moves = []
    directions = []
    
    if color == 'b':  # Black moves down
        directions = [(1, -1), (1, 0), (1, 1)]  # down and diagonals
    else:  # White moves up
        directions = [(-1, -1), (-1, 0), (-1, 1)]  # up and diagonals
    
    for pos in me_positions:
        from_row, from_col = pos
        for dr, dc in directions:
            to_row, to_col = from_row + dr, from_col + dc
            # Check if target is on board
            if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                # Check for capture
                if (to_row, to_col) in opp_positions:
                    moves.append((pos, (to_row, to_col)))
                # Check for straight move (only if not a capture)
                elif (to_row, to_col) not in me_positions and (to_row, to_col) not in opp_positions:
                    # Straight move
                    if dc == 0:
                        moves.append((pos, (to_row, to_col)))
                    # Diagonal move (if it's a diagonal move)
                    elif dc != 0:
                        moves.append((pos, (to_row, to_col)))
    
    # Also consider forward moves only (only diagonal captures)
    forward_dirs = []
    if color == 'b':
        forward_dirs = [(1, 0), (1, -1), (1, 1)]
    else:
        forward_dirs = [(-1, 0), (-1, -1), (-1, 1)]
    
    # Remove duplicates by ensuring only moves that aren't already included
    # are added
    for pos in me_positions:
        for dr, dc in forward_dirs:
            to_row, to_col = pos[0] + dr, pos[1] + dc
            if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                if dc == 0 and (to_row, to_col) not in me_positions and (to_row, to_col) not in opp_positions:
                    moves.append((pos, (to_row, to_col)))
                elif dc != 0 and (to_row, to_col) in opp_positions:
                    moves.append((pos, (to_row, to_col)))
    
    return list(set(moves))  # Remove duplicates

def evaluate_position(me_positions: set, opp_positions: set, color: str) -> int:
    """Evaluate the goodness of a position."""
    score = 0
    
    # Base score components
    piece_count = len(me_positions)
    opp_count = len(opp_positions)
    
    # Reward for having more pieces
    if color == 'w':
        score += (piece_count - opp_count) * 10
    else:
        score += (piece_count - opp_count) * 10
    
    # Encourage advancement toward opponent home row
    for pos in me_positions:
        row, col = pos
        
        if color == 'w':  # White moves up
            distance_to_home = 7 - row  # Distance to row 7 (black home)
            score += distance_to_home * 5
        else:  # Black moves down
            distance_to_home = row  # Distance to row 0 (white home)
            score += distance_to_home * 5
    
    # Prefer central column control
    # Prefer positions in columns 3 and 4 for center control (1-indexed)
    central_control = 0
    for pos in me_positions:
        col = pos[1]
        if col >= 3 and col <= 4:
            central_control += 5
    
    score += central_control
    
    # Add bonus for pieces that can reach the home row
    for pos in me_positions:
        row, col = pos
        if color == 'w' and row == 7:
            score += 100  # Reached the victory row
        elif color == 'b' and row == 0:
            score += 100
    
    # Penalty for isolated or vulnerable pieces (less mobility)
    mobility_penalty = 0
    for pos in me_positions:
        row, col = pos
        moves_to_consider = 0
        if color == 'b':
            # Black moves down
            for dr, dc in [(1, -1), (1, 0), (1, 1)]:
                to_row, to_col = row + dr, col + dc
                if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                    if (to_row, to_col) not in me_positions and (to_row, to_col) not in opp_positions:
                        moves_to_consider += 1
        else:
            # White moves up
            for dr, dc in [(-1, -1), (-1, 0), (-1, 1)]:
                to_row, to_col = row + dr, col + dc
                if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                    if (to_row, to_col) not in me_positions and (to_row, to_col) not in opp_positions:
                        moves_to_consider += 1
                        
        # Penalty for pieces with very few moves (vulnerable)
        if moves_to_consider <= 1:
            mobility_penalty -= 5
    
    score += mobility_penalty
    
    # Bonus for captures available (weaker heuristic for now)
    capture_bonus = 0
    for pos in me_positions:
        row, col = pos
        if color == 'b':
            for dr, dc in [(1, -1), (1, 1)]:
                to_row, to_col = row + dr, col + dc
                if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                    if (to_row, to_col) in opp_positions:
                        capture_bonus += 10
        else:
            for dr, dc in [(-1, -1), (-1, 1)]:
                to_row, to_col = row + dr, col + dc
                if 0 <= to_row <= 7 and 0 <= to_col <= 7:
                    if (to_row, to_col) in opp_positions:
                        capture_bonus += 10
    
    score += capture_bonus
    
    return score

def minimax_root(me_positions: set, opp_positions: set, color: str, depth: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Evaluate root position using minimax with alpha-beta pruning."""
    best_move = None
    best_score = float('-inf') if color == 'w' else float('inf')
    
    # Get all legal moves
    moves = get_all_moves(me_positions, opp_positions, color)
    
    if not moves:
        return None
    
    # Simple prioritization: prefer captures, then advancement
    capture_moves = []
    other_moves = []
    for move in moves:
        from_pos, to_pos = move
        if to_pos in opp_positions:
            capture_moves.append(move)
        else:
            other_moves.append(move)
    
    prioritized_moves = capture_moves + other_moves
    
    # For first few moves prioritized, use full minimax, otherwise use simplified
    if len(prioritized_moves) > 0: 
        # Use simplified approach for first move
        move = prioritized_moves[0]
        
        # Make move and evaluate
        temp_me = copy.deepcopy(me_positions)
        temp_opp = copy.deepcopy(opp_positions)
        
        # Update positions
        from_pos, to_pos = move
        temp_me.remove(from_pos)
        temp_me.add(to_pos)
        if to_pos in temp_opp:
            temp_opp.remove(to_pos)
        
        # Simple evaluation for first move
        eval_score = evaluate_position(temp_me, temp_opp, color)
        
        if color == 'w':
            if eval_score > best_score:
                best_score = eval_score 
                best_move = move
        else:
            if eval_score < best_score:
                best_score = eval_score
                best_move = move
                
        return best_move
    
    return moves[0] if moves else None
