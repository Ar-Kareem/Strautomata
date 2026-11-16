
import numpy as np
import time

# Global constants for readability
PLAYER = 1
OPPONENT = -1
EMPTY = 0
BOARD_SIZE = 4
WIN_LENGTH = 4
TIME_LIMIT = 0.95  # seconds

class GameLogic:
    @staticmethod
    def get_winner(board):
        """Check for a winner. Returns 1, -1, or 0 (no winner yet)."""
        # Check rows and columns
        for i in range(BOARD_SIZE):
            if np.all(board[i, :] == PLAYER) or np.all(board[:, i] == PLAYER):
                return PLAYER
            if np.all(board[i, :] == OPPONENT) or np.all(board[:, i] == OPPONENT):
                return OPPONENT
        
        # Check diagonals
        diag_main = np.diag(board)
        diag_anti = np.diag(np.fliplr(board))
        if np.all(diag_main == PLAYER) or np.all(diag_anti == PLAYER):
            return PLAYER
        if np.all(diag_main == OPPONENT) or np.all(diag_anti == OPPONENT):
            return OPPONENT
        
        return 0

    @staticmethod
    def is_terminal(board):
        """Check if game is over (win or draw)."""
        winner = GameLogic.get_winner(board)
        if winner != 0:
            return True
        return not np.any(board == EMPTY)

    @staticmethod
    def evaluate(board):
        """Heuristic evaluation of the board state."""
        score = 0
        lines = []
        
        # Rows and Columns
        for i in range(BOARD_SIZE):
            lines.append(board[i, :])
            lines.append(board[:, i])
            
        # Diagonals
        lines.append(np.diag(board))
        lines.append(np.diag(np.fliplr(board)))
        
        for line in lines:
            p_count = np.sum(line == PLAYER)
            o_count = np.sum(line == OPPONENT)
            
            if p_count > 0 and o_count == 0:
                # Player has potential in this line
                if p_count == 3: score += 100
                elif p_count == 2: score += 10
                elif p_count == 1: score += 1
            elif o_count > 0 and p_count == 0:
                # Opponent has potential in this line
                if o_count == 3: score -= 100
                elif o_count == 2: score -= 10
                elif o_count == 1: score -= 1
                
        return score

def minimax(board, depth, alpha, beta, maximizing_player, start_time):
    """Minimax algorithm with Alpha-Beta pruning."""
    
    # Time check to avoid disqualification
    if time.time() - start_time > TIME_LIMIT:
        return 0, None, True # Timed out flag

    if GameLogic.is_terminal(board):
        winner = GameLogic.get_winner(board)
        if winner == PLAYER:
            return 10000 + depth, None, False
        elif winner == OPPONENT:
            return -10000 - depth, None, False
        else:
            return 0, None, False # Draw

    if depth == 0:
        return GameLogic.evaluate(board), None, False

    moves = np.argwhere(board == EMPTY)
    # Move ordering heuristic: prioritize center, then corners, then edges
    # Center is (1,1), (1,2), (2,1), (2,2)
    # This helps Alpha-Beta prune earlier
    def move_score(move):
        r, c = move
        score = 0
        if 1 <= r <= 2 and 1 <= c <= 2: score += 3 # Center
        elif (r in [0, 3] and c in [0, 3]): score += 2 # Corners
        return score
    
    moves = sorted(moves, key=move_score, reverse=True)

    best_move = tuple(moves[0]) # Default to first available move

    if maximizing_player:
        max_eval = -float('inf')
        for r, c in moves:
            board[r, c] = PLAYER
            eval_val, _, timed_out = minimax(board, depth - 1, alpha, beta, False, start_time)
            board[r, c] = EMPTY
            
            if timed_out: return 0, None, True
            
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = (r, c)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval, best_move, False
    else:
        min_eval = float('inf')
        for r, c in moves:
            board[r, c] = OPPONENT
            eval_val, _, timed_out = minimax(board, depth - 1, alpha, beta, True, start_time)
            board[r, c] = EMPTY
            
            if timed_out: return 0, None, True
            
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = (r, c)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval, best_move, False

def policy(board: list[list[int]]) -> tuple[int, int]:
    start_time = time.time()
    np_board = np.array(board, dtype=int)
    
    # 1. Check for immediate win
    moves = np.argwhere(np_board == EMPTY)
    for r, c in moves:
        np_board[r, c] = PLAYER
        if GameLogic.get_winner(np_board) == PLAYER:
            return (r, c)
        np_board[r, c] = EMPTY

    # 2. Check for immediate block
    for r, c in moves:
        np_board[r, c] = OPPONENT
        if GameLogic.get_winner(np_board) == OPPONENT:
            return (r, c)
        np_board[r, c] = EMPTY

    # 3. Iterative Deepening Minimax
    best_move = tuple(moves[0]) # Fallback
    
    # Max depth for 4x4 can be up to 16, but time limits us.
    # We iterate upwards until time runs out.
    for depth in range(1, 16):
        _, move, timed_out = minimax(np_board, depth, -float('inf'), float('inf'), True, start_time)
        if timed_out:
            break
        if move:
            best_move = move
        
        # If we found a forced win, no need to search further
        # (logic check in minimax handles terminal scores)
        
    return best_move
