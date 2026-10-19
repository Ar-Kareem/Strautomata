
from typing import List, Tuple

# Precompute all 49 winning lines in 3x3x3 tic tac toe.
LINES: List[List[Tuple[int, int, int]]] = []

# Straight lines along axes
for j in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for i in range(3)])
for i in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for j in range(3)])
for i in range(3):
    for j in range(3):
        LINES.append([(i, j, k) for k in range(3)])

# Diagonals in xy planes (fixed k)
for k in range(3):
    LINES.append([(d, d, k) for d in range(3)])
    LINES.append([(d, 2 - d, k) for d in range(3)])

# Diagonals in xz planes (fixed j)
for j in range(3):
    LINES.append([(d, j, d) for d in range(3)])
    LINES.append([(d, j, 2 - d) for d in range(3)])

# Diagonals in yz planes (fixed i)
for i in range(3):
    LINES.append([(i, d, d) for d in range(3)])
    LINES.append([(i, d, 2 - d) for d in range(3)])

# Space diagonals
LINES.append([(d, d, d) for d in range(3)])
LINES.append([(d, d, 2 - d) for d in range(3)])
LINES.append([(d, 2 - d, d) for d in range(3)])
LINES.append([(d, 2 - d, 2 - d) for d in range(3)])

CELL_TO_LINES = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            CELL_TO_LINES[(i, j, k)] = []
for idx, line in enumerate(LINES):
    for cell in line:
        CELL_TO_LINES[cell].append(idx)

# Positional preference: center > corners > face-centers/edges.
POSITION_WEIGHTS = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            c = (1 if i == 1 else 0) + (1 if j == 1 else 0) + (1 if k == 1 else 0)
            if c == 3:
                w = 9   # center
            elif c == 0:
                w = 6   # corners
            elif c == 2:
                w = 4   # edge-centers
            else:
                w = 3   # face-centers
            # Also reward participation in many winning lines.
            w += len(CELL_TO_LINES[(i, j, k)]) * 0.2
            POSITION_WEIGHTS[(i, j, k)] = w


def legal_moves(board: List[List[List[int]]]) -> List[Tuple[int, int, int]]:
    moves = []
    for i in range(3):
        for j in range(3):
            for k in range(3):
                if board[i][j][k] == 0:
                    moves.append((i, j, k))
    return moves


def winner(board: List[List[List[int]]]) -> int:
    for line in LINES:
        s = 0
        for i, j, k in line:
            s += board[i][j][k]
        if s == 3:
            return 1
        if s == -3:
            return -1
    return 0


def immediate_winning_moves(board: List[List[List[int]]], player: int) -> List[Tuple[int, int, int]]:
    wins = []
    for move in legal_moves(board):
        i, j, k = move
        board[i][j][k] = player
        if winner(board) == player:
            wins.append(move)
        board[i][j][k] = 0
    return wins


def evaluate(board: List[List[List[int]]]) -> float:
    w = winner(board)
    if w == 1:
        return 100000.0
    if w == -1:
        return -100000.0

    score = 0.0

    # Positional score
    for i in range(3):
        for j in range(3):
            for k in range(3):
                v = board[i][j][k]
                if v == 1:
                    score += POSITION_WEIGHTS[(i, j, k)]
                elif v == -1:
                    score -= POSITION_WEIGHTS[(i, j, k)]

    # Line-based score
    for line in LINES:
        vals = [board[i][j][k] for i, j, k in line]
        cnt1 = vals.count(1)
        cntm1 = vals.count(-1)
        cnt0 = vals.count(0)

        if cnt1 > 0 and cntm1 > 0:
            continue

        if cnt1 == 2 and cnt0 == 1:
            score += 120
        elif cnt1 == 1 and cnt0 == 2:
            score += 12

        if cntm1 == 2 and cnt0 == 1:
            score -= 140
        elif cntm1 == 1 and cnt0 == 2:
            score -= 14

    return score


def ordered_moves(board: List[List[List[int]]], player: int) -> List[Tuple[int, int, int]]:
    moves = legal_moves(board)

    def move_key(move):
        i, j, k = move
        base = POSITION_WEIGHTS[move]

        # Tactical bonuses
        bonus = 0.0

        # If move wins immediately, huge bonus
        board[i][j][k] = player
        if winner(board) == player:
            bonus += 10000.0
        board[i][j][k] = 0

        # If move blocks opponent immediate win, strong bonus
        board[i][j][k] = -player
        opp_wins_if_they_play_here = (winner(board) == -player)
        board[i][j][k] = 0
        if opp_wins_if_they_play_here:
            bonus += 5000.0

        # Prefer moves on many lines
        bonus += len(CELL_TO_LINES[move]) * 2.0

        return -(base + bonus)

    moves.sort(key=move_key)
    return moves


def minimax(board: List[List[List[int]]], depth: int, alpha: float, beta: float, player: int) -> float:
    w = winner(board)
    if w == 1:
        return 100000.0 + depth
    if w == -1:
        return -100000.0 - depth

    moves = legal_moves(board)
    if not moves:
        return 0.0
    if depth == 0:
        return evaluate(board)

    # Tactical pruning: immediate wins / forced blocks
    current_wins = immediate_winning_moves(board, player)
    if current_wins:
        return 100000.0 + depth if player == 1 else -100000.0 - depth

    opp_wins = immediate_winning_moves(board, -player)
    # If opponent has multiple immediate wins, usually losing.
    if len(opp_wins) >= 2:
        return -90000.0 if player == 1 else 90000.0

    if player == 1:
        value = float("-inf")
        for move in ordered_moves(board, player):
            i, j, k = move
            board[i][j][k] = 1
            val = minimax(board, depth - 1, alpha, beta, -1)
            board[i][j][k] = 0
            if val > value:
                value = val
            if value > alpha:
                alpha = value
            if alpha >= beta:
                break
        return value
    else:
        value = float("inf")
        for move in ordered_moves(board, player):
            i, j, k = move
            board[i][j][k] = -1
            val = minimax(board, depth - 1, alpha, beta, 1)
            board[i][j][k] = 0
            if val < value:
                value = val
            if value < beta:
                beta = value
            if alpha >= beta:
                break
        return value


def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    moves = legal_moves(board)
    if not moves:
        return (0, 0, 0)  # fallback; should not happen in valid play

    # 1. Immediate win
    wins = immediate_winning_moves(board, 1)
    if wins:
        return wins[0]

    # 2. Immediate block
    opp_wins = immediate_winning_moves(board, -1)
    if opp_wins:
        # If several exist, any legal move may still lose, but choose one of the threats to block.
        return opp_wins[0]

    # 3. Search depth based on game stage
    empties = len(moves)
    if empties >= 20:
        depth = 2
    elif empties >= 12:
        depth = 3
    elif empties >= 7:
        depth = 4
    else:
        depth = 5

    best_move = moves[0]
    best_value = float("-inf")

    for move in ordered_moves(board, 1):
        i, j, k = move
        board[i][j][k] = 1
        val = minimax(board, depth - 1, float("-inf"), float("inf"), -1)
        board[i][j][k] = 0
        if val > best_value:
            best_value = val
            best_move = move

    # Ensure legality
    i, j, k = best_move
    if 0 <= i < 3 and 0 <= j < 3 and 0 <= k < 3 and board[i][j][k] == 0:
        return best_move

    # Ultimate fallback: first legal move
    return moves[0]
