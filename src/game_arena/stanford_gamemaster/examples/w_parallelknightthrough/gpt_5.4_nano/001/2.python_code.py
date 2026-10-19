
import re
from typing import List, Tuple, Dict, Optional

# Board columns are letters a,b,c and rows are 1..8.
COLS = ["a", "b", "c"]
COL_TO_I = {c: i for i, c in enumerate(COLS)}

KNIGHT_DELTAS = [
    (1, 2), (2, 1), (-1, 2), (-2, 1),
    (1, -2), (2, -1), (-1, -2), (-2, -1),
]

def _is_white(role: str) -> bool:
    return role.strip().lower() == "white"

def _target_row(color: str) -> int:
    # White wins by reaching 8th row of the 1st board; black wins by reaching 1st row of the 3rd board.
    return 8 if color == "white" else 1

def _forward_condition(color: str, dr: int) -> bool:
    # White moves forward (increasing row index). Black moves forward (decreasing row index).
    return dr > 0 if color == "white" else dr < 0

def _parse_state(state: List[List[object]]) -> Tuple[Dict[Tuple[str,int,str], str], Optional[str]]:
    """
    Returns:
      cells: mapping (col, row, board) -> color ('white'/'black')
      control_color: 'white'/'black'/None from any ['control', color] fact
    """
    cells: Dict[Tuple[str,int,str], str] = {}
    control_color = None
    for fact in state:
        if not fact:
            continue
        if fact[0] == "control" and len(fact) >= 2:
            control_color = str(fact[1])
        elif fact[0] == "cell" and len(fact) >= 6:
            # Example: ["cell","a","a","1","white"] -> col, board, row, color
            col = str(fact[1])
            board = str(fact[2])  # 'a','b','c' board index in input
            row = int(fact[3])
            color = str(fact[4])
            cells[(col, row, board)] = color
    return cells, control_color

def _generate_moves(cells: Dict[Tuple[str,int,str], str], color: str) -> List[Tuple[Tuple[str,int,str], Tuple[str,int,str]]]:
    moves = []
    for (col, row, board), c in cells.items():
        if c != color:
            continue
        # Try all knight deltas; enforce forward-only
        for dc_i, dr in KNIGHT_DELTAS:
            # dc in terms of column letters delta 1 or 2
            nc_i = COL_TO_I[col] + dc_i
            if nc_i < 0 or nc_i >= len(COLS):
                continue
            ncol = COLS[nc_i]
            nrow = row + dr
            if nrow < 1 or nrow > 8:
                continue
            if not _forward_condition(color, dr):
                continue
            # board stays same (only rows/cols within each 3x8 board)
            nboard = board
            # can't land on own piece
            if (ncol, nrow, nboard) in cells and cells[(ncol, nrow, nboard)] == color:
                continue
            moves.append(((col, row, board), (ncol, nrow, nboard)))
    return moves

def _action_from_move(frm: Tuple[str,int,str], to: Tuple[str,int,str]) -> str:
    # move(a,a,1,b,3)  where third is board? Actually format example: move(a,a,1,b,3)
    # From examples: move(from_col, board, from_row, to_col, to_row)
    fcol, frow, fboard = frm  # careful: our tuple order is (col,row,board)
    tcol, trow, tboard = to
    return f"move({fcol},{fboard},{frow},{tcol},{trow})"

def _best_move(state: List[List[object]], role: str) -> str:
    cells, control_color = _parse_state(state)

    role_color = role.strip().lower()
    # If it's not our turn, default to tick (should be safe when control doesn't match).
    if control_color is not None and control_color != role_color:
        return "tick"

    color = role_color
    moves = _generate_moves(cells, color)
    if not moves:
        return "tick"

    opp = "black" if color == "white" else "white"
    target = _target_row(color)

    def score(frm_to):
        frm, to = frm_to
        fcol, frow, fboard = frm
        tcol, trow, tboard = to

        # Primary: reaching winning row sooner
        win = 1 if trow == target else 0
        # distance progressed
        if color == "white":
            progress = trow - frow
        else:
            progress = frow - trow

        # avoid captures of safety heuristic: prefer capturing opponent
        capture = 1 if (tcol, trow, tboard) in cells and cells[(tcol, trow, tboard)] == opp else 0

        # Penalize landing next to? we don't have immediate threat modeling; just simple capture/avoid.
        occupied_by_opp = 1 if (tcol, trow, tboard) in cells and cells[(tcol, trow, tboard)] == opp else 0
        occupied_by_own = 1 if (tcol, trow, tboard) in cells and cells[(tcol, trow, tboard)] == color else 0

        # Convert to heuristic: winning dominates, then progress, then capture, then slightly prefer central column.
        col_center_bonus = 1 if tcol == "b" else 0

        s = 0
        s += win * 10_000
        s += progress * 300
        s += capture * 200
        s += occupied_by_opp * 50
        s += col_center_bonus * 5
        s -= occupied_by_own * 1000  # should be zero because legality filtered
        return s

    moves_scored = sorted(moves, key=score, reverse=True)
    return _action_from_move(moves_scored[0][0], moves_scored[0][1])

def policy(state: list[list[object]], role: str) -> str:
    return _best_move(state, role)
