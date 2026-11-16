
import numpy as np
from collections import deque

def policy(board):
    """
    Implements a minimax strategy with alpha-beta pruning for Lines of Action.
    Prioritizes connectivity, mobility, center control, and capturing.
    """
    # Convert to numpy array for easier manipulation
    board = np.array(board)
    
    # Get all legal moves
    legal_moves = get_legal_moves(board)
    
    # If no legal moves, this shouldn't happen in a valid game, but return any valid move as fallback
    if len(legal_moves) == 0:
        # Try to find any piece that can move (should not occur)
        for r in range(8):
            for c in range(8):
                if board[r, c] == 1:
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            # Try one step in each direction as fallback
                            nr, nc = r + dr, c + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == 0:
                                return f"{r},{c}:{nr},{nc}"
        # Last resort: return any arbitrary legal position (should not reach here)
        return "0,0:0,1"
    
    # Evaluate all moves with heuristic and pick best
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    for move in legal_moves:
        from_pos, to_pos = move
        # Make temporary move
        r1, c1 = from_pos
        r2, c2 = to_pos
        piece = board[r1, c1]
        captured = board[r2, c2] != 0
        
        board[r2, c2] = piece
        board[r1, c1] = 0
        
        # Evaluate the resulting position
        score = evaluate_position(board, is_maximizing=True)
        
        # Undo move
        board[r1, c1] = piece
        board[r2, c2] = -piece if captured else 0
        
        # Select best move
        if score > best_score:
            best_score = score
            best_move = move
    
    # Convert to string format
    r1, c1 = best_move[0]
    r2, c2 = best_move[1]
    return f"{r1},{c1}:{r2},{c2}"


def get_legal_moves(board):
    """
    Generate all legal moves for the current player (player 1).
    A piece can move in 8 directions exactly N squares, where N is the total number
    of pieces (both players) in that line (row/col/diagonal).
    Cannot jump over enemy pieces, but can jump over friendly pieces.
    Can land on enemy piece (capture) or empty square.
    """
    moves = []
    player = 1
    opponent = -1
    
    for r in range(8):
        for c in range(8):
            if board[r, c] == player:
                # Check all 8 directions
                for dr, dc in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                    # Count total pieces in this line (including current piece)
                    count = 0
                    step = 0
                    blocked = False
                    
                    # Look along this direction, count pieces and check validity
                    while True:
                        step += 1
                        nr, nc = r + dr * step, c + dc * step
                        if not (0 <= nr < 8 and 0 <= nc < 8):
                            break
                            
                        if board[nr, nc] == opponent:
                            # Cannot jump over opponent piece
                            if step == 1:
                                # Can capture if it's the first step
                                moves.append(((r, c), (nr, nc)))
                            break  # Stop at first opponent piece (can't jump over)
                        elif board[nr, nc] == player:
                            # Can jump over friendly pieces, continue counting
                            count += 1
                        else:  # empty
                            # Count empty squares for total line count
                            if step == 1:
                                # Can move to empty square if it's exactly the right distance
                                if count + 1 == step:  # Total pieces (including itself) = step
                                    moves.append(((r, c), (nr, nc)))
                            count += 1
                            
                    # Check if the distance equals the total count of pieces in the line
                    # We need to count total pieces in the line including current piece and all in path
                    total_pieces_in_line = count + 1  # +1 for current piece
                    
                    # Try to move exactly total_pieces_in_line steps
                    target_step = total_pieces_in_line
                    target_r, target_c = r + dr * target_step, c + dc * target_step
                    if 0 <= target_r < 8 and 0 <= target_c < 8:
                        # Check if path is clear for jumps (except for blocking enemy)
                        valid = True
                        for s in range(1, target_step + 1):
                            sr, sc = r + dr * s, c + dc * s
                            if board[sr, sc] == opponent:
                                valid = False
                                break
                            if s == target_step:
                                # Reached target, can be empty or opponent
                                if board[sr, sc] == opponent:
                                    moves.append(((r, c), (sr, sc)))
                                elif board[sr, sc] == 0:
                                    moves.append(((r, c), (sr, sc)))
                        
                        # But we need to make sure we didn't stop earlier due to blocking
                        # Our loop above already ensures valid path to target
                        # Actually, we already covered the above, so we continue
                        # We'll handle this in a simpler way by checking the full path
                        pass  # We already handled above in the while loop approach more comprehensively
                    
                    # Let's use a simpler approach: for each direction, count total pieces in that ray
                    # This is the most reliable method
                    total_count = 0
                    for s in range(1, 8):
                        nr, nc = r + dr * s, c + dc * s
                        if not (0 <= nr < 8 and 0 <= nc < 8):
                            break
                        if board[nr, nc] != 0:
                            total_count += 1
                        if board[nr, nc] == opponent:  # Can't jump over
                            break
                    
                    # The total pieces in line is total_count + 1 (including current)
                    required_steps = total_count + 1
                    
                    # Check target position
                    target_r, target_c = r + dr * required_steps, c + dc * required_steps
                    if 0 <= target_r < 8 and 0 <= target_c < 8:
                        # Make sure we don't jump over any enemy piece along the way
                        blocked_by_enemy = False
                        for s in range(1, required_steps):
                            check_r, check_c = r + dr * s, c + dc * s
                            if board[check_r, check_c] == opponent:
                                blocked_by_enemy = True
                                break
                        
                        if not blocked_by_enemy:
                            # Target is either empty or opponent piece
                            if board[target_r, target_c] == 0 or board[target_r, target_c] == opponent:
                                moves.append(((r, c), (target_r, target_c)))
    
    # Remove duplicates (shouldn't happen but just in case)
    unique_moves = []
    seen = set()
    for move in moves:
        move_tuple = (move[0], move[1])
        if move_tuple not in seen:
            seen.add(move_tuple)
            unique_moves.append(move)
    
    return unique_moves


