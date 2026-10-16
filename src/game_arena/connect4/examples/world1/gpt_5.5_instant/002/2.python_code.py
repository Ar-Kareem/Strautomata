
import math
import time

ROWS = 6
COLS = 7
CENTER_ORDER = [3, 2, 4, 1, 5, 0, 6]

def policy(board: list[list[int]]) -> int:
    start_time = time.time()
    time_limit = 0.92

    def legal_moves(b):
        return [c for c in CENTER_ORDER if b[0][c] == 0]

    def drop(b, col, player):
        nb = [row[:] for row in b]
        for r in range(ROWS - 1, -1, -1):
            if nb[r][col] == 0:
                nb[r][col] = player
                return nb, r
        return nb, -1

    def winning_move(b, player):
        # Horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if b[r][c] == player and b[r][c+1] == player and b[r][c+2] == player and b[r][c+3] == player:
                    return True
        # Vertical
        for c in range(COLS):
            for r in range(ROWS - 3):
                if b[r][c] == player and b[r+1][c] == player and b[r+2][c] == player and b[r+3][c] == player:
                    return True
        # Positive diagonal
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if b[r][c] == player and b[r+1][c+1] == player and b[r+2][c+2] == player and b[r+3][c+3] == player:
                    return True
        # Negative diagonal
        for r in range(3, ROWS):
            for c in range(COLS - 3):
                if b[r][c] == player and b[r-1][c+1] == player and b[r-2][c+2] == player and b[r-3][c+3] == player:
                    return True
        return False

    def is_terminal(b):
        return winning_move(b, 1) or winning_move(b, -1) or not any(b[0][c] == 0 for c in range(COLS))

    def count_immediate_wins(b, player):
        cnt = 0
        for c in legal_moves(b):
            nb, _ = drop(b, c, player)
            if winning_move(nb, player):
                cnt += 1
        return cnt

    def eval_window(window):
        my_count = window.count(1)
        opp_count = window.count(-1)
        empty_count = window.count(0)

        if my_count and opp_count:
            return 0

        score = 0
        if my_count == 4:
            score += 1000000
        elif my_count == 3 and empty_count == 1:
            score += 120
        elif my_count == 2 and empty_count == 2:
            score += 14
        elif my_count == 1 and empty_count == 3:
            score += 2

        if opp_count == 4:
            score -= 1000000
        elif opp_count == 3 and empty_count == 1:
            score -= 150
        elif opp_count == 2 and empty_count == 2:
            score -= 16
        elif opp_count == 1 and empty_count == 3:
            score -= 1

        return score

    def evaluate(b):
        if winning_move(b, 1):
            return 100000000
        if winning_move(b, -1):
            return -100000000

        score = 0

        # Center control is important in Connect 4.
        center_col = [b[r][3] for r in range(ROWS)]
        score += center_col.count(1) * 8
        score -= center_col.count(-1) * 8

        # Slight weighting by column centrality.
        weights = [3, 4, 5, 7, 5, 4, 3]
        for r in range(ROWS):
            for c in range(COLS):
                if b[r][c] == 1:
                    score += weights[c]
                elif b[r][c] == -1:
                    score -= weights[c]

        # Score all windows of length 4.
        for r in range(ROWS):
            for c in range(COLS - 3):
                score += eval_window([b[r][c+i] for i in range(4)])

        for c in range(COLS):
            for r in range(ROWS - 3):
                score += eval_window([b[r+i][c] for i in range(4)])

        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                score += eval_window([b[r+i][c+i] for i in range(4)])

        for r in range(3, ROWS):
            for c in range(COLS - 3):
                score += eval_window([b[r-i][c+i] for i in range(4)])

        # Reward creating multiple immediate threats and punish opponent forks.
        my_wins = count_immediate_wins(b, 1)
        opp_wins = count_immediate_wins(b, -1)
        if my_wins >= 2:
            score += 50000
        elif my_wins == 1:
            score += 800

        if opp_wins >= 2:
            score -= 70000
        elif opp_wins == 1:
            score -= 1000

        return score

    def move_is_safe(b, col):
        nb, _ = drop(b, col, 1)
        if winning_move(nb, 1):
            return True
        for oc in legal_moves(nb):
            ob, _ = drop(nb, oc, -1)
            if winning_move(ob, -1):
                return False
        return True

    def minimax(b, depth, alpha, beta, maximizing):
        if time.time() - start_time > time_limit:
            return evaluate(b), None

        term = is_terminal(b)
        if depth == 0 or term:
            return evaluate(b), None

        moves = legal_moves(b)
        if not moves:
            return 0, None

        if maximizing:
            best_val = -math.inf
            best_col = moves[0]
            for col in moves:
                nb, _ = drop(b, col, 1)
                if winning_move(nb, 1):
                    return 100000000 + depth, col
                val, _ = minimax(nb, depth - 1, alpha, beta, False)
                if val > best_val:
                    best_val = val
                    best_col = col
                alpha = max(alpha, best_val)
                if alpha >= beta:
                    break
            return best_val, best_col
        else:
            best_val = math.inf
            best_col = moves[0]
            for col in moves:
                nb, _ = drop(b, col, -1)
                if winning_move(nb, -1):
                    return -100000000 - depth, col
                val, _ = minimax(nb, depth - 1, alpha, beta, True)
                if val < best_val:
                    best_val = val
                    best_col = col
                beta = min(beta, best_val)
                if alpha >= beta:
                    break
            return best_val, best_col

    moves = legal_moves(board)
    if not moves:
        return 0

    # 1. Take an immediate win.
    for c in moves:
        nb, _ = drop(board, c, 1)
        if winning_move(nb, 1):
            return c

    # 2. Block opponent immediate win if present.
    opponent_winning_cols = []
    for c in moves:
        nb, _ = drop(board, c, -1)
        if winning_move(nb, -1):
            opponent_winning_cols.append(c)

    if len(opponent_winning_cols) == 1:
        return opponent_winning_cols[0]
    elif len(opponent_winning_cols) > 1:
        # Try to choose one that is legal and safest; if impossible, block a central one.
        safe_blocks = [c for c in opponent_winning_cols if move_is_safe(board, c)]
        if safe_blocks:
            return safe_blocks[0]
        return opponent_winning_cols[0]

    # 3. Prefer safe moves for search/root choice.
    safe_moves = [c for c in moves if move_is_safe(board, c)]
    candidate_moves = safe_moves if safe_moves else moves

    # 4. Iterative deepening. Usually depth 5-6 fits within 1 second.
    best_col = candidate_moves[0]
    best_score = -math.inf

    max_depth = 6
    filled = sum(1 for r in range(ROWS) for c in range(COLS) if board[r][c] != 0)
    if filled < 10:
        max_depth = 5
    if filled > 28:
        max_depth = 7

    for depth in range(1, max_depth + 1):
        if time.time() - start_time > time_limit:
            break

        local_best_col = best_col
        local_best_score = -math.inf

        for c in candidate_moves:
            if time.time() - start_time > time_limit:
                break
            nb, _ = drop(board, c, 1)
            score, _ = minimax(nb, depth - 1, -math.inf, math.inf, False)

            # Small root preference for center columns.
            score += (3 - abs(3 - c)) * 0.01

            if score > local_best_score:
                local_best_score = score
                local_best_col = c

        if time.time() - start_time <= time_limit:
            best_col = local_best_col
            best_score = local_best_score

    # 5. Avoid unsafe chosen move if there is a safe alternative.
    if best_col not in candidate_moves:
        best_col = candidate_moves[0]

    if not move_is_safe(board, best_col) and safe_moves:
        best_col = safe_moves[0]
        best_score = -math.inf
        for c in safe_moves:
            nb, _ = drop(board, c, 1)
            sc = evaluate(nb)
            if sc > best_score:
                best_score = sc
                best_col = c

    # Final legality guarantee.
    if best_col in moves and board[0][best_col] == 0:
        return int(best_col)

    for c in CENTER_ORDER:
        if board[0][c] == 0:
            return int(c)

    return 0
