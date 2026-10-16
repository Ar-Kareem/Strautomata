
import time
import numpy as np

# Global time control
_START_TIME = 0
_TIME_LIMIT = 0.9
_NODES = 0
_CHECK_INTERVAL = 5000

class TimeoutException(Exception):
    pass

def reset_time():
    global _START_TIME, _NODES
    _START_TIME = time.time()
    _NODES = 0

def check_timeout():
    global _NODES
    _NODES += 1
    if _NODES % _CHECK_INTERVAL == 0:
        if time.time() - _START_TIME > _TIME_LIMIT:
            raise TimeoutException()

def generate_moves(board, color):
    """Generate all legal moves for the given color."""
    moves = []
    if color == 'b':
        forward = -1
        my_piece = 1
        opp_piece = 2
    else:
        forward = 1
        my_piece = 2
        opp_piece = 1

    pieces = np.argwhere(board == my_piece)
    for r, c in pieces:
        nr = r + forward
        if 0 <= nr <= 7:
            # straight forward (must be empty)
            if board[nr, c] == 0:
                moves.append(((r, c), (nr, c)))
            # diagonal left (empty or opponent)
            if c > 0:
                target = board[nr, c-1]
                if target == 0 or target == opp_piece:
                    moves.append(((r, c), (nr, c-1)))
            # diagonal right (empty or opponent)
            if c < 7:
                target = board[nr, c+1]
                if target == 0 or target == opp_piece:
                    moves.append(((r, c), (nr, c+1)))
    return moves

def apply_move(board, move, color):
    """Apply a move and return the new board state."""
    new_board = board.copy()
    (r1, c1), (r2, c2) = move
    new_board[r1, c1] = 0
    if color == 'b':
        new_board[r2, c2] = 1
    else:
        new_board[r2, c2] = 2
    return new_board

def move_priority(move, board, color):
    """Heuristic value of a move for move ordering (from perspective of 'color')."""
    (r1, c1), (r2, c2) = move
    if color == 'b':
        opp = 2
    else:
        opp = 1
    score = 0
    # Captures are highly prioritized
    if board[r2, c2] == opp:
        score += 1000
    # Advancement: prefer moves that get closer to goal
    if color == 'b':
        dist = r2  # distance to row 0
        score += (7 - dist) * 10
    else:
        dist = 7 - r2  # distance to row 7
        score += (7 - dist) * 10
    # Small bonus for central columns
    if c2 in (3, 4):
        score += 5
    return score

def check_winner(board, ai_color):
    """Return 1 if AI wins, -1 if AI loses, 0 otherwise."""
    if ai_color == 'b':
        my_piece = 1
        opp_piece = 2
        my_goal = 0
        opp_goal = 7
    else:
        my_piece = 2
        opp_piece = 1
        my_goal = 7
        opp_goal = 0

    if np.any(board[my_goal, :] == my_piece):
        return 1
    if np.any(board[opp_goal, :] == opp_piece):
        return -1
    if not np.any(board == opp_piece):
        return 1
    if not np.any(board == my_piece):
        return -1
    return 0

def evaluate(board, ai_color):
    """Heuristic evaluation of the board from the AI's perspective."""
    if ai_color == 'b':
        my_piece = 1
        opp_piece = 2
    else:
        my_piece = 2
        opp_piece = 1

    my_positions = board == my_piece
    opp_positions = board == opp_piece
    my_count = np.count_nonzero(my_positions)
    opp_count = np.count_nonzero(opp_positions)

    # Terminal checks (should be caught by check_winner, but safe fallback)
    if opp_count == 0:
        return 100000
    if my_count == 0:
        return -100000

    if ai_color == 'b':
        if np.any(board[0, :] == my_piece):
            return 100000
        if np.any(board[7, :] == opp_piece):
            return -100000
    else:
        if np.any(board[7, :] == my_piece):
            return 100000
        if np.any(board[0, :] == opp_piece):
            return -100000

    # Material
    score = 100 * (my_count - opp_count)

    # Advancement: distance to opponent's home row
    my_indices = np.argwhere(my_positions)
    opp_indices = np.argwhere(opp_positions)

    if ai_color == 'b':
        my_dist = np.sum(my_indices[:, 0])          # want to minimize row (closer to 0)
        opp_dist = np.sum(7 - opp_indices[:, 0])    # opponent wants to reach row 7
        score -= 2 * my_dist
        score += 2 * opp_dist
    else:
        my_dist = np.sum(7 - my_indices[:, 0])      # want to minimize distance to 7
        opp_dist = np.sum(opp_indices[:, 0])        # opponent wants to reach row 0
        score -= 2 * my_dist
        score += 2 * opp_dist

    # Center control
    center_cols = [3, 4]
    my_center = np.sum(my_positions[:, center_cols])
    opp_center = np.sum(opp_positions[:, center_cols])
    score += 10 * (my_center - opp_center)

    return score

def minimax(board, depth, alpha, beta, maximizing, current_color, ai_color):
    """Minimax with alpha-beta pruning and timeout check."""
    check_timeout()

    winner = check_winner(board, ai_color)
    if winner == 1:
        return 100000 + depth   # prefer faster win
    elif winner == -1:
        return -100000 - depth  # prefer slower loss

    if depth == 0:
        return evaluate(board, ai_color)

    moves = generate_moves(board, current_color)
    if not moves:
        # No legal moves -> current player loses
        if current_color == ai_color:
            return -100000 - depth
        else:
            return 100000 + depth

    # Move ordering
    moves = sorted(moves, key=lambda m: move_priority(m, board, current_color), reverse=True)

    opp_color = 'w' if current_color == 'b' else 'b'

    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_color)
            val = minimax(new_board, depth-1, alpha, beta, False, opp_color, ai_color)
            if val > max_eval:
                max_eval = val
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_color)
            val = minimax(new_board, depth-1, alpha, beta, True, opp_color, ai_color)
            if val < min_eval:
                min_eval = val
            beta = min(beta, val)
            if beta <= alpha:
                break
        return min_eval

def policy(me, opp, color):
    """Return the best legal move."""
    # Build board matrix: 1 = black, 2 = white
    board = np.zeros((8, 8), dtype=np.int8)
    if color == 'b':
        my_piece = 1
        opp_piece = 2
    else:
        my_piece = 2
        opp_piece = 1
    for r, c in me:
        board[r, c] = my_piece
    for r, c in opp:
        board[r, c] = opp_piece

    opp_color = 'w' if color == 'b' else 'b'
    moves = generate_moves(board, color)

    if not moves:
        # Should never happen if game is ongoing, but for safety
        return ((0, 0), (0, 0))

    # 1. Immediate winning move?
    for move in moves:
        if check_winner(apply_move(board, move, color), color) == 1:
            return move

    # 2. Iterative deepening search with time limit
    reset_time()
    best_move = moves[0]

    try:
        for depth in range(1, 20):
            if time.time() - _START_TIME > _TIME_LIMIT:
                break

            alpha = -float('inf')
            beta = float('inf')
            current_best = None

            ordered_moves = sorted(moves, key=lambda m: move_priority(m, board, color), reverse=True)
            for move in ordered_moves:
                new_board = apply_move(board, move, color)
                val = minimax(new_board, depth-1, alpha, beta, False, opp_color, color)
                if val > alpha:
                    alpha = val
                    current_best = move
                if alpha >= 100000:
                    break

            if current_best is not None:
                best_move = current_best
            # Stop if we found a forced win
            if alpha >= 100000:
                break

    except TimeoutException:
        pass

    return best_move
