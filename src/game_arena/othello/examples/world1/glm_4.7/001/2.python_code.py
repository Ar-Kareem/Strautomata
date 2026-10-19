
import numpy as np

# Precomputed weights for positional strategy.
# Corners are very high value. X-squares (e.g., b2, g7) are negative to avoid giving away corners.
WEIGHTS = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [  5,  -2, -1, -1, -1, -1,  -2,   5],
    [ 10,  -2, -1, -1, -1, -1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
], dtype=np.int32)

DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1)
]

def get_legal_moves(board: np.ndarray, player: int) -> list:
    """Returns a list of (r, c) tuples for legal moves."""
    moves = []
    # Find all empty squares
    empties = np.argwhere(board == 0)
    
    for r, c in empties:
        legal = False
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == -player:
                # Found opponent piece, look for own piece further out
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr, nc] == player:
                        legal = True
                        break
                    elif board[nr, nc] == 0:
                        break
                    nr += dr
                    nc += dc
            if legal:
                break
        if legal:
            moves.append((r, c))
    return moves

def apply_move(board: np.ndarray, r: int, c: int, player: int) -> np.ndarray:
    """Applies a move and returns the new board state."""
    new_board = board.copy()
    new_board[r, c] = player
    
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        to_flip = []
        while 0 <= nr < 8 and 0 <= nc < 8:
            if new_board[nr, nc] == -player:
                to_flip.append((nr, nc))
            elif new_board[nr, nc] == player:
                if to_flip:
                    for fr, fc in to_flip:
                        new_board[fr, fc] = player
                break
            else:
                # Empty cell
                break
            nr += dr
            nc += dc
    return new_board

def evaluate(board: np.ndarray) -> float:
    """Heuristic evaluation of the board state from the perspective of player 1."""
    # 1. Positional score using weighted matrix
    pos_score = np.sum(board * WEIGHTS)
    
    # 2. Mobility (simple move count difference)
    # We estimate mobility for current state. 
    # In a full search, we would calculate this for the specific player to move,
    # but here we calculate relative material/positional advantage.
    # To save time, we skip dynamic mobility calculation in leaves and rely on weights,
    # which implicitly capture mobility (corners open up moves).
    
    return pos_score

def alphabeta(board: np.ndarray, depth: int, alpha: float, beta: float, player: int) -> float:
    """Minimax with Alpha-Beta pruning."""
    if depth == 0:
        # Return score relative to player 1 (the original caller)
        # Since 'player' alternates, we multiply by 'player' to align scores
        return evaluate(board) * player

    legal_moves = get_legal_moves(board, player)
    
    # If no moves for current player
    if not legal_moves:
        # Check if opponent has moves
        if not get_legal_moves(board, -player):
            # Game over: Return massive score or count discs
            # Simple disc count
            if np.sum(board) > 0: return 10000 * player
            if np.sum(board) < 0: return -10000 * player
            return 0
        # Pass turn
        return alphabeta(board, depth, alpha, beta, -player)

    if player == 1: # Maximizing
        max_eval = -np.inf
        for r, c in legal_moves:
            new_board = apply_move(board, r, c, player)
            eval = alphabeta(new_board, depth - 1, alpha, beta, -player)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else: # Minimizing
        min_eval = np.inf
        for r, c in legal_moves:
            new_board = apply_move(board, r, c, player)
            eval = alphabeta(new_board, depth - 1, alpha, beta, -player)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """
    Main policy function.
    you: 8x8 array, 1 for your discs, 0 otherwise.
    opponent: 8x8 array, 1 for opponent discs, 0 otherwise.
    """
    # Convert to unified board representation: 1 (you), -1 (opponent), 0 (empty)
    board = you.astype(np.int8) - opponent.astype(np.int8)
    
    legal_moves = get_legal_moves(board, 1)
    
    if not legal_moves:
        return "pass"
    
    # If only one move, take it immediately (save time)
    if len(legal_moves) == 1:
        r, c = legal_moves[0]
        return f"{chr(c + ord('a'))}{r + 1}"

    best_score = -np.inf
    best_move = legal_moves[0]
    
    # Depth 3 search. 1 is the maximizing player in the internal representation.
    # We are player 1.
    
    # Simple ordering: check corners first for better alpha-beta pruning
    def move_priority(move):
        r, c = move
        if (r in [0, 7] and c in [0, 7]): return 2 # Corners
        if (r in [0, 7] or c in [0, 7]): return 1 # Edges
        return 0
        
    legal_moves.sort(key=move_priority, reverse=True)

    for r, c in legal_moves:
        new_board = apply_move(board, r, c, 1)
        score = alphabeta(new_board, 3, -np.inf, np.inf, -1)
        
        if score > best_score:
            best_score = score
            best_move = (r, c)
            
    r, c = best_move
    return f"{chr(c + ord('a'))}{r + 1}"
