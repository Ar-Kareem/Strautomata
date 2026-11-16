
import time
from typing import List, Tuple

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
MAX_COLS = 7          # number of columns in Connect Four
MAX_ROWS = 6          # number of rows
WIN_SCORE = 1_000_000   # large value for a winning position
INF = 10**9

# ----------------------------------------------------------------------
# Board utilities
# ----------------------------------------------------------------------
def parse_state(state: List[List]) -> Tuple[List[List[int]], List[int]]:
    """
    Convert the list of Stanford propositions into a 7x6 integer board
    and the current height of each column.
    board[col][row]  -> 0 empty, 1 red, 2 black
    row 0 is the bottom row.
    """
    board = [[0] * MAX_ROWS for _ in range(MAX_COLS)]
    for prop in state:
        if prop[0] == "cell":
            row = int(prop[1]) - 1          # 0‑based, bottom row = 0
            col = int(prop[2]) - 1
            color = prop[3]
            board[col][row] = 1 if color == "red" else 2

    # Compute column heights
    heights = [0] * MAX_COLS
    for c in range(MAX_COLS):
        h = 0
        for r in range(MAX_ROWS):
            if board[c][r] != 0:
                h = r + 1
        heights[c] = h
    return board, heights


def check_win(board: List[List[int]], col: int, row: int, player: int) -> bool:
    """
    Check whether the last placed disc (at board[col][row]) completes a
    four‑in‑a‑row for `player`.
    """
    # Horizontal
    cnt = 0
    c = col
    while c < MAX_COLS and board[c][row] == player:
        cnt += 1
        c += 1
    c = col - 1
    while c >= 0 and board[c][row] == player:
        cnt += 1
        c -= 1
    if cnt >= 4:
        return True

    # Vertical (only upward needed – a disc always lands on the lowest empty cell)
    cnt = 0
    r = row
    while r < MAX_ROWS and board[col][r] == player:
        cnt += 1
        r += 1
    if cnt >= 4:
        return True

    # Diagonal “\”
    cnt = 0
    c, r = col, row
    while c < MAX_COLS and r < MAX_ROWS and board[c][r] == player:
        cnt += 1
        c += 1
        r += 1
    c, r = col - 1, row - 1
    while c >= 0 and r >= 0 and board[c][r] == player:
        cnt += 1
        c -= 1
        r -= 1
    if cnt >= 4:
        return True

    # Diagonal “/”
    cnt = 0
    c, r = col, row
    while c < MAX_COLS and r >= 0 and board[c][r] == player:
        cnt += 1
        c += 1
        r -= 1
    c, r = col - 1, row + 1
    while c >= 0 and r < MAX_ROWS and board[c][r] == player:
        cnt += 1
        c -= 1
        r += 1
    if cnt >= 4:
        return True

    return False


def evaluate(board: List[List[int]], player: int) -> int:
    """
    Heuristic evaluation of the board from the perspective of `player`.
    Higher scores are better for `player`.
    """
    opponent = 3 - player
    weight = [0, 1, 10, 100, 1000]          # score for 0‑4 pieces in a window
    score = 0

    # Horizontal windows
    for r in range(MAX_ROWS):
        for c in range(MAX_COLS - 3):
            window = [board[c + i][r] for i in range(4)]
            cnt_player = sum(1 for x in window if x == player)
            cnt_op = sum(1 for x in window if x == opponent)
            if cnt_op == 0:
                score += weight[cnt_player]
            elif cnt_player == 0:
                score -= weight[cnt_op]

    # Vertical windows
    for c in range(MAX_COLS):
        for r in range(MAX_ROWS - 3):
            window = [board[c][r + i] for i in range(4)]
            cnt_player = sum(1 for x in window if x == player)
            cnt_op = sum(1 for x in window if x == opponent)
            if cnt_op == 0:
                score += weight[cnt_player]
            elif cnt_player == 0:
                score -= weight[cnt_op]

    # Diagonal “\” windows
    for c in range(MAX_COLS - 3):
        for r in range(MAX_ROWS - 3):
            window = [board[c + i][r + i] for i in range(4)]
            cnt_player = sum(1 for x in window if x == player)
            cnt_op = sum(1 for x in window if x == opponent)
            if cnt_op == 0:
                score += weight[cnt_player]
            elif cnt_player == 0:
                score -= weight[cnt_op]

    # Diagonal “/” windows
    for c in range(MAX_COLS - 3):
        for r in range(3, MAX_ROWS):
            window = [board[c + i][r - i] for i in range(4)]
            cnt_player = sum(1 for x in window if x == player)
            cnt_op = sum(1 for x in window if x == opponent)
            if cnt_op == 0:
                score += weight[cnt_player]
            elif cnt_player == 0:
                score -= weight[cnt_op]

    # Central column preference (column 4, 0‑based index 3)
    centre = 3
    for r in range(MAX_ROWS):
        if board[centre][r] == player:
            score += 3
        elif board[centre][r] == opponent:
            score -= 3

    return score


