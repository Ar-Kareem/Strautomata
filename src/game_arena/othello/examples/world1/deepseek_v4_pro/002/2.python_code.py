
import numpy as np
import time

# Direction vectors for the 8 possible directions
DIRECTIONS = [(-1, -1), (-1, 0), (-1, 1),
              (0, -1),           (0, 1),
              (1, -1), (1, 0), (1, 1)]

# Positional weights (classic Othello heuristic)
WEIGHTS = np.array([
    [100, -20, 10,  5,  5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10,  -2, -1, -1, -1, -1,  -2,  10],
    [5,   -2, -1,  0,  0, -1,  -2,   5],
    [5,   -2, -1,  0,  0, -1,  -2,   5],
    [10,  -2, -1, -1, -1, -1,  -2,  10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10,  5,  5, 10, -20, 100]
])

class TimeoutException(Exception):
    """Raised when the search time exceeds the limit."""
    pass

def get_legal_moves(you, opponent):
    """Return a list of legal moves for the player represented by 'you'."""
    moves = []
    board = you * 1 + opponent * -1  # 1 = you, -1 = opponent, 0 = empty
    for r in range(8):
        for c in range(8):
            if board[r, c] != 0:
                continue
            # Check all 8 directions
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if not (0 <= nr < 8 and 0 <= nc < 8):
                    continue
                if board[nr, nc] != -1:
                    continue
                # Found an adjacent opponent piece; follow the line
                flips = [(nr, nc)]
                nr += dr
                nc += dc
                while 0 <= nr < 8 and 0 <= nc < 8:
                    if board[nr, nc] == 0:
                        flips = []
                        break
                    if board[nr, nc] == 1:
                        break
                    if board[nr, nc] == -1:
                        flips.append((nr, nc))
                    nr += dr
                    nc += dc
                else:
                    flips = []  # went out of bounds
                if flips:
                    moves.append((r, c))
                    break  # move is legal, no need to check other directions
    return moves

def make_move(you, opponent, move):
    """Apply a move and return the new (you, opponent) boards."""
    r, c = move
    new_you = you.copy()
    new_opponent = opponent.copy()
    new_you[r, c] = 1
    board = new_you * 1 + new_opponent * -1
    for dr, dc in DIRECTIONS:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < 8 and 0 <= nc < 8):
            continue
        if board[nr, nc] != -1:
            continue
        flips = [(nr, nc)]
        nr += dr
        nc += dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            if board[nr, nc] == 0:
                flips = []
                break
            if board[nr, nc] == 1:
                break
            if board[nr, nc] == -1:
                flips.append((nr, nc))
            nr += dr
            nc += dc
        else:
            flips = []
        for fr, fc in flips:
            new_opponent[fr, fc] = 0
            new_you[fr, fc] = 1
    return new_you, new_opponent

def evaluate(you, opponent):
    """Evaluate the board from the perspective of 'you'."""
    total_discs = np.sum(you) + np.sum(opponent)
    empty = 64 - total_discs

    # Game stage based on remaining empty squares
    if empty > 40:
        # Early game: mobility and positional
        mobility_weight = 10
        positional_weight = 1
        disc_weight = 0
    elif empty > 20:
        # Mid game
        mobility_weight = 5
        positional_weight = 2
        disc_weight = 1
    else:
        # Late game: disc count dominates
        mobility_weight = 0
        positional_weight = 1
        disc_weight = 10

    # Positional score
    pos_score = np.sum(WEIGHTS * you) - np.sum(WEIGHTS * opponent)

    # Mobility
    your_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    mob_score = your_moves - opp_moves

    # Disc count
    disc_score = np.sum(you) - np.sum(opponent)

    return (pos_score * positional_weight +
            mob_score * mobility_weight +
            disc_score * disc_weight)

def quick_eval(you, opponent):
    """Fast positional evaluation for move ordering."""
    return np.sum(WEIGHTS * you) - np.sum(WEIGHTS * opponent)

def alphabeta(you, opponent, depth, alpha, beta, maximizing, start_time, time_limit):
    """Alpha-beta search with time check."""
    if time.time() - start_time > time_limit:
        raise TimeoutException()

    if depth == 0:
        return evaluate(you, opponent), None

    if maximizing:
        moves = get_legal_moves(you, opponent)
        if not moves:
            # No legal moves for 'you' – pass turn
            opp_moves = get_legal_moves(opponent, you)
            if not opp_moves:
                return evaluate(you, opponent), None  # Game over
            return alphabeta(you, opponent, depth, alpha, beta, False, start_time, time_limit)

        # Sort moves by quick evaluation (best first)
        moves.sort(key=lambda m: quick_eval(*make_move(you, opponent, m)), reverse=True)
        best_move = None
        for move in moves:
            new_you, new_opp = make_move(you, opponent, move)
            val, _ = alphabeta(new_opp, new_you, depth - 1, alpha, beta, False, start_time, time_limit)
            if val > alpha:
                alpha = val
                best_move = move
            if alpha >= beta:
                break
        return alpha, best_move
    else:
        moves = get_legal_moves(opponent, you)
        if not moves:
            your_moves = get_legal_moves(you, opponent)
            if not your_moves:
                return evaluate(you, opponent), None  # Game over
            return alphabeta(you, opponent, depth, alpha, beta, True, start_time, time_limit)

        # Sort moves from opponent's perspective (best for opponent first)
        moves.sort(key=lambda m: quick_eval(*make_move(opponent, you, m)), reverse=True)
        best_move = None
        for move in moves:
            new_opp, new_you = make_move(opponent, you, move)
            val, _ = alphabeta(new_you, new_opp, depth - 1, alpha, beta, True, start_time, time_limit)
            if val < beta:
                beta = val
                best_move = move
            if alpha >= beta:
                break
        return beta, best_move

def move_to_str(move):
    """Convert (r, c) move to algebraic notation like 'd3'."""
    if move is None:
        return "pass"
    r, c = move
    return f"{chr(c + ord('a'))}{r + 1}"

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Return the best move for the current player."""
    start_time = time.time()
    time_limit = 0.9  # seconds, leave a small margin

    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"

    best_move = legal_moves[0]  # fallback in case of timeout before any search completes
    try:
        for depth in range(1, 100):
            alpha = -float('inf')
            beta = float('inf')
            val, move = alphabeta(you, opponent, depth, alpha, beta, True, start_time, time_limit)
            if move is not None:
                best_move = move
    except TimeoutException:
        pass  # use the best move from the deepest completed search

    return move_to_str(best_move)
