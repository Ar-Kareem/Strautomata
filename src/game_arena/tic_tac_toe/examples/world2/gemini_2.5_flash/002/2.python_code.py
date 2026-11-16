
import math

# --- Constants ---
N = 4
PLAYER = 1
OPPONENT = -1
EMPTY = 0

WIN_SCORE = 1000000  # Score for a winning state
LOSE_SCORE = -1000000 # Score for a losing state
DRAW_SCORE = 0       # Score for a draw

MAX_DEPTH = 6 # Maximum search depth for minimax for performance.
              # A depth of 6 means looking 3 moves ahead for each player (P_1 -> O_1 -> P_2 -> O_2 -> P_3 -> O_3)

# --- Helper Functions ---

def check_win(board: list[list[int]]) -> None:
    """
    Checks if the current board state has a winner or is a draw.
    Returns PLAYER if PLAYER wins, OPPONENT if OPPONENT wins,
    EMPTY if it's a draw, or None if the game is still ongoing.
    """
    # Check rows
    for r in range(N):
        if all(board[r][c] == PLAYER for c in range(N)):
            return PLAYER
        if all(board[r][c] == OPPONENT for c in range(N)):
            return OPPONENT

    # Check columns
    for c in range(N):
        if all(board[r][c] == PLAYER for r in range(N)):
            return PLAYER
        if all(board[r][c] == OPPONENT for r in range(N)):
            return OPPONENT

    # Check main diagonal
    if all(board[i][i] == PLAYER for i in range(N)):
        return PLAYER
    if all(board[i][i] == OPPONENT for i in range(N)):
        return OPPONENT

    # Check anti-diagonal
    if all(board[i][N - 1 - i] == PLAYER for i in range(N)):
        return PLAYER
    if all(board[i][N - 1 - i] == OPPONENT for i in range(N)):
        return OPPONENT

    # Check for draw (no empty cells)
    if all(board[r][c] != EMPTY for r in range(N) for c in range(N)):
        return EMPTY  # Draw

    return None # Game ongoing

def count_open_lines(board: list[list[int]], player: int) -> int:
    """
    Evaluates the board based on potential winning lines for a given player.
    Higher score for more immediate threats / opportunities.
    """
    score = 0
    opponent = -player
    
    # Define all 4-cell segments (rows, columns, main diagonals, anti-diagonals)
    segments = []
    
    # Rows
    for r in range(N):
        for c in range(N - 3): # Only one segment per row for N=4, starting at c=0
           segments.append([(r, c + i) for i in range(4)])
    
    # Columns
    for c in range(N):
        for r in range(N - 3): # Only one segment per column for N=4, starting at r=0
            segments.append([(r + i, c) for i in range(4)])
            
    # Main diagonals (top-left to bottom-right)
    for r in range(N - 3): # Only one segment: (0,0)-(3,3)
        for c in range(N - 3):
            segments.append([(r + i, c + i) for i in range(4)])
            
    # Anti-diagonals (top-right to bottom-left)
    for r in range(N - 3): # Only one segment: (0,3)-(3,0)
        for c in range(3, N): # c starts at 3 for N=4
            segments.append([(r + i, c - i) for i in range(4)])

    for seg in segments:
        player_count = 0
        opponent_count = 0
        empty_count = 0
        
        for r, c in seg:
            if board[r][c] == player:
                player_count += 1
            elif board[r][c] == opponent:
                opponent_count += 1
            else: # EMPTY
                empty_count += 1

        # If a segment is not blocked by the opponent, evaluate its potential
        if opponent_count == 0:
            if player_count == 3 and empty_count == 1:
                score += 100 # Near win (3-in-a-row with 1 empty cell to complete 4)
            elif player_count == 2 and empty_count == 2:
                score += 10  # Two steps to win
            elif player_count == 1 and empty_count == 3:
                score += 1   # Three steps to win
    return score

def heuristic_eval(board: list[list[int]]) -> int:
    """
    Evaluates a non-terminal board state using a heuristic.
    """
    return count_open_lines(board, PLAYER) - count_open_lines(board, OPPONENT)

# --- Minimax with Alpha-Beta Pruning ---