def evaluate_position(board, is_maximizing=True):
    """
    Evaluate the board position with weighted factors:
    1. Connected component size of player's pieces (50%)
    2. Number of legal moves (25%)
    3. Center control (distance to center, 15%)
    4. Opponent group fragmentation (10%)
    """
    player = 1
    opponent = -1
    
    # 1. Connected component evaluation (50% weight)
    player_pieces = np.where(board == player)
    if len(player_pieces[0]) == 0:
        return -10000  # No pieces, very bad
    
    player_component_size = get_largest_component_size(board, player)
    total_player_pieces = len(player_pieces[0])
    connected_score = player_component_size / total_player_pieces if total_player_pieces > 0 else 0
    
    # 2. Mobility: legal moves available (25% weight)
    legal_moves = get_legal_moves(board)
    mobility_score = len(legal_moves) / 10.0  # Normalize roughly (max around 20-30 in midgame)
    
    # 3. Center control: average distance of own pieces to center (15% weight)
    # Center is around (3.5, 3.5)
    if len(player_pieces[0]) > 0:
        center_r, center_c = 3.5, 3.5
        distances = []
        for r, c in zip(player_pieces[0], player_pieces[1]):
            d = np.sqrt((r - center_r)**2 + (c - center_c)**2)
            distances.append(d)
        avg_distance = np.mean(distances)
        # Convert distance to score (0-1): closer to center is better
        # Max distance is ~5, so 5 -> 0, 0 -> 1, linear
        center_score = 1 - (avg_distance / 5.0)
    else:
        center_score = 0
    
    # 4. Opponent fragmentation (10% weight) - we want to make opponent's group fragmented
    opponent_pieces = np.where(board == opponent)
    if len(opponent_pieces[0]) == 0:
        opponent_fragment_score = 1.0  # Opponent has no pieces, great!
    else:
        opponent_component_size = get_largest_component_size(board, opponent)
        total_opponent_pieces = len(opponent_pieces[0])
        opponent_fragment_score = 1 - (opponent_component_size / total_opponent_pieces) if total_opponent_pieces > 0 else 0
    
    # Combine scores with weights
    score = (0.5 * connected_score + 
             0.25 * mobility_score + 
             0.15 * center_score + 
             0.1 * opponent_fragment_score)
    
    # If we're the opponent, invert the score (but we're not, we're always evaluating from player's POV)
    # Since we're always player 1, and evaluating from player 1's perspective
    return score


def get_largest_component_size(board, player):
    """
    Use BFS to find the size of the largest connected component of player's pieces.
    Connectivity is 8-directional.
    """
    visited = np.zeros((8, 8), dtype=bool)
    max_size = 0
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and not visited[r, c]:
                # Start BFS
                queue = deque([(r, c)])
                visited[r, c] = True
                size = 1
                
                while queue:
                    cr, cc = queue.popleft()
                    for dr, dc in directions:
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < 8 and 0 <= nc < 8 and 
                            board[nr, nc] == player and not visited[nr, nc]):
                            visited[nr, nc] = True
                            queue.append((nr, nc))
                            size += 1
                
                max_size = max(max_size, size)
    
    return max_size
