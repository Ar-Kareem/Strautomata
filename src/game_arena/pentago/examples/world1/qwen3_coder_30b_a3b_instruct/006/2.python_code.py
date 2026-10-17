
import numpy as np
from copy import deepcopy

def check_win(board, player):
    """Check if player has won (5 or more in a row)"""
    # Check horizontal
    for row in range(6):
        for col in range(2):
            if all(board[row][col+i] == player for i in range(5)):
                return True
    # Check vertical
    for col in range(6):
        for row in range(2):
            if all(board[row+i][col] == player for i in range(5)):
                return True
    # Check diagonal (top-left to bottom-right)
    for row in range(2):
        for col in range(2):
            if all(board[row+i][col+i] == player for i in range(5)):
                return True
    # Check diagonal (top-right to bottom-left)
    for row in range(2):
        for col in range(4, 6):
            if all(board[row+i][col-i] == player for i in range(5)):
                return True
    return False

def rotate_quadrant(board, quad, direction):
    """Rotate a quadrant: 0=top-left, 1=top-right, 2=bottom-left, 3=bottom-right"""
    # Define quadrant bounds
    quad_bounds = [
        (0, 3, 0, 3),  # top-left
        (0, 3, 3, 6),  # top-right
        (3, 6, 0, 3),  # bottom-left
        (3, 6, 3, 6)   # bottom-right
    ]
    
    r_start, r_end, c_start, c_end = quad_bounds[quad]
    
    # Extract quadrant
    quadrant = [board[i][c_start:c_end] for i in range(r_start, r_end)]
    
    # Rotate
    if direction == 'R':
        # 90 degrees clockwise
        quadrant = list(zip(*quadrant[::-1]))
    else:
        # 90 degrees counter-clockwise
        quadrant = list(zip(*quadrant))[::-1]
    
    # Place back
    for i in range(r_start, r_end):
        for j in range(c_start, c_end):
            board[i][j] = quadrant[i - r_start][j - c_start]

def evaluate_board(board, player):
    """Simple heuristic evaluation function"""
    score = 0
    opponent = 3 - player  # 1->2, 2->1
    
    # Count 4-in-a-rows and 3-in-a-rows for each player
    for row in range(6):
        for col in range(2):
            consecutive = 0
            player_count = 0
            for i in range(5):
                if board[row][col+i] == player:
                    player_count += 1
                    consecutive += 1
                elif board[row][col+i] == 0:
                    consecutive = 0
                else:
                    consecutive = 0
                    
            if player_count == 4:
                score += 100
            elif player_count == 3 and consecutive == 3:
                score += 10
            
            consecutive = 0
            player_count = 0
            for i in range(5):
                if board[row+i][col] == player:
                    player_count += 1
                    consecutive += 1
                elif board[row+i][col] == 0:
                    consecutive = 0
                else:
                    consecutive = 0
                    
            if player_count == 4:
                score += 100
            elif player_count == 3 and consecutive == 3:
                score += 10

    # Diagonal evaluation
    for row in range(2):
        for col in range(2):
            consecutive = 0
            player_count = 0
            for i in range(5):
                if board[row+i][col+i] == player:
                    player_count += 1
                    consecutive += 1
                elif board[row+i][col+i] == 0:
                    consecutive = 0
                else:
                    consecutive = 0
                    
            if player_count == 4:
                score += 100
            elif player_count == 3 and consecutive == 3:
                score += 10

    # Center control bonus
    center_positions = [[2,2], [2,3], [3,2], [3,3]]
    for r, c in center_positions:
        if board[r][c] == player:
            score += 5
    
    return score

def get_legal_moves(you, opponent):
    """Generate all possible legal moves for the current player"""
    moves = []
    # Try placing on each empty position
    for r in range(6):
        for c in range(6):
            if you[r][c] == 0 and opponent[r][c] == 0:
                # Try rotating each quadrant
                for quad in range(4):
                    for direction in ['L', 'R']:
                        moves.append((r, c, quad, direction))
    return moves

def policy(you, opponent):
    """The main policy function to determine the next move"""
    you = np.array(you)
    opponent = np.array(opponent)
    
    # Evaluate all legal moves
    best_move = None
    best_value = float('-inf')
    
    legal_moves = get_legal_moves(you, opponent)
    
    # Evaluate each move
    for r, c, quad, direction in legal_moves:
        # Make a temporary copy of the board
        temp_you = deepcopy(you)
        temp_opponent = deepcopy(opponent)
        
        # Place the marble
        temp_you[r][c] = 1
        
        # Rotate the quadrant
        rotate_quadrant(temp_you, quad, direction)
        rotate_quadrant(temp_opponent, quad, direction)
        
        # Check if this gives us an immediate win
        if check_win(temp_you, 1):
            return f"{r+1},{c+1},{quad},{direction}"
        
        # Check if opponent can win next move
        opponent_wins = False
        temp_legal_moves = get_legal_moves(temp_you, temp_opponent) 
        for nr, nc, nquad, ndir in temp_legal_moves:
            # Make opponent move
            temp_you2 = deepcopy(temp_you)
            temp_opponent2 = deepcopy(temp_opponent)
            temp_opponent2[nr][nc] = 1
            rotate_quadrant(temp_you2, nquad, ndir)
            rotate_quadrant(temp_opponent2, nquad, ndir)
            
            if check_win(temp_opponent2, 2):
                opponent_wins = True
                break
        
        # If opponent can win, block it immediately
        if opponent_wins:
            return f"{r+1},{c+1},{quad},{direction}"
        
        # Otherwise evaluate using our heuristic
        eval_score = evaluate_board(temp_you, 1)
        
        # Prefer moves that don't create immediate opponent threats  
        if eval_score > best_value:
            best_value = eval_score
            best_move = (r, c, quad, direction)
    
    # If no good move found, make a basic move
    if best_move is None:
        # Select a simple move
        for r in range(6):
            for c in range(6):
                if you[r][c] == 0 and opponent[r][c] == 0:
                    for quad in range(4):
                        return f"{r+1},{c+1},{quad},L"
        
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
