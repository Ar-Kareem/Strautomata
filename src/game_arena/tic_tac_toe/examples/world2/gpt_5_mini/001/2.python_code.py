
from typing import List, Tuple, Optional, Dict

# 4x4 Tic Tac Toe policy
# board: list[list[int]] with 0 empty, 1 = us, -1 = opponent
# returns (row, col)

LINES = []
# Precompute all winning lines for 4x4: 4 rows, 4 cols, 2 diagonals
for r in range(4):
    LINES.append([(r, c) for c in range(4)])
for c in range(4):
    LINES.append([(r, c) for r in range(4)])
LINES.append([(i, i) for i in range(4)])
LINES.append([(i, 3 - i) for i in range(4)])

def check_winner(board: List[List[int]]) -> int:
    # returns 1 if we win, -1 if opponent wins, 0 otherwise
    for line in LINES:
        s = sum(board[r][c] for (r, c) in line)
        if s == 4:
            return 1
        if s == -4:
            return -1
    return 0

def is_full(board: List[List[int]]) -> bool:
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                return False
    return True

def heuristic(board: List[List[int]]) -> int:
    # Heuristic based on potential lines. Strongly favors lines with more marks.
    score = 0
    for line in LINES:
        vals = [board[r][c] for (r, c) in line]
        if 1 in vals and -1 in vals:
            continue
        count_us = vals.count(1)
        count_op = vals.count(-1)
        if count_us > 0:
            # weight grows exponentially with more in-line
            score += 10 ** count_us
        elif count_op > 0:
            score -= 10 ** count_op
    # small center preference (positions near center)
    center_weight = [
        [1, 2, 2, 1],
        [2, 3, 3, 2],
        [2, 3, 3, 2],
        [1, 2, 2, 1]
    ]
    for r in range(4):
        for c in range(4):
            if board[r][c] == 1:
                score += center_weight[r][c]
            elif board[r][c] == -1:
                score -= center_weight[r][c]
    return score

def legal_moves(board: List[List[int]]) -> List[Tuple[int,int]]:
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves

def board_to_key(board: List[List[int]]) -> Tuple[int, ...]:
    return tuple(board[r][c] for r in range(4) for c in range(4))

def minimax(board: List[List[int]], player: int, depth: int, alpha: int, beta: int,
            memo: Dict, allow_full_search: bool) -> Tuple[int, Optional[Tuple[int,int]]]:
    # Returns (score, move)
    winner = check_winner(board)
    if winner != 0:
        return (10**6 * winner, None)  # huge positive for win, negative for loss
    if is_full(board):
        return (0, None)
    if depth == 0:
        return (heuristic(board), None)

    key = (board_to_key(board), player, depth)
    if key in memo:
        return memo[key]

    moves = legal_moves(board)
    best_move = None

    if player == 1:
        value = -10**9
        for (r, c) in moves:
            board[r][c] = player
            # If allow_full_search is False, but few empties remain we can go deeper by depth-1
            sc, _ = minimax(board, -player, depth - 1, alpha, beta, memo, allow_full_search)
            board[r][c] = 0
            if sc > value:
                value = sc
                best_move = (r, c)
            alpha = max(alpha, value)
            if alpha >= beta:
                break
    else:
        value = 10**9
        for (r, c) in moves:
            board[r][c] = player
            sc, _ = minimax(board, -player, depth - 1, alpha, beta, memo, allow_full_search)
            board[r][c] = 0
            if sc < value:
                value = sc
                best_move = (r, c)
            beta = min(beta, value)
            if beta <= alpha:
                break

    memo[key] = (value, best_move)
    return memo[key]

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Defensive copy not strictly necessary, but avoid mutating input.
    b = [row[:] for row in board]
    moves = legal_moves(b)
    if not moves:
        return (0, 0)

    # 1) Immediate win?
    for (r, c) in moves:
        b[r][c] = 1
        if check_winner(b) == 1:
            return (r, c)
        b[r][c] = 0

    # 2) Immediate block: if opponent can win next move, block it
    opponent_wins = []
    for (r, c) in moves:
        b[r][c] = -1
        if check_winner(b) == -1:
            opponent_wins.append((r, c))
        b[r][c] = 0
    if len(opponent_wins) == 1:
        return opponent_wins[0]
    # If multiple immediate threats (fork), fall through to search

    # 3) Minimax with alpha-beta and memoization
    empties = len(moves)
    # If near end, search fully; else limit depth to keep fast
    if empties <= 8:
        depth = empties  # search to terminal
        allow_full_search = True
    else:
        depth = 6  # modest depth for speed
        allow_full_search = False

    memo = {}
    score, move = minimax(b, 1, depth, -10**9, 10**9, memo, allow_full_search)
    if move is not None:
        return move

    # fallback: pick center-ish or first available
    preferred = sorted(moves, key=lambda rc: (-(2 - abs(rc[0]-1.5)) - abs(rc[1]-1.5)))
    return preferred[0]
