
import numpy as np

def policy(you, opponent) -> str:
    # Convert inputs to numpy arrays
    you = np.array(you)
    opponent = np.array(opponent)
    board = np.zeros((6, 6), dtype=int)
    board[you == 1] = 1
    board[opponent == 1] = 2

    # Quadrant definitions (0-indexed rows and cols)
    quad_ranges = [
        (slice(0, 3), slice(0, 3)),  # quad 0
        (slice(0, 3), slice(3, 6)),  # quad 1
        (slice(3, 6), slice(0, 3)),  # quad 2
        (slice(3, 6), slice(3, 6)),  # quad 3
    ]

    # Direction mapping for rotation
    def rotate_block(block, direction):
        if direction == 'R':
            return np.rot90(block, k=3)  # 90 degrees clockwise
        elif direction == 'L':
            return np.rot90(block, k=1)  # 90 degrees anticlockwise

    # Check if a player has 5 in a row
    def has_won(state, player):
        # Check rows, cols, diagonals
        b = (state == player)
        for r in range(6):
            for c in range(2):
                if np.all(b[r, c:c+5]):
                    return True
        for c in range(6):
            for r in range(2):
                if np.all(b[r:r+5, c]):
                    return True
        # Diagonals
        for r in range(2):
            for c in range(2):
                if np.all([b[r+i, c+i] for i in range(5)]):
                    return True
        for r in range(2):
            for c in range(4, 6):
                if np.all([b[r+i, c-i] for i in range(5)]):
                    return True
        return False

    # Evaluate board heuristic (higher = better for us)
    def evaluate(state):
        score = 0
        # Center control bonus
        center = [(2,2), (2,3), (3,2), (3,3)]
        for r, c in center:
            if state[r, c] == 1:
                score += 2
        # Line evaluation: reward 2/3/4 in a row, penalize opponent
        for length in [2, 3, 4]:
            my_count = count_n_in_a_row(state, 1, length)
            opp_count = count_n_in_a_row(state, 2, length)
            score += length * length * my_count
            score -= 1.5 * length * length * opp_count
        return score

    # Count sequences of exactly `length` (with room to extend) for a player
    def count_n_in_a_row(state, player, length):
        count = 0
        b = (state == player)
        empty = (state == 0)
        # Check horizontal
        for r in range(6):
            for c in range(6 - length + 1):
                window = b[r, c:c+length]
                if np.all(window):
                    # Check if has empty adjacent to extend
                    left_ok = (c > 0) and empty[r, c-1]
                    right_ok = (c + length < 6) and empty[r, c + length]
                    if left_ok or right_ok:
                        count += 1
        # Vertical
        for c in range(6):
            for r in range(6 - length + 1):
                window = b[r:r+length, c]
                if np.all(window):
                    up_ok = (r > 0) and empty[r-1, c]
                    down_ok = (r + length < 6) and empty[r + length, c]
                    if up_ok or down_ok:
                        count += 1
        # Diagonals
        for r in range(6 - length + 1):
            for c in range(6 - length + 1):
                diag1 = [b[r+i, c+i] for i in range(length)]
                if all(diag1):
                    left_ok = (r > 0 and c > 0) and empty[r-1, c-1]
                    right_ok = (r+length < 6 and c+length < 6) and empty[r+length, c+length]
                    if left_ok or right_ok:
                        count += 1
        for r in range(6 - length + 1):
            for c in range(length - 1, 6):
                diag2 = [b[r+i, c-i] for i in range(length)]
                if all(diag2):
                    left_ok = (r > 0 and c < 5) and empty[r-1, c+1]
                    right_ok = (r+length < 6 and c-length >= 0) and empty[r+length, c-length]
                    if left_ok or right_ok:
                        count += 1
        return count

    # Apply a move to a state and return new state
    def make_move(state, row, col, quad, direction):
        new_state = state.copy()
        # Place move
        if new_state[row, col] != 0:
            return None  # invalid
        new_state[row, col] = 1

        # Rotate quadrant
        r_slice, c_slice = quad_ranges[quad]
        block = new_state[r_slice, c_slice].copy()
        rotated = rotate_block(block, direction)
        new_state[r_slice, c_slice] = rotated

        # After rotation, some of your pieces might have moved
        # But opponent pieces also move
        return new_state

    # Get all legal moves
    def get_legal_moves(state):
        moves = []
        for r in range(6):
            for c in range(6):
                if state[r, c] == 0:
                    for q in range(4):
                        for d in ['L', 'R']:
                            moves.append((r, c, q, d))
        return moves

    # Check if a move leads to immediate win
    def is_winning_move(state, row, col, quad, direction):
        new_state = make_move(state, row, col, quad, direction)
        if new_state is None:
            return False
        return has_won(new_state, 1)

    # Minimax with alpha-beta pruning (2-ply)
    def minimax(state, depth, alpha, beta, maximizing):
        if depth == 0:
            return evaluate(state)

        moves = get_legal_moves(state)
        if maximizing:
            max_eval = -np.inf
            for r, c, q, d in moves:
                new_state = make_move(state, r, c, q, d)
                if new_state is None:
                    continue
                # Simulate opponent moves in next depth
                if has_won(new_state, 1):
                    return np.inf
                if has_won(new_state, 2):
                    continue  # avoid losing moves
                eval = minimax(new_state, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = np.inf
            # Simulate opponent's optimal moves
            opp_state = state.copy()
            opp_state[opp_state == 1] = -1  # swap roles
            opp_state[opp_state == 2] = 1
            opp_state[opp_state == -1] = 2
            moves = get_legal_moves(opp_state)
            for r, c, q, d in moves:
                new_state = make_move(opp_state, r, c, q, d)
                if new_state is None:
                    continue
                if has_won(new_state, 2):
                    return -np.inf  # opponent wins
                # Switch back
                rev_state = new_state.copy()
                rev_state[rev_state == 2] = -1
                rev_state[rev_state == 1] = 2
                rev_state[rev_state == -1] = 1
                eval = minimax(rev_state, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval if min_eval != np.inf else 0

    # Try to find a winning move first
    legal_moves = get_legal_moves(board)
    best_move = None
    best_score = -np.inf

    for move in legal_moves:
        r, c, q, d = move
        if is_winning_move(board, r, c, q, d):
            return f"{r+1},{c+1},{q},{d}"

    # Otherwise, search with 2-ply minimax
    for move in legal_moves:
        r, c, q, d = move
        new_state = make_move(board, r, c, q, d)
        if new_state is None:
            continue
        if has_won(new_state, 2):  # avoids losing move
            continue
        score = minimax(new_state, 1, -np.inf, np.inf, False)  # look 2 plies ahead
        if score > best_score:
            best_score = score
            best_move = move

    if best_move is None:
        # Fallback: pick first legal move
        r, c, q, d = legal_moves[0]
        return f"{r+1},{c+1},{q},{d}"

    r, c, q, d = best_move
    return f"{r+1},{c+1},{q},{d}"
