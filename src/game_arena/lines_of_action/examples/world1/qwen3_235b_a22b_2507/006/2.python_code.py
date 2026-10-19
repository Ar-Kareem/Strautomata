
import numpy as np
from typing import List, Tuple, Optional
import time

# Direction vectors for 8 directions: N, NE, E, SE, S, SW, W, NW
DIRS = [(-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1)]

def get_legal_moves(board: np.ndarray, player: int) -> List[Tuple[int, int, int, int]]:
    """Generate all legal moves for the current player."""
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r, c] != player:
                continue
            for dr, dc in DIRS:
                count = count_pieces_in_direction(board, r, c, dr, dc)
                if count == 0:
                    continue
                nr, nc = r + dr * count, c + dc * count
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue
                if not is_clear_path(board, r, c, dr, dc, count, player):
                    continue
                if board[nr, nc] == player:
                    continue
                moves.append((r, c, nr, nc))
    return moves

def count_pieces_in_direction(board: np.ndarray, r: int, c: int, dr: int, dc: int) -> int:
    """Count total pieces along a direction from (r,c) until edge."""
    count = 0
    cr, cc = r + dr, c + dc
    while 0 <= cr < 8 and 0 <= cc < 8:
        if board[cr, cc] != 0:
            count += 1
        cr, cc = cr + dr, cc + dc
    cr, cc = r - dr, c - dc
    while 0 <= cr < 8 and 0 <= cc < 8:
        if board[cr, cc] != 0:
            count += 1
        cr, cc = cr - dr, cc - dc
    return count

def is_clear_path(board: np.ndarray, r: int, c: int, dr: int, dc: int, steps: int, player: int) -> bool:
    """Check if the path is clear for moving `steps` steps in direction (dr,dc)."""
    for i in range(1, steps):
        nr, nc = r + dr * i, c + dc * i
        if 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr, nc] == -player:  # opponent piece blocks
                return False
    return True

def get_connected_groups(board: np.ndarray, player: int):
    """Return list of connected groups (as sets of coordinates) for player."""
    visited = np.zeros((8,8), dtype=bool)
    groups = []
    for i in range(8):
        for j in range(8):
            if board[i,j] == player and not visited[i,j]:
                group = set()
                stack = [(i,j)]
                while stack:
                    r, c = stack.pop()
                    if visited[r,c]:
                        continue
                    visited[r,c] = True
                    group.add((r,c))
                    for dr, dc in DIRS:
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr,nc] == player and not visited[nr,nc]:
                            stack.append((nr,nc))
                groups.append(group)
    return groups

def evaluate(board: np.ndarray, player: int) -> float:
    """Heuristic evaluation of board for player."""
    # Maximize size of largest group
    groups = get_connected_groups(board, player)
    if not groups:
        return -1000
    max_own_group = max(len(g) for g in groups)
    
    # Penalize opponent's connectivity
    opp_groups = get_connected_groups(board, -player)
    max_opp_group = max(len(g) for g in opp_groups) if opp_groups else 0

    # Reward mobility
    own_moves = len(get_legal_moves(board, player))
    opp_moves = len(get_legal_moves(board, -player))
    
    # Normalize and combine
    connectivity_score = max_own_group * 10
    mobility_score = (own_moves - opp_moves) * 0.5
    opp_penalty = -max_opp_group * 5
    
    total = connectivity_score + mobility_score + opp_penalty
    return total

def make_move(board: np.ndarray, move: Tuple[int,int,int,int]) -> np.ndarray:
    """Apply move and return new board."""
    r1, c1, r2, c2 = move
    new_board = board.copy()
    player = board[r1, c1]
    new_board[r2, c2] = player
    new_board[r1, c1] = 0
    return new_board

def minimax(board: np.ndarray, depth: int, alpha: float, beta: float, maximizing: bool, player: int, start_time: float, time_limit: float = 0.95) -> Tuple[float, Optional[Tuple[int,int,int,int]]]:
    """Minimax with alpha-beta pruning."""
    if time.time() - start_time > time_limit:
        return evaluate(board, player), None

    if depth == 0:
        return evaluate(board, player), None

    moves = get_legal_moves(board, player if maximizing else -player)
    if not moves:
        # No moves: evaluate current position
        score = evaluate(board, player) if maximizing else evaluate(board, -player)
        return score, None

    best_move = moves[0]
    if maximizing:
        max_eval = float('-inf')
        for move in moves:
            new_board = make_move(board, move)
            score, _ = minimax(new_board, depth - 1, alpha, beta, False, player, start_time, time_limit)
            if score > max_eval:
                max_eval = score
                best_move = move
            alpha = max(alpha, score)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = make_move(board, move)
            score, _ = minimax(new_board, depth - 1, alpha, beta, True, player, start_time, time_limit)
            if score < min_eval:
                min_eval = score
                best_move = move
            beta = min(beta, score)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board) -> str:
    """
    Main policy function. Returns a legal move string.
    Uses minimax with iterative deepening within time limit.
    """
    board = np.array(board)
    start_time = time.time()
    player = 1  # We are always the current player (1)

    # Get all legal moves
    legal_moves = get_legal_moves(board, player)
    if not legal_moves:
        # Fallback: should not happen, but return a dummy move
        for r in range(8):
            for c in range(8):
                if board[r,c] == player:
                    return f"{r},{c}:{r},{c}"

    # Check if any move wins immediately
    for move in legal_moves:
        new_board = make_move(board, move)
        groups = get_connected_groups(new_board, player)
        if len(groups) == 1 and sum(len(g) for g in groups) == np.sum(board == player):
            return f"{move[0]},{move[1]}:{move[2]},{move[3]}"

    # Use iterative deepening
    best_move = legal_moves[0]
    for depth in range(1, 4):  # Try depth 1, 2, 3
        if time.time() - start_time > 0.9:
            break
        try:
            _, move = minimax(board, depth, float('-inf'), float('inf'), True, player, start_time)
            if move is not None:
                best_move = move
        except:
            break

    # Ensure best_move is legal
    if best_move not in legal_moves:
        best_move = legal_moves[0]

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
