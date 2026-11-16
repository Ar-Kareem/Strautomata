
import numpy as np
import time
from collections import deque

# Directions for 8-way movement
DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1),
              (1, 1), (1, -1), (-1, 1), (-1, -1)]

def policy(board) -> str:
    start_time = time.time()
    best_move = None
    depth = 1

    # Get all legal moves for the current player
    legal_moves = get_legal_moves(board)

    if not legal_moves:
        # Shouldn't happen as per problem statement, but handle gracefully
        return random_legal_move(board)

    # Iterative deepening with time management
    while time.time() - start_time < 0.9:  # Leave 0.1s buffer
        try:
            _, move = minimax(board, depth, -float('inf'), float('inf'), True, start_time)
            if move:
                best_move = move
            depth += 1
        except:
            break

    # If no move found from search (shouldn't happen), return random legal move
    return best_move if best_move else random_legal_move(board)

def minimax(board, depth, alpha, beta, maximizing_player, start_time):
    if time.time() - start_time > 0.95:  # Time's up
        raise Exception("Time limit reached")

    if depth == 0:
        return evaluate_board(board), None

    legal_moves = get_legal_moves(board)
    if not legal_moves:
        # Game over - no legal moves means current player loses
        return -10000 if maximizing_player else 10000, None

    best_move = None
    if maximizing_player:
        max_eval = -float('inf')
        # Order moves by heuristic to improve alpha-beta pruning
        ordered_moves = order_moves(board, legal_moves)
        for move in ordered_moves:
            new_board = make_move(board, move)
            eval, _ = minimax(new_board, depth - 1, alpha, beta, False, start_time)
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        # Order moves by heuristic to improve alpha-beta pruning
        ordered_moves = order_moves(board, legal_moves)
        for move in ordered_moves:
            new_board = make_move(board, move)
            eval, _ = minimax(new_board, depth - 1, alpha, beta, True, start_time)
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def evaluate_board(board):
    # Count connected components for both players
    my_components = count_components(board, 1)
    opp_components = count_components(board, -1)

    # Piece count difference
    my_pieces = np.sum(board == 1)
    opp_pieces = np.sum(board == -1)
    piece_diff = my_pieces - opp_pieces

    # Mobility (number of legal moves)
    my_mobility = len(get_legal_moves(board))
    opp_board = -np.array(board)
    opp_mobility = len(get_legal_moves(opp_board))

    # Center control (weighted by distance from center)
    center_control = 0
    for i in range(8):
        for j in range(8):
            if board[i][j] == 1:
                center_control += 1 / (1 + abs(i - 3.5) + abs(j - 3.5))
            elif board[i][j] == -1:
                center_control -= 1 / (1 + abs(i - 3.5) + abs(j - 3.5))

    # Weighted evaluation
    eval = (-my_components * 100) + (-opp_components * 50) + (piece_diff * 10) + \
           ((my_mobility - opp_mobility) * 5) + (center_control * 20)

    return eval

def count_components(board, player):
    visited = set()
    components = 0

    for i in range(8):
        for j in range(8):
            if board[i][j] == player and (i, j) not in visited:
                components += 1
                queue = deque([(i, j)])
                visited.add((i, j))

                while queue:
                    x, y = queue.popleft()
                    for dx, dy in DIRECTIONS:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 8 and 0 <= ny < 8:
                            if board[nx][ny] == player and (nx, ny) not in visited:
                                visited.add((nx, ny))
                                queue.append((nx, ny))
    return components

def get_legal_moves(board):
    moves = []
    for i in range(8):
        for j in range(8):
            if board[i][j] == 1:  # Current player's piece
                for di, dj in DIRECTIONS:
                    # Calculate how many pieces are in this line
                    count = 0
                    for k in range(1, 8):
                        ni, nj = i + k*di, j + k*dj
                        if 0 <= ni < 8 and 0 <= nj < 8:
                            if board[ni][nj] != 0:
                                count += 1
                        else:
                            break

                    if count == 0:
                        continue

                    # Check possible landing positions
                    for k in range(1, 8):
                        ni, nj = i + k*di, j + k*dj
                        if 0 <= ni < 8 and 0 <= nj < 8:
                            # Can't jump over enemy pieces
                            if board[ni][nj] == -1 and k < count:
                                break
                            # Valid move if we move exactly 'count' squares
                            if k == count:
                                # Can land on empty or enemy piece
                                if board[ni][nj] != 1:
                                    moves.append(f"{i},{j}:{ni},{nj}")
                                break
                        else:
                            break
    return moves

def make_move(board, move_str):
    new_board = [row[:] for row in board]
    from_row, from_col, to_row, to_col = map(int, move_str.replace(':', ',').split(','))
    new_board[to_row][to_col] = new_board[from_row][from_col]
    new_board[from_row][from_col] = 0
    return new_board

def order_moves(board, moves):
    # Simple heuristic: prioritize moves that capture opponent pieces
    capture_moves = []
    other_moves = []

    for move in moves:
        _, _, to_row, to_col = map(int, move.replace(':', ',').split(','))
        if board[to_row][to_col] == -1:
            capture_moves.append(move)
        else:
            other_moves.append(move)

    return capture_moves + other_moves

def random_legal_move(board):
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        # This should never happen per problem statement
        return "0,0:0,1"  # Fallback to a dummy move
    return np.random.choice(legal_moves)
