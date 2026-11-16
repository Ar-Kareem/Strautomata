
#!/usr/bin/env python3
from typing import List, Optional

ROWS = 6
COLS = 7
PLAYER = 1
OPP = -1

def get_drop_row(board: List[List[int]], col: int) -> Optional[int]:
    """Return the row index where a disc would land in column col, or None if the column is full."""
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return None

def make_move(board: List[List[int]], col: int, player: int) -> List[List[int]]:
    """Return a new board with player dropped in col (assumes legal move)."""
    newb = [row[:] for row in board]
    r = get_drop_row(newb, col)
    if r is None:
        return newb
    newb[r][col] = player
    return newb

def is_win(board: List[List[int]], player: int) -> bool:
    """Check whether player has a 4-in-a-row on the board."""
    # horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            if all(board[r][c + i] == player for i in range(4)):
                return True
    # vertical
    for c in range(COLS):
        for r in range(ROWS - 3):
            if all(board[r + i][c] == player for i in range(4)):
                return True
    # diag down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            if all(board[r + i][c + i] == player for i in range(4)):
                return True
    # diag down-left
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            if all(board[r + i][c - i] == player for i in range(4)):
                return True
    return False

def legal_columns(board: List[List[int]]) -> List[int]:
    return [c for c in range(COLS) if get_drop_row(board, c) is not None]

def opponent_can_win_after(board: List[List[int]], player_move_col: int) -> bool:
    """Return True if after making our move in player_move_col, the opponent has any immediate winning move."""
    newb = make_move(board, player_move_col, PLAYER)
    opp_legal = legal_columns(newb)
    for c in opp_legal:
        b2 = make_move(newb, c, OPP)
        if is_win(b2, OPP):
            return True
    return False

def policy(board: List[List[int]]) -> int:
    """
    Choose a column (0-6) to drop the current player's disc.
    Strategy:
      1. Play immediate winning move if available.
      2. Block opponent immediate winning moves.
      3. Avoid moves that give the opponent an immediate win.
      4. Prefer center columns to help create connections.
      5. Fallback to any legal move.
    """
    cols = legal_columns(board)
    if not cols:
        # No legal moves; shouldn't happen under contract, but return 0
        return 0

    # 1) Immediate winning move
    for c in cols:
        b = make_move(board, c, PLAYER)
        if is_win(b, PLAYER):
            return c

    # 2) Moves that block opponent immediate wins (threats)
    opponent_threats = []
    for c in cols:
        b_opp = make_move(board, c, OPP)
        if is_win(b_opp, OPP):
            opponent_threats.append(c)

    # If the opponent has threats, try to block
    if opponent_threats:
        # If there's only one threat, try to play that column (drop above their winning spot)
        for threat_col in opponent_threats:
            if threat_col in cols:
                # If playing this column blocks and doesn't immediately allow opponent win, play it
                if not opponent_can_win_after(board, threat_col):
                    return threat_col
        # If none of the threat columns are safe or direct block isn't possible, we'll fall through to safe-move selection

    # 3) Avoid moves that allow immediate opponent win
    safe_moves = []
    for c in cols:
        if not opponent_can_win_after(board, c):
            safe_moves.append(c)

    # If there are safe moves, pick one by heuristic preference (center-out)
    center_order = sorted(cols, key=lambda x: (abs(x - 3), x))  # prefer center (3), then closer columns
    if safe_moves:
        # From center_order, pick the first that is safe
        for c in center_order:
            if c in safe_moves:
                return c

    # 4) If no safe moves (all allow opponent immediate win), try to at least block if possible
    if opponent_threats:
        # try to play in any threat col even if not safe
        for c in opponent_threats:
            if c in cols:
                return c

    # 5) Fallback: pick center-most legal column
    for c in center_order:
        if c in cols:
            return c

    # Shouldn't reach here, but return first legal column
    return cols[0]

# If run as script, a simple random test could be added, but per instructions we only provide the policy function.
if __name__ == "__main__":
    # Example empty board test
    empty = [[0]*COLS for _ in range(ROWS)]
    print(policy(empty))  # expects 3 (center) or similar preference
