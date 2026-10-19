
from typing import List

ROWS = 6
COLS = 7
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]
WIN_SCORE = 10**9
INF = 10**18

# Bitboard mapping:
# bit index = col * 7 + row, with row in [0..5] plus one sentinel bit at row 6
# This is the standard 7-bits-per-column encoding.


def policy(board: List[List[int]]) -> int:
    legal = legal_moves_board(board)
    if not legal:
        return 0

    # Immediate tactical checks on board form for safety.
    for c in CENTER_ORDER:
        if c in legal and is_winning_move_board(board, c, 1):
            return c

    opp_wins = []
    for c in CENTER_ORDER:
        if c in legal and is_winning_move_board(board, c, -1):
            opp_wins.append(c)
    if opp_wins:
        for c in CENTER_ORDER:
            if c in opp_wins:
                return c

    my_bits, opp_bits, heights, moves_played = board_to_bitboards(board)

    # Iterative deepening-ish fixed depth chosen for speed/strength balance.
    empties = ROWS * COLS - moves_played
    if empties >= 30:
        depth = 5
    elif empties >= 18:
        depth = 6
    elif empties >= 10:
        depth = 7
    else:
        depth = 8

    best_move = None
    best_score = -INF
    alpha = -INF
    beta = INF

    ordered = ordered_legal_moves(heights)

    # Prefer legal safe moves; if all searched moves are dangerous, still return a legal move.
    fallback = ordered[0] if ordered else legal[0]

    for c in ordered:
        move_bit = 1 << heights[c]
        new_heights = heights[:]
        new_heights[c] += 1

        if is_win_bitboard(my_bits | move_bit):
            return c

        # After our move, avoid allowing opponent immediate win if possible.
        opp_reply_wins = immediate_wins_bitboard(opp_bits, my_bits | move_bit, new_heights)
        dangerous = len(opp_reply_wins) > 0

        score = -negamax(
            opp_bits,
            my_bits | move_bit,
            new_heights,
            depth - 1,
            -beta,
            -alpha,
        )

        # Penalize obviously dangerous moves a bit so safe alternatives are preferred.
        if dangerous:
            score -= 500000

        # Small move-order preference for center.
        score += center_preference(c)

        if score > best_score:
            best_score = score
            best_move = c
        if score > alpha:
            alpha = score

    if best_move is not None and best_move in legal:
        return best_move

    return fallback


def legal_moves_board(board: List[List[int]]) -> List[int]:
    return [c for c in range(COLS) if board[0][c] == 0]


def center_preference(c: int) -> int:
    return [0, 1, 2, 3, 2, 1, 0][c]


def board_to_bitboards(board: List[List[int]]):
    my_bits = 0
    opp_bits = 0
    heights = [c * 7 for c in range(COLS)]
    moves_played = 0

    for c in range(COLS):
        h = c * 7
        for r in range(ROWS - 1, -1, -1):
            v = board[r][c]
            if v == 0:
                continue
            rr = ROWS - 1 - r
            bit = 1 << (c * 7 + rr)
            if v == 1:
                my_bits |= bit
            else:
                opp_bits |= bit
            moves_played += 1
            h = c * 7 + rr + 1
        heights[c] = h

    return my_bits, opp_bits, heights, moves_played


def ordered_legal_moves(heights: List[int]) -> List[int]:
    return [c for c in CENTER_ORDER if heights[c] < c * 7 + ROWS]


def is_win_bitboard(pos: int) -> bool:
    m = pos & (pos >> 1)
    if m & (m >> 2):
        return True
    m = pos & (pos >> 7)
    if m & (m >> 14):
        return True
    m = pos & (pos >> 6)
    if m & (m >> 12):
        return True
    m = pos & (pos >> 8)
    if m & (m >> 16):
        return True
    return False


def immediate_wins_bitboard(cur_bits: int, opp_bits: int, heights: List[int]) -> List[int]:
    wins = []
    occ = cur_bits | opp_bits
    for c in CENTER_ORDER:
        if heights[c] >= c * 7 + ROWS:
            continue
        bit = 1 << heights[c]
        if is_win_bitboard(cur_bits | bit):
            wins.append(c)
    return wins


def is_winning_move_board(board: List[List[int]], col: int, player: int) -> bool:
    row = drop_row(board, col)
    if row == -1:
        return False
    board[row][col] = player
    ok = check_win_from(board, row, col, player)
    board[row][col] = 0
    return ok


