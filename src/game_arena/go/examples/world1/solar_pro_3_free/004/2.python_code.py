
import numpy as np
from typing import List, Tuple, Set

# -------------------------------------------------
# Constants
# -------------------------------------------------
NEIGH = [(-1, -1), (-1, 0), (-1, 1),
         ( 0, -1),          ( 0, 1),
         ( 1, -1), ( 1, 0), ( 1, 1)]

# Influence bonuses – higher values for classic strong points
BONUS: dict[Tuple[int, int], int] = {
    # Corners
    (0, 0): 10, (0, 18): 10, (18, 0): 10, (18, 18): 10,
    # Star points
    (8, 8): 8, (9, 8): 8, (8, 9): 8, (9, 9): 8,
    # Edge centers
    (4, 8): 4, (14, 8): 4, (8, 4): 4, (8, 14): 4,
    # Strong second‑line points
    (4, 4): 2, (14, 4): 2, (4, 14): 2, (14, 14): 2
}

# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def board_from_stones(me: Set[Tuple[int, int]], opp: Set[Tuple[int, int]]) -> np.ndarray:
    """Create a 19×19 board where +1 = my stones, -1 = opponent."""
    b = np.zeros((19, 19), dtype=int)
    for r, c in me:
        b[r][c] = 1
    for r, c in opp:
        b[r][c] = -1
    return b

def static_score(me: Set[Tuple[int, int]], opp: Set[Tuple[int, int]]) -> int:
    """Simple territory influence score – sum of neighbor counts for all empty points."""
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = -1
    score = 0
    for r in range(19):
        for c in range(19):
            if board[r][c] == 0:               # empty point
                influence = 0
                for dr, dc in NEIGH:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 19 and 0 <= nc < 19:
                        influence += board[nr][nc]
                score += influence
    return score

def zero_liberty_groups(board: np.ndarray, color: int) -> List[List[Tuple[int, int]]]:
    """Return all groups of `color` that have no liberties."""
    visited = np.full((19, 19), False, dtype=bool)
    groups = []
    for r in range(19):
        for c in range(19):
            if board[r][c] == color and not visited[r][c]:
                stack = [(r, c)]
                visited[r][c] = True
                group = [(r, c)]
                while stack:
                    cur = stack.pop()
                    for dr, dc in NEIGH:
                        nr, nc = cur[0] + dr, cur[1] + dc
                        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == color and not visited[nr][nc]:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                            group.append((nr, nc))
                # Compute liberties for this group
                liberties = set()
                for pos in group:
                    for dr, dc in NEIGH:
                        nr, nc = pos[0] + dr, pos[1] + dc
                        if board[nr][nc] == 0:
                            liberties.add((nr, nc))
                if not liberties:
                    groups.append(group)
    return groups

def is_legal(color: int, move: Tuple[int, int],
             stones: Set[Tuple[int, int]], opponents: Set[Tuple[int, int]]) -> bool:
    """
    Return True if a move by `color` at `move` is legal (no suicide without capture).
    """
    board = board_from_stones(stones, opponents)
    board[move[0]][move[1]] = color
    # Check for self‑atari
    self_zero = zero_liberty_groups(board, color)
    if self_zero:
        # Capture count for the opponent (stones of the opposite color)
        captured = sum(len(g) for g in zero_liberty_groups(board, -color))
        if captured == 0:
            return False
    return True

