
import numpy as np

def policy(board):
    """Main policy function that returns the best column move."""
    board_np = np.array(board)
    
    # Get valid moves
    valid_moves = [c for c in range(7) if board_np[0, c] == 0]
    if not valid_moves:
        return 3  # Fallback to center
    
    # 1. Check for immediate winning move
    for col in valid_moves:
        row = get_next_open_row(board_np, col)
        if is_winning_move(board_np, row, col, 1):
            return col
    
    # 2. Check for opponent's immediate win and block
    for col in valid_moves:
        row = get_next_open_row(board_np, col)
        board_np[row, col] = -1
        if is_winning_move(board_np, row, col, -1):
            board_np[row, col] = 0
            return col
        board_np[row, col] = 0
    
    # 3. Use minimax with alpha-beta pruning
    # Order columns by preference (center first for better pruning)
    ordered_cols = [3, 2, 4, 1, 5, 0, 6]
    valid_ordered = [c for c in ordered_cols if c in valid_moves]
    
    best_score = -np.inf
    best_col = valid_ordered[0]
    
    # Depth 5 provides good balance of strength and speed
    for col in valid_ordered:
        row = get_next_open_row(board_np, col)
        board_np[row, col] = 1
        score = minimax(board_np, 5, -np.inf, np.inf, False)
        board_np[row, col] = 0
        
        if score > best_score:
            best_score = score
            best_col = col
    
    return best_col

def get_next_open_row(board, col):
    """Find the lowest empty row in the given column."""
    for r in range(5, -1, -1):
        if board[r, col] == 0:
            return r

def is_winning_move(board, row, col, player):
    """Check if placing a disc at (row, col) results in a win."""
    # Check horizontal
    count = 1
    c = col - 1
    while c >= 0 and board[row, c] == player:
        count += 1
        c -= 1
    c = col + 1
    while c < 7 and board[row, c] == player:
        count += 1
        c += 1
    if count >= 4:
        return True
    
    # Check vertical (only need to check down)
    if row <= 2:
        count = 1
        for r in range(row + 1, row + 4):
            if board[r, col] == player:
                count += 1
            else:
                break
        if count == 4:
            return True
    
    # Check positive diagonal (\)
    count = 1
    r, c = row - 1, col - 1
    while r >= 0 and c >= 0 and board[r, c] == player:
        count += 1
        r -= 1
        c -= 1
    r, c = row + 1, col + 1
    while r < 6 and c < 7 and board[r, c] == player:
        count += 1
        r += 1
        c += 1
    if count >= 4:
        return True
    
    # Check negative diagonal (/)
    count = 1
    r, c = row - 1, col + 1
    while r >= 0 and c < 7 and board[r, c] == player:
        count += 1
        r -= 1
        c += 1
    r, c = row + 1, col - 1
    while r < 6 and c >= 0 and board[r, c] == player:
        count += 1
        r += 1
        c -= 1
    if count >= 4:
        return True
    
    return False

def get_winner(board):
    """Check if game has a winner. Returns 1, -1, 0 (draw), or None."""
    # Check horizontal
    for r in range(6):
        for c in range(4):
            if board[r, c] != 0 and all(board[r, c + i] == board[r, c] for i in range(4)):
                return board[r, c]
    
    # Check vertical
    for c in range(7):
        for r in range(3):
            if board[r, c] != 0 and all(board[r + i, c] == board[r, c] for i in range(4)):
                return board[r, c]
    
    # Check positive diagonal
    for r in range(3):
        for c in range(4):
            if board[r, c] != 0 and all(board[r + i, c + i] == board[r, c] for i in range(4)):
                return board[r, c]
    
    # Check negative diagonal
    for r in range(3):
        for c in range(3, 7):
            if board[r, c] != 0 and all(board[r + i, c - i] == board[r, c] for i in range(4)):
                return board[r, c]
    
    # Check draw
    if not np.any(board == 0):
        return 0
    
    return None

def evaluate_window(window, player):
    """Score a window of 4 cells from AI's perspective."""
    score = 0
    opponent = -player
    
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = window.count(0)
    
    if player_count == 4:
        score += 100
    elif player_count == 3 and empty_count == 1:
        score += 5
    elif player_count == 2 and empty_count == 2:
        score += 2
    
    if opponent_count == 4:
        score -= 100
    elif opponent_count == 3 and empty_count == 1:
        score -= 4
    
    return score

def evaluate(board):
    """Evaluate board state from AI player (1) perspective."""
    score = 0
    player = 1
    
    # Center column preference
    center_array = [int(i) for i in list(board[:, 3])]
    center_count = center_array.count(player)
    score += center_count * 3
    
    # Horizontal windows
    for r in range(6):
        row_array = [int(i) for i in list(board[r, :])]
        for c in range(4):
            window = row_array[c:c+4]
            score += evaluate_window(window, player)
    
    # Vertical windows
    for c in range(7):
        col_array = [int(i) for i in list(board[:, c])]
        for r in range(3):
            window = col_array[r:r+4]
            score += evaluate_window(window, player)
    
    # Positive diagonal windows
    for r in range(3):
        for c in range(4):
            window = [board[r+i, c+i] for i in range(4)]
            score += evaluate_window(window, player)
    
    # Negative diagonal windows
    for r in range(3):
        for c in range(3, 7):
            window = [board[r+i, c-i] for i in range(4)]
            score += evaluate_window(window, player)
    
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """Minimax algorithm with alpha-beta pruning."""
    valid_moves = [c for c in range(7) if board[0, c] == 0]
    
    # Terminal state
    winner = get_winner(board)
    if depth == 0 or winner is not None:
        if winner == 1:
            return 1000000
        elif winner == -1:
            return -1000000
        elif winner == 0:
            return 0
        return evaluate(board)
    
    if maximizing_player:
        value = -np.inf
        for col in valid_moves:
            row = get_next_open_row(board, col)
            board[row, col] = 1
            value = max(value, minimax(board, depth-1, alpha, beta, False))
            board[row, col] = 0
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = np.inf
        for col in valid_moves:
            row = get_next_open_row(board, col)
            board[row, col] = -1
            value = min(value, minimax(board, depth-1, alpha, beta, True))
            board[row, col] = 0
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value
