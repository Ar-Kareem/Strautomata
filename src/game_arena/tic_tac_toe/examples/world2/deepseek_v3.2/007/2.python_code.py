
import math
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Returns the next move for the AI player (1) on a 4x4 board.
    Uses minimax with alpha-beta pruning and a depth-limited evaluation.
    """
    # First, check for immediate winning move
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = 1
                if get_winner(board) == 1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # Then, check for opponent's immediate winning move and block it
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = -1
                if get_winner(board) == -1:
                    board[r][c] = 0
                    return (r, c)
                board[r][c] = 0

    # Otherwise, run minimax with alpha-beta pruning to find the best move
    best_move = None
    best_score = -math.inf
    depth = 4  # Depth limit for search

    # Get all empty cells and order them by heuristic to improve pruning
    moves = get_available_moves(board)
    if not moves:
        return (0, 0)  # No moves left, should not happen

    # Order moves by a simple heuristic: center first, then others
    move_scores = []
    for (r, c) in moves:
        # Prefer center squares (the inner 2x2 area)
        center_score = (1.5 - abs(r - 1.5)) * (1.5 - abs(c - 1.5))
        move_scores.append((center_score, (r, c)))
    move_scores.sort(reverse=True)
    ordered_moves = [move for _, move in move_scores]

    for (r, c) in ordered_moves:
        board[r][c] = 1
        score = minimax(board, depth - 1, -math.inf, math.inf, False)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)

    if best_move is None:
        # Fallback: pick the first available move
        best_move = moves[0]

    return best_move


def get_winner(board: list[list[int]]) -> int:
    """
    Returns 1 if player 1 wins, -1 if player -1 wins, 0 otherwise.
    """
    # Check rows
    for r in range(4):
        if all(board[r][c] == 1 for c in range(4)):
            return 1
        if all(board[r][c] == -1 for c in range(4)):
            return -1

    # Check columns
    for c in range(4):
        if all(board[r][c] == 1 for r in range(4)):
            return 1
        if all(board[r][c] == -1 for r in range(4)):
            return -1

    # Check main diagonal
    if all(board[i][i] == 1 for i in range(4)):
        return 1
    if all(board[i][i] == -1 for i in range(4)):
        return -1

    # Check anti-diagonal
    if all(board[i][3 - i] == 1 for i in range(4)):
        return 1
    if all(board[i][3 - i] == -1 for i in range(4)):
        return -1

    return 0


def get_available_moves(board: list[list[int]]) -> list[tuple[int, int]]:
    """Return list of (row, col) for empty cells."""
    moves = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                moves.append((r, c))
    return moves


def evaluate(board: list[list[int]]) -> float:
    """
    Heuristic evaluation of the board for player 1.
    Positive is good for player 1, negative for player -1.
    """
    winner = get_winner(board)
    if winner == 1:
        return 1000
    if winner == -1:
        return -1000

    # Heuristic: score each line (row, column, diagonal) that is still winnable
    score = 0

    # Rows
    for r in range(4):
        our_count = sum(1 for c in range(4) if board[r][c] == 1)
        opp_count = sum(1 for c in range(4) if board[r][c] == -1)
        if our_count > 0 and opp_count == 0:
            score += our_count * our_count
        elif opp_count > 0 and our_count == 0:
            score -= opp_count * opp_count

    # Columns
    for c in range(4):
        our_count = sum(1 for r in range(4) if board[r][c] == 1)
        opp_count = sum(1 for r in range(4) if board[r][c] == -1)
        if our_count > 0 and opp_count == 0:
            score += our_count * our_count
        elif opp_count > 0 and our_count == 0:
            score -= opp_count * opp_count

    # Main diagonal
    our_count = sum(1 for i in range(4) if board[i][i] == 1)
    opp_count = sum(1 for i in range(4) if board[i][i] == -1)
    if our_count > 0 and opp_count == 0:
        score += our_count * our_count
    elif opp_count > 0 and our_count == 0:
        score -= opp_count * opp_count

    # Anti-diagonal
    our_count = sum(1 for i in range(4) if board[i][3 - i] == 1)
    opp_count = sum(1 for i in range(4) if board[i][3 - i] == -1)
    if our_count > 0 and opp_count == 0:
        score += our_count * our_count
    elif opp_count > 0 and our_count == 0:
        score -= opp_count * opp_count

    # Slight bonus for center squares (inner 2x2)
    center_bonus = 0.1
    for r in (1, 2):
        for c in (1, 2):
            if board[r][c] == 1:
                score += center_bonus
            elif board[r][c] == -1:
                score -= center_bonus

    return score


def minimax(board: list[list[int]], depth: int, alpha: float, beta: float, maximizing_player: bool) -> float:
    """
    Minimax with alpha-beta pruning.
    Returns the evaluation score for the current board state.
    """
    winner = get_winner(board)
    if winner != 0:
        return evaluate(board)

    if depth == 0:
        return evaluate(board)

    moves = get_available_moves(board)
    if not moves:
        return 0  # Draw

    if maximizing_player:
        max_eval = -math.inf
        for (r, c) in moves:
            board[r][c] = 1
            eval_score = minimax(board, depth - 1, alpha, beta, False)
            board[r][c] = 0
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        for (r, c) in moves:
            board[r][c] = -1
            eval_score = minimax(board, depth - 1, alpha, beta, True)
            board[r][c] = 0
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
