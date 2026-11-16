
import numpy as np
import math

def evaluate_board(board: list[list[int]], player: int) -> float:
    """
    Heuristic evaluation of the board from the perspective of 'player'.
    Positive score is good for player, negative is good for opponent.
    """
    opponent = -player
    score = 0.0

    lines = []

    # Rows and columns
    for i in range(4):
        lines.append([board[i][j] for j in range(4)])
        lines.append([board[j][i] for j in range(4)])

    # Diagonals
    lines.append([board[i][i] for i in range(4)])
    lines.append([board[i][3 - i] for i in range(4)])

    # All corners and center 2x2
    corners = [board[0][0], board[0][3], board[3][0], board[3][3]]
    center = [board[1][1], board[1][2], board[2][1], board[2][2]]
    
    for line in lines:
        player_count = line.count(player)
        opponent_count = line.count(opponent)
        empty_count = line.count(0)

        if opponent_count == 0:
            # Potential for player
            if player_count == 3:
                score += 100
            elif player_count == 2:
                score += 10
            elif player_count == 1:
                score += 1
        if player_count == 0:
            # Potential for opponent (we want to block)
            if opponent_count == 3:
                score -= 100  # Blocking is urgent
            elif opponent_count == 2:
                score -= 10
            elif opponent_count == 1:
                score -= 1
        if player_count > 0 and opponent_count > 0:
            # Mixed line, dead for both
            pass

    # Slight bonus for controlling center/corners in early game
    for cell in corners:
        if cell == player:
            score += 3
        elif cell == opponent:
            score -= 3
    for cell in center:
        if cell == player:
            score += 2
        elif cell == opponent:
            score -= 2

    return score


def is_terminal(board: list[list[int]]) -> bool:
    """Check if the game is over (win or draw)."""
    lines = []
    for i in range(4):
        lines.append([board[i][j] for j in range(4)])
        lines.append([board[j][i] for j in range(4)])
    lines.append([board[i][i] for i in range(4)])
    lines.append([board[i][3 - i] for i in range(4)])

    for line in lines:
        if line.count(1) == 4 or line.count(-1) == 4:
            return True

    # No empty cells
    for row in board:
        if 0 in row:
            return False
    return True


def minimax(board: list[list[int]], depth: int, alpha: float, beta: float, maximizing: bool, player: int) -> float:
    """
    Minimax with alpha-beta pruning.
    maximizing = True if current move is for 'player'.
    """
    if depth == 0 or is_terminal(board):
        return evaluate_board(board, player)

    opponent = -player

    if maximizing:
        max_eval = -math.inf
        moves = get_empty_cells(board)
        # Order moves heuristically (center/corners first)
        moves = order_moves(board, moves, player)
        for (r, c) in moves:
            board[r][c] = player
            eval_val = minimax(board, depth - 1, alpha, beta, False, player)
            board[r][c] = 0
            max_eval = max(max_eval, eval_val)
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = math.inf
        moves = get_empty_cells(board)
        moves = order_moves(board, moves, opponent)
        for (r, c) in moves:
            board[r][c] = opponent
            eval_val = minimax(board, depth - 1, alpha, beta, True, player)
            board[r][c] = 0
            min_eval = min(min_eval, eval_val)
            beta = min(beta, eval_val)
            if beta <= alpha:
                break
        return min_eval


def get_empty_cells(board: list[list[int]]) -> list[tuple[int, int]]:
    """Return list of empty cell coordinates."""
    empty = []
    for i in range(4):
        for j in range(4):
            if board[i][j] == 0:
                empty.append((i, j))
    return empty


def order_moves(board: list[list[int]], moves: list[tuple[int, int]], player: int) -> list[tuple[int, int]]:
    """
    Simple move ordering: immediate wins, then blocks, then center/corners.
    """
    opponent = -player

    def move_score(move):
        r, c = move
        # Check instant win
        board[r][c] = player
        if check_win(board, player):
            board[r][c] = 0
            return 1000
        board[r][c] = 0

        # Check block opponent win
        board[r][c] = opponent
        if check_win(board, opponent):
            board[r][c] = 0
            return 900
        board[r][c] = 0

        # Positional score
        pos_score = 0
        if (r, c) in [(0, 0), (0, 3), (3, 0), (3, 3)]:
            pos_score = 3
        elif (r, c) in [(1, 1), (1, 2), (2, 1), (2, 2)]:
            pos_score = 2
        return pos_score

    return sorted(moves, key=move_score, reverse=True)


def check_win(board: list[list[int]], player: int) -> bool:
    lines = []
    for i in range(4):
        lines.append([board[i][j] for j in range(4)])
        lines.append([board[j][i] for j in range(4)])
    lines.append([board[i][i] for i in range(4)])
    lines.append([board[i][3 - i] for i in range(4)])
    for line in lines:
        if line.count(player) == 4:
            return True
    return False


def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    Main policy: returns best move for player '1'.
    """
    empty = get_empty_cells(board)

    # If board empty, take center
    if len(empty) == 16:
        return (1, 1)

    # Check immediate win
    for (r, c) in empty:
        board[r][c] = 1
        if check_win(board, 1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Check immediate block
    for (r, c) in empty:
        board[r][c] = -1
        if check_win(board, -1):
            board[r][c] = 0
            return (r, c)
        board[r][c] = 0

    # Use iterative deepening / fixed depth search
    best_move = empty[0]
    best_score = -math.inf

    # Dynamic depth based on remaining moves
    remaining = len(empty)
    if remaining > 10:
        depth = 3
    elif remaining > 6:
        depth = 4
    else:
        depth = 6  # Can go deeper toward endgame

    # Order moves for root
    moves = order_moves(board, empty, 1)

    for (r, c) in moves:
        board[r][c] = 1
        score = minimax(board, depth - 1, -math.inf, math.inf, False, 1)
        board[r][c] = 0
        if score > best_score:
            best_score = score
            best_move = (r, c)

    return best_move
