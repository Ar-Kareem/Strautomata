
import random
import copy
from typing import List, Tuple, Dict, Set

# --------------------------------------------------------------
# Helper conversion functions (row‑major order)
# --------------------------------------------------------------
def idx_to_rc(idx: int) -> Tuple[int, int]:
    """Convert 0‑8 board index to (row, col)."""
    return divmod(idx, 3)  # Python's divmod returns (quotient, remainder)

def rc_to_idx(row: int, col: int) -> int:
    """Convert (row, col) to 0‑8 board index."""
    return row * 3 + col

# --------------------------------------------------------------
# Winning lines (row, column, diagonal triples)
# --------------------------------------------------------------
WIN_LINES: List[Tuple[int, int, int]] = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),  # rows
    (0, 3, 6), (1, 4, 7), (2, 5, 8),  # columns
    (0, 4, 8), (2, 4, 6)               # diagonals
]

# --------------------------------------------------------------
# Persistent state across calls for a single game
# --------------------------------------------------------------
_STATE: Dict[str, any] = {
    "prev_board": None,       # board snapshot before the last attempted move
    "last_move": None,        # index of the cell we attempted last turn
    "opp_marks": set(),       # indices known to be occupied by opponent
    "my_marks": set()         # set of our confirmed marks (derived from board)
}

# --------------------------------------------------------------
# Main policy function required by the arena
# --------------------------------------------------------------
def policy(board: List[List[int]], legal_moves: List[int]) -> Tuple[int, int]:
    """
    Choose a cell to attempt to mark for Phantom Tic‑Tac‑Toe.
    
    Parameters
    ----------
    board : list[list[int]]
        3×3 matrix where 1 indicates a confirmed mark of ours, 0 indicates
        a cell that is not confirmed as ours (may be empty or occupied by the
        opponent).
    legal_moves : list[int]
        List of cell indices (0‑8) that are currently allowed for a placement
        attempt.
    
    Returns
    -------
    tuple[int, int]
        (row, col) of the chosen cell.
    """
    # ------------------------------------------------------------------
    # 1. Extract our confirmed marks from the board
    # ------------------------------------------------------------------
    my_marks: Set[int] = {
        rc_to_idx(r, c) for r in range(3) for c in range(3) if board[r][c] == 1
    }
    _STATE["my_marks"] = my_marks

    # ------------------------------------------------------------------
    # 2. Update opponent‑known cells based on the outcome of the previous
    #    attempted move.
    # ------------------------------------------------------------------
    if _STATE["last_move"] is not None:
        last_idx = _STATE["last_move"]
        # If the cell we tried is still not a confirmed mark, it must have been
        # occupied by the opponent.
        if last_idx not in my_marks and last_idx not in _STATE["opp_marks"]:
            _STATE["opp_marks"].add(last_idx)

    # ------------------------------------------------------------------
    # 3. Determine the set of truly unknown cells (not ours, not opponent‑known)
    # ------------------------------------------------------------------
    unknown_cells: Set[int] = set(range(9)) - my_marks - _STATE["opp_marks"]
    possible_moves: List[int] = [idx for idx in legal_moves if idx in unknown_cells]

    # ------------------------------------------------------------------
    # 4. Helper: return a move if a winning/defensive move exists in a line
    # ------------------------------------------------------------------
    def find_line_with_two_marks(own: Set[int], opp: Set[int]) -> None:
        """Search for a line with two own marks and one unknown cell."""
        for a, b, c in WIN_LINES:
            line = (a, b, c)
            own_cnt = sum(1 for i in line if i in own)
            opp_cnt = sum(1 for i in line if i in opp)
            if own_cnt == 2 and opp_cnt == 0:
                # The missing cell is the winning move
                for i in line:
                    if i not in own:
                        return i
        return None

    # ------------------------------------------------------------------
    # 5. Immediate winning move (our two marks in a line)
    # ------------------------------------------------------------------
    win_move = find_line_with_two_marks(my_marks, _STATE["opp_marks"])
    if win_move is not None:
        row, col = idx_to_rc(win_move)
        _STATE["prev_board"] = copy.deepcopy(board)
        _STATE["last_move"] = win_move
        return (row, col)

    # ------------------------------------------------------------------
    # 6. Immediate blocking move (opponent has two known marks in a line)
    # ------------------------------------------------------------------
    block_move = find_line_with_two_marks(_STATE["opp_marks"], my_marks)
    if block_move is not None:
        row, col = idx_to_rc(block_move)
        _STATE["prev_board"] = copy.deepcopy(board)
        _STATE["last_move"] = block_move
        return (row, col)

    # ------------------------------------------------------------------
    # 7. Fork detection – create a move that opens two winning possibilities
    # ------------------------------------------------------------------
    best_fork_idx = None
    best_fork_score = -1
    for move in possible_moves:
        # Simulate placing our mark at `move`
        new_my_marks = my_marks | {move}
        # Count lines that would have two of our marks after the placement
        score = 0
        for a, b, c in WIN_LINES:
            line = (a, b, c)
            own_cnt = sum(1 for i in line if i in new_my_marks)
            opp_cnt = sum(1 for i in line if i in _STATE["opp_marks"])
            if own_cnt == 2 and opp_cnt == 0:
                score += 1
        if score > best_fork_score:
            best_fork_score = score
            best_fork_idx = move

    if best_fork_score >= 2:  # At least two almost‑winning lines → strong fork
        row, col = idx_to_rc(best_fork_idx)
        _STATE["prev_board"] = copy.deepcopy(board)
        _STATE["last_move"] = best_fork_idx
        return (row, col)

    # ------------------------------------------------------------------
    # 8. Extension heuristic – prefer cells that belong to many lines already
    #    containing one of our marks.
    # ------------------------------------------------------------------
    best_moves: List[int] = []
    best_score = -1
    for move in possible_moves:
        score = 0
        for a, b, c in WIN_LINES:
            if move in (a, b, c) and any(i in my_marks for i in (a, b, c)):
                score += 1
        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    # Preference order: centre, then corners, then edges (classic priority)
    priority = [4, 0, 2, 6, 8, 1, 3, 5, 7]
    for cand in priority:
        if cand in best_moves:
            row, col = idx_to_rc(cand)
            _STATE["prev_board"] = copy.deepcopy(board)
            _STATE["last_move"] = cand
            return (row, col)

    # ------------------------------------------------------------------
    # 9. Fallback – random legal move (should rarely be needed)
    # ------------------------------------------------------------------
    if not possible_moves:
        # All cells are known opponent marks – still must return a legal move
        chosen = random.choice(legal_moves)
    else:
        chosen = random.choice(possible_moves)
    row, col = idx_to_rc(chosen)
    _STATE["prev_board"] = copy.deepcopy(board)
    _STATE["last_move"] = chosen
    return (row, col)
