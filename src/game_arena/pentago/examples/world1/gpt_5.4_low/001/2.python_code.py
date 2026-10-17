
from typing import List, Tuple

# ---------- Precomputed geometry ----------

SEGMENTS = []

# Rows: 6 rows * 2 length-5 windows
for r in range(6):
    for c in range(2):
        SEGMENTS.append([(r, c + i) for i in range(5)])

# Cols: 6 cols * 2 length-5 windows
for c in range(6):
    for r in range(2):
        SEGMENTS.append([(r + i, c) for i in range(5)])

# Diagonal down-right windows
# Starts that produce diagonals of length >= 5:
# (0,0) length 6 -> two windows
# (0,1) length 5 -> one window
# (1,0) length 5 -> one window
SEGMENTS.append([(0 + i, 0 + i) for i in range(5)])
SEGMENTS.append([(1 + i, 1 + i) for i in range(5)])
SEGMENTS.append([(0 + i, 1 + i) for i in range(5)])
SEGMENTS.append([(1 + i, 0 + i) for i in range(5)])

# Diagonal down-left windows
# (0,5) length 6 -> two windows
# (0,4) length 5 -> one window
# (1,5) length 5 -> one window
SEGMENTS.append([(0 + i, 5 - i) for i in range(5)])
SEGMENTS.append([(1 + i, 4 - i) for i in range(5)])
SEGMENTS.append([(0 + i, 4 - i) for i in range(5)])
SEGMENTS.append([(1 + i, 5 - i) for i in range(5)])

# Mild center preference
CELL_WEIGHT = [
    [0, 1, 2, 2, 1, 0],
    [1, 3, 4, 4, 3, 1],
    [2, 4, 5, 5, 4, 2],
    [2, 4, 5, 5, 4, 2],
    [1, 3, 4, 4, 3, 1],
    [0, 1, 2, 2, 1, 0],
]

LINE_SCORE = {
    0: 0,
    1: 2,
    2: 12,
    3: 80,
    4: 700,
    5: 1000000,
}


# ---------- Board helpers ----------

def to_board(you, opponent) -> List[List[int]]:
    board = [[0] * 6 for _ in range(6)]
    for r in range(6):
        yr = you[r]
        orow = opponent[r]
        for c in range(6):
            if yr[c]:
                board[r][c] = 1
            elif orow[c]:
                board[r][c] = 2
    return board


def copy_board(board: List[List[int]]) -> List[List[int]]:
    return [row[:] for row in board]


def rotate_quad_inplace(board: List[List[int]], quad: int, direction: str) -> None:
    if quad == 0:
        r0, c0 = 0, 0
    elif quad == 1:
        r0, c0 = 0, 3
    elif quad == 2:
        r0, c0 = 3, 0
    else:
        r0, c0 = 3, 3

    sub = [board[r0 + i][c0:c0 + 3] for i in range(3)]

    if direction == 'R':
        # clockwise
        rot = [
            [sub[2][0], sub[1][0], sub[0][0]],
            [sub[2][1], sub[1][1], sub[0][1]],
            [sub[2][2], sub[1][2], sub[0][2]],
        ]
    else:
        # anticlockwise
        rot = [
            [sub[0][2], sub[1][2], sub[2][2]],
            [sub[0][1], sub[1][1], sub[2][1]],
            [sub[0][0], sub[1][0], sub[2][0]],
        ]

    for i in range(3):
        for j in range(3):
            board[r0 + i][c0 + j] = rot[i][j]


def apply_move(board: List[List[int]], move: Tuple[int, int, int, str], player: int) -> List[List[int]]:
    r, c, q, d = move
    nb = copy_board(board)
    nb[r][c] = player
    rotate_quad_inplace(nb, q, d)
    return nb


def has_five(board: List[List[int]], player: int) -> bool:
    for seg in SEGMENTS:
        ok = True
        for r, c in seg:
            if board[r][c] != player:
                ok = False
                break
        if ok:
            return True
    return False


def empties(board: List[List[int]]) -> List[Tuple[int, int]]:
    out = []
    for r in range(6):
        row = board[r]
        for c in range(6):
            if row[c] == 0:
                out.append((r, c))
    return out


def legal_moves(board: List[List[int]]) -> List[Tuple[int, int, int, str]]:
    moves = []
    for r, c in empties(board):
        for q in range(4):
            moves.append((r, c, q, 'L'))
            moves.append((r, c, q, 'R'))
    return moves