def find_capture_moves(me: Set[Tuple[int, int]], opp: Set[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """Return empty points that are the only liberty of an opponent group."""
    board = board_from_stones(me, opp)
    visited = np.full((19, 19), False, dtype=bool)
    capture_positions = set()
    for r in range(19):
        for c in range(19):
            if board[r][c] == -1 and not visited[r][c]:
                stack = [(r, c)]
                visited[r][c] = True
                group = [(r, c)]
                while stack:
                    cur = stack.pop()
                    for dr, dc in NEIGH:
                        nr, nc = cur[0] + dr, cur[1] + dc
                        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr][nc] == -1 and not visited[nr][nc]:
                            visited[nr][nc] = True
                            stack.append((nr, nc))
                            group.append((nr, nc))
                liberties = set()
                for pos in group:
                    for dr, dc in NEIGH:
                        nr, nc = pos[0] + dr, pos[1] + dc
                        if board[nr][nc] == 0:
                            liberties.add((nr, nc))
                if len(liberties) == 1:
                    capture_positions.update(liberties)
    return list(capture_positions)

def get_top_candidate_moves(me: Set[Tuple[int, int]],
                           opp: Set[Tuple[int, int]],
                           k: int = 15) -> List[Tuple[int, int]]:
    """
    Return the `k` best legal moves for my side ordered by influence.
    """
    board = board_from_stones(me, opp)
    empty = [(r, c) for r in range(19) for c in range(19) if board[r][c] == 0]
    if not empty:
        return []
    # Compute influence + bonus for every empty point
    influence = {}
    for r, c in empty:
        neigh_sum = sum(board[r + dr][c + dc] for dr, dc in NEIGH
                        if 0 <= r + dr < 19 and 0 <= c + dc < 19)
        influence[(r, c)] = neigh_sum + BONUS.get((r, c), 0)
    # Filter legal moves
    candidates = []
    for (r, c), score in influence.items():
        if is_legal(1, (r, c), me | {(r, c)}, opp):
            candidates.append(((r, c), score))
    candidates.sort(key=lambda x: x[1], reverse=True)   # highest first
    return [move for move, _ in candidates[:k]]

def get_top_opponent_moves(opp: Set[Tuple[int, int]],
                          me: Set[Tuple[int, int]],
                          k: int = 10) -> List[Tuple[int, int]]:
    """
    Return the `k` best legal moves for the opponent ordered by
    decreasing opponent‑influence (i.e. decreasing my influence).
    """
    board = board_from_stones(opp, me)
    empty = [(r, c) for r in range(19) for c in range(19) if board[r][c] == 0]
    opp_score = {}
    for r, c in empty:
        neigh_sum = sum(board[r + dr][c + dc] for dr, dc in NEIGH
                        if 0 <= r + dr < 19 and 0 <= c + dc < 19)
        opp_score[(r, c)] = -neigh_sum          # opponent wants -my neighbor_sum
    candidates = []
    for (r, c), score in opp_score.items():
        if is_legal(-1, (r, c), opp | {(r, c)}, me):
            candidates.append(((r, c), score))
    candidates.sort(key=lambda x: x[1])          # smallest neigh_sum first
    return [move for move, _ in candidates[:k]]

def minimax(me: Set[Tuple[int, int]],
            opp: Set[Tuple[int, int]],
            depth: int,
            alpha: float,
            beta: float,
            is_my_turn: bool,
            k_my: int,
            k_opp: int) -> Tuple[int, Tuple[int, int]]:
    """
    Mini‑max search with α‑β pruning, depth = number of plies left.
    Returns (score from my perspective, move of the player whose turn it is).
    """
    if depth == 0:
        return static_score(me, opp), None

    if is_my_turn:
        moves = get_top_candidate_moves(me, opp, k=k_my)
    else:
        moves = get_top_opponent_moves(opp, me, k=k_opp)

    if not moves:   # pass
        if is_my_turn:
            return minimax(opp, me, depth - 1, alpha, beta, False, k_my, k_opp)
        else:
            return minimax(me, opp, depth - 1, alpha, beta, True, k_my, k_opp)

    if is_my_turn:
        best_val = -float('inf')
        best_move = None
        for mv in moves:
            new_me = me | {mv}
            val, _ = minimax(opp, new_me, depth - 1, alpha, beta, False, k_my, k_opp)
            if val > best_val:
                best_val = val
                best_move = mv
            alpha = max(alpha, best_val)
            if beta <= alpha:
                break
        return best_val, best_move
    else:
        best_val = float('inf')
        best_move = None
        for mv in moves:
            new_opp = opp | {mv}
            val, _ = minimax(new_opp, me, depth - 1, alpha, beta, True, k_my, k_opp)
            if val < best_val:
                best_val = val
                best_move = mv
            beta = min(beta, best_val)
            if beta <= alpha:
                break
        return best_val, best_move

# -------------------------------------------------
# Public API
# -------------------------------------------------
def policy(me: List[Tuple[int, int]],
           opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Return the next legal move as a (row, col) tuple.
    Row and column are 1‑based (1 … 19). Use (0, 0) to pass.
    """
    me_set: Set[Tuple[int, int]] = set(me)
    opp_set: Set[Tuple[int, int]] = set(opponent)

    # 1️⃣ Immediate capture moves
    capture_moves = find_capture_moves(me_set, opp_set)
    if capture_moves:
        best_move = None
        best_score = -float('inf')
        for mv in capture_moves:
            # simulate the capture
            board = board_from_stones(me_set, opp_set)
            board[mv[0]][mv[1]] = 1
            score = static_score(me_set | {mv}, opp_set)
            if score > best_score:
                best_score = score
                best_move = mv
        if best_move is not None:
            return (best_move[0] + 1, best_move[1] + 1)   # convert to 1‑based

    # 2️⃣ Check for pass (board full)
    board = board_from_stones(me_set, opp_set)
    if np.all(board != 0):
        return (0, 0)

    # 3️⃣ Limited look‑ahead (depth‑2) with α‑β
    value, move = minimax(me_set, opp_set,
                         depth=2,
                         alpha=-float('inf'),
                         beta=float('inf'),
                         is_my_turn=True,
                         k_my=15,
                         k_opp=10)
    if move is None:
        return (0, 0)
    return (move[0] + 1, move[1] + 1)   # 1‑based output
