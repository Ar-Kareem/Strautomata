
import numpy as np

def get_legal_moves(horizontal, vertical):
    moves = []
    for r in range(5):
        for c in range(5):
            if horizontal[r, c] == 0 and 0 <= r <= 4 and 0 <= c <= 3:
                moves.append((r, c, 'H'))
            if vertical[r, c] == 0 and 0 <= r <= 3 and 0 <= c <= 4:
                moves.append((r, c, 'V'))
    return moves

def simulate_state(horizontal, vertical, capture, move):
    r, c, d = move
    h = horizontal.copy()
    v = vertical.copy()
    cap = capture.copy()
    if d == 'H':
        h[r, c] = 1
    else:
        v[r, c] = 1
    # Check for new captures after move
    for i in range(4):
        for j in range(4):
            if cap[i, j] == 0:
                top = h[i, j]
                bottom = h[i + 1, j]
                left = v[i, j]
                right = v[i, j + 1]
                if top != 0 and bottom != 0 and left != 0 and right != 0:
                    cap[i, j] = 1
    return h, v, cap

def simulate_move_captures(horizontal, vertical, capture, move):
    _, _, cap = simulate_state(horizontal, vertical, capture, move)
    captured = np.sum(cap - capture > 0)
    return captured

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    legal_moves = get_legal_moves(horizontal, vertical)
    capturing_moves = []
    non_capturing_moves = []
    for move in legal_moves:
        captured = simulate_move_captures(horizontal, vertical, capture, move)
        if captured > 0:
            capturing_moves.append((move, captured))
        else:
            non_capturing_moves.append(move)
    
    if capturing_moves:
        # Select the move that captures the most boxes
        best_move, _ = max(capturing_moves, key=lambda x: x[1])
    else:
        # Find safe moves that don't allow opponent an immediate capture
        safe_moves = []
        for move in non_capturing_moves:
            temp_h, temp_v, temp_cap = simulate_state(horizontal, vertical, capture, move)
            opp_captures = []
            for opp_move in get_legal_moves(temp_h, temp_v):
                if simulate_move_captures(temp_h, temp_v, temp_cap, opp_move) > 0:
                    opp_captures.append(opp_move)
            if not opp_captures:
                safe_moves.append(move)
        if safe_moves:
            # Arbitrarily pick the first safe move for simplicity
            best_move = safe_moves[0]
        elif non_capturing_moves:
            # Forced to allow opponent capture, pick first anyway
            best_move = non_capturing_moves[0]
        else:
            # Should never happen if the game isn't over, but fallback to any legal if possible
            if legal_moves:
                best_move = legal_moves[0]
            else:
                raise ValueError("No legal moves available, but policy should only be called when moves exist.")
    
    r, c, d = best_move
    return f"{r},{c},{d}"