def minimax(board: list[list[int]], depth: int, alpha: float, beta: float, maximizing_player: bool) -> int:
    """
    Minimax algorithm with alpha-beta pruning.
    """
    winner = check_win(board)
    if winner is not None: # Game is over
        if winner == PLAYER:
            return WIN_SCORE - depth # Prefer faster wins
        elif winner == OPPONENT:
            return LOSE_SCORE + depth # Delay losses
        else: # Draw
            return DRAW_SCORE
    
    if depth == MAX_DEPTH: # If depth limit reached, use heuristic evaluation
        return heuristic_eval(board)

    if maximizing_player:
        max_eval = -math.inf
        for r in range(N):
            for c in range(N):
                if board[r][c] == EMPTY:
                    board[r][c] = PLAYER # Make the move
                    eval = minimax(board, depth + 1, alpha, beta, False)
                    board[r][c] = EMPTY # Undo the move
                    max_eval = max(max_eval, eval)
                    alpha = max(alpha, eval)
                    if beta <= alpha: # Alpha-beta pruning
                        return max_eval # Prune the rest of this branch
        return max_eval
    else: # Minimizing player
        min_eval = math.inf
        for r in range(N):
            for c in range(N):
                if board[r][c] == EMPTY:
                    board[r][c] = OPPONENT # Make the move
                    eval = minimax(board, depth + 1, alpha, beta, True)
                    board[r][c] = EMPTY # Undo the move
                    min_eval = min(min_eval, eval)
                    beta = min(beta, eval)
                    if beta <= alpha: # Alpha-beta pruning
                        return min_eval # Prune the rest of this branch
        return min_eval

# --- Policy Function ---

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Determines the best move for the AI player.
    """
    best_move = None
    best_value = -math.inf
    
    empty_cells = []
    for r in range(N):
        for c in range(N):
            if board[r][c] == EMPTY:
                empty_cells.append((r, c))

    if not empty_cells: # Failsafe, should not happen in a valid game state for policy call
        return (0, 0) # Just return any valid cell or raise error

    # 1. Check for an immediate winning move for the current player
    for r, c in empty_cells:
        board[r][c] = PLAYER
        if check_win(board) == PLAYER:
            board[r][c] = EMPTY # Undo move
            return (r, c)
        board[r][c] = EMPTY # Undo move
        
    # 2. If the board is empty (first move of the game), play a central position
    if len(empty_cells) == N * N:
        return (1, 1) # A good common first move for N=4, prefer (N/2 -1, N/2 -1) if N is even

    # 3. Use Minimax with Alpha-Beta pruning to find the optimal move
    
    # Store moves and their evaluations
    move_evaluations = []

    for r, c in empty_cells:
        board[r][c] = PLAYER  # Make the potential move
        # Evaluate the resulting board state from the opponent's perspective (minimizing player)
        score = minimax(board, 0, -math.inf, math.inf, False) 
        board[r][c] = EMPTY   # Undo the move to restore board for next iteration
        
        move_evaluations.append((score, (r, c)))

    # Sort moves by their evaluated score in descending order
    move_evaluations.sort(key=lambda x: x[0], reverse=True)

    best_value = move_evaluations[0][0]
    
    # Filter for moves that achieve the best-evaluated score
    top_moves = [move for score, move in move_evaluations if score == best_value]

    # Among the top-scoring moves, apply a positional preference (central > corner > edge)
    # This helps in breaking ties when multiple moves lead to the same best outcome.
    # For a 4x4 board, (1,1), (1,2), (2,1), (2,2) are central.
    # (0,0), (0,3), (3,0), (3,3) are corners.
    center_preferences = [(1,1), (1,2), (2,1), (2,2), # Center squares
                          (0,0), (0,3), (3,0), (3,3), # Corners
                          (0,1), (0,2), (1,0), (1,3), # Edge squares (remaining)
                          (2,0), (2,3), (3,1), (3,2)]
    
    for preferred_move in center_preferences:
        if preferred_move in top_moves:
            return preferred_move
            
    # If no preferred move is in top_moves (e.g., all top moves are non-preferred edge cells),
    # just return the first one from the sorted top_moves list.
    return top_moves[0]
