
from typing import List, Tuple
import math
import time

N = 4

# Precompute all winning lines for 4x4 tic tac toe:
# 4 rows, 4 cols, 2 diagonals
LINES = []

for r in range(N):
    LINES.append([(r, c) for c in range(N)])
for c in range(N):
    LINES.append([(r, c) for r in range(N)])
LINES.append([(i, i) for i in range(N)])
LINES.append([(i, N - 1 - i) for i in range(N)])

# Cell participation count in winning lines, useful for positional value
PARTICIPATION = [[0] * N for _ in range(N)]
for line in LINES:
    for r, c in line:
        PARTICIPATION[r][c] += 1

# Slight preference for center-ish cells on 4x4
POSITION_WEIGHT = [
    [3, 4, 4, 3],
    [4, 5, 5, 4],
    [4, 5, 5, 4],
    [3, 4, 4, 3],
]


def legal_moves(board: List[List[int]]) -> List[Tuple[int, int]]:
    return [(r, c) for r in range(N) for c in range(N) if board[r][c] == 0]


def check_winner(board: List[List[int]]) -> int:
    for line in LINES:
        s = sum(board[r][c] for r, c in line)
        if s == N:
            return 1
        if s == -N:
            return -1
    return 0


def is_full(board: List[List[int]]) -> bool:
    for r in range(N):
        for c in range(N):
            if board[r][c] == 0:
                return False
    return True


def immediate_winning_moves(board: List[List[int]], player: int) -> List[Tuple[int, int]]:
    wins = []
    for r, c in legal_moves(board):
        board[r][c] = player
        if check_winner(board) == player:
            wins.append((r, c))
        board[r][c] = 0
    return wins


def evaluate(board: List[List[int]]) -> int:
    winner = check_winner(board)
    if winner == 1:
        return 1_000_000
    if winner == -1:
        return -1_000_000

    score = 0

    # Line-based evaluation
    # Reward lines containing only us+empty, punish lines containing only opp+empty
    for line in LINES:
        vals = [board[r][c] for r, c in line]
        my_count = vals.count(1)
        opp_count = vals.count(-1)
        empty_count = vals.count(0)

        if opp_count == 0 and my_count > 0:
            # stronger reward for more marks in open line
            score += [0, 8, 40, 200, 0][my_count]
            if empty_count == 1 and my_count == 3:
                score += 500
        elif my_count == 0 and opp_count > 0:
            score -= [0, 8, 40, 200, 0][opp_count]
            if empty_count == 1 and opp_count == 3:
                score -= 600

    # Positional evaluation
    for r in range(N):
        for c in range(N):
            if board[r][c] == 1:
                score += POSITION_WEIGHT[r][c] + 2 * PARTICIPATION[r][c]
            elif board[r][c] == -1:
                score -= POSITION_WEIGHT[r][c] + 2 * PARTICIPATION[r][c]

    return score


def ordered_moves(board: List[List[int]], player: int) -> List[Tuple[int, int]]:
    moves = legal_moves(board)

    def move_key(move: Tuple[int, int]):
        r, c = move
        val = POSITION_WEIGHT[r][c] + 2 * PARTICIPATION[r][c]

        # Tactical priority
        board[r][c] = player
        win_now = (check_winner(board) == player)
        board[r][c] = 0

        board[r][c] = -player
        block_now = (check_winner(board) == -player)
        board[r][c] = 0

        return (
            2 if win_now else 1 if block_now else 0,
            val
        )

    moves.sort(key=move_key, reverse=True)
    return moves


def minimax(board: List[List[int]], depth: int, alpha: int, beta: int, player: int, deadline: float) -> int:
    if time.time() >= deadline:
        return evaluate(board)

    winner = check_winner(board)
    if winner != 0:
        return evaluate(board)
    if is_full(board):
        return 0
    if depth == 0:
        return evaluate(board)

    moves = ordered_moves(board, player)

    # Tactical shortcut: if current player has immediate win, take/evaluate it strongly
    wins = immediate_winning_moves(board, player)
    if wins:
        return 900_000 if player == 1 else -900_000

    if player == 1:
        best = -math.inf
        for r, c in moves:
            board[r][c] = 1
            val = minimax(board, depth - 1, alpha, beta, -1, deadline)
            board[r][c] = 0
            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if beta <= alpha:
                break
        return best
    else:
        best = math.inf
        for r, c in moves:
            board[r][c] = -1
            val = minimax(board, depth - 1, alpha, beta, 1, deadline)
            board[r][c] = 0
            if val < best:
                best = val
            if best < beta:
                beta = best
            if beta <= alpha:
                break
        return best


def policy(board: List[List[int]]) -> Tuple[int, int]:
    moves = legal_moves(board)
    if not moves:
        return (0, 0)  # Should never happen in a valid game, but ensures a tuple is returned.

    # 1. Immediate win
    wins = immediate_winning_moves(board, 1)
    if wins:
        return wins[0]

    # 2. Immediate block
    opp_wins = immediate_winning_moves(board, -1)
    if opp_wins:
        # If multiple blocking moves exist, choose the most valuable one
        opp_wins.sort(key=lambda mv: POSITION_WEIGHT[mv[0]][mv[1]] + 2 * PARTICIPATION[mv[0]][mv[1]], reverse=True)
        return opp_wins[0]

    empties = len(moves)

    # Iterative depth choice by game stage
    if empties >= 13:
        max_depth = 4
    elif empties >= 9:
        max_depth = 5
    elif empties >= 6:
        max_depth = 7
    else:
        max_depth = 10

    deadline = time.time() + 0.92

    best_move = None
    best_score = -math.inf

    candidate_moves = ordered_moves(board, 1)

    # Iterative deepening for better time robustness
    for depth in range(2, max_depth + 1):
        if time.time() >= deadline:
            break

        current_best_move = None
        current_best_score = -math.inf

        for r, c in candidate_moves:
            if time.time() >= deadline:
                break

            board[r][c] = 1
            score = minimax(board, depth - 1, -math.inf, math.inf, -1, deadline)
            board[r][c] = 0

            # Small tie-break using static move value
            score2 = score * 1000 + POSITION_WEIGHT[r][c] + 2 * PARTICIPATION[r][c]

            if score2 > current_best_score:
                current_best_score = score2
                current_best_move = (r, c)

        if current_best_move is not None:
            best_move = current_best_move
            best_score = current_best_score
            # Move ordering improvement for next iteration
            candidate_moves.sort(
                key=lambda mv: 1 if mv == best_move else 0,
                reverse=True
            )

    if best_move is not None and board[best_move[0]][best_move[1]] == 0:
        return best_move

    # Heuristic fallback
    legal = legal_moves(board)
    legal.sort(
        key=lambda mv: POSITION_WEIGHT[mv[0]][mv[1]] + 2 * PARTICIPATION[mv[0]][mv[1]],
        reverse=True
    )
    return legal[0]
