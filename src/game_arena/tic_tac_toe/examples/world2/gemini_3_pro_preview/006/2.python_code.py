
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next move (row, col) for the 4x4 Tic Tac Toe game.
    The AI plays as 1, opponent as -1.
    """
    
    # Constants
    PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    SIZE = 4
    MAX_DEPTH = 3  # Depth limit to stay within 1s time limit (Python is slow)
    INF = float('inf')

    def check_winner(b):
        # Rows, Columns
        for i in range(SIZE):
            if abs(sum(b[i])) == SIZE: return b[i][0]
            if abs(sum(b[r][i] for r in range(SIZE))) == SIZE: return b[0][i]
        
        # Diagonals
        diag1 = sum(b[i][i] for i in range(SIZE))
        if abs(diag1) == SIZE: return b[0][0]
        
        diag2 = sum(b[i][SIZE-1-i] for i in range(SIZE))
        if abs(diag2) == SIZE: return b[0][SIZE-1]
        
        # Draw check
        if all(cell != EMPTY for row in b for cell in row):
            return 0
            
        return None

    def evaluate(b):
        score = 0
        lines = []
        
        # Collect all lines (rows, cols, diags)
        for i in range(SIZE):
            lines.append(b[i]) # Row
            lines.append([b[r][i] for r in range(SIZE)]) # Col
        lines.append([b[i][i] for i in range(SIZE)]) # Main diag
        lines.append([b[i][SIZE-1-i] for i in range(SIZE)]) # Anti diag

        for line in lines:
            if OPPONENT not in line:
                count_p = line.count(PLAYER)
                if count_p == 4: score += 10000
                elif count_p == 3: score += 100
                elif count_p == 2: score += 10
                elif count_p == 1: score += 1
            elif PLAYER not in line:
                count_o = line.count(OPPONENT)
                if count_o == 4: score -= 10000
                elif count_o == 3: score -= 100
                elif count_o == 2: score -= 10
                elif count_o == 1: score -= 1
        return score

    def minimax(b, depth, alpha, beta, is_maximizing):
        winner = check_winner(b)
        if winner == PLAYER: return 100000 - depth # Prefer faster wins
        if winner == OPPONENT: return -100000 + depth # Prefer slower losses
        if winner == 0: return 0
        
        if depth >= MAX_DEPTH:
            return evaluate(b)

        moves = [(r, c) for r in range(SIZE) for c in range(SIZE) if b[r][c] == EMPTY]
        
        # Heuristic sort to improve pruning: check center first
        moves.sort(key=lambda m: abs(m[0]-1.5) + abs(m[1]-1.5))

        if is_maximizing:
            max_eval = -INF
            for r, c in moves:
                b[r][c] = PLAYER
                eval_val = minimax(b, depth + 1, alpha, beta, False)
                b[r][c] = EMPTY
                max_eval = max(max_eval, eval_val)
                alpha = max(alpha, eval_val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = INF
            for r, c in moves:
                b[r][c] = OPPONENT
                eval_val = minimax(b, depth + 1, alpha, beta, True)
                b[r][c] = EMPTY
                min_eval = min(min_eval, eval_val)
                beta = min(beta, eval_val)
                if beta <= alpha:
                    break
            return min_eval

    # --- Main Logic ---
    valid_moves = [(r, c) for r in range(SIZE) for c in range(SIZE) if board[r][c] == EMPTY]
    
    # If starting or early game, pick center or random to save time
    if len(valid_moves) >= 15:
        # Prefer center
        centers = [(1,1), (1,2), (2,1), (2,2)]
        avail_centers = [m for m in centers if m in valid_moves]
        if avail_centers: return random.choice(avail_centers)
        return random.choice(valid_moves)

    best_score = -INF
    best_move = valid_moves[0]
    
    # Root level search
    for r, c in valid_moves:
        board[r][c] = PLAYER
        score = minimax(board, 0, -INF, INF, False)
        board[r][c] = EMPTY
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    return best_move