def order_moves(legal: List[int], board: List[List[int]],
                heights: List[int], player: int) -> List[int]:
    """
    Return a list of columns ordered for exploration:
    1) winning moves for the player,
    2) opponent’s immediate winning moves (must block),
    3) otherwise by distance to the centre column.
    """
    opponent = 3 - player

    # Player winning moves
    for c in legal:
        r = heights[c]
        board[c][r] = player
        if check_win(board, c, r, player):
            board[c][r] = 0
            return [c]
        board[c][r] = 0

    # Opponent winning moves – they must be blocked
    blocking = []
    for c in legal:
        r = heights[c]
        board[c][r] = opponent
        if check_win(board, c, r, opponent):
            blocking.append(c)
        board[c][r] = 0
    if blocking:
        blocking.sort(key=lambda x: abs(x - 3))
        return blocking

    # Default: centre‑first order
    legal.sort(key=lambda x: abs(x - 3))
    return legal


def negamax(board: List[List[int]], heights: List[int],
            depth: int, alpha: int, beta: int, player: int) -> Tuple[int, int]:
    """
    Negamax search with alpha‑beta pruning.
    Returns (score, best_column) from the perspective of the player to move.
    """
    legal = [c for c in range(MAX_COLS) if heights[c] < MAX_ROWS]
    if not legal:
        return 0, None

    # Immediate winning move?
    for c in legal:
        r = heights[c]
        board[c][r] = player
        if check_win(board, c, r, player):
            board[c][r] = 0
            return WIN_SCORE + depth, c
        board[c][r] = 0

    # Depth limit reached – use static evaluation
    if depth == 0:
        return evaluate(board, player), None

    # Move ordering
    ordered = order_moves(legal, board, heights, player)

    best_score = -INF
    best_move = None
    for col in ordered:
        r = heights[col]
        board[col][r] = player
        heights[col] = r + 1

        score, _ = negamax(board, heights, depth - 1, -beta, -alpha, 3 - player)
        score = -score

        board[col][r] = 0
        heights[col] = r

        if score > best_score:
            best_score = score
            best_move = col
            if best_score > alpha:
                alpha = best_score
                if alpha >= beta:
                    break

    return best_score, best_move


# ----------------------------------------------------------------------
# Policy entry point
# ----------------------------------------------------------------------
def policy(state: List[List[object]], role: str) -> str:
    """
    Main API function required by the arena.
    `state` – list of true Stanford propositions.
    `role`  – either "red" or "black".
    Returns a legal move string such as "drop(3)".
    """
    board, heights = parse_state(state)
    player = 1 if role == "red" else 2

    start_time = time.time()
    max_depth = 1
    best_move = None

    # Iterative deepening – run as many depths as time permits
    while True:
        if time.time() - start_time > 0.85:
            break
        alpha = -INF
        beta = INF
        _, move = negamax(board, heights, max_depth, alpha, beta, player)
        if move is not None:
            best_move = move
        max_depth += 1
        if max_depth > 20:          # hard safety limit
            break

    # Fallback (should never be needed)
    if best_move is None:
        for c in range(MAX_COLS):
            if heights[c] < MAX_ROWS:
                best_move = c
                break

    return f"drop({best_move + 1})"
