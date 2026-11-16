
import numpy as np
import time

# Precompute all reachable squares in each of the 8 directions for every square
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]
SQUARE_DIRS = []
for r in range(6):
    for c in range(6):
        idx = r * 6 + c
        dirs = []
        for dr, dc in DIRECTIONS:
            squares = []
            nr, nc = r + dr, c + dc
            while 0 <= nr < 6 and 0 <= nc < 6:
                squares.append(nr * 6 + nc)
                nr += dr
                nc += dc
            dirs.append(squares)
        SQUARE_DIRS.append(dirs)


def get_moves(board, player):
    """Generate all legal moves for the given player (1 or 2)."""
    moves = []
    for i in range(36):
        if board[i] == player:
            from_idx = i
            for dir_squares in SQUARE_DIRS[from_idx]:
                for to_idx in dir_squares:
                    if board[to_idx] != 0:
                        break
                    # Simulate the amazon move
                    board[from_idx] = 0
                    board[to_idx] = player
                    # Generate arrow shots
                    for arrow_dir_squares in SQUARE_DIRS[to_idx]:
                        for arrow_idx in arrow_dir_squares:
                            if board[arrow_idx] != 0:
                                break
                            moves.append((from_idx, to_idx, arrow_idx))
                    # Restore the board
                    board[to_idx] = 0
                    board[from_idx] = player
    return moves


def count_moves(board, player):
    """Count the number of legal moves for the given player."""
    count = 0
    for i in range(36):
        if board[i] == player:
            from_idx = i
            for dir_squares in SQUARE_DIRS[from_idx]:
                for to_idx in dir_squares:
                    if board[to_idx] != 0:
                        break
                    board[from_idx] = 0
                    board[to_idx] = player
                    for arrow_dir_squares in SQUARE_DIRS[to_idx]:
                        for arrow_idx in arrow_dir_squares:
                            if board[arrow_idx] != 0:
                                break
                            count += 1
                    board[to_idx] = 0
                    board[from_idx] = player
    return count


def apply_move(board, move, player):
    """Return a new board after applying the given move."""
    from_idx, to_idx, arrow_idx = move
    new_board = board[:]  # shallow copy of the flat list
    new_board[from_idx] = 0
    new_board[to_idx] = player
    new_board[arrow_idx] = -1
    return new_board


def minimax(board, depth, alpha, beta, maximizing_player, player, opponent):
    """Alpha-beta minimax search."""
    if depth == 0:
        return count_moves(board, 1) - count_moves(board, 2)

    current_player = player if maximizing_player else opponent
    moves = get_moves(board, current_player)

    if not moves:
        # No legal moves: current player loses
        return -float('inf') if maximizing_player else float('inf')

    if maximizing_player:
        value = -float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_player)
            val = minimax(new_board, depth - 1, alpha, beta, False, player, opponent)
            if val > value:
                value = val
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        return value
    else:
        value = float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_player)
            val = minimax(new_board, depth - 1, alpha, beta, True, player, opponent)
            if val < value:
                value = val
            beta = min(beta, value)
            if alpha >= beta:
                break
        return value


def best_move_at_depth(board, depth):
    """Find the best move at the given search depth."""
    player = 1
    opponent = 2
    moves = get_moves(board, player)
    if not moves:
        return None

    best_val = -float('inf')
    best_move = None
    alpha = -float('inf')
    beta = float('inf')

    for move in moves:
        new_board = apply_move(board, move, player)
        val = minimax(new_board, depth - 1, alpha, beta, False, player, opponent)
        if val > best_val:
            best_val = val
            best_move = move
        alpha = max(alpha, best_val)

    return best_move


def policy(board):
    """Return the next move string in the required format."""
    # Convert the numpy board to a flat list of ints
    if isinstance(board, np.ndarray):
        board_flat = board.astype(int).flatten().tolist()
    else:
        board_flat = list(board)

    start_time = time.time()
    time_limit = 0.9
    best_move = None

    # Iterative deepening from depth 1 to 4
    for depth in range(1, 5):
        if time.time() - start_time > time_limit * 0.5:
            if depth > 1:
                break
        move = best_move_at_depth(board_flat, depth)
        if move is None:
            break
        best_move = move
        if time.time() - start_time > time_limit:
            break

    # Fallback to any legal move if search failed
    if best_move is None:
        moves = get_moves(board_flat, 1)
        if moves:
            best_move = moves[0]
        else:
            # Should never be called without a legal move, but return a dummy
            return "0,0:0,0:0,0"

    from_idx, to_idx, arrow_idx = best_move
    from_r, from_c = divmod(from_idx, 6)
    to_r, to_c = divmod(to_idx, 6)
    arr_r, arr_c = divmod(arrow_idx, 6)
    return f"{from_r},{from_c}:{to_r},{to_c}:{arr_r},{arr_c}"
