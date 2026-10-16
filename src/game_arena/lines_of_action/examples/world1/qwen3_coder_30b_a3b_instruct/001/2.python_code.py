
import numpy as np
import random

def policy(board) -> str:
    # Convert board to numpy array for easier manipulation
    board = np.array(board)
    
    # Find all my pieces (1)
    my_pieces = []
    for r in range(8):
        for c in range(8):
            if board[r, c] == 1:
                my_pieces.append((r, c))
    
    # Generate all legal moves
    legal_moves = []
    
    for r, c in my_pieces:
        # Check all 8 directions
        directions = [
            (-1, -1), (-1, 0), (-1, 1),  # up-left, up, up-right
            (0, -1),           (0, 1),   # left, right
            (1, -1),  (1, 0),  (1, 1)    # down-left, down, down-right
        ]
        
        for dr, dc in directions:
            # Try all possible distances (1 to 7)
            for distance in range(1, 8):
                new_r = r + dr * distance
                new_c = c + dc * distance
                
                # Check if target position is within board
                if not (0 <= new_r < 8 and 0 <= new_c < 8):
                    break
                    
                # Check if move is valid
                # 1. Must move exactly as many squares as pieces in line
                # 2. Can't jump over enemy pieces
                # 3. Can land on empty or enemy square
                
                # Count pieces in the line
                pieces_in_line = count_pieces_in_line(board, r, c, dr, dc)
                
                if pieces_in_line != distance:
                    # If line doesn't match the distance, we can't move here
                    break
                    
                # Check if path is clear (no enemy pieces)
                if not is_path_clear(board, r, c, dr, dc, distance):
                    break
                    
                # Valid move if distance matches pieces in line and path is clear
                if distance == pieces_in_line:
                    # Check if we can arrive at this position
                    if not (0 <= new_r < 8 and 0 <= new_c < 8):
                        break
                    
                    # Can we move here?
                    if board[new_r, new_c] == 0 or board[new_r, new_c] == -1:  # empty or opponent
                        legal_moves.append(((r, c), (new_r, new_c)))
                    break  # Only one valid move per line in this direction
    
    # If no legal moves, try to find any possible move so we can still play
    if len(legal_moves) == 0:
        # Fallback: try all possible moves on any of the pieces
        for r in range(8):
            for c in range(8):
                if board[r, c] == 1:
                    # Try each direction
                    directions = [(-1, -1), (-1, 0), (-1, 1),
                                  (0, -1),           (0, 1),
                                  (1, -1),  (1, 0),  (1, 1)]
                    for dr, dc in directions:
                        for distance in range(1, 8):
                            new_r = r + dr * distance
                            new_c = c + dc * distance
                            if not (0 <= new_r < 8 and 0 <= new_c < 8):
                                break
                            if board[new_r, new_c] == 0 or board[new_r, new_c] == -1:
                                legal_moves.append(((r, c), (new_r, new_c)))
                                break
                        break
                                
    if len(legal_moves) == 0:
        # This is really bad - just make a random valid move
        # We'll start trying from top-left and see what's available
        for r in range(8):
            for c in range(8):
                if board[r, c] == 1:
                    directions = [(-1, -1), (-1, 0), (-1, 1),
                                  (0, -1),           (0, 1),
                                  (1, -1),  (1, 0),  (1, 1)]
                    for dr, dc in directions:
                        new_r = r + dr
                        new_c = c + dc
                        if 0 <= new_r < 8 and 0 <= new_c < 8:
                            if board[new_r, new_c] == 0 or board[new_r, new_c] == -1:
                                return f"{r},{c}:{new_r},{new_c}"
    
    # Score moves based on strategy
    best_move = None
    best_score = -float('inf')
    
    for from_pos, to_pos in legal_moves:
        score = score_move(board, from_pos, to_pos)
        if score > best_score:
            best_score = score
            best_move = (from_pos, to_pos)
    
    if best_move is None:
        # Even if no good moves, pick first one
        best_move = legal_moves[0] if legal_moves else ((0,0), (0,1))
    
    from_r, from_c = best_move[0]
    to_r, to_c = best_move[1]
    return f"{from_r},{from_c}:{to_r},{to_c}"

def count_pieces_in_line(board, start_r, start_c, dr, dc):
    """Count pieces in the line from start in direction (dr, dc)"""
    count = 0
    r, c = start_r, start_c
    while True:
        r += dr
        c += dc
        if not (0 <= r < 8 and 0 <= c < 8):
            break
        if board[r, c] != 0:
            count += 1
    return count

def is_path_clear(board, start_r, start_c, dr, dc, distance):
    """Check if the path from piece to destination is clear except for 
    possible destination which can contain enemy or empty"""
    r, c = start_r, start_c
    # We check all spots along the way except the final spot 
    # (final spot may be enemy or empty)
    for i in range(1, distance):
        r += dr
        c += dc
        if board[r, c] == -1:  # enemy piece blocks path
            return False
    return True

