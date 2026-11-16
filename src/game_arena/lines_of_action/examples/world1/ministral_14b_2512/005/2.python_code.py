
import numpy as np
from collections import deque

def policy(board):
    # Convert board to numpy array for easier manipulation
    board = np.array(board, dtype=int)
    my_pieces = np.where(board == 1)
    opp_pieces = np.where(board == -1)

    # Generate all possible legal moves
    legal_moves = generate_legal_moves(board, my_pieces[0], my_pieces[1])

    if not legal_moves:
        # No legal moves (should not happen per problem statement)
        return "0,0:0,0"

    # Evaluate moves using a heuristic + search
    best_move = None
    best_score = -float('inf')

    # Use a simple heuristic for now (can be replaced with search)
    for move in legal_moves:
        from_row, from_col, to_row, to_col = move
        # Simulate the move
        new_board = board.copy()
        new_board[from_row, from_col] = 0
        new_board[to_row, to_col] = 1

        # Evaluate the new board
        score = evaluate_board(new_board, my_pieces, opp_pieces)

        if score > best_score:
            best_score = score
            best_move = move

    # Format the best move
    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"

def generate_legal_moves(board, my_rows, my_cols):
    legal_moves = []
    directions = [(-1,-1), (-1,0), (-1,1),
                  (0,-1),          (0,1),
                  (1,-1),  (1,0), (1,1)]

    for i in range(len(my_rows)):
        row, col = my_rows[i], my_cols[i]
        for dr, dc in directions:
            # Check all possible lines in the direction
            for step in range(1, 8):
                nr, nc = row + dr * step, col + dc * step
                if 0 <= nr < 8 and 0 <= nc < 8:
                    # Count pieces in the line (including current piece)
                    line_pieces = 0
                    for k in range(step + 1):
                        r, c = row + dr * k, col + dc * k
                        if 0 <= r < 8 and 0 <= c < 8:
                            if board[r, c] != 0:
                                line_pieces += 1
                    # Must move exactly line_pieces squares
                    if step == line_pieces:
                        # Check if path is clear (no opponent pieces in between)
                        clear = True
                        for k in range(1, step):
                            r, c = row + dr * k, col + dc * k
                            if board[r, c] == -1:
                                clear = False
                                break
                        if clear:
                            # Check if landing on opponent (capture)
                            if board[nr, nc] == -1:
                                legal_moves.append((row, col, nr, nc))
                            else:
                                # Check if landing on empty or friendly (but not blocked)
                                if board[nr, nc] == 0 or board[nr, nc] == 1:
                                    legal_moves.append((row, col, nr, nc))
                else:
                    break
    return legal_moves

def evaluate_board(board, my_pieces, opp_pieces):
    # Count connected components for my pieces
    my_rows, my_cols = np.where(board == 1)
    if len(my_rows) == 0:
        return 0

    # Use BFS to count connected components
    visited = set()
    components = 0
    for i in range(len(my_rows)):
        row, col = my_rows[i], my_cols[i]
        if (row, col) not in visited:
            components += 1
            queue = deque([(row, col)])
            visited.add((row, col))
            while queue:
                r, c = queue.popleft()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in visited and board[nr, nc] == 1:
                            visited.add((nr, nc))
                            queue.append((nr, nc))

    # Prefer fewer components (contiguity)
    contiguity_score = -components

    # Prefer capturing opponent pieces
    opp_rows, opp_cols = np.where(board == -1)
    capture_score = -len(opp_rows)  # More captures are better

    # Prefer moves that reduce opponent's contiguity
    opp_visited = set()
    opp_components = 0
    for i in range(len(opp_rows)):
        row, col = opp_rows[i], opp_cols[i]
        if (row, col) not in opp_visited:
            opp_components += 1
            queue = deque([(row, col)])
            opp_visited.add((row, col))
            while queue:
                r, c = queue.popleft()
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and (nr, nc) not in opp_visited and board[nr, nc] == -1:
                            opp_visited.add((nr, nc))
                            queue.append((nr, nc))
    opp_contiguity_score = opp_components

    # Combine scores (weights can be tuned)
    total_score = contiguity_score + capture_score + opp_contiguity_score
    return total_score
