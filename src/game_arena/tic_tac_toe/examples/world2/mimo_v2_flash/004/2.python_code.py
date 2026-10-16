
import sys
import time

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Minimax with Alpha-Beta pruning for 4x4 Tic Tac Toe.
    Assumes standard 4-in-a-row win condition.
    """
    # Constants for players
    AI_PLAYER = 1
    OPPONENT = -1
    EMPTY = 0
    
    # Board size
    SIZE = 4
    WIN_LENGTH = 4  # Standard for 4x4 Tic Tac Toe
    
    # Heuristic weights
    WIN_SCORE = 1000
    BLOCK_WIN_SCORE = 500  # If opponent has 3 in a row, blocking is crucial
    POTENTIAL_WIN_SCORE = 10 # Encourages building lines
    
    # Time limit guard (in seconds)
    TIMEOUT = 0.9
    start_time = time.time()

    def is_full(b):
        return all(cell != EMPTY for row in b for cell in row)

    def get_valid_moves(b):
        moves = []
        for r in range(SIZE):
            for c in range(SIZE):
                if b[r][c] == EMPTY:
                    moves.append((r, c))
        return moves

    def check_winner(b, player):
        # Check Horizontal
        for r in range(SIZE):
            for c in range(SIZE - WIN_LENGTH + 1):
                if all(b[r][c+i] == player for i in range(WIN_LENGTH)):
                    return True
        
        # Check Vertical
        for r in range(SIZE - WIN_LENGTH + 1):
            for c in range(SIZE):
                if all(b[r+i][c] == player for i in range(WIN_LENGTH)):
                    return True
        
        # Check Diagonal (Top-Left to Bottom-Right)
        for r in range(SIZE - WIN_LENGTH + 1):
            for c in range(SIZE - WIN_LENGTH + 1):
                if all(b[r+i][c+i] == player for i in range(WIN_LENGTH)):
                    return True
        
        # Check Anti-Diagonal (Top-Right to Bottom-Left)
        for r in range(SIZE - WIN_LENGTH + 1):
            for c in range(WIN_LENGTH - 1, SIZE):
                if all(b[r+i][c-i] == player for i in range(WIN_LENGTH)):
                    return True
        
        return False

    def evaluate_window(window, player):
        opponent = -player
        score = 0
        
        player_count = window.count(player)
        empty_count = window.count(EMPTY)
        opponent_count = window.count(opponent)
        
        # Immediate Win
        if player_count == WIN_LENGTH:
            return WIN_SCORE
        
        # Potential Win (opportunity)
        if player_count == WIN_LENGTH - 1 and empty_count == 1:
            score += POTENTIAL_WIN_SCORE * 5
            
        # Potential Threat (opponent is about to win)
        if opponent_count == WIN_LENGTH - 1 and empty_count == 1:
            score -= BLOCK_WIN_SCORE
            
        # Building lines
        if player_count == WIN_LENGTH - 2 and empty_count == 2:
            score += POTENTIAL_WIN_SCORE
            
        return score

    def evaluate_board(b, player):
        score = 0
        
        # Center preference (usually good in grid games)
        center_array = [b[i][j] for i in range(1, SIZE-1) for j in range(1, SIZE-1)]
        center_count = center_array.count(player)
        score += center_count * 3

        # Horizontal Windows
        for r in range(SIZE):
            row_array = list(b[r])
            for c in range(SIZE - WIN_LENGTH + 1):
                window = row_array[c:c+WIN_LENGTH]
                score += evaluate_window(window, player)
        
        # Vertical Windows
        for c in range(SIZE):
            col_array = [b[r][c] for r in range(SIZE)]
            for r in range(SIZE - WIN_LENGTH + 1):
                window = col_array[r:r+WIN_LENGTH]
                score += evaluate_window(window, player)
                
        # Diagonal Windows
        for r in range(SIZE - WIN_LENGTH + 1):
            for c in range(SIZE - WIN_LENGTH + 1):
                window = [b[r+i][c+i] for i in range(WIN_LENGTH)]
                score += evaluate_window(window, player)
                
        for r in range(SIZE - WIN_LENGTH + 1):
            for c in range(WIN_LENGTH - 1, SIZE):
                window = [b[r+i][c-i] for i in range(WIN_LENGTH)]
                score += evaluate_window(window, player)
                
        return score

    def minimax(b, depth, alpha, beta, maximizing_player):
        # Check timeout
        if time.time() - start_time > TIMEOUT:
            return 0, None

        # Terminal states
        if check_winner(b, AI_PLAYER):
            return (WIN_SCORE + depth), None
        if check_winner(b, OPPONENT):
            return -(WIN_SCORE + depth), None
        if is_full(b) or depth == 0:
            return evaluate_board(b, AI_PLAYER), None

        valid_moves = get_valid_moves(b)
        
        # Move Ordering: Prioritize center and edges for better pruning
        # This heuristic sorts moves to find the best branches first
        valid_moves.sort(key=lambda m: (
            (m[0] in [1, 2] and m[1] in [1, 2]),
            (m[0] in [0, 3] and m[1] in [0, 3])
        ), reverse=True)

        best_move = valid_moves[0]

        if maximizing_player:
            max_eval = -float('inf')
            for move in valid_moves:
                b[move[0]][move[1]] = AI_PLAYER
                eval_score, _ = minimax(b, depth - 1, alpha, beta, False)
                b[move[0]][move[1]] = EMPTY
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in valid_moves:
                b[move[0]][move[1]] = OPPONENT
                eval_score, _ = minimax(b, depth - 1, alpha, beta, True)
                b[move[0]][move[1]] = EMPTY
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval, best_move

    # Main Logic
    # 1. Check for immediate win
    valid_moves = get_valid_moves(board)
    for r, c in valid_moves:
        board[r][c] = AI_PLAYER
        if check_winner(board, AI_PLAYER):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # 2. Check for immediate block
    for r, c in valid_moves:
        board[r][c] = OPPONENT
        if check_winner(board, OPPONENT):
            board[r][c] = EMPTY
            return (r, c)
        board[r][c] = EMPTY

    # 3. Run Minimax Search
    # Depth 4-5 is usually sufficient for 4x4 to prevent timeout and be smart enough
    _, best_move = minimax(board, 4, -float('inf'), float('inf'), True)

    return best_move
