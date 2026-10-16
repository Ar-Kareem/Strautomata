
import numpy as np
from collections import deque

def policy(board):
    """
    Selects the best move for Lines of Action using a heuristic-based policy
    """
    board = np.array(board)
    
    # Find all our pieces (1s)
    our_pieces = list(zip(*np.where(board == 1)))
    
    if not our_pieces:
        return "0,0:0,0"  # Fallback - should never happen in valid game
    
    # Generate all legal moves
    legal_moves = []
    
    # For each piece, try all possible moves
    for r, c in our_pieces:
        # Try all 8 directions
        directions = [
            (-1, -1), (-1, 0), (-1, 1),   # Up-left, up, up-right
            (0, -1),           (0, 1),    # Left, Right
            (1, -1), (1, 0), (1, 1)       # Down-left, down, down-right
        ]
        
        for dr, dc in directions:
            # Calculate how many pieces are in this line
            line_count = 0
            # Start from this piece's position
            line_positions = [(r, c)]
            
            # Count pieces in this direction
            nr, nc = r + dr, c + dc
            while 0 <= nr < 8 and 0 <= nc < 8:
                if board[nr][nc] != 0:
                    line_count += 1
                    line_positions.append((nr, nc))
                if board[nr][nc] == -1:  # Enemy piece - stop counting
                    break
                nr += dr
                nc += dc
            
            # The number of squares to move equals the line count
            move_distance = line_count
            if move_distance == 0:
                # No pieces in this line, can move any distance
                # But let's be conservative and move 1 square in valid directions
                move_distance = 1
                # Check if this direction is valid for movement
                test_r, test_c = r + dr, c + dc
                if 0 <= test_r < 8 and 0 <= test_c < 8 and board[test_r][test_c] == 0:
                    # Valid single move, add as valid move
                    legal_moves.append((r, c, r + dr, c + dc))
            else:
                # We can move move_distance squares in this direction
                new_r, new_c = r + dr * move_distance, c + dc * move_distance
                if 0 <= new_r < 8 and 0 <= new_c < 8:
                    # Check if new position is empty or contains opponent
                    if board[new_r][new_c] == 0 or board[new_r][new_c] == -1:
                        # Validate jumping over friendly pieces only
                        valid_move = True
                        # Check that we're not jumping over enemy pieces
                        check_r, check_c = r + dr, c + dc
                        for i in range(1, move_distance):
                            if 0 <= check_r < 8 and 0 <= check_c < 8:
                                if board[check_r][check_c] == -1:  # Enemy piece in path
                                    valid_move = False
                                    break
                            check_r += dr
                            check_c += dc
                        
                        if valid_move:
                            legal_moves.append((r, c, new_r, new_c))
    
    if not legal_moves:
        # No legal moves - find any move to avoid error
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:  # Our piece
                    # Try to move to adjacent empty cell if possible
                    for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 0:
                            return f"{r},{c}:{nr},{nc}"
        return "0,0:0,0"  # Final fallback
    
    # Score each move
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    for r1, c1, r2, c2 in legal_moves:
        score = 0
        
        # Mobility bonus - more possible moves for next turn
        new_board = board.copy()
        new_board[r1][c1] = 0
        new_board[r2][c2] = 1
        
        # Count how many legal moves our opponent would have from new state
        opponent_moves = 0
        for or1, oc1 in zip(*np.where(new_board == -1)):
            for dr, dc in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                for distance in range(1, 9):
                    nr, nc = or1 + dr * distance, oc1 + dc * distance
                    if not (0 <= nr < 8 and 0 <= nc < 8):
                        break
                    if new_board[nr][nc] != 0 and new_board[nr][nc] != -1:
                        break
                    if new_board[nr][nc] == 1:  # Friendly piece in path
                        break
                    opponent_moves += 1
                    # We could break if we want to optimize for more precise counting
                    break  # Just one move per direction for simplicity
        
        # Mobility benefit = smaller number of future opponent moves = better
        score += 0.1 * opponent_moves  # Penalty for giving opponent more moves
        
        # Connectivity bonus - count how connected our pieces are
        connected_count = count_connected_components(new_board, 1)
        score += 0.5 * connected_count
        
        # Central positioning bonus
        distance_bonus = 0
        target_r, target_c = (r2 + c2) / 2, (r2 + c2) / 2
        distance_bonus = 1.0 - (abs(3.5 - r2) + abs(3.5 - c2)) / 7.0
        score += 0.3 * distance_bonus
        
        # Capture bonus - move to capture opponent
        if new_board[r2][c2] == -1:
            score += 1.0
        
        # Prefer moves that don't move pieces to the same row/column unless captured
        if r1 == r2 or c1 == c2:
            score += 0.1  # Small preference for straight moves
        
        if score > best_score:
            best_score = score
            best_move = (r1, c1, r2, c2)
    
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

def count_connected_components(board, player=1):
    """
    Count connected components of player pieces.
    Returns number of separate groups.
    """
    visited = [[False]*8 for _ in range(8)]
    count = 0
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    
    for r in range(8):
        for c in range(8):
            if board[r][c] == player and not visited[r][c]:
                count += 1
                # BFS to mark all connected pieces
                queue = deque([(r, c)])
                visited[r][c] = True
                
                while queue:
                    cr, cc = queue.popleft()
                    for dr, dc in directions:
                        nr, nc = cr + dr, cc + dc
                        if (0 <= nr < 8 and 0 <= nc < 8 
                            and board[nr][nc] == player and not visited[nr][nc]):
                            visited[nr][nc] = True
                            queue.append((nr, nc))
    
    return count
