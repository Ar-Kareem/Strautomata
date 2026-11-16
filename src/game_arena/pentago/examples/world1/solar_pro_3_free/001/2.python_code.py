
import random
import numpy as np

# ----------------------------------------------------------------------
# Constants for evaluation
WIN_SCORE = 200   # for a full 5‑in‑a‑row
MID_SCORE = 20    # for a near‑win (4‑in‑a‑row)

# ----------------------------------------------------------------------
def _combine_board(you: list | np.ndarray, opponent: list | np.ndarray) -> list[list]:
    """Merge two 6×6 boards into a single board with 0/1/2."""
    board = [[0] * 6 for _ in range(6)]
    # support both list and numpy inputs
    if isinstance(you, np.ndarray):
        you = you.tolist()
    if isinstance(opponent, np.ndarray):
        opponent = opponent.tolist()
    for r in range(6):
        for c in range(6):
            if you[r][c] == 1:
                board[r][c] = 1
            elif opponent[r][c] == 1:
                board[r][c] = 2
    return board

def _apply_move(board: list[list], r: int, c: int,
                quad: int, dir_: str, piece: int) -> list[list]:
    """Place *piece* (1 or 2) at (r,c) then rotate quadrant *quad*."""
    new_board = [row[:] for row in board]      # deep copy
    new_board[r][c] = piece

    # quadrant offset
    row_off = (quad // 2) * 3   # top/bottom half
    col_off = (quad % 2) * 3    # left/right half

    if dir_ == 'L':
        # anticlockwise 90°
        for i in range(3):
            for j in range(3):
                new_i = 2 - j
                new_j = i
                new_board[row_off + new_i][col_off + new_j] = board[row_off + i][col_off + j]
    else:  # 'R'
        # clockwise 90°
        for i in range(3):
            for j in range(3):
                new_i = j
                new_j = 2 - i
                new_board[row_off + new_i][col_off + new_j] = board[row_off + i][col_off + j]

    return new_board

def _has_won(board: list[list], piece: int) -> bool:
    """Return True if *piece* (1 for me, 2 for opponent) has a 5‑in‑a‑row."""
    # Horizontal windows
    for r in range(6):
        for s in (0, 1):
            if all(board[r][c] == piece for c in range(s, s + 5)):
                return True
    # Vertical windows
    for c in range(6):
        for s in (0, 1):
            if all(board[r][c] == piece for r in range(s, s + 5)):
                return True
    # Main diagonal windows
    for s in (0, 1):
        for t in (0, 1):
            if all(board[r+i][c+i] == piece for i in range(5)):
                return True
    # Anti‑diagonal windows
    for s in (0, 1):
        for t in (0, 1):
            if all(board[r+i][5 - (c+i)] == piece for i in range(5)):
                return True
    return False

def _evaluate(board: list[list]) -> int:
    """Zero‑sum heuristic: + for me, – for opponent."""
    score = 0
    # Helper to count pieces in a window
    def _window_counts(window):
        cnt_me = sum(1 for v in window if v == 1)
        cnt_opp = sum(1 for v in window if v == 2)
        return cnt_me, cnt_opp

    # Horizontal and vertical windows
    for start_row in range(6):
        for start_col in (0, 1):
            win_segment = board[start_row][start_col: start_col + 5]
            me, opp = _window_counts(win_segment)
            if me == 5:
                score += WIN_SCORE
            elif opp == 5:
                score -= WIN_SCORE
            elif me == 4 and opp == 0:
                score += MID_SCORE
            elif opp == 4 and me == 0:
                score -= MID_SCORE
    # Main diagonals
    for start_row in (0, 1):
        for start_col in (0, 1):
            win_segment = [board[start_row + i][start_col + i] for i in range(5)]
            me, opp = _window_counts(win_segment)
            if me == 5:
                score += WIN_SCORE
            elif opp == 5:
                score -= WIN_SCORE
            elif me == 4 and opp == 0:
                score += MID_SCORE
            elif opp == 4 and me == 0:
                score -= MID_SCORE
    # Anti‑diagonals
    for start_row in (0, 1):
        for start_col in (0, 1):
            win_segment = [board[start_row + i][5 - (start_col + i)] for i in range(5)]
            me, opp = _window_counts(win_segment)
            if me == 5:
                score += WIN_SCORE
            elif opp == 5:
                score -= WIN_SCORE
            elif me == 4 and opp == 0:
                score += MID_SCORE
            elif opp == 4 and me == 0:
                score -= MID_SCORE
    return score

def _generate_moves(board: list[list], piece: int):
    """Yield (move_string, resulting_board) for all legal moves of *piece*."""
    moves = []
    for r in range(6):
        for c in range(6):
            if board[r][c] != 0:
                continue
            for quad in range(4):
                for dir_ in ('L', 'R'):
                    new_board = _apply_move(board, r, c, quad, dir_, piece)
                    # The move is always legal – placement and rotation never clash
                    move_str = f"{r+1},{c+1},{quad},{dir_}"
                    moves.append((move_str, new_board))
    return moves

def policy(you, opponent):
    """Return the next legal move as a string: \"row,col,quad,dir\"."""
    # ------------------------------------------------------------------
    # 1. Combine both player arrays into a unified board.
    board = _combine_board(you, opponent)

    # ------------------------------------------------------------------
    # 2. Immediate win detection – our move must finish the game if possible.
    for move_str, new_board in _generate_moves(board, piece=1):
        if _has_won(new_board, piece=1):
            return move_str

    # ------------------------------------------------------------------
    # 3. One‑ply minimax (max‑min) look‑ahead.
    best_score = float('-inf')
    best_moves: list[str] = []

    for move_str, my_board in _generate_moves(board, piece=1):
        # Simulate opponent's response and evaluate the worst case for me.
        # If board is already full, opponent has no moves.
        opponent_scores = []
        for opp_move_str, opp_board in _generate_moves(my_board, piece=2):
            opponent_scores.append(_evaluate(opp_board))

        if not opponent_scores:   # opponent cannot move → board is full
            final_score = _evaluate(my_board)
        else:
            final_score = min(opponent_scores)   # worst outcome for me

        if final_score > best_score:
            best_score = final_score
            best_moves = [move_str]
        elif final_score == best_score:
            best_moves.append(move_str)

    # ------------------------------------------------------------------
    # 4. Tie‑breaking with randomness (ensures a legal move is always returned)
    return random.choice(best_moves)
