
# Constants
ROWS = 6
COLS = 7

# Precompute all possible lines of 4 for efficiency
lines = []
# Horizontal lines
for r in range(ROWS):
    for c in range(COLS-3):
        lines.append([(r, c+i) for i in range(4)])
# Vertical lines
for c in range(COLS):
    for r in range(ROWS-3):
        lines.append([(r+i, c) for i in range(4)])
# Diagonal lines (down-right)
for r in range(ROWS-3):
    for c in range(COLS-3):
        lines.append([(r+i, c+i) for i in range(4)])
# Diagonal lines (down-left)
for r in range(ROWS-3):
    for c in range(3, COLS):
        lines.append([(r+i, c-i) for i in range(4)])

def make_move(board, col, player):
    """Simulate dropping a disc in the specified column."""
    new_board = [row[:] for row in board]
    for row in range(ROWS-1, -1, -1):
        if new_board[row][col] == 0:
            new_board[row][col] = player
            break
    return new_board

def is_winner(board, player):
    """Check if the specified player has won."""
    for line in lines:
        if all(board[r][c] == player for r, c in line):
            return True
    return False

def evaluate_board(board):
    """Evaluate the board state for the current player (1)."""
    score = 0
    for line in lines:
        my_count = sum(1 for r, c in line if board[r][c] == 1)
        opp_count = sum(1 for r, c in line if board[r][c] == -1)
        
        if opp_count > 0:
            if my_count == 0:
                if opp_count == 4:
                    score -= 100000
                elif opp_count == 3:
                    score -= 100
                elif opp_count == 2:
                    score -= 10
        else:
            if my_count == 4:
                score += 100000
            elif my_count == 3:
                score += 100
            elif my_count == 2:
                score += 10
            elif my_count == 1:
                score += 1
    return score

def center_bias(board):
    """Calculate a bonus for discs in the center of the board."""
    score = 0
    for r in range(ROWS):
        for c in range(COLS):
            if board[r][c] == 1:
                if c == 3:
                    score += 1
                elif c in (2, 4):
                    score += 0.5
                elif c in (1, 5):
                    score += 0.25
                else:  # c in (0, 6)
                    score += 0.125
    return score

def policy(board):
    """Main policy function to determine the next move."""
    # Find all valid moves (columns with at least one empty space)
    possible_moves = [col for col in range(COLS) if board[0][col] == 0]
    
    if not possible_moves:
        return 0  # Fallback if no moves available (should not happen in valid states)
    
    # 1. Check for immediate wins
    for col in possible_moves:
        new_board = make_move(board, col, 1)
        if is_winner(new_board, 1):
            return col
    
    # 2. Check for blocking moves (prevent opponent's immediate win)
    safe_moves = []
    for col in possible_moves:
        new_board = make_move(board, col, 1)
        opponent_has_win = False
        
        # Check if opponent has any winning move
        opp_moves = [c for c in range(COLS) if new_board[0][c] == 0]
        for opp_col in opp_moves:
            opp_board = make_move(new_board, opp_col, -1)
            if is_winner(opp_board, -1):
                opponent_has_win = True
                break
        
        if not opponent_has_win:
            safe_moves.append(col)
    
    # Use safe_moves if available, otherwise consider all moves
    moves_to_evaluate = safe_moves if safe_moves else possible_moves
    
    # 3. Evaluate remaining moves using heuristics
    best_col = None
    best_score = float('-inf')
    
    for col in moves_to_evaluate:
        new_board = make_move(board, col, 1)
        score = evaluate_board(new_board) + center_bias(new_board)
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col
