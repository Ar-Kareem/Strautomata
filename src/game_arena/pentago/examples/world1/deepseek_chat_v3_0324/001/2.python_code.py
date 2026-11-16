
import numpy as np
import random

def policy(you, opponent):
    # Convert to numpy arrays for easier manipulation
    you_array = np.array(you)
    opp_array = np.array(opponent)
    board = you_array - opp_array  # 1=your stone, -1=opponent, 0=empty
    
    EMPTY = 0
    YOUR = 1
    OPP = -1
    
    # First check for immediate winning moves
    for r in range(6):
        for c in range(6):
            if board[r][c] == EMPTY:
                # Test placing here
                temp_board = np.copy(board)
                temp_board[r][c] = YOUR
                if check_win(temp_board, YOUR):
                    # Found winning move, just need to pick any valid rotation
                    quad = random.choice([0,1,2,3])
                    dir = random.choice(['L','R'])
                    return f"{r+1},{c+1},{quad},{dir}"
    
    # Then check if we need to block opponent's winning moves
    for r in range(6):
        for c in range(6):
            if board[r][c] == EMPTY:
                temp_board = np.copy(board)
                temp_board[r][c] = OPP
                if check_win(temp_board, OPP):
                    # Block this space, then pick rotation that least helps opponent
                    quad, dir = find_safest_rotation(board, r, c)
                    return f"{r+1},{c+1},{quad},{dir}"
    
    # Find all empty positions
    empty_positions = [(r,c) for r in range(6) for c in range(6) if board[r][c] == EMPTY]
    
    # Score positions based on centrality and potential
    scored_moves = []
    for r,c in empty_positions:
        score = 0
        # Center control bonus
        if (r in [2,3] and c in [2,3]):
            score += 2
        elif (r in [1,4] and c in [1,4]):
            score += 1
        
        # Potential lines evaluation
        score += evaluate_position(board, r, c, YOUR)
        
        scored_moves.append((score, r, c))
    
    # Sort by score descending
    scored_moves.sort(reverse=True)
    
    # Select top move (with some randomness among top candidates if tied)
    max_score = scored_moves[0][0]
    top_moves = [m for m in scored_moves if m[0] == max_score]
    _, best_r, best_c = random.choice(top_moves)
    
    # Choose rotation that improves our position
    quad, dir = find_best_rotation(board, best_r, best_c)
    
    return f"{best_r+1},{best_c+1},{quad},{dir}"

def check_win(board, player):
    # Check if player has 5 in a row
    for r in range(6):
        for c in range(6):
            if c <= 1:  # Horizontal
                if all(board[r][c+i] == player for i in range(5)):
                    return True
            if r <= 1:  # Vertical
                if all(board[r+i][c] == player for i in range(5)):
                    return True
            if r <= 1 and c <= 1:  # Diagonal down-right
                if all(board[r+i][c+i] == player for i in range(5)):
                    return True
            if r <= 1 and c >= 4:  # Diagonal down-left
                if all(board[r+i][c-i] == player for i in range(5)):
                    return True
    return False

def evaluate_position(board, r, c, player):
    directions = [(1,0), (0,1), (1,1), (1,-1)]  # Vertical, horizontal, diagonal
    score = 0
    
    for dr, dc in directions:
        count_left = 0
        count_right = 0
        
        # Check one direction
        for i in range(1, 5):
            nr, nc = r + dr*i, c + dc*i
            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == player:
                count_right += 1
            else:
                break
        
        # Check opposite direction
        for i in range(1, 5):
            nr, nc = r - dr*i, c - dc*i
            if 0 <= nr < 6 and 0 <= nc < 6 and board[nr][nc] == player:
                count_left += 1
            else:
                break
        
        total = count_left + count_right + 1
        if total >= 5:
            return 100  # Win next move
        if total == 4:
            score += 10
        elif total == 3:
            score += 5
        elif total == 2:
            score += 2
    
    return score

def get_quadrant(r, c):
    if r < 3:
        if c < 3: return 0
        else: return 1
    else:
        if c < 3: return 2
        else: return 3

def find_safest_rotation(board, r, c):
    # Try rotations that minimize opponent potential
    quad = get_quadrant(r, c)
    dir = random.choice(['L','R'])
    return quad, dir

def find_best_rotation(board, r, c):
    # Simple heuristic: choose rotation in same quadrant as placement
    quad = get_quadrant(r, c)
    dir = random.choice(['L','R'])
    return quad, dir