def score_move(board, from_pos, to_pos):
    """Score the move based on various factors"""
    from_r, from_c = from_pos
    to_r, to_c = to_pos
    
    score = 0
    
    # Capture bonus
    if board[to_r, to_c] == -1:
        score += 10
    
    # Mobility bonus: how many moves are available after this move?
    # This is a simplified measure - we count number of pieces that can move
    new_board = board.copy()
    new_board[from_r, from_c] = 0
    new_board[to_r, to_c] = 1
    
    # Count possible moves for this player after this move 
    mobility = 0
    my_pieces = []
    for r in range(8):
        for c in range(8):
            if new_board[r, c] == 1:
                my_pieces.append((r, c))
    
    for r, c in my_pieces:
        directions = [(-1, -1), (-1, 0), (-1, 1),
                      (0, -1),           (0, 1),
                      (1, -1),  (1, 0),  (1, 1)]
        for dr, dc in directions:
            for distance in range(1, 8):
                new_r = r + dr * distance
                new_c = c + dc * distance
                if not (0 <= new_r < 8 and 0 <= new_c < 8):
                    break
                # Simple check - probably not very accurate but good enough
                pieces_in_line = count_pieces_in_line(new_board, r, c, dr, dc)
                if pieces_in_line == distance:
                    if new_board[new_r, new_c] == 0 or new_board[new_r, new_c] == -1:
                        mobility += 1
                        break
    score += mobility * 0.5
    
    # Center control bonus
    center_bonus = 0
    center_r, center_c = 3.5, 3.5
    dist_from_center = abs(to_r - center_r) + abs(to_c - center_c)  # Manhattan distance
    center_bonus = 20 - dist_from_center  # The closer to center, the better
    score += center_bonus
    
    # Connectivity bonus: try to connect pieces
    # Find all pieces and check if this move helps connect them
    pieces = []
    for r in range(8):
        for c in range(8):
            if new_board[r, c] == 1:
                pieces.append((r, c))
    
    if len(pieces) > 1:
        # Check if pieces are connected (simple check)
        # This is a rough approximation - we check if the piece is 
        # adjacent to another piece in 8 directions (but that's a separate function)
        conn_bonus = measure_connectivity(new_board)
        score += conn_bonus
    
    return score

def measure_connectivity(board):
    """Simple connectivity measure"""
    # Find all my pieces (1s)
    pieces = []
    for r in range(8):
        for c in range(8):
            if board[r, c] == 1:
                pieces.append((r, c))

    if len(pieces) <= 1:
        return 0
    
    # Simple heuristic: check if any piece is reachable from any other piece
    # Such as if there is a path of some length (N) which can be traversed by
    # a piece moving through one or more opponent pieces and then a free landing.
    # But this is too complicated, so let's just count the distance
    # between pieces and award a bonus for smaller average distances.
    
    if len(pieces) <= 1:
        return 0
        
    total_dist = 0
    count = 0
    for i in range(len(pieces)):
        for j in range(i+1, len(pieces)):
            r1, c1 = pieces[i]
            r2, c2 = pieces[j]
            # Manhattan distance
            dist = abs(r1 - r2) + abs(c1 - c2)
            total_dist += dist
            count += 1
    
    if count == 0:
        return 0
    
    avg_dist = total_dist / count
    
    # The more connected pieces (smaller average distance), the better
    # Reward for smaller distances. Score is negative avg dist (so smaller is better)
    return -avg_dist * 0.5

# The move generation logic is minimal and will ensure minimal conflicts.
# Let's improve it by writing a correct version:
def generate_legal_moves(board):
    """Generate all legal moves for current player (1) based on rules"""
    moves = []
    
    piece_positions = []
    for r in range(8):
        for c in range(8):
            if board[r, c] == 1:
                piece_positions.append((r,c))
    
    if not piece_positions:
        return []
    
    directions = [
        (-1, -1), (-1, 0), (-1, 1),
        (0, -1),           (0, 1), 
        (1, -1),  (1, 0),  (1, 1)
    ]
    
    for start_r, start_c in piece_positions:
        # Check each direction
        for dr, dc in directions:
            # We need to try each possible distance that could be valid
            for distance in range(1, 8):
                # Compute end position
                end_r = start_r + dr * distance
                end_c = start_c + dc * distance
                
                # Check bounds
                if not (0 <= end_r < 8 and 0 <= end_c < 8):
                    break
                
                # Count pieces in the line (including the moving piece)
                pieces_count = 1  # Start piece is included, but let's properly count
                r, c = start_r + dr, start_c + dc
                while 0 <= r < 8 and 0 <= c < 8:
                    if board[r, c] != 0:
                        pieces_count += 1
                    r += dr
                    c += dc
                    
                # The number of pieces in this line is pieces_count  
                # and we should move exactly that many squares as pieces_in_line  
                # So, if pieces_count is distance, move is valid.
                if pieces_count == distance:
                    # Check path is clear (the line must not include enemy pieces in the way)
                    # Let's make sure we don't jump over enemies
                    valid = True
                    r, c = start_r + dr, start_c + dc
                    steps = 1
                    while steps < distance:
                        if board[r, c] == -1:
                            valid = False
                            break
                        r += dr
                        c += dc
                        steps += 1
                    if not valid:
                        break
                        
                    # Now if the dest is enemy or empty, that's valid
                    if board[end_r, end_c] == 0 or board[end_r, end_c] == -1:
                        moves.append(((start_r, start_c), (end_r, end_c)))
                        break
                elif pieces_count < distance:
                    break  # Can't move further along this line 
    return moves

