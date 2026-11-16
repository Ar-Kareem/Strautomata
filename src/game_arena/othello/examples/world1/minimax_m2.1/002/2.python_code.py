
import numpy as np

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Determine the best move for the Othello AI player.
    
    Args:
        you: 8x8 numpy array where 1 indicates your discs
        opponent: 8x8 numpy array where 1 indicates opponent's discs
    
    Returns:
        A move string in algebraic notation (e.g., "d3") or "pass" if no moves
    """
    # Combine boards to get the full game state
    board = you + opponent
    empty_cells = (board == 0)
    
    # Find all legal moves
    legal_moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    # Check each empty cell to see if it's a legal move
    for row in range(8):
        for col in range(8):
            if not empty_cells[row, col]:
                continue
            
            # Check all 8 directions for potential captures
            for d_row, d_col in directions:
                new_row, new_col = row + d_row, col + d_col
                
                # Skip if out of bounds or not adjacent to opponent piece
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    continue
                if opponent[new_row, new_col] != 1:
                    continue
                
                # Traverse in this direction looking for our piece
                current_row, current_col = new_row + d_row, new_col + d_col
                found_our_piece = False
                
                while 0 <= current_row < 8 and 0 <= current_col < 8:
                    if board[current_row, current_col] == 0:
                        # Empty cell, no capture in this direction
                        break
                    elif you[current_row, current_col] == 1:
                        # Found our piece, valid capture!
                        found_our_piece = True
                        break
                    current_row += d_row
                    current_col += d_col
                
                if found_our_piece:
                    legal_moves.append((row, col))
                    break  # No need to check other directions for this cell
    
    # No legal moves available
    if not legal_moves:
        return "pass"
    
    # Count total disks to determine game phase
    total_disks = np.sum(you) + np.sum(opponent)
    
    # Determine phase: opening (<20 disks), midgame (20-50), endgame (>50)
    if total_disks < 20:
        phase_weight = 0.3  # Opening: prioritize mobility
    elif total_disks < 50:
        phase_weight = 0.5  # Midgame: balanced approach
    else:
        phase_weight = 0.8  # Endgame: prioritize disk count
    
    # Evaluate each legal move
    best_move = None
    best_score = -float('inf')
    
    for move_row, move_col in legal_moves:
        # Skip dangerous moves (X-squares) unless they're corners
        if (move_row, move_col) in [(0, 1), (1, 0), (1, 1), (0, 6), (1, 6), (1, 7),
                                     (6, 0), (6, 1), (7, 1), (6, 6), (6, 7), (7, 6)]:
            # Unless this move captures a corner
            if not captures_corner(you, opponent, move_row, move_col):
                continue
        
        move_score = evaluate_move(move_row, move_col, you, opponent, phase_weight)
        
        # Prefer moves that capture more disks
        flips = count_flips(you, opponent, move_row, move_col)
        move_score += flips * 0.5
        
        # Small random factor to add variety (deterministic within same state)
        move_score += 0.001 * (move_row * 8 + move_col)
        
        if move_score > best_score:
            best_score = move_score
            best_move = (move_row, move_col)
    
    # Fallback to first legal move if all were filtered (shouldn't happen)
    if best_move is None:
        best_move = legal_moves[0]
    
    # Convert to algebraic notation
    col_letter = chr(ord('a') + best_move[1])
    row_number = str(best_move[0] + 1)
    return col_letter + row_number


def captures_corner(you: np.ndarray, opponent: np.ndarray, row: int, col: int) -> bool:
    """Check if this move would secure a corner."""
    corners = [(0, 0), (0, 7), (7, 0), (7, 7)]
    
    for corner_row, corner_col in corners:
        # Check if this move is a corner
        if row == corner_row and col == corner_col:
            return True
        
        # Check if this move captures the corner
        if you[corner_row, corner_col] == 1:
            # Check if this move helps secure the corner
            for d_row in [-1, 0, 1]:
                for d_col in [-1, 0, 1]:
                    if d_row == 0 and d_col == 0:
                        continue
                    check_row, check_col = corner_row + d_row, corner_col + d_col
                    if 0 <= check_row < 8 and 0 <= check_col < 8:
                        if check_row == row and check_col == col:
                            # This move is adjacent to an owned corner
                            # Count opponent discs between this move and corner
                            # to see if we capture it
                            if you[row, col] == 0 and opponent[row, col] == 0:
                                return True
    
    return False


def evaluate_move(row: int, col: int, you: np.ndarray, opponent: np.ndarray, 
                  phase_weight: float) -> float:
    """
    Evaluate the strategic value of a move.
    
    Returns a score based on:
    - Positional value (board weights)
    - Impact on mobility
    - Strategic positioning
    """
    # Base positional value from the weight matrix
    score = POSITIONAL_WEIGHTS[row, col]
    
    # Count disks for scoring
    my_disks = np.sum(you)
    opp_disks = np.sum(opponent)
    
    # Disk count component (more important in endgame)
    score += (my_disks - opp_disks) * phase_weight * 2
    
    # Mobility component: count legal moves after this move
    my_mobility = count_moves(you, opponent)
    
    # Temporarily simulate the move to count opponent's response
    temp_you = you.copy()
    temp_you[row, col] = 1
    flip_disks(temp_you, opponent, row, col)
    opp_mobility = count_moves(opponent, temp_you)
    
    # Positive if we have more mobility than opponent
    if my_mobility > 0:
        score += (my_mobility - opp_mobility) * 5
    
    return score


def count_flips(you: np.ndarray, opponent: np.ndarray, row: int, col: int) -> int:
    """Count how many opponent disks would be flipped by this move."""
    board = you + opponent
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    total_flips = 0
    
    for d_row, d_col in directions:
        current_row, current_col = row + d_row, col + d_col
        flips_in_direction = 0
        
        while 0 <= current_row < 8 and 0 <= current_col < 8:
            if board[current_row, current_col] == 0:
                break
            elif you[current_row, current_col] == 1:
                total_flips += flips_in_direction
                break
            flips_in_direction += 1
            current_row += d_row
            current_col += d_col
    
    return total_flips


def flip_disks(you: np.ndarray, opponent: np.ndarray, row: int, col: int) -> None:
    """Flip opponent disks that would be captured by this move."""
    board = you + opponent
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    for d_row, d_col in directions:
        current_row, current_col = row + d_row, col + d_col
        disks_to_flip = []
        
        while 0 <= current_row < 8 and 0 <= current_col < 8:
            if board[current_row, current_col] == 0:
                break
            elif you[current_row, current_col] == 1:
                # Flip all captured disks in this direction
                for f_row, f_col in disks_to_flip:
                    you[f_row, f_col] = 1
                    opponent[f_row, f_col] = 0
                break
            else:
                disks_to_flip.append((current_row, current_col))
            current_row += d_row
            current_col += d_col


def count_moves(current_player: np.ndarray, opponent: np.ndarray) -> int:
    """Count the number of legal moves for the current player."""
    board = current_player + opponent
    empty_cells = (board == 0)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]
    
    move_count = 0
    
    for row in range(8):
        for col in range(8):
            if not empty_cells[row, col]:
                continue
            
            for d_row, d_col in directions:
                new_row, new_col = row + d_row, col + d_col
                if not (0 <= new_row < 8 and 0 <= new_col < 8):
                    continue
                if opponent[new_row, new_col] != 1:
                    continue
                
                current_row, current_col = new_row + d_row, new_col + d_col
                found_our_piece = False
                
                while 0 <= current_row < 8 and 0 <= current_col < 8:
                    if board[current_row, current_col] == 0:
                        break
                    elif current_player[current_row, current_col] == 1:
                        found_our_piece = True
                        break
                    current_row += d_row
                    current_col += d_col
                
                if found_our_piece:
                    move_count += 1
                    break
    
    return move_count


# Strategic positional weights for Othello
# Higher values = more desirable squares
# Corners (100) are most valuable as they cannot be captured
# X-squares (-50) are dangerous as they give opponent access to corners
POSITIONAL_WEIGHTS = np.array([
    [ 100,  -20,   5,   2,   2,   5,  -20,  100],
    [ -20,  -50,  -2,  -2,  -2,  -2,  -50,  -20],
    [   5,   -2,  -1,  -1,  -1,  -1,   -2,    5],
    [   2,   -2,  -1,   0,   0,  -1,   -2,    2],
    [   2,   -2,  -1,   0,   0,  -1,   -2,    2],
    [   5,   -2,  -1,  -1,  -1,  -1,   -2,    5],
    [ -20,  -50,  -2,  -2,  -2,  -2,  -50,  -20],
    [ 100,  -20,   5,   2,   2,   5,  -20,  100]
])