# ---------- Evaluation ----------

def evaluate(board: List[List[int]]) -> int:
    my_win = has_five(board, 1)
    opp_win = has_five(board, 2)

    if my_win and not opp_win:
        return 10**9
    if opp_win and not my_win:
        return -10**9
    if my_win and opp_win:
        return 0

    score = 0

    # Cell weights
    for r in range(6):
        for c in range(6):
            v = board[r][c]
            if v == 1:
                score += CELL_WEIGHT[r][c]
            elif v == 2:
                score -= CELL_WEIGHT[r][c]

    # Segment pattern scores
    for seg in SEGMENTS:
        my_count = 0
        opp_count = 0
        for r, c in seg:
            v = board[r][c]
            if v == 1:
                my_count += 1
            elif v == 2:
                opp_count += 1

        if my_count and opp_count:
            continue
        if my_count:
            score += LINE_SCORE[my_count]
        elif opp_count:
            score -= LINE_SCORE[opp_count]

    return score


# ---------- Threat search ----------

def opponent_immediate_win_count(board: List[List[int]], limit: int = 1) -> int:
    """
    Number of immediate winning replies available to opponent (player 2).
    Stops early once count reaches limit.
    """
    count = 0
    for mv in legal_moves(board):
        nb = apply_move(board, mv, 2)
        opp_win = has_five(nb, 2)
        my_win = has_five(nb, 1)
        if opp_win and not my_win:
            count += 1
            if count >= limit:
                return count
    return count


def move_to_str(move: Tuple[int, int, int, str]) -> str:
    r, c, q, d = move
    return f"{r+1},{c+1},{q},{d}"


# ---------- Main policy ----------

def policy(you, opponent) -> str:
    board = to_board(you, opponent)
    moves = legal_moves(board)

    # Absolute legal fallback
    fallback = move_to_str(moves[0])

    scored_moves = []
    best_draw_move = None
    best_draw_score = -10**18

    # 1) Immediate win if available
    for mv in moves:
        nb = apply_move(board, mv, 1)
        my_win = has_five(nb, 1)
        opp_win = has_five(nb, 2)

        if my_win and not opp_win:
            return move_to_str(mv)

        sc = evaluate(nb)
        scored_moves.append((sc, mv, nb))

        # If both win, it's a draw; keep as possible emergency choice
        if my_win and opp_win and sc > best_draw_score:
            best_draw_score = sc
            best_draw_move = mv

    # 2) If opponent has an immediate threat, search all moves for safe defense
    threat_now = opponent_immediate_win_count(board, limit=1) > 0

    if threat_now:
        best_safe = None
        best_safe_score = -10**18

        best_least_bad = None
        best_least_bad_wins = 10**9
        best_least_bad_score = -10**18

        for sc, mv, nb in scored_moves:
            wins = opponent_immediate_win_count(nb, limit=999999)
            if wins == 0:
                if sc > best_safe_score:
                    best_safe_score = sc
                    best_safe = mv
            else:
                if wins < best_least_bad_wins or (wins == best_least_bad_wins and sc > best_least_bad_score):
                    best_least_bad_wins = wins
                    best_least_bad_score = sc
                    best_least_bad = mv

        if best_safe is not None:
            return move_to_str(best_safe)
        if best_draw_move is not None:
            return move_to_str(best_draw_move)
        if best_least_bad is not None:
            return move_to_str(best_least_bad)
        return fallback

    # 3) Otherwise, search promising moves and avoid giving immediate losses
    scored_moves.sort(key=lambda x: x[0], reverse=True)

    empty_count = len(empties(board))
    if empty_count >= 20:
        top_k = 20
    elif empty_count >= 12:
        top_k = 32
    else:
        top_k = len(scored_moves)

    best_move = None
    best_value = -10**18

    for sc, mv, nb in scored_moves[:top_k]:
        # Penalize moves that allow immediate opponent win
        opp_wins = opponent_immediate_win_count(nb, limit=2)
        if opp_wins >= 1:
            val = sc - 500000
        else:
            val = sc

        if val > best_value:
            best_value = val
            best_move = mv

    if best_move is not None:
        return move_to_str(best_move)

    if best_draw_move is not None:
        return move_to_str(best_draw_move)

    return fallback
