
import time
from math import inf

ROWS = 6
COLS = 7

# Preferred move order (center-first) for better pruning and play quality
MOVE_ORDER = [3, 2, 4, 1, 5, 0, 6]

# Heuristic weights
WIN_SCORE = 10_000_000
THREE_SCORE = 120
TWO_SCORE = 12
OPP_THREE_PENALTY = 140
CENTER_WEIGHT = 6

class _Timeout(Exception):
    pass

def policy(board: list[list[int]]) -> int:
    """
    Returns a legal column index [0..6] that is not full.
    board is a 6x7 grid with 0 empty, 1 us, -1 opponent.
    """
    start = time.time()
    # Keep a small safety margin
    time_limit = 0.95

    # Convert to fast indexable structure (list of lists already fine)
    # but ensure it's 6x7 to avoid crashes on malformed input.
    if not board or len(board) != ROWS or any(len(r) != COLS for r in board):
        # Fallback: choose first legal-like column from 0..6
        for c in range(COLS):
            return c
        return 0

    def time_left() -> float:
        return time_limit - (time.time() - start)

    def valid_moves(b):
        return [c for c in range(COLS) if b[0][c] == 0]

    def get_next_open_row(b, col):
        for r in range(ROWS - 1, -1, -1):
            if b[r][col] == 0:
                return r
        return None

    def make_move(b, col, player):
        r = get_next_open_row(b, col)
        if r is None:
            return None
        nb = [row[:] for row in b]
        nb[r][col] = player
        return nb

    def is_full(b):
        return all(b[0][c] != 0 for c in range(COLS))

    def check_winner(b, player):
        # Horizontal
        for r in range(ROWS):
            row = b[r]
            for c in range(COLS - 3):
                if row[c] == player and row[c+1] == player and row[c+2] == player and row[c+3] == player:
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                    return True
        # Diagonal down-right
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                    return True
        # Diagonal up-right
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                    return True
        return False

    def immediate_winning_moves(b, player):
        wins = []
        for c in valid_moves(b):
            nb = make_move(b, c, player)
            if nb is not None and check_winner(nb, player):
                wins.append(c)
        return wins

    def score_window(window, player):
        opp = -player
        pc = window.count(player)
        oc = window.count(opp)
        ec = window.count(0)
        if pc == 4:
            return WIN_SCORE
        if pc == 3 and ec == 1:
            return THREE_SCORE
        if pc == 2 and ec == 2:
            return TWO_SCORE
        if oc == 4:
            return -WIN_SCORE
        # Blocking opponent threats is important
        if oc == 3 and ec == 1:
            return -OPP_THREE_PENALTY
        return 0

    def evaluate(b, player):
        # If terminal, return huge score
        if check_winner(b, player):
            return WIN_SCORE
        if check_winner(b, -player):
            return -WIN_SCORE
        if is_full(b):
            return 0

        score = 0

        # Center column preference
        center_col = 3
        center_count = sum(1 for r in range(ROWS) if b[r][center_col] == player)
        score += center_count * CENTER_WEIGHT

        # Score all windows of 4
        # Horizontal windows
        for r in range(ROWS):
            for c in range(COLS - 3):
                window = [b[r][c+i] for i in range(4)]
                score += score_window(window, player)

        # Vertical windows
        for c in range(COLS):
            for r in range(ROWS - 3):
                window = [b[r+i][c] for i in range(4)]
                score += score_window(window, player)

        # Positive diagonal windows
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                window = [b[r+i][c+i] for i in range(4)]
                score += score_window(window, player)

        # Negative diagonal windows
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                window = [b[r-i][c+i] for i in range(4)]
                score += score_window(window, player)

        return score

    # Transposition table: key -> (searched_depth, value)
    # Key includes player to move because evaluation differs by side.
    tt = {}

    def board_key(b, player):
        # Compact, hashable representation
        return (player, tuple(cell for row in b for cell in row))

    def ordered_moves(b):
        vm = set(valid_moves(b))
        return [c for c in MOVE_ORDER if c in vm]

    def gives_opponent_immediate_win(b_after_our_move):
        # If opponent can win immediately, it's dangerous
        return len(immediate_winning_moves(b_after_our_move, -1)) > 0

    def negamax(b, depth, alpha, beta, player_to_move):
        # Time check
        if time_left() <= 0:
            raise _Timeout()

        k = board_key(b, player_to_move)
        if k in tt:
            d0, v0 = tt[k]
            if d0 >= depth:
                return v0

        # Terminal / depth limit
        if depth == 0 or is_full(b) or check_winner(b, 1) or check_winner(b, -1):
            v = evaluate(b, player_to_move)
            tt[k] = (depth, v)
            return v

        best = -inf

        for c in ordered_moves(b):
            nb = make_move(b, c, player_to_move)
            if nb is None:
                continue

            # Standard negamax recursion
            val = -negamax(nb, depth - 1, -beta, -alpha, -player_to_move)

            if val > best:
                best = val
            if best > alpha:
                alpha = best
            if alpha >= beta:
                break

        tt[k] = (depth, best)
        return best

    # --- Root decision logic (must return a legal move) ---
    vm = valid_moves(board)
    if not vm:
        return 0  # no legal moves; should not happen in normal play

    # 1) Immediate win
    wins = immediate_winning_moves(board, 1)
    if wins:
        # Prefer center-ish winning moves
        for c in MOVE_ORDER:
            if c in wins:
                return c
        return wins[0]

    # 2) Immediate block
    opp_wins = immediate_winning_moves(board, -1)
    if opp_wins:
        for c in MOVE_ORDER:
            if c in opp_wins and c in vm:
                return c
        # fallback
        return opp_wins[0] if opp_wins[0] in vm else vm[0]

    # 3) Avoid obviously losing (allowing immediate opponent win), if possible
    safe_moves = []
    for c in ordered_moves(board):
        nb = make_move(board, c, 1)
        if nb is None:
            continue
        if not gives_opponent_immediate_win(nb):
            safe_moves.append(c)
    if safe_moves:
        root_moves = safe_moves
    else:
        root_moves = ordered_moves(board)

    # 4) Iterative deepening alpha-beta search
    best_move = root_moves[0]
    best_val = -inf

    # Start with shallow search; go deeper while time allows
    max_depth = 9  # realistic under 1s in Python with pruning on 6x7
    for depth in range(1, max_depth + 1):
        if time_left() <= 0.02:
            break
        try:
            current_best_move = best_move
            current_best_val = -inf

            alpha = -inf
            beta = inf

            for c in root_moves:
                if time_left() <= 0:
                    raise _Timeout()
                nb = make_move(board, c, 1)
                if nb is None:
                    continue
                val = -negamax(nb, depth - 1, -beta, -alpha, -1)

                # Extra safety: strongly discourage moves that give an immediate win
                if gives_opponent_immediate_win(nb):
                    val -= 50_000

                if val > current_best_val:
                    current_best_val = val
                    current_best_move = c
                if val > alpha:
                    alpha = val

            # If we completed this depth, commit it
            best_move = current_best_move
            best_val = current_best_val

        except _Timeout:
            break

    # Final legality check
    if best_move not in vm:
        # Return first available move in preferred order
        for c in MOVE_ORDER:
            if c in vm:
                return c
        return vm[0]
    return best_move
