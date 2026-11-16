
import numpy as np

def policy(you, opponent):
    # Convert inputs to numpy arrays for easier manipulation
    you = np.array(you)
    opponent = np.array(opponent)
    board = you + opponent  # 0=empty, 1=you, 2=opponent
    
    # Find all empty cells
    empty_cells = [(r, c) for r in range(6) for c in range(6) if board[r][c] == 0]
    
    # Precompute all possible lines (5-in-a-row positions)
    lines = []
    # Horizontal
    for r in range(6):
        for c in range(2):
            lines.append([(r, c+i) for i in range(5)])
    # Vertical
    for r in range(2):
        for c in range(6):
            lines.append([(r+i, c) for i in range(5)])
    # Diagonal down-right
    for r in range(2):
        for c in range(2):
            lines.append([(r+i, c+i) for i in range(5)])
    # Diagonal up-right
    for r in range(4, 6):
        for c in range(2):
            lines.append([(r-i, c+i) for i in range(5)])
    
    # Helper function to check if a player has a winning line on a board
    def has_win(player_board, board):
        for line in lines:
            if all(board[pos[0]][pos[1]] == player_board[pos[0]][pos[1]] and board[pos[0]][pos[1]] != 0 for pos in line):
                return True
        return False
    
    # Helper function to count connected groups for heuristic
    def evaluate_board(player_board, board):
        score = 0
        # Check all 5-in-a-row lines
        for line in lines:
            count = 0
            for r, c in line:
                if player_board[r][c] == 1:
                    count += 1
            # Reward potential lines
            if count == 5:
                score += 10000
            elif count == 4:
                # Check if it's a real threat (can be completed)
                empty_pos = [(r, c) for r, c in line if player_board[r][c] == 0]
                if len(empty_pos) == 1:
                    er, ec = empty_pos[0]
                    if board[er][ec] == 0:  # Empty cell
                        score += 1000
                else:
                    score += 100
            elif count == 3:
                empty_pos = [(r, c) for r, c in line if player_board[r][c] == 0]
                if len(empty_pos) == 2:
                    # Check if both are empty (potential double threat)
                    if all(board[r][c] == 0 for r, c in empty_pos):
                        score += 200
                    else:
                        score += 50
                else:
                    score += 30
            elif count == 2:
                score += 10
            elif count == 1:
                score += 2
        
        # Additional heuristic: center control
        center_bonus = 0
        for r in range(2, 4):
            for c in range(2, 4):
                if player_board[r][c] == 1:
                    center_bonus += 5
        score += center_bonus
        
        return score
    
    best_move = None
    best_score = -float('inf')
    
    # Try all possible moves
    for r, c in empty_cells:
        # Temporarily place marble
        temp_board = board.copy()
        temp_board[r][c] = 1  # Player's marble
        
        # Try all quadrants and rotations
        for quad in range(4):
            for direction in ['L', 'R']:
                # Create rotated board
                rotated = temp_board.copy()
                
                # Define quadrant bounds
                if quad == 0:
                    rows, cols = slice(0, 3), slice(0, 3)
                elif quad == 1:
                    rows, cols = slice(0, 3), slice(3, 6)
                elif quad == 2:
                    rows, cols = slice(3, 6), slice(0, 3)
                else:  # quad == 3
                    rows, cols = slice(3, 6), slice(3, 6)
                
                quadrant = rotated[rows, cols].copy()
                
                if direction == 'R':  # Clockwise
                    rotated[rows, cols] = np.rot90(quadrant, k=-1)
                else:  # 'L' - Anticlockwise
                    rotated[rows, cols] = np.rot90(quadrant, k=1)
                
                # Check if this move wins
                you_after = (rotated == 1).astype(int)
                opponent_after = (rotated == 2).astype(int)
                
                you_win = has_win(you_after, rotated)
                opp_win = has_win(opponent_after, rotated)
                
                if you_win and not opp_win:
                    # Winning move
                    return f"{r+1},{c+1},{quad},{direction}"
                
                # Evaluate non-winning moves
                if not opp_win:  # Don't make moves that let opponent win immediately
                    score = 0
                    
                    # Heuristic evaluation
                    you_score = evaluate_board(you_after, rotated)
                    opp_score = evaluate_board(opponent_after, rotated)
                    
                    score = you_score - opp_score
                    
                    # Bonus for immediate threats
                    for line in lines:
                        you_count = sum(1 for r2, c2 in line if you_after[r2][c2] == 1)
                        opp_count = sum(1 for r2, c2 in line if opponent_after[r2][c2] == 1)
                        
                        if you_count == 4:
                            score += 500
                        elif opp_count == 4:
                            score -= 800  # Block opponent's threat
                    
                    # Bonus for creating multiple threats
                    threat_count = 0
                    for line in lines:
                        you_count = sum(1 for r2, c2 in line if you_after[r2][c2] == 1)
                        if you_count >= 4:
                            threat_count += 1
                    if threat_count >= 2:
                        score += 300
                    
                    if score > best_score:
                        best_score = score
                        best_move = (r, c, quad, direction)
    
    # Fallback: return any legal move if something went wrong
    if best_move is None and empty_cells:
        r, c = empty_cells[0]
        return f"{r+1},{c+1},0,R"
    
    r, c, quad, direction = best_move
    return f"{r+1},{c+1},{quad},{direction}"
