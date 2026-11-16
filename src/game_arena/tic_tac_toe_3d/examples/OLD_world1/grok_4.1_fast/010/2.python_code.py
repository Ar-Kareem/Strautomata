
import sys

sys.setrecursionlimit(10000)

def is_winner(board: list[list[list[int]]], player: int) -> bool:
    # Along x (fixed z, y)
    for i in range(3):
        for j in range(3):
            if all(board[i][j][k] == player for k in range(3)):
                return True
    # Along y (fixed z, x)
    for i in range(3):
        for k in range(3):
            if all(board[i][j][k] == player for j in range(3)):
                return True
    # Along z (fixed y, x)
    for j in range(3):
        for k in range(3):
            if all(board[i][j][k] == player for i in range(3)):
                return True
    # Diagonals in xy-planes (fixed z)
    for i in range(3):
        if all(board[i][j][j] == player for j in range(3)):
            return True
        if all(board[i][j][2 - j] == player for j in range(3)):
            return True
    # Diagonals in xz-planes (fixed y)
    for j in range(3):
        if all(board[i][j][i] == player for i in range(3)):
            return True
        if all(board[i][j][2 - i] == player for i in range(3)):
            return True
    # Diagonals in yz-planes (fixed x)
    for k in range(3):
        if all(board[i][i][k] == player for i in range(3)):
            return True
        if all(board[i][2 - i][k] == player for i in range(3)):
            return True
    # Space diagonals
    if all(board[i][i][i] == player for i in range(3)):
        return True
    if all(board[i][i][2 - i] == player for i in range(3)):
        return True
    if all(board[i][2 - i][i] == player for i in range(3)):
        return True
    if all(board[i][2 - i][2 - i] == player for i in range(3)):
        return True
    return False

def board_to_int(board: list[list[list[int]]]) -> int:
    state = 0
    for i in range(3):
        for j in range(3):
            for k in range(3):
                val = board[i][j][k]
                state = state * 3 + (val + 1)  # -1 -> 0, 0 -> 1, 1 -> 2
    return state

def get_moves(board: list[list[list[int]]]) -> list[tuple[int, int, int]]:
    moves = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    moves.sort(key=lambda m: abs(m[0] - 1) + abs(m[1] - 1) + abs(m[2] - 1))
    return moves

def minimax(board: list[list[list[int]]], player: int, alpha: int, beta: int, memo: dict) -> int:
    if is_winner(board, 1):
        return 1
    if is_winner(board, -1):
        return -1

    state = board_to_int(board)
    key = (state, player)
    if key in memo:
        return memo[key]

    moves = get_moves(board)
    if not moves:
        score = 0
    else:
        if player == 1:
            score = -2
            for i, j, k in moves:
                board[i][j][k] = 1
                if is_winner(board, 1):
                    val = 1
                else:
                    val = minimax(board, -1, alpha, beta, memo)
                board[i][j][k] = 0
                score = max(score, val)
                alpha = max(alpha, score)
                if alpha >= beta:
                    break
        else:
            score = 2
            for i, j, k in moves:
                board[i][j][k] = -1
                if is_winner(board, -1):
                    val = -1
                else:
                    val = minimax(board, 1, alpha, beta, memo)
                board[i][j][k] = 0
                score = min(score, val)
                beta = min(beta, score)
                if alpha >= beta:
                    break

    memo[key] = score
    return score

def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    memo: dict = {}
    best_score = -2
    best_move: tuple[int, int, int] | None = None
    moves = get_moves(board)
    for i, j, k in moves:
        board[i][j][k] = 1
        if is_winner(board, 1):
            val = 1
        else:
            next_moves = get_moves(board)
            if not next_moves:
                val = 0
            else:
                val = minimax(board, -1, -2, 2, memo)
        board[i][j][k] = 0
        if val > best_score:
            best_score = val
            best_move = (i, j, k)
            if best_score == 1:
                return best_move  # Early return on guaranteed win
    return best_move  # type: ignore
