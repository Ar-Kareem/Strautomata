
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    # Determine movement direction based on color
    direction = 1 if color == 'b' else -1  # Black moves down (increasing row), white moves up (decreasing row)
    home_row = 7 if color == 'b' else 0
    opponent_home_row = 0 if color == 'b' else 7
    
    # Convert opponent positions to a set for faster lookup
    opp_positions = set(opp)
    
    # Generate all legal moves
    legal_moves = []
    
    for piece in me:
        row, col = piece
        
        # Check forward move
        forward_pos = (row + direction, col)
        if 0 <= forward_pos[0] <= 7 and 0 <= forward_pos[1] <= 7 and forward_pos not in me and forward_pos not in opp_positions:
            legal_moves.append((piece, forward_pos))
            
        # Check diagonal left capture
        diag_left = (row + direction, col - 1)
        if 0 <= diag_left[0] <= 7 and 0 <= diag_left[1] <= 7:
            if diag_left in opp_positions:
                legal_moves.append((piece, diag_left))
                
        # Check diagonal right capture
        diag_right = (row + direction, col + 1)
        if 0 <= diag_right[0] <= 7 and 0 <= diag_right[1] <= 7:
            if diag_right in opp_positions:
                legal_moves.append((piece, diag_right))
                
        # Check diagonal left move (non-capture)
        diag_left_move = (row + direction, col - 1)
        if 0 <= diag_left_move[0] <= 7 and 0 <= diag_left_move[1] <= 7:
            if diag_left_move not in me and diag_left_move not in opp_positions:
                legal_moves.append((piece, diag_left_move))
                
        # Check diagonal right move (non-capture)
        diag_right_move = (row + direction, col + 1)
        if 0 <= diag_right_move[0] <= 7 and 0 <= diag_right_move[1] <= 7:
            if diag_right_move not in me and diag_right_move not in opp_positions:
                legal_moves.append((piece, diag_right_move))
    
    # If no legal moves, return a default (should not happen in valid game state)
    if not legal_moves:
        return ((0, 0), (0, 0))
    
    # Prioritize winning moves (reach opponent's home row)
    winning_moves = [move for move in legal_moves if move[1][0] == opponent_home_row]
    if winning_moves:
        return random.choice(winning_moves)
    
    # Prioritize capturing moves
    capturing_moves = [move for move in legal_moves if move[1] in opp_positions]
    if capturing_moves:
        # Choose capture that advances most toward opponent's home row
        best_capture = max(capturing_moves, key=lambda m: (m[1][0] * direction, -abs(m[1][1] - 3.5)))
        return best_capture
    
    # Prioritize advancing pieces closest to opponent's home row
    def move_priority(move):
        piece, target = move
        # Prioritize advancement, then central control
        advancement = target[0] * direction
        centrality = -abs(target[1] - 3.5)  # Prefer center columns
        return (advancement, centrality)
    
    # Return the best move based on priority
    best_move = max(legal_moves, key=move_priority)
    return best_move
