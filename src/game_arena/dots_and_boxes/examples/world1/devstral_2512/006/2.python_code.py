
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Create a copy of the current state to simulate moves
    h = horizontal.copy()
    v = vertical.copy()
    c = capture.copy()

    # Directions and their corresponding arrays
    directions = {'H': h, 'V': v}
    opposite_dir = {'H': 'V', 'V': 'H'}

    # List to store all legal moves
    legal_moves = []

    # First pass: Find all legal moves and immediate scoring opportunities
    for row in range(5):
        for col in range(5):
            # Check horizontal edges (can't be in last row)
            if row < 4 and h[row, col] == 0:
                legal_moves.append((row, col, 'H'))
            # Check vertical edges (can't be in last column)
            if col < 4 and v[row, col] == 0:
                legal_moves.append((row, col, 'V'))

    # If no legal moves (shouldn't happen in normal game), return a dummy move
    if not legal_moves:
        return "0,0,H"

    # Function to check if a move completes any boxes
    def completes_box(row, col, dir):
        boxes_completed = []
        if dir == 'H':
            # Check box above the edge (if exists)
            if row > 0:
                box_row, box_col = row - 1, col
                if (h[box_row, box_col] != 0 and h[box_row + 1, box_col] != 0 and
                    v[box_row, box_col] != 0 and v[box_row, box_col + 1] != 0):
                    boxes_completed.append((box_row, box_col))
            # Check box below the edge (if exists)
            if row < 4:
                box_row, box_col = row, col
                if (h[box_row, box_col] != 0 and h[box_row + 1, box_col] != 0 and
                    v[box_row, box_col] != 0 and v[box_row, box_col + 1] != 0):
                    boxes_completed.append((box_row, box_col))
        else:  # 'V'
            # Check box to the left of the edge (if exists)
            if col > 0:
                box_row, box_col = row, col - 1
                if (h[box_row, box_col] != 0 and h[box_row + 1, box_col] != 0 and
                    v[box_row, box_col] != 0 and v[box_row, box_col + 1] != 0):
                    boxes_completed.append((box_row, box_col))
            # Check box to the right of the edge (if exists)
            if col < 4:
                box_row, box_col = row, col
                if (h[box_row, box_col] != 0 and h[box_row + 1, box_col] != 0 and
                    v[box_row, box_col] != 0 and v[box_row, box_col + 1] != 0):
                    boxes_completed.append((box_row, box_col))
        return boxes_completed

    # Function to check if a move creates a double cross opportunity for opponent
    def creates_double_cross(row, col, dir):
        # Simulate the move
        if dir == 'H':
            h[row, col] = 1
        else:
            v[row, col] = 1

        double_cross = False

        # Check all boxes adjacent to the move
        if dir == 'H':
            # Check boxes above and below
            for box_row in [row - 1, row] if 0 <= row - 1 < 4 else [row]:
                if 0 <= box_row < 4 and 0 <= col < 4:
                    # Count how many edges are already drawn for this box
                    edges = [
                        h[box_row, col],     # top
                        h[box_row + 1, col], # bottom
                        v[box_row, col],     # left
                        v[box_row, col + 1]  # right
                    ]
                    # If exactly 3 edges are drawn, opponent can complete the box
                    if edges.count(0) == 1:
                        # Check if the missing edge is not the one we just played
                        if (box_row == row and edges[1] == 0) or (box_row == row - 1 and edges[0] == 0):
                            continue
                        # Now check if this would create another such opportunity
                        # by looking at adjacent boxes
                        for adj_row, adj_col in [(box_row - 1, col), (box_row + 1, col),
                                               (box_row, col - 1), (box_row, col + 1)]:
                            if 0 <= adj_row < 4 and 0 <= adj_col < 4:
                                adj_edges = [
                                    h[adj_row, adj_col],     # top
                                    h[adj_row + 1, adj_col], # bottom
                                    v[adj_row, adj_col],     # left
                                    v[adj_row, adj_col + 1]  # right
                                ]
                                if adj_edges.count(0) == 1:
                                    double_cross = True
                                    break
                        if double_cross:
                            break
        else:  # 'V'
            # Check boxes left and right
            for box_col in [col - 1, col] if 0 <= col - 1 < 4 else [col]:
                if 0 <= row < 4 and 0 <= box_col < 4:
                    edges = [
                        h[row, box_col],     # top
                        h[row + 1, box_col], # bottom
                        v[row, box_col],     # left
                        v[row, box_col + 1]  # right
                    ]
                    if edges.count(0) == 1:
                        if (box_col == col and edges[3] == 0) or (box_col == col - 1 and edges[2] == 0):
                            continue
                        for adj_row, adj_col in [(row - 1, box_col), (row + 1, box_col),
                                               (row, box_col - 1), (row, box_col + 1)]:
                            if 0 <= adj_row < 4 and 0 <= adj_col < 4:
                                adj_edges = [
                                    h[adj_row, adj_col],     # top
                                    h[adj_row + 1, adj_col], # bottom
                                    v[adj_row, adj_col],     # left
                                    v[adj_row, adj_col + 1]  # right
                                ]
                                if adj_edges.count(0) == 1:
                                    double_cross = True
                                    break
                        if double_cross:
                            break

        # Undo the simulated move
        if dir == 'H':
            h[row, col] = 0
        else:
            v[row, col] = 0

        return double_cross

    # First priority: moves that complete boxes (immediate scoring)
    scoring_moves = []
    for move in legal_moves:
        row, col, dir = move
        boxes = completes_box(row, col, dir)
        if boxes:
            scoring_moves.append((move, len(boxes)))

    if scoring_moves:
        # Among scoring moves, prefer those that complete more boxes
        scoring_moves.sort(key=lambda x: -x[1])
        best_move = scoring_moves[0][0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Second priority: avoid creating double cross opportunities
    safe_moves = []
    for move in legal_moves:
        row, col, dir = move
        if not creates_double_cross(row, col, dir):
            safe_moves.append(move)

    if safe_moves:
        legal_moves = safe_moves

    # Third priority: look for moves that set up chain reactions
    chain_moves = []
    for move in legal_moves:
        row, col, dir = move
        # Simulate the move
        if dir == 'H':
            h[row, col] = 1
        else:
            v[row, col] = 1

        # Check if this move creates new scoring opportunities
        new_scoring = []
        for r in range(5):
            for c in range(5):
                if r < 4 and h[r, c] == 0:
                    boxes = completes_box(r, c, 'H')
                    if boxes:
                        new_scoring.append(((r, c, 'H'), len(boxes)))
                if c < 4 and v[r, c] == 0:
                    boxes = completes_box(r, c, 'V')
                    if boxes:
                        new_scoring.append(((r, c, 'V'), len(boxes)))

        # Undo the move
        if dir == 'H':
            h[row, col] = 0
        else:
            v[row, col] = 0

        if new_scoring:
            chain_moves.append((move, sum(s[1] for s in new_scoring)))

    if chain_moves:
        chain_moves.sort(key=lambda x: -x[1])
        best_move = chain_moves[0][0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Fourth priority: strategic moves based on box potential
    # Calculate potential for each box (number of edges already drawn)
    box_potential = np.zeros((4, 4), dtype=int)
    for row in range(4):
        for col in range(4):
            edges = [
                h[row, col],     # top
                h[row + 1, col], # bottom
                v[row, col],     # left
                v[row, col + 1]  # right
            ]
            box_potential[row, col] = sum(1 for e in edges if e != 0)

    # Score each move based on how it affects box potentials
    move_scores = []
    for move in legal_moves:
        row, col, dir = move
        score = 0

        # Simulate the move
        if dir == 'H':
            h[row, col] = 1
        else:
            v[row, col] = 1

        # Calculate new potentials
        if dir == 'H':
            # Affects boxes above and below
            for box_row in [row - 1, row]:
                if 0 <= box_row < 4 and 0 <= col < 4:
                    edges = [
                        h[box_row, col],     # top
                        h[box_row + 1, col], # bottom
                        v[box_row, col],     # left
                        v[box_row, col + 1]  # right
                    ]
                    new_potential = sum(1 for e in edges if e != 0)
                    # Reward increasing potential, penalize completing to 3 (dangerous)
                    if new_potential == 3:
                        score -= 10  # Very bad - opponent can score
                    elif new_potential > box_potential[box_row, col]:
                        score += new_potential - box_potential[box_row, col]
        else:  # 'V'
            # Affects boxes left and right
            for box_col in [col - 1, col]:
                if 0 <= row < 4 and 0 <= box_col < 4:
                    edges = [
                        h[row, box_col],     # top
                        h[row + 1, box_col], # bottom
                        v[row, box_col],     # left
                        v[row, box_col + 1]  # right
                    ]
                    new_potential = sum(1 for e in edges if e != 0)
                    if new_potential == 3:
                        score -= 10
                    elif new_potential > box_potential[row, box_col]:
                        score += new_potential - box_potential[row, box_col]

        # Undo the move
        if dir == 'H':
            h[row, col] = 0
        else:
            v[row, col] = 0

        move_scores.append((move, score))

    # Sort moves by score (highest first)
    move_scores.sort(key=lambda x: -x[1])

    # Return the best move
    best_move = move_scores[0][0]
    return f"{best_move[0]},{best_move[1]},{best_move[2]}"