def drop_row(board: List[List[int]], col: int) -> int:
    for r in range(ROWS - 1, -1, -1):
        if board[r][col] == 0:
            return r
    return -1


def check_win_from(board: List[List[int]], r: int, c: int, player: int) -> bool:
    for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
        cnt = 1
        rr, cc = r + dr, c + dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            cnt += 1
            rr += dr
            cc += dc
        rr, cc = r - dr, c - dc
        while 0 <= rr < ROWS and 0 <= cc < COLS and board[rr][cc] == player:
            cnt += 1
            rr -= dr
            cc -= dc
        if cnt >= 4:
            return True
    return False


def negamax(cur_bits: int, opp_bits: int, heights: List[int], depth: int, alpha: int, beta: int) -> int:
    legal = ordered_legal_moves(heights)
    if not legal:
        return 0

    # If current side has immediate win, take it in evaluation.
    for c in legal:
        bit = 1 << heights[c]
        if is_win_bitboard(cur_bits | bit):
            return WIN_SCORE - (42 - sum(h - c * 7 for c, h in enumerate(heights)))

    if depth == 0:
        return evaluate(cur_bits, opp_bits, heights)

    # If opponent has multiple immediate wins next turn, position is near-lost.
    opp_immediate = immediate_wins_bitboard(opp_bits, cur_bits, heights)
    if len(opp_immediate) >= 2:
        return -WIN_SCORE // 2

    best = -INF

    for c in legal:
        bit = 1 << heights[c]
        new_heights = heights[:]
        new_heights[c] += 1

        score = -negamax(opp_bits, cur_bits | bit, new_heights, depth - 1, -beta, -alpha)

        # Discourage moves allowing immediate opponent wins.
        opp_wins = immediate_wins_bitboard(opp_bits, cur_bits | bit, new_heights)
        if opp_wins:
            score -= 300000 + 10000 * len(opp_wins)

        score += center_preference(c)

        if score > best:
            best = score
        if best > alpha:
            alpha = best
        if alpha >= beta:
            break

    return best


def evaluate(cur_bits: int, opp_bits: int, heights: List[int]) -> int:
    score = 0

    # Center occupancy
    for r in range(ROWS):
        bit = 1 << (3 * 7 + r)
        if cur_bits & bit:
            score += 18
        elif opp_bits & bit:
            score -= 18

    # Window-based heuristic on reconstructed board.
    grid = bitboards_to_grid(cur_bits, opp_bits)

    windows = []
    # Horizontal
    for r in range(ROWS):
        for c in range(COLS - 3):
            windows.append([grid[r][c + i] for i in range(4)])
    # Vertical
    for r in range(ROWS - 3):
        for c in range(COLS):
            windows.append([grid[r + i][c] for i in range(4)])
    # Diag down-right
    for r in range(ROWS - 3):
        for c in range(COLS - 3):
            windows.append([grid[r + i][c + i] for i in range(4)])
    # Diag down-left
    for r in range(ROWS - 3):
        for c in range(3, COLS):
            windows.append([grid[r + i][c - i] for i in range(4)])

    for w in windows:
        score += eval_window(w)

    # Immediate tactical threats
    my_wins = len(immediate_wins_bitboard(cur_bits, opp_bits, heights))
    opp_wins = len(immediate_wins_bitboard(opp_bits, cur_bits, heights))
    score += 5000 * my_wins
    score -= 7000 * opp_wins

    return score


def bitboards_to_grid(cur_bits: int, opp_bits: int) -> List[List[int]]:
    grid = [[0 for _ in range(COLS)] for _ in range(ROWS)]
    for c in range(COLS):
        for rr in range(ROWS):
            bit = 1 << (c * 7 + rr)
            r = ROWS - 1 - rr
            if cur_bits & bit:
                grid[r][c] = 1
            elif opp_bits & bit:
                grid[r][c] = -1
    return grid


def eval_window(w: List[int]) -> int:
    me = w.count(1)
    opp = w.count(-1)
    emp = w.count(0)

    if me and opp:
        return 0
    if me == 4:
        return 100000
    if opp == 4:
        return -100000
    if me == 3 and emp == 1:
        return 120
    if me == 2 and emp == 2:
        return 12
    if me == 1 and emp == 3:
        return 2
    if opp == 3 and emp == 1:
        return -150
    if opp == 2 and emp == 2:
        return -15
    if opp == 1 and emp == 3:
        return -2
    return 0
