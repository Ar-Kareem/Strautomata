
import numpy as np
from typing import List, Tuple, Optional

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Main policy function that determines the next move for a Checkers game.
    
    Args:
        my_men: List of coordinates for my regular pieces
        my_kings: List of coordinates for my kings
        opp_men: List of coordinates for opponent's regular pieces
        opp_kings: List of coordinates for opponent's kings
        color: 'b' for black (moves downward) or 'w' for white (moves upward)
    
    Returns:
        Tuple containing ((from_row, from_col), (to_row, to_col))
    """
    
    def is_valid_square(row, col):
        """Check if a square is valid (within bounds and dark)"""
        return 0 <= row < 8 and 0 <= col < 8 and (row + col) % 2 == 1
    
    def get_piece_type(row, col, my_men, my_kings, opp_men, opp_kings):
        """Determine what type of piece is on a given square"""
        if (row, col) in my_men:
            return 'my_men'
        elif (row, col) in my_kings:
            return 'my_kings'
        elif (row, col) in opp_men:
            return 'opp_men'
        elif (row, col) in opp_kings:
            return 'opp_kings'
        return None
    
    def get_possible_moves(men, kings, opp_men, opp_kings, color):
        """Generate all possible moves for the current player"""
        moves = []
        captures = []
        
        # Combine my pieces
        my_pieces = men + kings
        
        for row, col in my_pieces:
            # Determine if piece is a king
            is_king = (row, col) in kings
            
            # Determine direction of movement
            directions = []
            if not is_king:
                if color == 'b':
                    directions = [(-1, -1), (-1, 1)]  # Black moves up
                else:
                    directions = [(1, -1), (1, 1)]    # White moves down
            else:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]  # Kings move in all directions
            
            # Check for captures first
            for dr, dc in directions:
                new_row, new_col = row + dr, col + dc
                jump_row, jump_col = row + 2*dr, col + 2*dc
                
                # Check if we can capture
                if (is_valid_square(new_row, new_col) and 
                    is_valid_square(jump_row, jump_col) and
                    get_piece_type(new_row, new_col, men, kings, opp_men, opp_kings) in ['opp_men', 'opp_kings'] and
                    get_piece_type(jump_row, jump_col, men, kings, opp_men, opp_kings) is None):
                    
                    # Create new board state after capture
                    new_men = [p for p in men if p != (row, col)]
                    new_kings = [p for p in kings if p != (row, col)]
                    new_opp_men = [p for p in opp_men if p != (new_row, new_col)]
                    new_opp_kings = [p for p in opp_kings if p != (new_row, new_col)]
                    
                    # Check if piece becomes a king
                    if not is_king:
                        if (color == 'b' and jump_row == 0) or (color == 'w' and jump_row == 7):
                            new_kings.append((jump_row, jump_col))
                        else:
                            new_men.append((jump_row, jump_col))
                    else:
                        new_kings.append((jump_row, jump_col))
                    
                    # Recursively check for additional captures
                    additional_captures = get_possible_captures(jump_row, jump_col, new_men, new_kings, new_opp_men, new_opp_kings, color)
                    
                    if additional_captures:
                        for capture in additional_captures:
                            captures.append([(row, col)] + capture)
                    else:
                        captures.append([(row, col), (jump_row, jump_col)])
            
            # If no captures, check for regular moves
            if not captures:
                for dr, dc in directions:
                    new_row, new_col = row + dr, col + dc
                    
                    if (is_valid_square(new_row, new_col) and 
                        get_piece_type(new_row, new_col, men, kings, opp_men, opp_kings) is None):
                        
                        # Check if piece becomes a king
                        if not is_king:
                            if (color == 'b' and new_row == 0) or (color == 'w' and new_row == 7):
                                new_kings = kings.copy()
                                new_men = [p for p in men if p != (row, col)]
                                new_kings.append((new_row, new_col))
                            else:
                                new_men = men.copy()
                                new_men.remove((row, col))
                                new_men.append((new_row, new_col))
                                new_kings = kings.copy()
                        else:
                            new_men = men.copy()
                            new_kings = kings.copy()
                            new_kings.remove((row, col))
                            new_kings.append((new_row, new_col))
                        
                        moves.append([(row, col), (new_row, new_col)])
        
        # Return captures if available, otherwise return regular moves
        if captures:
            return captures
        return moves
    
    def get_possible_captures(row, col, men, kings, opp_men, opp_kings, color):
        """Recursively find all possible capture sequences from a given position"""
        captures = []
        is_king = (row, col) in kings
        
        # Determine directions
        directions = []
        if not is_king:
            if color == 'b':
                directions = [(-1, -1), (-1, 1)]
            else:
                directions = [(1, -1), (1, 1)]
        else:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            jump_row, jump_col = row + 2*dr, col + 2*dc
            
            if (is_valid_square(new_row, new_col) and 
                is_valid_square(jump_row, jump_col) and
                get_piece_type(new_row, new_col, men, kings, opp_men, opp_kings) in ['opp_men', 'opp_kings'] and
                get_piece_type(jump_row, jump_col, men, kings, opp_men, opp_kings) is None):
                
                # Create new board state
                new_men = men.copy()
                new_kings = kings.copy()
                new_opp_men = [p for p in opp_men if p != (new_row, new_col)]
                new_opp_kings = [p for p in opp_kings if p != (new_row, new_col)]
                
                # Update position
                if (row, col) in new_men:
                    new_men.remove((row, col))
                    if (color == 'b' and jump_row == 0) or (color == 'w' and jump_row == 7):
                        new_kings.append((jump_row, jump_col))
                    else:
                        new_men.append((jump_row, jump_col))
                else:
                    new_kings.remove((row, col))
                    new_kings.append((jump_row, jump_col))
                
                # Recursively find more captures
                additional_captures = get_possible_captures(jump_row, jump_col, new_men, new_kings, new_opp_men, new_opp_kings, color)
                
                if additional_captures:
                    for capture in additional_captures:
                        captures.append([(row, col)] + capture)
                else:
                    captures.append([(row, col), (jump_row, jump_col)])
        
        return captures
    
    def evaluate_board(men, kings, opp_men, opp_kings, color):
        """Evaluate the current board state"""
        score = 0
        
        # Piece values
        men_value = 100
        kings_value = 200
        
        # Evaluate my pieces
        for row, col in men:
            score += men_value
            # Bonus for being closer to promotion
            if color == 'b':
                score += (7 - row) * 10
            else:
                score += row * 10
        
        for row, col in kings:
            score += kings_value
        
        # Evaluate opponent pieces
        for row, col in opp_men:
            score -= men_value
            # Bonus for being closer to promotion
            if color == 'b':
                score -= row * 10
            else:
                score -= (7 - row) * 10
        
        for row, col in opp_kings:
            score -= kings_value
        
        # Mobility bonus
        my_moves = len(get_possible_moves(men, kings, opp_men, opp_kings, color))
        opp_moves = len(get_possible_moves(opp_men, opp_kings, men, kings, 'w' if color == 'b' else 'b'))
        score += (my_moves - opp_moves) * 5
        
        # Center control bonus
        center_squares = [(3, 3), (3, 5), (4, 2), (4, 4)]
        for row, col in men + kings:
            if (row, col) in center_squares:
                score += 10
        
        for row, col in opp_men + opp_kings:
            if (row, col) in center_squares:
                score -= 10
        
        return score
    
    def minimax(men, kings, opp_men, opp_kings, color, depth, alpha, beta, maximizing_player):
        """Minimax algorithm with alpha-beta pruning"""
        if depth == 0:
            return evaluate_board(men, kings, opp_men, opp_kings, color), None
        
        # Determine current player
        current_men = men if maximizing_player else opp_men
        current_kings = kings if maximizing_player else opp_kings
        current_color = color if maximizing_player else ('w' if color == 'b' else 'b')
        
        # Get possible moves
        moves = get_possible_moves(current_men, current_kings, opp_men, opp_kings, current_color)
        
        if not moves:
            # No moves available, game over
            return evaluate_board(men, kings, opp_men, opp_kings, color), None
        
        best_move = None
        
        if maximizing_player:
            max_eval = float('-inf')
            for move_seq in moves:
                # Execute move
                from_pos = move_seq[0]
                to_pos = move_seq[-1]
                
                # Update board state
                new_men = men.copy()
                new_kings = kings.copy()
                new_opp_men = opp_men.copy()
                new_opp_kings = opp_kings.copy()
                
                # Remove from original position
                if from_pos in new_men:
                    new_men.remove(from_pos)
                elif from_pos in new_kings:
                    new_kings.remove(from_pos)
                
                # Add to new position
                if from_pos in men:
                    if (color == 'b' and to_pos[0] == 0) or (color == 'w' and to_pos[0] == 7):
                        new_kings.append(to_pos)
                    else:
                        new_men.append(to_pos)
                else:
                    new_kings.append(to_pos)
                
                # Remove captured pieces
                for i in range(1, len(move_seq)):
                    mid_row = (move_seq[i-1][0] + move_seq[i][0]) // 2
                    mid_col = (move_seq[i-1][1] + move_seq[i][1]) // 2
                    
                    if (mid_row, mid_col) in new_opp_men:
                        new_opp_men.remove((mid_row, mid_col))
                    elif (mid_row, mid_col) in new_opp_kings:
                        new_opp_kings.remove((mid_row, mid_col))
                
                # Recurse
                eval_score, _ = minimax(new_men, new_kings, new_opp_men, new_opp_kings, color, depth - 1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move_seq
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move_seq in moves:
                # Execute move
                from_pos = move_seq[0]
                to_pos = move_seq[-1]
                
                # Update board state
                new_men = opp_men.copy()
                new_kings = opp_kings.copy()
                new_opp_men = men.copy()
                new_opp_kings = kings.copy()
                
                # Remove from original position
                if from_pos in new_men:
                    new_men.remove(from_pos)
                elif from_pos in new_kings:
                    new_kings.remove(from_pos)
                
                # Add to new position
                if from_pos in opp_men:
                    if (current_color == 'b' and to_pos[0] == 0) or (current_color == 'w' and to_pos[0] == 7):
                        new_kings.append(to_pos)
                    else:
                        new_men.append(to_pos)
                else:
                    new_kings.append(to_pos)
                
                # Remove captured pieces
                for i in range(1, len(move_seq)):
                    mid_row = (move_seq[i-1][0] + move_seq[i][0]) // 2
                    mid_col = (move_seq[i-1][1] + move_seq[i][1]) // 2
                    
                    if (mid_row, mid_col) in new_opp_men:
                        new_opp_men.remove((mid_row, mid_col))
                    elif (mid_row, mid_col) in new_opp_kings:
                        new_opp_kings.remove((mid_row, mid_col))
                
                # Recurse
                eval_score, _ = minimax(new_opp_men, new_opp_kings, new_men, new_kings, color, depth - 1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move_seq
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    # Determine search depth based on number of pieces
    total_pieces = len(my_men) + len(my_kings) + len(opp_men) + len(opp_kings)
    if total_pieces > 20:
        depth = 4
    elif total_pieces > 12:
        depth = 5
    else:
        depth = 6
    
    # Get best move
    _, best_move = minimax(my_men, my_kings, opp_men, opp_kings, color, depth, float('-inf'), float('inf'), True)
    
    # Return the first move in the sequence
    if best_move and len(best_move) >= 2:
        return best_move[0], best_move[1]
    
    # Fallback: return first available move
    available_moves = get_possible_moves(my_men, my_kings, opp_men, opp_kings, color)
    if available_moves:
        return available_moves[0][0], available_moves[0][1]
    
    # Emergency fallback: return a dummy move
    return ((0, 0), (0, 0))
