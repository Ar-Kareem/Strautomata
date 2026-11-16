
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Generate all legal moves
    moves = []
    # Horizontal moves: i from 0 to 4, j from 0 to 3
    for i in range(5):
        for j in range(4):
            if horizontal[i, j] == 0:
                moves.append(('H', i, j))
    # Vertical moves: i from 0 to 3, j from 0 to 4
    for i in range(4):
        for j in range(5):
            if vertical[i, j] == 0:
                moves.append(('V', i, j))

    # If no moves, return a default (should not happen)
    if not moves:
        return "0,0,H"

    # First, try to find a move that captures boxes
    best_move = None
    max_captures = -1

    for move in moves:
        # Simulate the move
        h_copy = horizontal.copy()
        v_copy = vertical.copy()
        cap_copy = capture.copy()

        if move[0] == 'H':
            i, j = move[1], move[2]
            h_copy[i, j] = 1
            # Check box above if exists
            if i > 0:
                # Box (i-1, j): edges H[i-1,j], H[i,j], V[i-1,j], V[i-1,j+1]
                if h_copy[i-1, j] != 0 and h_copy[i, j] != 0 and v_copy[i-1, j] != 0 and v_copy[i-1, j+1] != 0:
                    cap_copy[i-1, j] = 1
            # Check box below if exists
            if i < 4:
                # Box (i, j): edges H[i,j], H[i+1,j], V[i,j], V[i,j+1]
                if h_copy[i, j] != 0 and h_copy[i+1, j] != 0 and v_copy[i, j] != 0 and v_copy[i, j+1] != 0:
                    cap_copy[i, j] = 1
        else:  # move is vertical
            i, j = move[1], move[2]
            v_copy[i, j] = 1
            # Check box left if exists
            if j > 0:
                # Box (i, j-1): edges H[i,j-1], H[i+1,j-1], V[i,j-1], V[i,j]
                if h_copy[i, j-1] != 0 and h_copy[i+1, j-1] != 0 and v_copy[i, j-1] != 0 and v_copy[i, j] != 0:
                    cap_copy[i, j-1] = 1
            # Check box right if exists (only for j<3)
            if j < 3:
                # Box (i, j): edges H[i,j], H[i+1,j], V[i,j], V[i,j+1]
                if h_copy[i, j] != 0 and h_copy[i+1, j] != 0 and v_copy[i, j] != 0 and v_copy[i, j+1] != 0:
                    cap_copy[i, j] = 1

        # Count boxes captured
        captured = np.sum(cap_copy == 1)
        if captured > max_captures:
            max_captures = captured
            best_move = move

    # If a capturing move is found, return it
    if best_move is not None:
        if best_move[0] == 'H':
            return f"{best_move[1]},{best_move[2]},H"
        else:
            return f"{best_move[1]},{best_move[2]},V"

    # If no capturing move, choose one that minimizes three-sided boxes
    best_move = None
    min_three_sided = float('inf')

    for move in moves:
        # Simulate the move without caring about capture
        h_copy = horizontal.copy()
        v_copy = vertical.copy()

        if move[0] == 'H':
            i, j = move[1], move[2]
            h_copy[i, j] = 1
        else:
            i, j = move[1], move[2]
            v_copy[i, j] = 1

        # Count three-sided boxes after the move
        three_sided = 0
        for i in range(4):
            for j in range(4):
                # Check four edges for box (i,j)
                edges = [h_copy[i, j], h_copy[i+1, j], v_copy[i, j], v_copy[i, j+1]]
                drawn = sum(1 for edge in edges if edge != 0)
                if drawn == 3:
                    three_sided += 1

        if three_sided < min_three_sided:
            min_three_sided = three_sided
            best_move = move

    # Return the move that minimizes three-sided boxes
    if best_move is not None:
        if best_move[0] == 'H':
            return f"{best_move[1]},{best_move[2]},H"
        else:
            return f"{best_move[1]},{best_move[2]},V"

    # Fallback (should not be reached)
    return "0,0,H"
