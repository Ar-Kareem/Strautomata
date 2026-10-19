
import numpy as np
import math
from typing import List, Tuple, Optional

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy function. Returns the best move as a string like 'd3' or 'pass'."""
    
    # Game state representation
    board_size = 8
    EMPTY = 0
    PLAYER = 1
    OPPONENT = -1
    
    # Convert input to internal representation
    board = np.zeros((board_size, board_size), dtype=int)
    board[you == 1] = PLAYER
    board[opponent == 1] = OPPONENT
    
    # Check for legal moves
    legal_moves = get_legal_moves(board, PLAYER)
    
    if not legal_moves:
        return "pass"
    
    # Determine game phase (early/mid/end)
    total_discs = np.count_nonzero(board != EMPTY)
    game_phase = "end" if total_discs >= 50 else "mid" if total_discs >= 20 else "early"
    
    # Choose best move
    best_move = None
    
    if game_phase == "end" and total_discs >= 50:
        # Endgame with perfect lookahead (up to 5 plies)
        best_move = iterative_deepening(board, PLAYER, max_depth=min(64 - total_discs, 6))
    else:
        # Early/mid game with adaptive depth
        depth = 4 if total_discs < 45 else 5
        best_move = iterative_deepening(board, PLAYER, max_depth=depth)
    
    if best_move is None:
        # Fallback to first legal move (shouldn't happen)
        best_move = legal_moves[0]
    
    # Convert to algebraic notation
    return f"{chr(ord('a') + best_move[1])}{best_move[0] + 1}"


def get_legal_moves(board: np.ndarray, player: int) -> List[Tuple[int, int]]:
    """Return list of (row, col) legal moves for the given player."""
    size = board.shape[0]
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]
    
    for r in range(size):
        for c in range(size):
            if board[r, c] != 0:
                continue
                
            for dr, dc in directions:
                if is_valid_move(board, r, c, dr, dc, player):
                    moves.append((r, c))
                    break
    
    return moves


def is_valid_move(board: np.ndarray, r: int, c: int, dr: int, dc: int, player: int) -> bool:
    """Check if placing at (r, c) captures in direction (dr, dc)."""
    size = board.shape[0]
    opponent = -player
    nr, nc = r + dr, c + dc
    
    # Must start adjacent to opponent disc
    if nr < 0 or nr >= size or nc < 0 or nc >= size or board[nr, nc] != opponent:
        return False
    
    # Keep moving in direction
    while True:
        nr += dr
        nc += dc
        if nr < 0 or nr >= size or nc < 0 or nc >= size:
            return False
        if board[nr, nc] == 0:
            return False
        if board[nr, nc] == player:
            return True


def make_move(board: np.ndarray, r: int, c: int, player: int) -> np.ndarray:
    """Return new board after making move at (r, c)."""
    new_board = board.copy()
    size = board.shape[0]
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),          (0, 1),
                  (1, -1),  (1, 0), (1, 1)]
    
    new_board[r, c] = player
    opponent = -player
    
    for dr, dc in directions:
        if is_valid_move(board, r, c, dr, dc, player):
            nr, nc = r + dr, c + dc
            while board[nr, nc] == opponent:
                new_board[nr, nc] = player
                nr += dr
                nc += dc
    
    return new_board


def evaluate_board(board: np.ndarray, player: int) -> float:
    """Evaluate board position for the given player."""
    size = board.shape[0]
    total_discs = np.count_nonzero(board)
    opponent = -player
    
    # Corner values (extremely important)
    corners = [(0, 0), (0, size-1), (size-1, 0), (size-1, size-1)]
    corner_weight = 50
    my_corners = sum(1 for r, c in corners if board[r, c] == player)
    opp_corners = sum(1 for r, c in corners if board[r, c] == opponent)
    
    # C-squares (dangerous squares adjacent to corners)
    c_squares = [(0, 1), (1, 0), (0, size-2), (1, size-1),
                 (size-2, 0), (size-1, 1), (size-2, size-1), (size-1, size-2)]
    c_square_weight = -25
    my_c_squares = sum(1 for r, c in c_squares if board[r, c] == player)
    opp_c_squares = sum(1 for r, c in c_squares if board[r, c] == opponent)
    
    # X-squares (very dangerous squares diagonal to corners)
    x_squares = [(1, 1), (1, size-2), (size-2, 1), (size-2, size-2)]
    x_square_weight = -30
    my_x_squares = sum(1 for r, c in x_squares if board[r, c] == player)
    opp_x_squares = sum(1 for r, c in x_squares if board[r, c] == opponent)
    
    # Edge values (excluding corners)
    edge_weight = 5
    my_edges, opp_edges = 0, 0
    for i in range(1, size-1):
        if board[0, i] == player: my_edges += 1
        if board[0, i] == opponent: opp_edges += 1
        if board[size-1, i] == player: my_edges += 1
        if board[size-1, i] == opponent: opp_edges += 1
        if board[i, 0] == player: my_edges += 1
        if board[i, 0] == opponent: opp_edges += 1
        if board[i, size-1] == player: my_edges += 1
        if board[i, size-1] == opponent: opp_edges += 1
    
    # Mobility (number of legal moves)
    my_mobility = len(get_legal_moves(board, player))
    opp_mobility = len(get_legal_moves(board, opponent))
    mobility_weight = 2.5
    
    # Disc count (more important in endgame)
    my_discs = np.sum(board == player)
    opp_discs = np.sum(board == opponent)
    
    # Adaptive weights based on game phase
    if total_discs < 20:  # Early game
        disc_weight = 0.2
    elif total_discs < 50:  # Mid game
        disc_weight = 0.5
    else:  # End game
        disc_weight = 1.5
    
    # Calculate score
    score = 0
    score += corner_weight * (my_corners - opp_corners)
    score += c_square_weight * (my_c_squares - opp_c_squares)
    score += x_square_weight * (my_x_squares - opp_x_squares)
    score += edge_weight * (my_edges - opp_edges)
    score += mobility_weight * (my_mobility - opp_mobility)
    score += disc_weight * (my_discs - opp_discs)
    
    # Parity bonus (want to play last in endgame)
    if total_discs > 50:
        empty = size * size - total_discs
        if empty % 2 == 0:
            score += 10  # Want to move when even number of empties left
        else:
            score -= 10
    
    return score


def alpha_beta(board: np.ndarray, depth: int, alpha: float, beta: float, 
               player: int, maximizing: bool) -> float:
    """Alpha-beta pruning search."""
    if depth == 0:
        return evaluate_board(board, player if maximizing else -player)
    
    current_player = player if maximizing else -player
    legal_moves = get_legal_moves(board, current_player)
    
    if not legal_moves:
        # If no moves, check if opponent also has no moves (game over)
        opponent_moves = get_legal_moves(board, -current_player)
        if not opponent_moves:
            # Game over, evaluate final score
            my_discs = np.sum(board == player)
            opp_discs = np.sum(board == -player)
            if my_discs > opp_discs:
                return 10000
            elif my_discs < opp_discs:
                return -10000
            else:
                return 0
        # Pass turn to opponent
        next_board = board.copy()
        return alpha_beta(next_board, depth - 1, alpha, beta, player, not maximizing)
    
    # Move ordering: sort by potential gain
    def move_value(move):
        r, c = move
        new_board = make_move(board, r, c, current_player)
        return evaluate_board(new_board, current_player)
    
    legal_moves.sort(key=move_value, reverse=maximizing)
    
    if maximizing:
        value = -float('inf')
        for r, c in legal_moves:
            new_board = make_move(board, r, c, current_player)
            value = max(value, alpha_beta(new_board, depth - 1, alpha, beta, player, False))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = float('inf')
        for r, c in legal_moves:
            new_board = make_move(board, r, c, current_player)
            value = min(value, alpha_beta(new_board, depth - 1, alpha, beta, player, True))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value


def iterative_deepening(board: np.ndarray, player: int, max_depth: int = 5) -> Optional[Tuple[int, int]]:
    """Perform iterative deepening search with time management."""
    legal_moves = get_legal_moves(board, player)
    if not legal_moves:
        return None
    
    # Early game: quick search with good move ordering
    total_discs = np.count_nonzero(board)
    if total_discs < 10:
        max_depth = min(max_depth, 4)
    
    # Move ordering for root moves
    def root_move_value(move):
        r, c = move
        new_board = make_move(board, r, c, player)
        return evaluate_board(new_board, player)
    
    legal_moves.sort(key=root_move_value, reverse=True)
    
    best_move = legal_moves[0]
    best_value = -float('inf')
    
    # Search with increasing depth
    for depth in range(1, max_depth + 1):
        current_best = None
        current_value = -float('inf')
        
        for r, c in legal_moves:
            new_board = make_move(board, r, c, player)
            value = alpha_beta(new_board, depth - 1, -float('inf'), float('inf'), player, False)
            
            if value > current_value:
                current_value = value
                current_best = (r, c)
        
        if current_best is not None:
            best_move = current_best
            best_value = current_value
    
    return best_move
