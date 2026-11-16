
import random
import numpy as np
from collections import defaultdict, deque

def get_liberties(board, row, col, color):
    """Get liberties of a stone group"""
    if board[row][col] != color:
        return set()
    
    visited = set()
    queue = deque([(row, col)])
    visited.add((row, col))
    liberties = set()
    
    while queue:
        r, c = queue.popleft()
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board[nr][nc] == 0:  # Empty
                    liberties.add((nr, nc))
                elif board[nr][nc] == color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    queue.append((nr, nc))
    
    return liberties

def is_valid_move(board, row, col, color):
    """Check if move is valid"""
    if row < 0 or row >= 19 or col < 0 or col >= 19:
        return False
    if board[row][col] != 0:
        return False
    
    # Check for suicide
    board[row][col] = color
    liberties = get_liberties(board, row, col, color)
    if liberties and len(liberties) > 0:
        board[row][col] = 0
        return True
    
    # Check if it captures opponent stones
    opponent_color = 3 - color
    captured = False
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = row + dr, col + dc
        if 0 <= nr < 19 and 0 <= nc < 19:
            if board[nr][nc] == opponent_color:
                opponent_liberties = get_liberties(board, nr, nc, opponent_color)
                if len(opponent_liberties) == 1:  # Will be captured
                    captured = True
                    break
    
    board[row][col] = 0
    return captured or len(liberties) > 0

def get_all_liberties(board, color):
    """Get all liberties of all groups of a color"""
    liberties = []
    visited = set()
    
    for r in range(19):
        for c in range(19):
            if board[r][c] == color and (r, c) not in visited:
                # Find all stones in this group
                group = set()
                queue = deque([(r, c)])
                group.add((r, c))
                visited.add((r, c))
                
                while queue:
                    gr, gc = queue.popleft()
                    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nr, nc = gr + dr, gc + dc
                        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == color and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            group.add((nr, nc))
                            queue.append((nr, nc))
                
                # Get liberties for this group
                for stone in group:
                    g_liberties = get_liberties(board, stone[0], stone[1], color)
                    liberties.extend(g_liberties)
    
    return set(liberties)

def evaluate_position(board, me, opponent, memory):
    """Evaluate the current board position"""
    # Convert input lists to board representation
    board_copy = [row[:] for row in board]  # Deep copy
    
    # Simple evaluation: prioritize:
    # 1. Immediate captures
    # 2. Liberties for own stones
    # 3. Attacking opponent liberties
    # 4. Connectivity
    # 5. Corner/center control
    
    # Convert positions to board indices (1-based to 0-based)
    me_positions = [(r-1, c-1) for r, c in me]
    opponent_positions = [(r-1, c-1) for r, c in opponent]
    
    # Update board with current positions
    for r, c in me_positions:
        board_copy[r][c] = 1
    for r, c in opponent_positions:
        board_copy[r][c] = 2
    
    # Find legal moves and their scores
    candidate_moves = []
    scores = []
    
    # Get empty positions
    empty_positions = []
    for r in range(19):
        for c in range(19):
            if board_copy[r][c] == 0:
                empty_positions.append((r, c))
    
    # Evaluate potential moves
    for r, c in empty_positions:
        # Skip if it's suicide (unless it captures)
        if not is_valid_move(board_copy, r, c, 1):
            continue
            
        score = 0
        
        # 1. Check if move captures opponent stones
        board_copy[r][c] = 1
        captures = 0
        opponent_liberties_lost = 0
        
        # Check adjacent opponent stones for capture
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board_copy[nr][nc] == 2:
                liberties = get_liberties(board_copy, nr, nc, 2)
                if len(liberties) == 1:
                    captures += 1
                    opponent_liberties_lost += 1
        
        score += captures * 20  # Capturing is very valuable
        
        # 2. Add liberties for own group
        own_liberties = get_liberties(board_copy, r, c, 1)
        score += len(own_liberties) * 2  # More liberties is better
        
        # 3. Minimize opponent liberties
        score -= opponent_liberties_lost * 5
        
        # 4. Prefer corners and center
        if (r, c) in [(0, 0), (0, 18), (18, 0), (18, 18)]:  # Corners
            score += 3
        elif r in [0, 18] or c in [0, 18]:  # Edges (but not corners)
            score += 2
        elif abs(r - 9) <= 2 and abs(c - 9) <= 2:  # Center area
            score += 2
            
        # 5. Prefer to connect to existing groups
        connections = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board_copy[nr][nc] == 1:
                connections += 1
        score += connections * 3
        
        # 6. Avoid surrounding empty areas (encourage territorial sense)
        # (rough approximation)
        surrounding_stones = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19:
                if board_copy[nr][nc] in [1, 2]:
                    surrounding_stones += 1
        score += surrounding_stones  # Encourage local density
        
        board_copy[r][c] = 0
        
        if score > 0:  # Only consider moves that are better or neutral
            candidate_moves.append((r, c))
            scores.append(score)
    
    # If no good moves, pass
    if not candidate_moves:
        return (0, 0), memory
    
    # Select best move based on scores
    if len(scores) == 0:
        return (0, 0), memory
    
    # Use weighted random selection to add some variety
    total_score = sum(scores)
    if total_score > 0:
        # Normalize weights
        weights = [score / total_score for score in scores]
        selected_idx = np.random.choice(range(len(candidate_moves)), p=weights)
    else:
        # All moves have score 0, just pick one
        selected_idx = random.randint(0, len(candidate_moves) - 1)
    
    return candidate_moves[selected_idx], memory

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """Main policy function"""
    
    # Initialize board
    board = [[0 for _ in range(19)] for _ in range(19)]
    
    # If this is the first move (we're empty), play in center
    if not me and not opponent:
        # Play in center, possibly corner for later moves
        return ((10, 10), memory)
    
    # Use the evaluation function
    action, memory = evaluate_position(board, me, opponent, memory)
    return action, memory
