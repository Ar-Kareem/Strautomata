
import random
from collections import deque
from typing import List, Tuple, Dict

# board constants
EMPTY = 0
ME = 1
OPP = 2
SIZE = 19
DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]  # up, down, left, right


def _in_bounds(r: int, c: int) -> bool:
    return 1 <= r <= SIZE and 1 <= c <= SIZE


def _board_from_lists(me: List[Tuple[int, int]],
                      opponent: List[Tuple[int, int]]) -> List[List[int]]:
    """Create a 19x19 board (1‑indexed) from stone lists."""
    board = [[EMPTY] * (SIZE + 1) for _ in range(SIZE + 1)]
    for r, c in me:
        board[r][c] = ME
    for r, c in opponent:
        board[r][c] = OPP
    return board


def _group_liberties(r: int, c: int,
                    board: List[List[int]],
                    player: int) -> Tuple[set, int]:
    """Return (set of stones in the group, number of liberties)."""
    visited = set()
    liberties = set()
    q = deque()
    q.append((r, c))
    visited.add((r, c))

    while q:
        cr, cc = q.popleft()
        for dr, dc in DIRS:
            nr, nc = cr + dr, cc + dc
            if not _in_bounds(nr, nc):
                continue
            cell = board[nr][nc]
            if cell == EMPTY:
                liberties.add((nr, nc))
            elif cell == player and (nr, nc) not in visited:
                visited.add((nr, nc))
                q.append((nr, nc))
    return visited, len(liberties)


def _capture_groups(board: List[List[int]],
                    opponent_player: int,
                    placed_r: int,
                    placed_c: int) -> List[Tuple[int, int]]:
    """Return list of opponent stones that would be captured after a move."""
    captured = []
    for dr, dc in DIRS:
        nr, nc = placed_r + dr, placed_c + dc
        if not _in_bounds(nr, nc):
            continue
        if board[nr][nc] != opponent_player:
            continue
        group, libs = _group_liberties(nr, nc, board, opponent_player)
        if libs == 0:
            captured.extend(group)
    return captured


def _is_suicide(board: List[List[int]],
                move_r: int,
                move_c: int) -> bool:
    """Check if placing ME at (move_r,move_c) would be suicide."""
    # simulate placement
    board[move_r][move_c] = ME

    # capture any opponent groups first
    captured = _capture_groups(board, OPP, move_r, move_c)
    for cr, cc in captured:
        board[cr][cc] = EMPTY

    # now test own group liberties
    group, libs = _group_liberties(move_r, move_c, board, ME)

    # revert board to original state
    board[move_r][move_c] = EMPTY
    for cr, cc in captured:
        board[cr][cc] = OPP

    # suicide if no liberties and no capture happened
    return libs == 0


def _legal_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    moves = []
    for r in range(1, SIZE + 1):
        for c in range(1, SIZE + 1):
            if board[r][c] != EMPTY:
                continue
            if not _is_suicide(board, r, c):
                moves.append((r, c))
    return moves


def _captures_if_move(board: List[List[int]],
                     r: int,
                     c: int) -> int:
    """Return number of opponent stones captured by playing at (r,c)."""
    # simulate placement
    board[r][c] = ME
    captured = _capture_groups(board, OPP, r, c)
    # revert
    board[r][c] = EMPTY
    return len(captured)


def policy(me: List[Tuple[int, int]],
           opponent: List[Tuple[int, int]],
           memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    """
    Return a legal move for the current player.

    Strategy:
    1. Find all legal moves.
    2. If any move captures opponent stones, choose the move with the most captures.
    3. Otherwise choose the legal move that is closest (Manhattan) to any opponent stone.
    4. If no legal move exists, pass.
    """
    board = _board_from_lists(me, opponent)

    legal = _legal_moves(board)
    if not legal:
        return (0, 0), memory  # pass

    # Step 1 – capture analysis
    best_capture = -1
    capture_moves = []
    for r, c in legal:
        cap = _captures_if_move(board, r, c)
        if cap > best_capture:
            best_capture = cap
            capture_moves = [(r, c)]
        elif cap == best_capture:
            capture_moves.append((r, c))

    if best_capture > 0:
        # there is at least one capturing move
        chosen = random.choice(capture_moves)
        return (chosen, memory)

    # Step 2 – aggressive positioning (closest to opponent stones)
    if opponent:
        opp_set = set(opponent)
        def min_distance_to_opp(move):
            mr, mc = move
            return min(abs(mr - or_) + abs(mc - oc) for or_, oc in opp_set)

        min_dist = min(min_distance_to_opp(m) for m in legal)
        candidates = [m for m in legal if min_distance_to_opp(m) == min_dist]
        chosen = random.choice(candidates)
        return (chosen, memory)

    # No opponent stones on board (very early game) – play near the centre
    centre = (10, 10)
    def dist_to_centre(move):
        return abs(move[0] - centre[0]) + abs(move[1] - centre[1])

    min_dist = min(dist_to_centre(m) for m in legal)
    candidates = [m for m in legal if dist_to_centre(m) == min_dist]
    chosen = random.choice(candidates)
    return (chosen, memory)
