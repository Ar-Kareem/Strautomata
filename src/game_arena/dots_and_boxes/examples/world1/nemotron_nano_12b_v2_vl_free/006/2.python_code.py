
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Step 1: Generate all legal moves
    legal_moves = []

    # Horizontal edges are 5x4 grid
    for i in range(5):
        for j in range(4):
            if horizontal[i, j] == 0:
                legal_moves.append((i, j, 'H'))

    # Vertical edges are 4x5 grid
    for i in range(4):
        for j in range(5):
            if vertical[i, j] == 0:
                legal_moves.append((i, j, 'V'))

    # Step 2: Evaluate each legal move
    move_details = []

    for move in legal_moves:
        i, j, edge_type = move

        new_h = np.copy(horizontal)
        new_v = np.copy(vertical)

        if edge_type == 'H':
            new_h[i, j] = 1
            boxes_to_check = [(i, j)]
            if i > 0:
                boxes_to_check.append((i - 1, j))
        else:  # 'V'
            new_v[i, j] = 1
            boxes_to_check = [(i, j)]
            if j > 0:
                boxes_to_check.append((i, j - 1))

        # Count captured boxes
        captured = 0
        for (b_row, b_col) in boxes_to_check:
            top = new_h[b_row, b_col]
            bottom = new_h[b_row + 1, b_col]
            left = new_v[b_row, b_col]
            right = new_v[b_row, b_col + 1]

            if top != 0 and bottom != 0 and left != 0 and right != 0:
                captured += 1

        # Count unsafe boxes
        unsafe_live = 0
        for b_row in range(4):
            for b_col in range(4):
                top = new_h[b_row, b_col]
                bottom = new_h[b_row + 1, b_col]
                left = new_v[b_row, b_col]
                right = new_v[b_row, b_col + 1]

                num_edges = (top != 0) + (bottom != 0) + (left != 0) + (right != 0)
                if num_edges == 3:
                    unsafe_live += 1

        move_details.append((captured, unsafe_live, move))

    # Step 3: Select the best move
    best_move = None

    # Group moves by captured boxes
    capture_moves = [(c, u, move) for c, u, move in move_details if c > 0]
    if capture_moves:
        # Prioritize moves with maximum captured boxes
        max_caps = max([c for c, u, m in capture_moves])
        filtered = [(u, move) for c, u, move in move_details if c == max_caps]
        # Choose the one with least unsafe_live
        filtered.sort(key=lambda x: (x[0],))
        best_move = filtered[0][1]
    else:
        # No captures possible
        safe_moves = [(u, move) for u, move in move_details if u == 0]
        if safe_moves:
            best_move = safe_moves[0][1]
        else:
            # No safe moves; choose one with least unsafe
            unsorted = [(u, move) for u, move in move_details if c == 0]
            unsorted.sort(key=lambda x: (x[0],))
            best_move = unsorted[0][1]

    # Return the chosen move in the correct format
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
