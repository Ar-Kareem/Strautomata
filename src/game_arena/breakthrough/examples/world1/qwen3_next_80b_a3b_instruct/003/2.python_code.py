
import numpy as np
from typing import List, Tuple

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Implements a minimax-based AI with alpha-beta pruning for Breakthrough.
    Prioritizes winning moves, captures, and advancement toward opponent's home row.
    """
    
    # Define home rows based on color
    if color == 'b':
        # Black moves downward (to lower row values), home row is row 0 for white
        home_row = 0
        direction = -1  # Black moves down (row decreases)
    else:  # color == 'w'
        # White moves upward (to higher row values), home row is row 7 for black
        home_row = 7
        direction = 1   # White moves up (row increases)
    
    # Check for immediate win: any piece can reach opponent's home row
    for piece in me:
        row, col = piece
        # Straight forward move to home row
        if row + direction == home_row:
            return ((row, col), (row + direction, col))
        
        # Diagonal forward moves to home row
        for dc in [-1, 1]:
            new_col = col + dc
            if 0 <= new_col <= 7:
                if row + direction == home_row:
                    return ((row, col), (row + direction, new_col))
    
    # Check for immediate captures
    for piece in me:
        row, col = piece
        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            # Check if diagonal move is within bounds
            if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                # Check if opponent piece is there
                if (new_row, new_col) in opp:
                    return ((row, col), (new_row, new_col))
    
    # Collect all possible moves
    possible_moves = []
    
    for piece in me:
        row, col = piece
        
        # Straight forward move
        new_row = row + direction
        new_col = col
        if 0 <= new_row <= 7 and 0 <= new_col <= 7:
            if (new_row, new_col) not in me and (new_row, new_col) not in opp:
                possible_moves.append(((row, col), (new_row, new_col)))
        
        # Diagonal forward moves (non-capturing)
        for dc in [-1, 1]:
            new_row = row + direction
            new_col = col + dc
            if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                if (new_row, new_col) not in me and (new_row, new_col) not in opp:
                    possible_moves.append(((row, col), (new_row, new_col)))
    
    # If no moves possible (shouldn't happen in practice), return dummy
    if not possible_moves:
        # This is a fallback - should never be reached in valid game state
        if me:
            return (me[0], (me[0][0] + direction, me[0][1]))
        else:
            return ((0, 0), (0, 0))
    
    # Use minimax with alpha-beta pruning for better move selection
    # Depth limited to 3 for performance, increase if few pieces remain
    total_pieces = len(me) + len(opp)
    depth = 3 if total_pieces > 10 else 4
    
    best_move = None
    best_value = float('-inf') if color == 'b' else float('inf')
    
    # For black (maximizer), we want highest score
    # For white (minimizer), we want lowest score
    is_maximizing = (color == 'b')
    
    # Sort moves to prioritize captures and advancement (move ordering for alpha-beta)
    def move_score(move):
        from_pos, to_pos = move
        row, col = from_pos
        new_row, new_col = to_pos
        
        score = 0
        
        # Bonus for advancing toward goal
        if color == 'b':  # Black moving down
            score += 10 * (7 - new_row)  # Higher score for closer to row 0
        else:  # White moving up
            score += 10 * new_row  # Higher score for closer to row 7
        
        # Bonus for capturing
        if to_pos in opp:
            score += 1000
            
        # Bonus for central control
        col_center_value = 4 - abs(new_col - 3.5)
        score += col_center_value * 2
        
        # Penalty for being isolated (no friendly pieces adjacent)
        has_neighbor = False
        for r_offset in [-1, 0, 1]:
            for c_offset in [-1, 1]:  # Only check diagonals for pawn structure
                neighbor_row, neighbor_col = row + r_offset, col + c_offset
                if 0 <= neighbor_row <= 7 and 0 <= neighbor_col <= 7:
                    if (neighbor_row, neighbor_col) in me:
                        has_neighbor = True
                        break
            if has_neighbor:
                break
        if not has_neighbor:
            score -= 5  # Penalty for isolated pawn
        
        return score
    
    possible_moves.sort(key=move_score, reverse=True)
    
    # Alpha-beta pruning search
    def alphabeta(board_me, board_opp, depth, alpha, beta, maximizing_player):
        # Terminal conditions
        if depth == 0:
            return evaluate_board(board_me, board_opp, color)
        
        # Check for immediate wins
        for piece in board_me:
            row, col = piece
            if row + direction == home_row:
                return float('inf') if maximizing_player else float('-inf')
        
        # Get all legal moves
        moves = []
        for piece in board_me:
            row, col = piece
            
            # Straight forward move
            new_row = row + direction
            new_col = col
            if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                if (new_row, new_col) not in board_me and (new_row, new_col) not in board_opp:
                    moves.append(((row, col), (new_row, new_col)))
            
            # Diagonal forward moves (non-capturing)
            for dc in [-1, 1]:
                new_row = row + direction
                new_col = col + dc
                if 0 <= new_row <= 7 and 0 <= new_col <= 7:
                    if (new_row, new_col) not in board_me and (new_row, new_col) not in board_opp:
                        moves.append(((row, col), (new_row, new_col)))
        
        # Prioritize captures
        capture_moves = []
        non_capture_moves = []
        for move in moves:
            from_pos, to_pos = move
            if to_pos in board_opp:
                capture_moves.append(move)
            else:
                non_capture_moves.append(move)
        
        # Reorder moves to prioritize captures
        moves = capture_moves + non_capture_moves
        
        if not moves:
            return evaluate_board(board_me, board_opp, color)
        
        if maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                # Make move
                from_pos, to_pos = move
                new_me = [p if p != from_pos else to_pos for p in board_me]
                new_opp = [p for p in board_opp if p != to_pos]  # If capture
                
                eval_score = alphabeta(new_me, new_opp, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break  # Beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                # Make move (for opponent)
                from_pos, to_pos = move
                new_opp = [p if p != from_pos else to_pos for p in board_opp]
                new_me = [p for p in board_me if p != to_pos]  # If capture
                
                eval_score = alphabeta(new_me, new_opp, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break  # Alpha cutoff
            return min_eval
    
    # Evaluate the board state
    def evaluate_board(my_pieces, opp_pieces, player_color):
        if not opp_pieces:  # We win if all opponent pieces are captured
            return float('inf')
        
        # Check if any of our pieces reached opponent's home row
        for row, col in my_pieces:
            if row == home_row:
                return float('inf')
        
        score = 0
        
        # Piece count advantage
        score += len(my_pieces) * 10
        score -= len(opp_pieces) * 10
        
        # Advancement toward goal
        for row, col in my_pieces:
            if player_color == 'b':  # Black wants to reach row 0
                score += (7 - row) * 2
            else:  # White wants to reach row 7
                score += row * 2
        
        # Center control
        for row, col in my_pieces:
            col_center_value = 4 - abs(col - 3.5)
            score += col_center_value * 1.5
        
        # Opponent advancement (penalty)
        for row, col in opp_pieces:
            if player_color == 'b':  # Opponent is white, wants to reach row 7
                score -= row * 1.5
            else:  # Opponent is black, wants to reach row 0
                score -= (7 - row) * 1.5
        
        # Connected pawns bonus
        for i, (row1, col1) in enumerate(my_pieces):
            for j in range(i + 1, len(my_pieces)):
                row2, col2 = my_pieces[j]
                # Check if pieces are adjacent (including diagonally)
                if abs(row1 - row2) <= 1 and abs(col1 - col2) <= 1:
                    score += 1
        
        # Isolated pawns penalty
        for row, col in my_pieces:
            isolated = True
            for dr in [-1, 0, 1]:
                for dc in [-1, 1]:  # Only check diagonals
                    nr, nc = row + dr, col + dc
                    if 0 <= nr <= 7 and 0 <= nc <= 7:
                        if (nr, nc) in my_pieces:
                            isolated = False
                            break
                if not isolated:
                    break
            if isolated:
                score -= 2
        
        return score
    
    # If we have very few pieces, do a full search
    if len(me) <= 2:
        depth = 4
    
    # Use alpha-beta to find best move
    best_move_score = float('-inf') if color == 'b' else float('inf')
    best_move_selected = possible_moves[0]  # Default
    
    for move in possible_moves:
        from_pos, to_pos = move
        new_me = [p if p != from_pos else to_pos for p in me]
        new_opp = [p for p in opp if p != to_pos]  # Remove captured piece
        
        if to_pos in opp:  # This is a capture
            move_score = 1000  # High priority for captures
        else:
            # Otherwise, evaluate this move with minimax
            if len(me) <= 3 or len(opp) <= 3:  # For endgames, go deeper
                child_score = alphabeta(new_me, new_opp, 4, float('-inf'), float('inf'), color == 'b')
            else:
                child_score = alphabeta(new_me, new_opp, depth, float('-inf'), float('inf'), color == 'b')
            
            move_score = child_score
            
            # Bonus for advancing toward goal
            row, col = from_pos
            new_row, new_col = to_pos
            if color == 'b':
                move_score += (7 - new_row) * 5 - (7 - row) * 5
            else:
                move_score += new_row * 5 - row * 5
        
        if (color == 'b' and move_score > best_move_score) or \
           (color == 'w' and move_score < best_move_score):
            best_move_score = move_score
            best_move_selected = move
    
    return best_move_selected
