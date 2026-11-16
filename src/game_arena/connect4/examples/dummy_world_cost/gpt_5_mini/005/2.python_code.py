
import math
import random
from typing import List, Tuple

ROWS = 6
COLS = 7
MY_ID = 1
OPP_ID = -1
INF = 10_000_000

def policy(board: List[List[int]]) -> int:
    """
    Choose a legal column (0-6) to play for the current player (encoded as 1).
    """
    # Make sure input is the expected shape
    if not board or len(board) != ROWS or any(len(row) != COLS for row in board):
        # fallback to center if malformed
        return 3

    # Helper functions
    def legal_moves(bd: List[List[int]]) -> List[int]:
        return [c for c in range(COLS) if bd[0][c] == 0]

    def get_next_row(bd: List[List[int]], col: int) -> int:
        for r in range(ROWS - 1, -1, -1):
            if bd[r][col] == 0:
                return r
        return -1

    def check_win(bd: List[List[int]], player: int) -> bool:
        # horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if bd[r][c] == player and bd[r][c+1] == player and bd[r][c+2] == player and bd[r][c+3] == player:
                    return True
        # vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if bd[r][c] == player and bd[r+1][c] == player and bd[r+2][c] == player and bd[r+3][c] == player:
                    return True
        # diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if bd[r][c] == player and bd[r+1][c+1] == player and bd[r+2][c+2] == player and bd[r+3][c+3] == player:
                    return True
        # diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if bd[r][c] == player and bd[r-1][c+1] == player and bd[r-2][c+2] == player and bd[r-3][c+3] == player:
                    return True
        return False

    def score_window(window: List[int], player: int) -> int:
        score = 0
        opp = -player
        count_player = window.count(player)
        count_opp = window.count(opp)
        count_empty = window.count(0)
        if count_player == 4:
            score += 1000
        elif count_player == 3 and count_empty == 1:
            score += 50
        elif count_player == 2 and count_empty == 2:
            score += 10
        if count_opp == 3 and count_empty == 1:
            score -= 80  # strong block necessity
        elif count_opp == 2 and count_empty == 2:
            score -= 5
        return score

    def evaluate_board(bd: List[List[int]]) -> int:
        # Score from MY_ID perspective (positive is good)
        score = 0
        # Center column preference
        center_col = [bd[r][COLS // 2] for r in range(ROWS)]
        center_count = center_col.count(MY_ID)
        score += center_count * 6
        # Horizontal windows
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [bd[r][c+i] for i in range(4)]
                score += score_window(window, MY_ID)
        # Vertical windows
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [bd[r+i][c] for i in range(4)]
                score += score_window(window, MY_ID)
        # Diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [bd[r+i][c+i] for i in range(4)]
                score += score_window(window, MY_ID)
        # Diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [bd[r-i][c+i] for i in range(4)]
                score += score_window(window, MY_ID)
        return score

    # Transposition table: map (board_flat_tuple, current_player, depth) -> score
    trans_table = {}

    def board_key(bd: List[List[int]]) -> Tuple[int, ...]:
        return tuple(val for row in bd for val in row)

    # Minimax with alpha-beta pruning
    def minimax(bd: List[List[int]], depth: int, alpha: int, beta: int, current_player: int) -> Tuple[int, int]:
        """
        Returns (best_col, score) where score is from MY_ID perspective
        """
        key = (board_key(bd), current_player, depth)
        if key in trans_table:
            return trans_table[key]

        legal = legal_moves(bd)
        # Terminal checks
        if check_win(bd, MY_ID):
            return (None, INF)
        if check_win(bd, OPP_ID):
            return (None, -INF)
        if not legal:
            return (None, 0)
        if depth == 0:
            val = evaluate_board(bd)
            return (None, val)

        best_col = random.choice(legal)
        if current_player == MY_ID:
            value = -INF
            # Order moves by heuristic: prefer center and higher immediate eval
            ordered = []
            for col in legal:
                r = get_next_row(bd, col)
                if r == -1:
                    continue
                bd[r][col] = current_player
                h = evaluate_board(bd)
                bd[r][col] = 0
                ordered.append((h, col))
            ordered.sort(reverse=True, key=lambda x: (x[0], -abs(x[1]-3)))  # prefer higher eval, then center
            for _, col in ordered:
                r = get_next_row(bd, col)
                if r == -1:
                    continue
                bd[r][col] = current_player
                _, score = minimax(bd, depth - 1, alpha, beta, -current_player)
                bd[r][col] = 0
                if score > value:
                    value = score
                    best_col = col
                alpha = max(alpha, value)
                if alpha >= beta:
                    break
        else:
            value = INF
            ordered = []
            for col in legal:
                r = get_next_row(bd, col)
                if r == -1:
                    continue
                bd[r][col] = current_player
                h = evaluate_board(bd)
                bd[r][col] = 0
                ordered.append((h, col))
            # Opponent will try to minimize my score -> sort ascending
            ordered.sort(key=lambda x: (x[0], abs(x[1]-3)))
            for _, col in ordered:
                r = get_next_row(bd, col)
                if r == -1:
                    continue
                bd[r][col] = current_player
                _, score = minimax(bd, depth - 1, alpha, beta, -current_player)
                bd[r][col] = 0
                if score < value:
                    value = score
                    best_col = col
                beta = min(beta, value)
                if alpha >= beta:
                    break

        trans_table[key] = (best_col, value)
        return (best_col, value)

    # Main decision logic
    moves = legal_moves(board)
    if not moves:
        return 0  # fallback

    # If only one legal move, take it
    if len(moves) == 1:
        return moves[0]

    # 1) Immediate win?
    for col in moves:
        r = get_next_row(board, col)
        if r == -1:
            continue
        board[r][col] = MY_ID
        win = check_win(board, MY_ID)
        board[r][col] = 0
        if win:
            return col

    # 2) Immediate block opponent's win?
    for col in moves:
        r = get_next_row(board, col)
        if r == -1:
            continue
        board[r][col] = OPP_ID
        opp_win = check_win(board, OPP_ID)
        board[r][col] = 0
        if opp_win:
            return col

    # Set search depth based on remaining empties (deeper near endgame)
    empty_count = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] == 0)
    if empty_count <= 10:
        max_depth = 8
    elif empty_count <= 20:
        max_depth = 7
    else:
        max_depth = 6

    # Root: use minimax to find best move
    best_col, best_score = minimax(board, max_depth, -INF, INF, MY_ID)

    # If minimax returns None or illegal, pick a reasonable fallback: center, then neighbors
    if best_col is None or board[0][best_col] != 0:
        preferred = [3, 2, 4, 1, 5, 0, 6]
        for c in preferred:
            if board[0][c] == 0:
                return c
        # ultimate fallback
        for c in range(COLS):
            if board[0][c] == 0:
                return c

    return best_col
