
def policy(state: list[list[object]], role: str) -> str:
    COLS = 7
    ROWS = 6
    
    # Parse the state
    board = {}  # (col, row) -> player
    heights = {c: 0 for c in range(1, COLS + 1)}  # col -> current height
    
    for prop in state:
        if len(prop) >= 4 and prop[0] == "cell":
            col = int(prop[1])
            row = int(prop[2])
            player = prop[3]
            board[(col, row)] = player
            if row > heights[col]:
                heights[col] = row
    
    opponent = "black" if role == "red" else "red"
    
    # Get legal columns (not full)
    legal_cols = [c for c in range(1, COLS + 1) if heights[c] < ROWS]
    
    if not legal_cols:
        return "drop(1)"  # Should not happen in valid game
    
    # Check for immediate win
    for c in legal_cols:
        r = heights[c] + 1
        board[(c, r)] = role
        if check_win(board, c, r, role):
            return f"drop({c})"
        board.pop((c, r))
    
    # Check for opponent immediate win (must block)
    for c in legal_cols:
        r = heights[c] + 1
        board[(c, r)] = opponent
        if check_win(board, c, r, opponent):
            board.pop((c, r))
            return f"drop({c})"
        board.pop((c, r))
    
    # Move ordering: prefer center columns (standard Connect Four strategy)
    move_order = [4, 3, 5, 2, 6, 1, 7]
    ordered_legal = [c for c in move_order if c in legal_cols]
    
    best_col = ordered_legal[0]
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Search with negamax
    for c in ordered_legal:
        r = heights[c] + 1
        board[(c, r)] = role
        heights[c] += 1
        
        score = -negamax(board, heights, opponent, 6, -beta, -alpha, ROWS, COLS)
        
        heights[c] -= 1
        board.pop((c, r))
        
        if score > best_score:
            best_score = score
            best_col = c
            alpha = max(alpha, score)
    
    return f"drop({best_col})"


def check_win(board, col, row, player):
    """Check if player has 4 in a row including the piece at col,row"""
    directions = [(1, 0), (0, 1), (1, 1), (1, -1)]
    for dc, dr in directions:
        count = 1
        # Forward direction
        c, r = col + dc, row + dr
        while board.get((c, r)) == player:
            count += 1
            c += dc
            r += dr
        # Backward direction
        c, r = col - dc, row - dr
        while board.get((c, r)) == player:
            count += 1
            c -= dc
            r -= dr
        if count >= 4:
            return True
    return False


def negamax(board, heights, player, depth, alpha, beta, ROWS, COLS):
    """Negamax search with alpha-beta pruning"""
    opponent = "black" if player == "red" else "red"
    
    # Get legal moves
    legal = [c for c in range(1, COLS + 1) if heights[c] < ROWS]
    
    if not legal:
        return 0  # Draw
    
    if depth == 0:
        return evaluate(board, heights, player, opponent, ROWS, COLS)
    
    move_order = [4, 3, 5, 2, 6, 1, 7]
    max_eval = -float('inf')
    
    for c in move_order:
        if c not in legal:
            continue
        
        r = heights[c] + 1
        board[(c, r)] = player
        heights[c] += 1
        
        # Check if this move wins immediately
        if check_win(board, c, r, player):
            eval_score = 100000 + depth  # Prefer earlier wins
        else:
            eval_score = -negamax(board, heights, opponent, depth - 1, -beta, -alpha, ROWS, COLS)
        
        heights[c] -= 1
        board.pop((c, r))
        
        max_eval = max(max_eval, eval_score)
        alpha = max(alpha, eval_score)
        if alpha >= beta:
            break
    
    return max_eval


def evaluate(board, heights, player, opponent, ROWS, COLS):
    """Evaluate board by checking all windows of 4"""
    score = 0
    
    # Horizontal windows
    for r in range(1, ROWS + 1):
        for c in range(1, COLS - 2):
            window = [board.get((c + i, r)) for i in range(4)]
            score += score_window(window, player, opponent)
    
    # Vertical windows
    for c in range(1, COLS + 1):
        for r in range(1, ROWS - 2):
            window = [board.get((c, r + i)) for i in range(4)]
            score += score_window(window, player, opponent)
    
    # Diagonal / windows
    for c in range(1, COLS - 2):
        for r in range(1, ROWS - 2):
            window = [board.get((c + i, r + i)) for i in range(4)]
            score += score_window(window, player, opponent)
    
    # Diagonal \ windows
    for c in range(1, COLS - 2):
        for r in range(4, ROWS + 1):
            window = [board.get((c + i, r - i)) for i in range(4)]
            score += score_window(window, player, opponent)
    
    return score


def score_window(window, player, opponent):
    """Score a 4-cell window"""
    player_count = window.count(player)
    opponent_count = window.count(opponent)
    empty_count = 4 - player_count - opponent_count
    
    if player_count == 4:
        return 1000
    if opponent_count == 4:
        return -1000
    if player_count == 3 and empty_count == 1:
        return 50  # Threat
    if opponent_count == 3 and empty_count == 1:
        return -50  # Must block
    if player_count == 2 and empty_count == 2:
        return 10
    if opponent_count == 2 and empty_count == 2:
        return -10
    return 0
