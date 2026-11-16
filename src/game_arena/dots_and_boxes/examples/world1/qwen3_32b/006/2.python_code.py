
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    # Generate all legal moves
    legal_moves = []
    # Horizontal moves
    for r in range(5):
        for c in range(4):
            if horizontal[r][c] == 0:
                legal_moves.append((r, c, 'H'))
    # Vertical moves
    for r in range(4):
        for c in range(5):
            if vertical[r][c] == 0:
                legal_moves.append((r, c, 'V'))

    # Step 1: Check for moves that capture boxes
    capturing_moves = []
    for move in legal_moves:
        r, c, m_type = move
        temp_horizontal = horizontal.copy()
        temp_vertical = vertical.copy()
        if m_type == 'H':
            temp_horizontal[r][c] = 1
        else:
            temp_vertical[r][c] = 1

        captured = 0
        for box_r in range(4):
            for box_c in range(4):
                top = temp_horizontal[box_r][box_c]
                bottom = temp_horizontal[box_r + 1][box_c]
                left = temp_vertical[box_r][box_c]
                right = temp_vertical[box_r][box_c + 1]
                if top and bottom and left and right and capture[box_r][box_c] == 0:
                    captured += 1
        if captured > 0:
            capturing_moves.append((move, captured))

    if capturing_moves:
        # Sort by number of captured boxes descending
        capturing_moves.sort(key=lambda x: x[1], reverse=True)
        best_move = capturing_moves[0][0]
        return f"{best_move[0]},{best_move[1]},{best_move[2]}"

    # Step 2: Block opponent's potential captures
    blocking_moves = []
    for move in legal_moves:
        r, c, m_type = move
        temp_horizontal = horizontal.copy()
        temp_vertical = vertical.copy()
        if m_type == 'H':
            temp_horizontal[r][c] = -1
        else:
            temp_vertical[r][c] = -1

        blocked = 0
        for box_r in range(4):
            for box_c in range(4):
                top = temp_horizontal[box_r][box_c]
                bottom = temp_horizontal[box_r + 1][box_c]
                left = temp_vertical[box_r][box_c]
                right = temp_vertical[box_r][box_c + 1]
                if top and bottom and left and right and capture[box_r][box_c] == 0:
                    blocked += 1
        if blocked > 0:
            blocking_moves.append((move, blocked))

    if blocking_moves:
        # Block the most threatening move
        blocking_moves.sort(key=lambda x: x[1], reverse=True)
        best_block_move = blocking_moves[0][0]
        return f"{best_block_move[0]},{best_block_move[1]},{best_block_move[2]}"

    # Step 3: Minimize opponent's future threats
    threat_moves = []
    for move in legal_moves:
        r, c, m_type = move
        temp_horizontal = horizontal.copy()
        temp_vertical = vertical.copy()
        if m_type == 'H':
            temp_horizontal[r][c] = 1
        else:
            temp_vertical[r][c] = 1

        threats = 0
        for box_r in range(4):
            for box_c in range(4):
                edges = 0
                edges += 1 if temp_horizontal[box_r][box_c] != 0 else 0
                edges += 1 if temp_horizontal[box_r + 1][box_c] != 0 else 0
                edges += 1 if temp_vertical[box_r][box_c] != 0 else 0
                edges += 1 if temp_vertical[box_r][box_c + 1] != 0 else 0
                if edges == 3:
                    threats += 1
        threat_moves.append((move, threats))

    # Select move with least threats
    threat_moves.sort(key=lambda x: x[1])
    best_threat_move = threat_moves[0][0]
    return f"{best_threat_move[0]},{best_threat_move[1]},{best_threat_move[2]}"
