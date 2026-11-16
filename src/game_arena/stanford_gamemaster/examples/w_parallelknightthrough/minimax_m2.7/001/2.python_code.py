
import sys
from typing import List, Dict, Set, Tuple

# Column <-> index mapping
col2idx = {"a": 0, "b": 1, "c": 2}
idx2col = {0: "a", 1: "b", 2: "c"}

def policy(state: List[List[object]], role: str) -> str:
    # ------------------------------------------------------------------
    # Parse the state
    # ------------------------------------------------------------------
    step: int = 0
    played_boards: Set[str] = set()
    pieces: Dict[str, List[Tuple[str, str, int]]] = {"white": [], "black": []}
    occupied: Dict[str, Set[Tuple[str, str, int]]] = {"white": set(), "black": set()}

    for fact in state:
        if not fact:
            continue
        if fact[0] == "step":
            step = int(fact[1])
        elif fact[0] == "control":
            # The control fact matches the role argument, we don't need it further
            pass
        elif fact[0] == "played":
            # Boards already used by the current player this step
            played_boards.add(fact[1])
        elif fact[0] == "cell":
            board, col, row_str, color = fact[1], fact[2], fact[3], fact[4]
            row = int(row_str)
            pieces.setdefault(color, []).append((board, col, row))
            occupied[color].add((board, col, row))

    opponent = "black" if role == "white" else "white"

    # ------------------------------------------------------------------
    # Generate all legal forward knight moves
    # ------------------------------------------------------------------
    best_move = None
    best_score = -1

    for board, col, row in pieces.get(role, []):
        # Skip if this board has already been played this step
        if board in played_boards:
            continue

        # Determine direction of movement
        if role == "white":
            dr_values = (1, 2)          # forward for white
        else:
            dr_values = (-1, -2)         # forward for black

        for dr in dr_values:
            dc = 3 - abs(dr)             # magnitude of column change (2 if dr=±1, 1 if dr=±2)
            row_to = row + dr
            # Row must stay inside the board (1‑8)
            if not (1 <= row_to <= 8):
                continue
            for dcsign in (-dc, dc):
                col_from_idx = col2idx[col]
                col_to_idx = col_from_idx + dcsign
                # Column must stay inside a‑c (0‑2)
                if not (0 <= col_to_idx <= 2):
                    continue
                col_to = idx2col[col_to_idx]
                dest = (board, col_to, row_to)

                # Cannot land on a square occupied by our own colour
                if dest in occupied[role]:
                    continue

                # Immediate winning move?
                if role == "white" and board == "a" and row_to == 8:
                    return f"move({board},{col},{row},{col_to},{row_to})"
                if role == "black" and board == "c" and row_to == 1:
                    return f"move({board},{col},{row},{col_to},{row_to})"

                # Score the move (higher is better)
                if role == "white":
                    base = row_to * 10
                    board_bonus = {"a": 10, "b": 5, "c": 0}.get(board, 0)
                else:  # black
                    base = (9 - row_to) * 10
                    board_bonus = {"c": 10, "b": 5, "a": 0}.get(board, 0)

                score = base + board_bonus

                # Small bonus for capturing an opponent piece
                if dest in occupied[opponent]:
                    score += 3

                if score > best_score:
                    best_score = score
                    best_move = f"move({board},{col},{row},{col_to},{row_to})"

    # If a legal move was found, return it; otherwise we must pass
    if best_move is not None:
        return best_move
    return "tick"
