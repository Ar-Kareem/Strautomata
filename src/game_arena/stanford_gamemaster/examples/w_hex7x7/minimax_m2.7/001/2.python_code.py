
import sys
from typing import List, Tuple, Dict

# ----------------------------------------------------------------------
# Constants
COLS = 7          # a … g
ROWS = 7          # 1 … 7
COL_LETTERS = [chr(ord('a') + i) for i in range(COLS)]

# ----------------------------------------------------------------------
# Helper functions
def col_to_idx(col: str) -> int:
    return ord(col) - ord('a')

def idx_to_col(idx: int) -> str:
    return COL_LETTERS[idx]

def parse_state(state: List[List[object]]) -> Dict[Tuple[int, int], str]:
    """Convert the list of facts into a dictionary {(col,row): colour}."""
    board = {}
    for fact in state:
        if not isinstance(fact, list) or len(fact) < 1:
            continue
        if fact[0] == "cell":
            # ["cell", "a", "1", "red"]
            col_str, row_str, colour = fact[1], fact[2], fact[3]
            col = col_to_idx(col_str)
            row = int(row_str) - 1
            board[(col, row)] = colour
        # other facts are ignored for the purpose of playing the move
    return board

def empty_cells(board: Dict[Tuple[int, int], str]) -> List[Tuple[int, int]]:
    """Return a list of all empty positions (col,row)."""
    result = []
    for c in range(COLS):
        for r in range(ROWS):
            if (c, r) not in board:
                result.append((c, r))
    return result

def neighbours(pos: Tuple[int, int]) -> List[Tuple[int, int]]:
    """All legal hex neighbours of a cell (col,row)."""
    c, r = pos
    offsets = [
        (c + 1, r),     # right
        (c - 1, r),     # left
        (c, r + 1),     # down
        (c, r - 1),     # up
        (c + 1, r - 1), # up‑right
        (c - 1, r + 1)  # down‑left
    ]
    return [(nc, nr) for nc, nr in offsets if 0 <= nc < COLS and 0 <= nr < ROWS]

# ----------------------------------------------------------------------
# Win detection
def check_win(board: Dict[Tuple[int, int], str], player: str) -> bool:
    """Return True iff `player` already has a winning path."""
    visited = set()
    for start, colour in board.items():
        if colour != player or start in visited:
            continue
        # BFS/DFS for this component
        comp = []
        stack = [start]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            if board[cur] == player:
                comp.append(cur)
                for nb in neighbours(cur):
                    if nb in board and board[nb] == player and nb not in visited:
                        stack.append(nb)
        # Does this component touch both required sides?
        if player == "red":
            has_left = any(c == 0 for c, _ in comp)
            has_right = any(c == COLS - 1 for c, _ in comp)
            if has_left and has_right:
                return True
        else:  # black
            has_top = any(r == 0 for _, r in comp)
            has_bottom = any(r == ROWS - 1 for _, r in comp)
            if has_top and has_bottom:
                return True
    return False

# ----------------------------------------------------------------------
# Static evaluation
def max_span(board: Dict[Tuple[int, int], str], player: str) -> int:
    """Largest distance between two cells of the same component in the
    goal direction (horizontal for red, vertical for black)."""
    visited = set()
    best = 0
    for pos, colour in board.items():
        if colour != player or pos in visited:
            continue
        comp = []
        stack = [pos]
        while stack:
            cur = stack.pop()
            if cur in visited:
                continue
            visited.add(cur)
            if board[cur] == player:
                comp.append(cur)
                for nb in neighbours(cur):
                    if nb in board and board[nb] == player and nb not in visited:
                        stack.append(nb)
        if player == "red":
            cols = [c for c, _ in comp]
            span = max(cols) - min(cols)
        else:
            rows = [r for _, r in comp]
            span = max(rows) - min(rows)
        if span > best:
            best = span
    return best

def sum_distance(board: Dict[Tuple[int, int], str], player: str) -> int:
    """Sum of distances of all pieces of `player` to the target side."""
    total = 0
    for (c, r), colour in board.items():
        if colour != player:
            continue
        if player == "red":
            total += (COLS - 1) - c      # distance to column g
        else:
            total += (ROWS - 1) - r      # distance to row 7
    return total

def evaluate_board(board: Dict[Tuple[int, int], str], player: str) -> float:
    """Static evaluation of the board from `player`'s perspective.
    Larger values are better for `player`."""
    opponent = "black" if player == "red" else "red"
    # Terminal states
    if check_win(board, player):
        return 1e9
    if check_win(board, opponent):
        return -1e9
    # Distance based term (smaller distance is better)
    dist_player = sum_distance(board, player)
    dist_opponent = sum_distance(board, opponent)
    # Span based term (larger span is better)
    span_player = max_span(board, player)
    span_opponent = max_span(board, opponent)
    # Piece count (tiny bonus)
    pieces_player = sum(1 for c in board.values() if c == player)
    pieces_opponent = sum(1 for c in board.values() if c == opponent)
    # Combine
    score = -dist_player + dist_opponent + 10 * (span_player - span_opponent) \
            + 0.1 * (pieces_player - pieces_opponent)
    return score

# ----------------------------------------------------------------------
# Minimax search (depth 2)
def best_move(board: Dict[Tuple[int, int], str], player: str) -> Tuple[int, int]:
    """Return the optimal move for `player` according to depth‑2 minimax."""
    opponent = "black" if player == "red" else "red"
    empties = empty_cells(board)
    # Immediate win?
    for mv in empties:
        board2 = board.copy()
        board2[mv] = player
        if check_win(board2, player):
            return mv
    best_score = -float('inf')
    best_move = empties[0] if empties else None
    for mv in empties:
        board2 = board.copy()
        board2[mv] = player
        # If opponent can win after this move, treat as worst case
        worst = float('inf')
        for opp_mv in empty_cells(board2):
            board3 = board2.copy()
            board3[opp_mv] = opponent
            if check_win(board3, opponent):
                worst = -1e9
                break
            else:
                val = evaluate_board(board3, player)
                if val < worst:
                    worst = val
        if worst > best_score:
            best_score = worst
            best_move = mv
    return best_move

# ----------------------------------------------------------------------
# Main policy entry point
def policy(state: List[List[object]], role: str) -> str:
    """Choose a legal move for the given role in the current state."""
    board = parse_state(state)
    move = best_move(board, role)
    if move is None:
        # Fallback (should never happen in a real game)
        return "place(a,1)"
    col_idx, row_idx = move
    return f"place({idx_to_col(col_idx)},{row_idx + 1})"
