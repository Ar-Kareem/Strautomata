
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """Return next move as (row, col)."""
    
    # Board setup
    BOARD_SIZE = 19
    EMPTY, MINE, OPP = 0, 1, -1
    
    # Initialize board with borders
    board = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=int)
    
    # Place stones (adjust for 1-indexed input and border offset)
    for r, c in me:
        board[r, c] = MINE
    for r, c in opponent:
        board[r, c] = OPP
    
    # Helper functions
    def is_in_bounds(r, c):
        return 1 <= r <= BOARD_SIZE and 1 <= c <= BOARD_SIZE
    
    def get_group(board, r, c, stone_type):
        """Find all connected stones of given type."""
        if board[r, c] != stone_type:
            return set()
        
        visited = set()
        stack = [(r, c)]
        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = cr + dr, cc + dc
                if board[nr, nc] == stone_type and (nr, nc) not in visited:
                    stack.append((nr, nc))
        return visited
    
    def has_liberties(board, group):
        """Check if group has any liberties."""
        for r, c in group:
            for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nr, nc = r + dr, c + dc
                if board[nr, nc] == EMPTY:
                    return True
        return False
    
    def is_legal_move(board, r, c, player):
        """Check if move is legal (not suicide, respects ko)."""
        if not is_in_bounds(r, c) or board[r, c] != EMPTY:
            return False
        
        # Make temporary board
        temp_board = board.copy()
        temp_board[r, c] = player
        
        # Check if move captures any opponent groups
        captures_any = False
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if temp_board[nr, nc] == -player:
                group = get_group(temp_board, nr, nc, -player)
                if not has_liberties(temp_board, group):
                    captures_any = True
                    break
        
        # If captures, move is legal
        if captures_any:
            return True
        
        # If no captures, check if own group has liberties
        group = get_group(temp_board, r, c, player)
        return has_liberties(temp_board, group)
    
    def calculate_influence(board, iterations=3):
        """Calculate influence map using diffusion."""
        influence = np.zeros((BOARD_SIZE + 2, BOARD_SIZE + 2), dtype=float)
        
        # Initial influence from stones
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if board[r, c] == MINE:
                    influence[r, c] = 5.0
                elif board[r, c] == OPP:
                    influence[r, c] = -5.0
        
        # Diffuse influence
        for _ in range(iterations):
            new_influence = influence.copy()
            for r in range(1, BOARD_SIZE + 1):
                for c in range(1, BOARD_SIZE + 1):
                    if board[r, c] != EMPTY:
                        continue
                    neighbor_sum = 0.0
                    count = 0
                    for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr <= BOARD_SIZE + 1 and 0 <= nc <= BOARD_SIZE + 1:
                            neighbor_sum += influence[nr, nc]
                            count += 1
                    if count > 0:
                        new_influence[r, c] = neighbor_sum / count
            influence = new_influence * 0.9  # Decay factor
        
        return influence
    
    def evaluate_move(board, r, c, influence):
        """Score a potential move."""
        if not is_legal_move(board, r, c, MINE):
            return -float('inf')
        
        score = 0.0
        
        # 1. Influence score
        score += influence[r, c] * 10.0
        
        # 2. Center preference
        center_r = BOARD_SIZE / 2 + 0.5
        center_c = BOARD_SIZE / 2 + 0.5
        distance_to_center = abs(r - center_r) + abs(c - center_c)
        score -= distance_to_center * 0.5
        
        # 3. Capture potential
        temp_board = board.copy()
        temp_board[r, c] = MINE
        
        captured_stones = 0
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if temp_board[nr, nc] == OPP:
                group = get_group(temp_board, nr, nc, OPP)
                if not has_liberties(temp_board, group):
                    captured_stones += len(group)
        
        score += captured_stones * 15.0
        
        # 4. Connection to existing stones
        my_neighbors = 0
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if temp_board[nr, nc] == MINE:
                my_neighbors += 1
        
        score += my_neighbors * 3.0
        
        # 5. Eye formation (penalize playing in single-point eyes)
        empty_neighbors = 0
        for dr, dc in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            nr, nc = r + dr, c + dc
            if temp_board[nr, nc] == EMPTY:
                empty_neighbors += 1
        
        if empty_neighbors == 0:
            score -= 100.0  # Strong penalty for suicide
        
        return score
    
    # Special case: first move
    if len(me) == 0 and len(opponent) == 0:
        # Play near center (tengen or star point)
        center = BOARD_SIZE // 2 + 1
        return (center, center)
    
    # Calculate influence map
    influence = calculate_influence(board)
    
    # Find best move
    best_score = -float('inf')
    best_move = (0, 0)  # Default pass
    
    # Check all empty intersections
    for r in range(1, BOARD_SIZE + 1):
        for c in range(1, BOARD_SIZE + 1):
            if board[r, c] == EMPTY:
                score = evaluate_move(board, r, c, influence)
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
    
    # If no good move found, try to find any legal move
    if best_score == -float('inf'):
        for r in range(1, BOARD_SIZE + 1):
            for c in range(1, BOARD_SIZE + 1):
                if board[r, c] == EMPTY and is_legal_move(board, r, c, MINE):
                    return (r, c)
    
    return best_move
