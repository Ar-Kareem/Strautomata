
import random
from typing import List, Tuple, Set, Dict, Any

BOARD_SIZE = 19

# Global set of all board positions that have occurred so far (super‑ko detection).
_seen_boards: Set[Tuple[Tuple[int, ...], ...]] = None


def board_to_tuple(board: List[List[int]]) -> Tuple[Tuple[int, ...], ...]:
    """Convert a 2‑D list board into a hash‑able tuple representation."""
    return tuple(tuple(row) for row in board)


def get_groups(board: List[List[int]], colour: int) -> List[Dict[str, Set[Tuple[int, int]]]]:
    """
    Return all connected groups of ``colour`` (1 for us, -1 for opponent).
    Each group is a dict with keys:
        'stones'  : set of (r,c) coordinates belonging to the group,
        'liberties': set of empty (r,c) adjacent to the group.
    """
    visited: Set[Tuple[int, int]] = set()
    groups: List[Dict[str, Set[Tuple[int, int]]]] = []

    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] == colour and (r, c) not in visited:
                # BFS for this group
                queue: List[Tuple[int, int]] = [(r, c)]
                stones: Set[Tuple[int, int]] = set()
                liberties: Set[Tuple[int, int]] = set()

                while queue:
                    cr, cc = queue.pop()
                    if (cr, cc) in stones:
                        continue
                    stones.add((cr, cc))
                    visited.add((cr, cc))
                    for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
                            val = board[nr][nc]
                            if val == 0:
                                liberties.add((nr, nc))
                            elif val == colour and (nr, nc) not in visited:
                                queue.append((nr, nc))
                groups.append({'stones': stones, 'liberties': liberties})
    return groups


def simulate_move(
    board: List[List[int]],
    move: Tuple[int, int],
    colour: int
) -> Tuple[List[List[int]], int, bool]:
    """
    Place a stone of ``colour`` at ``move`` on a copy of ``board``.

    Returns:
        new_board      – board after the move and after any captures,
        captured_stones – number of opponent stones removed,
        legal          – True iff the move is legal (no suicide).
    """
    r, c = move
    if board[r][c] != 0:
        # spot already occupied
        return (board, 0, False)

    new_board = [row[:] for row in board]
    new_board[r][c] = colour

    opp_colour = -colour
    opp_groups = get_groups(new_board, opp_colour)

    # Capture opponent groups that have no liberties
    captured_stones = 0
    groups_to_remove: List[Dict[str, Set[Tuple[int, int]]]] = []
    for grp in opp_groups:
        if not grp['liberties']:
            groups_to_remove.append(grp)
            captured_stones += len(grp['stones'])

    for grp in groups_to_remove:
        for sr, sc in grp['stones']:
            new_board[sr][sc] = 0

    # Check for suicide: any of our groups with zero liberties?
    my_groups = get_groups(new_board, colour)
    for grp in my_groups:
        if not grp['liberties']:
            return (board, captured_stones, False)   # illegal – suicide

    return (new_board, captured_stones, True)


def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Return a single move for the current player (``me``) on a 19×19 Go board.
    The move is a (row, col) tuple with 1‑based indices; (0,0) means pass.
    """
    global _seen_boards

    # ------------------------------------------------------------------ #
    # 0) Build the internal board representation (0‑based indices).      #
    # ------------------------------------------------------------------ #
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for r, c in me:
        board[r - 1][c - 1] = 1               # our stones
    for r, c in opponent:
        board[r - 1][c - 1] = -1              # opponent stones

    # ------------------------------------------------------------------ #
    # 1) Initialise / reset the super‑ko history when a new game starts. #
    # ------------------------------------------------------------------ #
    if _seen_boards is None:
        _seen_boards = set()
    # An empty board signals the start of a new game – clear history.
    if not me and not opponent:
        _seen_boards = set()

    cur_board_tuple = board_to_tuple(board)
    _seen_boards.add(cur_board_tuple)     # remember the position after opponent's move

    # ------------------------------------------------------------------ #
    # 2) Enumerate all legal moves (no suicide, no super‑ko).            #
    # ------------------------------------------------------------------ #
    legal_moves: List[Tuple[Tuple[int, int], int, Tuple[Tuple[int, ...], ...]]] = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r][c] != 0:
                continue
            move = (r, c)
            new_board, captured, legal = simulate_move(board, move, colour=1)
            if not legal:
                continue
            new_board_tuple = board_to_tuple(new_board)
            if new_board_tuple in _seen_boards:
                # super‑ko – would repeat a previous position
                continue
            legal_moves.append((move, captured, new_board_tuple))

    # No legal move → pass
    if not legal_moves:
        return (0, 0)

    # ------------------------------------------------------------------ #
    # 3) Prioritise captures (most stones captured).                     #
    # ------------------------------------------------------------------ #
    capture_moves = [(m, c, b) for (m, c, b) in legal_moves if c > 0]
    if capture_moves:
        # pick the move that captures the largest group
        max_captured = max(capture_moves, key=lambda x: x[1])[1]
        best_capture_moves = [m for m, c, b in capture_moves if c == max_captured]
        chosen_move = random.choice(best_capture_moves)
        # store the new position for future ko detection
        for m, c, b in capture_moves:
            if m == chosen_move:
                _seen_boards.add(b)
                break
        return (chosen_move[0] + 1, chosen_move[1] + 1)

    # ------------------------------------------------------------------ #
    # 4) Defend our own groups that are in Atari (single liberty).       #
    # ------------------------------------------------------------------ #
    our_groups = get_groups(board, colour=1)
    legal_move_set = {m for m, _, _ in legal_moves}
    defence_moves = []
    for grp in our_groups:
        if len(grp['liberties']) == 1:
            sole_liberty = next(iter(grp['liberties']))
            if sole_liberty in legal_move_set:
                defence_moves.append(sole_liberty)
    if defence_moves:
        chosen_move = random.choice(defence_moves)
        new_board, _, _ = simulate_move(board, chosen_move, colour=1)
        _seen_boards.add(board_to_tuple(new_board))
        return (chosen_move[0] + 1, chosen_move[1] + 1)

    # ------------------------------------------------------------------ #
    # 5) Play somewhere adjacent to one of our stones (expansion).       #
    # ------------------------------------------------------------------ #
    our_stones = [(r - 1, c - 1) for r, c in me]
    adjacent_to_us: Set[Tuple[int, int]] = set()
    for sr, sc in our_stones:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nr, nc = sr + dr, sc + dc
            if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE and board[nr][nc] == 0:
                adjacent_to_us.add((nr, nc))
    adjacent_legal = [m for m, _, _ in legal_moves if m in adjacent_to_us]
    if adjacent_legal:
        chosen_move = random.choice(adjacent_legal)
        new_board, _, _ = simulate_move(board, chosen_move, colour=1)
        _seen_boards.add(board_to_tuple(new_board))
        return (chosen_move[0] + 1, chosen_move[1] + 1)

    # ------------------------------------------------------------------ #
    # 6) Fallback – completely random legal move.                        #
    # ------------------------------------------------------------------ #
    chosen_move, _, new_board_tuple = random.choice(legal_moves)
    _seen_boards.add(new_board_tuple)
    return (chosen_move[0] + 1, chosen_move[1] + 1)
