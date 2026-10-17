
import numpy as np
from collections import deque

def policy(board):
    # Directions for movement: horizontal, vertical, and diagonals
    directions = [
        (0, 1), (1, 0), (1, 1), (1, -1),
        (0, -1), (-1, 0), (-1, -1), (-1, 1)
    ]

    def is_legal_move(board, from_row, from_col, to_row, to_col):
        # Check if the move is within bounds
        if not (0 <= to_row < 8 and 0 <= to_col < 8):
            return False

        # Calculate the direction of the move
        dr = to_row - from_row
        dc = to_col - from_col
        if dr == 0 and dc == 0:
            return False  # No move

        # Normalize the direction to one of the 8 possible directions
        gcd_val = np.gcd(abs(dr), abs(dc))
        if gcd_val == 0:
            return False
        dr //= gcd_val
        dc //= gcd_val

        # Check if the direction is valid
        if (dr, dc) not in directions:
            return False

        # Count the number of pieces in the line of movement
        count = 0
        r, c = from_row + dr, from_col + dc
        while 0 <= r < 8 and 0 <= c < 8:
            if board[r][c] != 0:
                count += 1
            r += dr
            c += dc

        # Check if the move distance equals the count
        distance = max(abs(dr * gcd_val), abs(dc * gcd_val))
        if distance != count:
            return False

        # Check if the move jumps over enemy pieces
        r, c = from_row + dr, from_col + dc
        while 0 <= r < 8 and 0 <= c < 8 and (r != to_row or c != to_col):
            if board[r][c] == -1:
                return False  # Cannot jump over enemy pieces
            r += dr
            c += dc

        # Check if the destination is empty or has an enemy piece
        if board[to_row][to_col] == 1:
            return False  # Cannot land on own piece

        return True

    def generate_legal_moves(board):
        moves = []
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1:
                    for dr, dc in directions:
                        for step in range(1, 8):
                            to_r, to_c = r + dr * step, c + dc * step
                            if 0 <= to_r < 8 and 0 <= to_c < 8:
                                if is_legal_move(board, r, c, to_r, to_c):
                                    moves.append((r, c, to_r, to_c))
        return moves

    def evaluate_board(board):
        # Evaluate connectivity using BFS
        visited = np.zeros((8, 8), dtype=bool)
        components = 0
        for r in range(8):
            for c in range(8):
                if board[r][c] == 1 and not visited[r][c]:
                    components += 1
                    queue = deque([(r, c)])
                    visited[r][c] = True
                    while queue:
                        x, y = queue.popleft()
                        for dx, dy in directions:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == 1 and not visited[nx][ny]:
                                visited[nx][ny] = True
                                queue.append((nx, ny))

        # Evaluate mobility: count legal moves
        mobility = len(generate_legal_moves(board))

        # Evaluate material: count pieces
        my_pieces = np.sum(board == 1)
        opponent_pieces = np.sum(board == -1)
        material = my_pieces - opponent_pieces

        # Combine evaluations with weights
        connectivity_weight = -2.0  # Fewer components is better
        mobility_weight = 0.1
        material_weight = 1.0

        score = connectivity_weight * components + mobility_weight * mobility + material_weight * material
        return score

    def minimax(board, depth, alpha, beta, maximizing_player):
        if depth == 0:
            return evaluate_board(board)

        legal_moves = generate_legal_moves(board)
        if not legal_moves:
            return evaluate_board(board)

        if maximizing_player:
            max_eval = -float('inf')
            for move in legal_moves:
                r, c, to_r, to_c = move
                new_board = np.copy(board)
                new_board[r][c] = 0
                new_board[to_r][to_c] = 1
                eval = minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in legal_moves:
                r, c, to_r, to_c = move
                new_board = np.copy(board)
                new_board[r][c] = 0
                new_board[to_r][to_c] = -1
                eval = minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval

    legal_moves = generate_legal_moves(board)
    if not legal_moves:
        return "0,0:0,0"  # Should not happen, but handle gracefully

    best_move = None
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')

    for move in legal_moves:
        r, c, to_r, to_c = move
        new_board = np.copy(board)
        new_board[r][c] = 0
        new_board[to_r][to_c] = 1
        score = minimax(new_board, depth=2, alpha=alpha, beta=beta, maximizing_player=False)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, score)

    if best_move is None:
        best_move = legal_moves[0]  # Fallback to first legal move

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
