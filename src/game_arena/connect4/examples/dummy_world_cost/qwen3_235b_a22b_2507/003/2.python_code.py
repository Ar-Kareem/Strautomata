
import numpy as np
from typing import List

def policy(board: List[List[int]]) -> int:
    # Convert to numpy for easier manipulation
    grid = np.array(board, dtype=np.int8)
    
    # Constants
    PLAYER = 1
    OPPONENT = -1
    COLS = 7
    ROWS = 6
    EMPTY = 0

    # Helper: check if column is valid
    def is_valid(col):
        return grid[ROWS-1][col] == EMPTY

    # Helper: drop piece
    def drop_piece(g, col, piece):
        for r in range(ROWS):
            if g[r][col] == EMPTY:
                g[r][col] = piece
                return r, col
        return None, None

    # Helper: undo drop
    def undo_drop(g, col):
        for r in range(ROWS-1, -1, -1):
            if g[r][col] != EMPTY:
                g[r][col] = EMPTY
                return

    # Evaluation function
    def evaluate(g):
        score = 0
        center_col = 3
        
        # Count center column pieces for central control
        for r in range(ROWS):
            if g[r][center_col] == PLAYER:
                score += 1
            elif g[r][center_col] == OPPONENT:
                score -= 1

        # Score all horizontal, vertical, diagonal windows
        def score_window(window, piece):
            score = 0
            opp_piece = OPPONENT if piece == PLAYER else PLAYER
            if list(window).count(piece) == 4:
                score += 1000
            elif list(window).count(piece) == 3 and list(window).count(EMPTY) == 1:
                score += 5
            elif list(window).count(piece) == 2 and list(window).count(EMPTY) == 2:
                score += 2
            if list(window).count(opp_piece) == 3 and list(window).count(EMPTY) == 1:
                score -= 80  # block opponent's 3-in-a-row
            return score

        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = g[r, c:c+4]
                score += score_window(window, PLAYER)
                score -= score_window(window, OPPONENT)

        # Vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                window = g[r:r+4, c]
                score += score_window(window, PLAYER)
                score -= score_window(window, OPPONENT)

        # Diagonal (both positive and negative slope)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                # Positive slope diagonal
                window = np.array([g[r+i][c+i] for i in range(4)])
                score += score_window(window, PLAYER)
                score -= score_window(window, OPPONENT)
                # Negative slope diagonal
                window = np.array([g[r+3-i][c+i] for i in range(4)])
                score += score_window(window, PLAYER)
                score -= score_window(window, OPPONENT)

        return score

    # Check for immediate win or block
    def check_immediate():
        for col in range(COLS):
            if not is_valid(col):
                continue
            row, _ = drop_piece(grid, col, PLAYER)
            if check_winner(grid, row, col):
                undo_drop(grid, col)
                return col
            undo_drop(grid, col)

        for col in range(COLS):
            if not is_valid(col):
                continue
            row, _ = drop_piece(grid, col, OPPONENT)
            if check_winner(grid, row, col):
                undo_drop(grid, col)
                return col
            undo_drop(grid, col)
        return None

    # Check if last move caused a win
    def check_winner(g, r, c):
        if g[r][c] == EMPTY:
            return False
        piece = g[r][c]
        # Check horizontal
        count = 1
        for dc in range(1, 4):
            if c + dc < COLS and g[r][c+dc] == piece:
                count += 1
            else:
                break
        for dc in range(1, 4):
            if c - dc >= 0 and g[r][c-dc] == piece:
                count += 1
            else:
                break
        if count >= 4:
            return True

        # Check vertical
        count = 1
        for dr in range(1, 4):
            if r + dr < ROWS and g[r+dr][c] == piece:
                count += 1
            else:
                break
        for dr in range(1, 4):
            if r - dr >= 0 and g[r-dr][c] == piece:
                count += 1
            else:
                break
        if count >= 4:
            return True

        # Check diagonal / (top-left to bottom-right)
        count = 1
        for d in range(1, 4):
            if r-d >= 0 and c-d >= 0 and g[r-d][c-d] == piece:
                count += 1
            else:
                break
        for d in range(1, 4):
            if r+d < ROWS and c+d < COLS and g[r+d][c+d] == piece:
                count += 1
            else:
                break
        if count >= 4:
            return True

        # Check diagonal \ (bottom-left to top-right)
        count = 1
        for d in range(1, 4):
            if r+d < ROWS and c-d >= 0 and g[r+d][c-d] == piece:
                count += 1
            else:
                break
        for d in range(1, 4):
            if r-d >= 0 and c+d < COLS and g[r-d][c+d] == piece:
                count += 1
            else:
                break
        return count >= 4

    # Minimax with alpha-beta pruning
    def minimax(g, depth, alpha, beta, maximizingPlayer):
        valid_moves = [c for c in range(COLS) if is_valid(c)]
        
        # Check terminal conditions
        # If no valid moves, it's a draw
        if not valid_moves:
            return 0
            
        if depth == 0:
            return evaluate(g)

        # Check for terminal state (win)
        # We cannot know the last move, so we do a full board scan
        player_wins = False
        opponent_wins = False
        for r in range(ROWS):
            for c in range(COLS):
                if g[r][c] != EMPTY:
                    if check_winner(g, r, c):
                        if g[r][c] == PLAYER:
                            player_wins = True
                        else:
                            opponent_wins = True

        if player_wins:
            return 10000
        if opponent_wins:
            return -10000

        if maximizingPlayer:
            max_eval = -float('inf')
            for col in valid_moves:
                r, c = drop_piece(g, col, PLAYER)
                eval_score = minimax(g, depth - 1, alpha, beta, False)
                undo_drop(g, col)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for col in valid_moves:
                r, c = drop_piece(g, col, OPPONENT)
                eval_score = minimax(g, depth - 1, alpha, beta, True)
                undo_drop(g, col)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # First, check for immediate win or block
    immediate = check_immediate()
    if immediate is not None:
        return immediate

    # Determine depth based on current state (limit to avoid timeout)
    # In early game, we can afford more depth
    total_moves = sum(1 for r in range(ROWS) for c in range(COLS) if grid[r][c] != EMPTY)
    depth = 5 if total_moves < 20 else 4

    valid_moves = [c for c in range(COLS) if is_valid(c)]
    best_move = valid_moves[0]
    best_value = -float('inf')
    
    # Iterative deepening for robustness
    try:
        for d in range(1, depth + 1):
            for col in valid_moves:
                r, c = drop_piece(grid, col, PLAYER)
                val = minimax(grid, d - 1, -float('inf'), float('inf'), False)
                undo_drop(grid, col)
                if val > best_value:
                    best_value = val
                    best_move = col
    except:
        pass  # In case of timeout during deep search

    # Ensure we return a valid move
    if not is_valid(best_move):
        best_move = valid_moves[0]  # fallback

    return best_move
