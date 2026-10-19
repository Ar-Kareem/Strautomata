
import copy
import math
import random
import time
from typing import List, Optional

ROWS = 6
COLS = 7
PLAYER = 1
OPP = -1

def policy(board: List[List[int]]) -> int:
    """
    Choose a column 0-6 to play next for the current player (encoded as 1).
    Board is a 6x7 list of lists, rows 0..5 top->bottom, cols 0..6 left->right.
    """
    start_time = time.time()
    time_limit = 0.95  # seconds

    # quick helpers
    def valid_moves(bd: List[List[int]]) -> List[int]:
        return [c for c in range(COLS) if bd[0][c] == 0]

    def find_row(bd: List[List[int]], col: int) -> Optional[int]:
        for r in range(ROWS - 1, -1, -1):
            if bd[r][col] == 0:
                return r
        return None

    def make_move(bd: List[List[int]], col: int, piece: int) -> int:
        r = find_row(bd, col)
        if r is None:
            raise ValueError("Making move on full column")
        bd[r][col] = piece
        return r

    def undo_move(bd: List[List[int]], row: int, col: int):
        bd[row][col] = 0

    def winning_move_at(bd: List[List[int]], row: int, col: int, piece: int) -> bool:
        # check four directions for a win including the (row,col) cell
        def count_dir(dr, dc):
            r, c = row + dr, col + dc
            cnt = 0
            while 0 <= r < ROWS and 0 <= c < COLS and bd[r][c] == piece:
                cnt += 1
                r += dr
                c += dc
            return cnt

        # horizontal
        if 1 + count_dir(0, 1) + count_dir(0, -1) >= 4:
            return True
        # vertical
        if 1 + count_dir(1, 0) + count_dir(-1, 0) >= 4:
            return True
        # diag /
        if 1 + count_dir(1, -1) + count_dir(-1, 1) >= 4:
            return True
        # diag \
        if 1 + count_dir(1, 1) + count_dir(-1, -1) >= 4:
            return True
        return False

    def is_terminal_node(bd: List[List[int]]) -> bool:
        # any win or full
        if any(check_winner(bd, p) for p in (PLAYER, OPP)):
            return True
        return all(bd[0][c] != 0 for c in range(COLS))

    def check_winner(bd: List[List[int]], piece: int) -> bool:
        # scan all positions for a win for piece
        for r in range(ROWS):
            for c in range(COLS):
                if bd[r][c] != piece:
                    continue
                # check four directions
                if c + 3 < COLS and all(bd[r][c + i] == piece for i in range(4)):
                    return True
                if r + 3 < ROWS and all(bd[r + i][c] == piece for i in range(4)):
                    return True
                if r + 3 < ROWS and c + 3 < COLS and all(bd[r + i][c + i] == piece for i in range(4)):
                    return True
                if r + 3 < ROWS and c - 3 >= 0 and all(bd[r + i][c - i] == piece for i in range(4)):
                    return True
        return False

    # Heuristic evaluation
    def evaluate_window(window: List[int], piece: int) -> int:
        score = 0
        opp_piece = OPP if piece == PLAYER else PLAYER
        cnt_piece = window.count(piece)
        cnt_opp = window.count(opp_piece)
        cnt_empty = window.count(0)
        if cnt_piece == 4:
            score += 100000
        elif cnt_piece == 3 and cnt_empty == 1:
            score += 100
        elif cnt_piece == 2 and cnt_empty == 2:
            score += 5
        if cnt_opp == 3 and cnt_empty == 1:
            score -= 80  # block imminent threat
        return score

    def score_position(bd: List[List[int]], piece: int) -> int:
        score = 0
        # center column preference
        center_array = [bd[r][COLS // 2] for r in range(ROWS)]
        center_count = center_array.count(piece)
        score += center_count * 6

        # Horizontal windows
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [bd[r][c + i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Vertical windows
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [bd[r + i][c] for i in range(4)]
                score += evaluate_window(window, piece)

        # Positive sloped diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [bd[r + i][c + i] for i in range(4)]
                score += evaluate_window(window, piece)

        # Negative sloped diagonal
        for r in range(ROWS - 3):
            for c in range(3, COLS):
                window = [bd[r + i][c - i] for i in range(4)]
                score += evaluate_window(window, piece)

        return score

    # Minimax with alpha-beta
    def minimax(bd: List[List[int]], depth: int, alpha: int, beta: int, maximizingPlayer: bool, start_time: float, time_limit: float):
        # time check
        if time.time() - start_time > time_limit:
            return None, score_position(bd, PLAYER)

        valid_cols = [c for c in range(COLS) if bd[0][c] == 0]
        is_terminal = is_terminal_node(bd)
        if depth == 0 or is_terminal:
            if is_terminal:
                if check_winner(bd, PLAYER):
                    return None, 10**9
                elif check_winner(bd, OPP):
                    return None, -10**9
                else:  # draw
                    return None, 0
            else:
                return None, score_position(bd, PLAYER)

        # Order moves: center first, then neighbors
        center = COLS // 2
        ordered = sorted(valid_cols, key=lambda x: abs(x - center))

        best_col = random.choice(ordered)
        if maximizingPlayer:
            value = -math.inf
            for col in ordered:
                row = find_row(bd, col)
                if row is None:
                    continue
                bd[row][col] = PLAYER
                # immediate win check
                if winning_move_at(bd, row, col, PLAYER):
                    bd[row][col] = 0
                    return col, 10**9
                _, new_score = minimax(bd, depth - 1, alpha, beta, False, start_time, time_limit)
                bd[row][col] = 0
                if new_score is None:
                    return None, None
                if new_score > value:
                    value = new_score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
            return best_col, value
        else:
            value = math.inf
            for col in ordered:
                row = find_row(bd, col)
                if row is None:
                    continue
                bd[row][col] = OPP
                if winning_move_at(bd, row, col, OPP):
                    bd[row][col] = 0
                    return col, -10**9
                _, new_score = minimax(bd, depth - 1, alpha, beta, True, start_time, time_limit)
                bd[row][col] = 0
                if new_score is None:
                    return None, None
                if new_score < value:
                    value = new_score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break
            return best_col, value

    # Strategy: immediate win -> immediate block -> minimax
    valid = [c for c in range(COLS) if board[0][c] == 0]
    if not valid:
        return 0

    # 1) Immediate winning move
    for col in valid:
        r = find_row(board, col)
        if r is None:
            continue
        board[r][col] = PLAYER
        if winning_move_at(board, r, col, PLAYER):
            board[r][col] = 0
            return col
        board[r][col] = 0

    # 2) Block opponent immediate winning move
    for col in valid:
        r = find_row(board, col)
        if r is None:
            continue
        board[r][col] = OPP
        if winning_move_at(board, r, col, OPP):
            board[r][col] = 0
            return col
        board[r][col] = 0

    # 3) Use minimax search
    # pick depth based on emptiness to be a bit deeper early game
    empties = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] == 0)
    if empties > 30:
        depth = 4
    else:
        depth = 5

    # Keep time-safety: reduce depth if nearing time limit
    best_col, best_score = minimax(board, depth, -math.inf, math.inf, True, start_time, time_limit)
    # If minimax aborted due to time (None), fallback to heuristic move ordering
    if best_col is None:
        # prefer center then next best by one-step heuristic
        center = COLS // 2
        ordered = sorted(valid, key=lambda x: abs(x - center))
        # pick highest immediate heuristic score after playing that move
        best_h = -math.inf
        best_c = ordered[0]
        for c in ordered:
            r = find_row(board, c)
            if r is None:
                continue
            board[r][c] = PLAYER
            h = score_position(board, PLAYER)
            board[r][c] = 0
            if h > best_h:
                best_h = h
                best_c = c
        return best_c

    return int(best_col)


# Minimal test when run as a script (not required by the arena, but harmless)
if __name__ == "__main__":
    # empty board -> should pick center 3
    empty = [[0] * COLS for _ in range(ROWS)]
    print("Chosen column on empty:", policy(empty))
