
import numpy as np

def get_legal_moves(board, player):
    """Generates all legal moves for a given player."""
    moves = []
    n = board.shape[0]
    pieces = np.argwhere(board == player)

    def is_valid(r, c):
        return 0 <= r < n and 0 <= c < n

    def count_pieces(board):
        return np.count_nonzero(board)

    def check_line(r, c, dr, dc, dist):
        nr, nc = r + dr * dist, c + dc * dist
        if not is_valid(nr, nc):
            return None
        if board[nr, nc] == player:
            return None

        intermediate_cells = [(r + dr * i, c + dc * i) for i in range(1, dist)]
        for ir, ic in intermediate_cells:
            if board[ir, ic] == -player:
                return None

        return (nr, nc)

    for r, c in pieces:
        dist = count_pieces(board)

        # Horizontal
        target = check_line(r, c, 0, 1, dist)
        if target:
            moves.append(((r, c), target))
        target = check_line(r, c, 0, -1, dist)
        if target:
            moves.append(((r, c), target))

        # Vertical
        target = check_line(r, c, 1, 0, dist)
        if target:
            moves.append(((r, c), target))
        target = check_line(r, c, -1, 0, dist)
        if target:
            moves.append(((r, c), target))

        # Diagonal
        target = check_line(r, c, 1, 1, dist)
        if target:
            moves.append(((r, c), target))
        target = check_line(r, c, 1, -1, dist)
        if target:
            moves.append(((r, c), target))
        target = check_line(r, c, -1, 1, dist)
        if target:
            moves.append(((r, c), target))
        target = check_line(r, c, -1, -1, dist)
        if target:
            moves.append(((r, c), target))

    return moves


def get_connected_components(board, player):
    """Calculates the number of connected components for a given player."""
    n = board.shape[0]
    visited = np.zeros_like(board, dtype=bool)
    count = 0

    def dfs(r, c):
        if not (0 <= r < n and 0 <= c < n) or visited[r, c] or board[r, c] != player:
            return
        visited[r, c] = True
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                dfs(r + dr, c + dc)

    for r in range(n):
        for c in range(n):
            if board[r, c] == player and not visited[r, c]:
                dfs(r, c)
                count += 1
    return count


def evaluate_move(board, move, player):
    """Evaluates a move based on several heuristics."""
    from_row, from_col = move[0]
    to_row, to_col = move[1]

    new_board = board.copy()
    new_board[to_row, to_col] = player
    new_board[from_row, from_col] = 0

    # Connectivity heuristic
    connectivity = get_connected_components(new_board, player)
    connectivity_score = -connectivity  # Lower is better

    # Capture heuristic
    capture = 1 if board[to_row, to_col] == -player else 0
    capture_score = capture * 5

    # Board center heuristic
    center_row = 3.5
    center_col = 3.5
    distance = np.sqrt(((to_row - center_row)**2) + ((to_col - center_col)**2))
    center_score = -distance

    #Blocking opponent heuristic: estimated number of available moves by opponent, after our move:
    opponent = -player
    num_available_moves = len(get_legal_moves(new_board, opponent))
    blocking_score = -num_available_moves * 0.5

    # Combine heuristics
    total_score = connectivity_score + capture_score + center_score + blocking_score
    return total_score

def policy(board):
    """Chooses the best move based on a combination of heuristics."""
    board = np.array(board)
    player = 1
    legal_moves = get_legal_moves(board, player)

    if not legal_moves:
        return "0,0:0,0" #Return no-op

    best_move = None
    best_score = float('-inf')

    for move in legal_moves:
        score = evaluate_move(board, move, player)
        if score > best_score:
            best_score = score
            best_move = move

    if best_move:
        from_row, from_col = best_move[0]
        to_row, to_col = best_move[1]
        return f"{from_row},{from_col}:{to_row},{to_col}"
    else:
        return "0,0:0,0" #Return no-op - should never happen as legal_moves is not empty.