# Corrected policy function that reimplements move generation properly:
def policy_final(board) -> str:
    # Simpler approach for correctness
    # Let's re-design the move generation properly
    moves = []
    
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                # Try all directions and distances (valid moves)
                directions = [(-1, -1), (-1, 0), (-1, 1),
                              (0, -1),           (0, 1),
                              (1, -1), (1, 0), (1, 1)]
                
                for dr, dc in directions:
                    moved = False
                    for distance in range(1, 8):
                        new_r = r + dr * distance
                        new_c = c + dc * distance
                        
                        # Check board bounds
                        if not (0 <= new_r < 8 and 0 <= new_c < 8):
                            break
                        
                        # Validate we can move to this spot
                        step_r = r + dr
                        step_c = c + dc
                        jumping_over_enemies = False
                        steps_made = 1
                        
                        # Check that we don't jump over enemies
                        while steps_made < distance:
                            if board[step_r][step_c] == -1:
                                jumping_over_enemies = True
                                break
                            step_r += dr
                            step_c += dc
                            steps_made += 1
                        
                        if jumping_over_enemies:
                            break
                        
                        # Now validate the move using actual piece counting
                        # Count total pieces in the line  
                        count = 0
                        line_r, line_c = r, c
                        while True:
                            line_r += dr
                            line_c += dc
                            if line_r < 0 or line_r >= 8 or line_c < 0 or line_c >= 8:
                                break
                            if board[line_r, line_c] != 0:
                                count += 1
                        count += 1  # include starting piece
                        
                        # Piece move should be exactly distance steps and match line count
                        if count == distance:
                            if board[new_r][new_c] in [0, -1]:
                                moves.append(((r, c), (new_r, new_c)))
                                moved = True
                                break
                        elif count < distance:
                            break
                        # If count > distance, then move likely isn't valid and we break
                        
    if moves:
        # Score these moves
        best_move = moves[0]
        best_score = -float('inf')
        
        for from_pos, to_pos in moves:
            score = score_move_simple(board, from_pos, to_pos)
            if score > best_score:
                best_score = score
                best_move = (from_pos, to_pos)
        
        from_r, from_c = best_move[0]
        to_r, to_c = best_move[1]
        return f"{from_r},{from_c}:{to_r},{to_c}"
    else:
        # If no moves, find any valid one
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    directions = [(-1, -1), (-1, 0), (-1, 1),
                                  (0, -1), (0, 1),
                                  (1, -1), (1, 0), (1, 1)]
                    for dr, dc in directions:
                        new_r = r + dr
                        new_c = c + dc
                        if 0 <= new_r < 8 and 0 <= new_c < 8:
                            if board[new_r][new_c] == 0 or board[new_r][new_c] == -1:
                                return f"{r},{c}:{new_r},{new_c}"
        # If still no valid moves, return arbitrary
        return "0,0:0,1"

def score_move_simple(board, from_pos, to_pos):
    """Simple scoring function"""
    from_r, from_c = from_pos
    to_r, to_c = to_pos
    
    score = 0
    
    # Capture bonus
    if board[to_r, to_c] == -1:
        score += 10
        
    # Mobility bonus (simplified)
    # Count how many moves our pieces can still make after this step
    # let's simplify and say the further than center, the better
    center_r, center_c = 3.5, 3.5
    dist_from_center = abs(to_r - center_r) + abs(to_c - center_c)
    score += 20 - dist_from_center
    
    # Connectivity bonus
    # Convert to numpy arrays for easier manipulation
    temp_board = np.array(board)
    temp_board[from_r, from_c] = 0
    temp_board[to_r, to_c] = 1
    
    # See if pieces are still close together (better connectivity)
    my_pieces = []
    for r in range(8):
        for c in range(8):
            if temp_board[r, c] == 1:
                my_pieces.append((r, c))
                
    if len(my_pieces) > 1:
        # Compute average distances between pieces
        total_dist = 0
        count = 0
        for i in range(len(my_pieces)):
            for j in range(i+1, len(my_pieces)):
                r1, c1 = my_pieces[i]
                r2, c2 = my_pieces[j]
                dist = abs(r1 - r2) + abs(c1 - c2)
                total_dist += dist
                count += 1
                
        avg_dist = total_dist / count if count > 0 else 0
        # Bonus for connecting pieces closer together
        score += - avg_dist * 0.2
    
    return score

def policy(board) -> str:
    return policy_final(board)

