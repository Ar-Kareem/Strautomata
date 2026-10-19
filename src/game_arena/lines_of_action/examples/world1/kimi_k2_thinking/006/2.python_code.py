
import numpy as np
import random
from collections import deque

def policy(board):
    """
    Main policy function for Lines of Action.
    Returns a legal move string in format "from_row,from_col:to_row,to_col".
    """
    board = np.array(board)
    player = 1
    opponent = -1
    
    # Get all legal moves
    moves = get_all_legal_moves(board, player, opponent)
    
    if not moves:
        # Fallback for edge cases
        return "0,0:0,0"
    
    # Evaluate all moves
    scored_moves = []
    for move in moves:
        score = evaluate_move(board, move, player, opponent)
        scored_moves.append((score, move))
    
    # Sort by score and pick from top 3 with randomness
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    top_n = min(3, len(scored_moves))
    chosen = random.choice(scored_moves[:top_n])
    
    from_pos, to_pos = chosen[1]
    return f"{from_pos[0]},{from_pos[1]}:{to_pos[0]},{to_pos[1]}"

def get_all_legal_moves(board, player, opponent):
    """
    Generate all legal moves for the given player.
    A move is legal if it moves exactly the number of squares equal to pieces 
    in that line, doesn't jump over opponent pieces, and doesn't land on own piece.
    """
    moves = []
    rows, cols = board.shape
    directions = [(-1,0), (-1,1), (0,1), (1,1), 
                  (1,0), (1,-1), (0,-1), (-1,-1)]
    
    for r in range(rows):
        for c in range(cols):
            if board[r, c] == player:
                for dr, dc in directions:
                    # Count pieces in this line
                    count = count_pieces_in_line(board, r, c, dr, dc)
                    if count == 0:
                        continue
                    
                    # Calculate target position
                    target_r, target_c = r + dr * count, c + dc * count
                    if not (0 <= target_r < rows and 0 <= target_c < cols):
                        continue
                    
                    # Check path is not blocked by opponent
                    blocked = False
                    for step in range(1, count):
                        check_r, check_c = r + dr * step, c + dc * step
                        if board[check_r, check_c] == opponent:
                            blocked = True
                            break
                    
                    if blocked:
                        continue
                    
                    # Cannot land on own piece
                    if board[target_r, target_c] == player:
                        continue
                    
                    moves.append(((r, c), (target_r, target_c)))
    
    return moves

def count_pieces_in_line(board, r, c, dr, dc):
    """
    Count all pieces (both players) in the given line (both directions).
    Includes the piece at (r,c) itself.
    """
    count = 0
    rows, cols = board.shape
    
    # Count in positive direction
    for i in range(1, 8):
        nr, nc = r + dr * i, c + dc * i
        if not (0 <= nr < rows and 0 <= nc < cols):
            break
        if board[nr, nc] != 0:
            count += 1
    
    # Count in negative direction
    for i in range(1, 8):
        nr, nc = r - dr * i, c - dc * i
        if not (0 <= nr < rows and 0 <= nc < cols):
            break
        if board[nr, nc] != 0:
            count += 1
    
    # Include starting piece
    if board[r, c] != 0:
        count += 1
    
    return count

def evaluate_move(board, move, player, opponent):
    """
    Evaluate a move based on multiple heuristics:
    - Immediate win
    - Captures
    - Connectivity improvement
    - Opponent disruption
    - Center control
    - Piece preservation
    """
    new_board = board.copy()
    from_pos, to_pos = move
    
    # Apply move
    piece_value = new_board[from_pos]
    new_board[from_pos] = 0
    new_board[to_pos] = piece_value
    
    # 1. Immediate win is highest priority
    if is_connected(new_board, player):
        return 10000
    
    score = 0
    
    # 2. Capture opponent pieces
    if board[to_pos] == opponent:
        score += 500
    
    # 3. Improve own connectivity (reduce number of groups)
    old_groups = count_groups(board, player)
    new_groups = count_groups(new_board, player)
    score += (old_groups - new_groups) * 300
    
    # 4. Disrupt opponent connectivity (increase their groups)
    old_opp_groups = count_groups(board, opponent)
    new_opp_groups = count_groups(new_board, opponent)
    score += (new_opp_groups - old_opp_groups) * 200
    
    # 5. Control center (Manhattan distance from center)
    center_r, center_c = 3.5, 3.5
    dist = abs(to_pos[0] - center_r) + abs(to_pos[1] - center_c)
    score -= int(dist * 10)
    
    # 6. Penalize losing pieces
    old_count = np.sum(board == player)
    new_count = np.sum(new_board == player)
    if new_count < old_count:
        score -= 1000
    
    # 7. Small randomization for variety
    score += random.uniform(-5, 5)
    
    return score

def is_connected(board, player):
    """
    Check if all player's pieces form a single connected group.
    Connectivity includes all 8 directions.
    """
    pieces = [(r, c) for r in range(8) for c in range(8) if board[r, c] == player]
    if len(pieces) <= 1:
        return True
    
    visited = set()
    queue = deque([pieces[0]])
    visited.add(pieces[0])
    
    while queue:
        r, c = queue.popleft()
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in visited and board[nr, nc] == player:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    
    return len(visited) == len(pieces)

def count_groups(board, player):
    """
    Count the number of connected groups for the player.
    """
    visited = set()
    groups = 0
    
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and (r, c) not in visited:
                groups += 1
                queue = deque([(r, c)])
                visited.add((r, c))
                while queue:
                    cr, cc = queue.popleft()
                    for dr in [-1, 0, 1]:
                        for dc in [-1, 0, 1]:
                            if dr == 0 and dc == 0:
                                continue
                            nr, nc = cr + dr, cc + dc
                            if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in visited and board[nr, nc] == player:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
    
    return groups
