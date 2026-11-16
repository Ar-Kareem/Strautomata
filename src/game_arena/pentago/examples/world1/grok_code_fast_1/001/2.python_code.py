
import numpy as np

def policy(you, opponent) -> str:
    you = np.array(you, dtype=int)
    opp = np.array(opponent, dtype=int)
    board = you - opp  # 1 for self, -1 for opponent, 0 empty

    # Precompute quadrant positions
    QUAD_POS = [
        [(0,0),(0,1),(0,2),(1,0),(1,1),(1,2),(2,0),(2,1),(2,2)],
        [(0,3),(0,4),(0,5),(1,3),(1,4),(1,5),(2,3),(2,4),(2,5)],
        [(3,0),(3,1),(3,2),(4,0),(4,1),(4,2),(5,0),(5,1),(5,2)],
        [(3,3),(3,4),(3,5),(4,3),(4,4),(4,5),(5,3),(5,4),(5,5)],
    ]

    # Generate all legal moves
    moves = [(r, c, q, d) for r in range(6) for c in range(6) if board[r, c] == 0 for q in range(4) for d in ['L', 'R']]

    def simulate_move(curr_board, r, c, q, d, player):
        new_board = curr_board.copy()
        new_board[r, c] = player
        quad_pos = QUAD_POS[q]
        vals = [new_board[pos[0], pos[1]] for pos in quad_pos]
        if d == 'L':
            # Anticlockwise
            new_vals = [vals[2], vals[5], vals[8], vals[1], vals[4], vals[7], vals[0], vals[3], vals[6]]
        else:
            # Clockwise
            new_vals = [vals[6], vals[3], vals[0], vals[7], vals[4], vals[1], vals[8], vals[5], vals[2]]
        for i, v in enumerate(new_vals):
            new_board[quad_pos[i][0], quad_pos[i][1]] = v
        return new_board

    def check_win(b):
        # Rows
        for r in range(6):
            for c in range(2):
                if np.all(b[r, c:c+5] == b[r, c]) and b[r, c] != 0:
                    return b[r, c]
        # Columns
        for c in range(6):
            for r in range(2):
                if np.all(b[r:r+5, c] == b[r, c]) and b[r, c] != 0:
                    return b[r, c]
        # Main diagonals (\)
        for r in range(2):
            for c in range(2):
                line = np.array([b[r+i, c+i] for i in range(5)])
                if np.all(line == line[0]) and line[0] != 0:
                    return line[0]
        # Anti-diagonals (/)
        for r in range(2):
            for c in range(4, 1, -1):
                line = np.array([b[r+i, c-i] for i in range(5)])
                if np.all(line == line[0]) and line[0] != 0:
                    return line[0]
        return 0

    # 1. Check for immediate winning moves
    for r, c, q, d in moves:
        new_board = simulate_move(board, r, c, q, d, 1)
        if check_win(new_board) == 1:
            return f"{r+1},{c+1},{q},{d}"

    # 2. Check for moves that block all opponent's immediate wins
    for r, c, q, d in moves:
        new_board = simulate_move(board, r, c, q, d, 1)
        opponent_can_win = False
        for r2 in range(6):
            for c2 in range(6):
                if new_board[r2, c2] == 0:
                    for q2 in range(4):
                        for d2 in ['L', 'R']:
                            new_board2 = simulate_move(new_board, r2, c2, q2, d2, -1)
                            if check_win(new_board2) == -1:
                                opponent_can_win = True
                                break
                        if opponent_can_win:
                            break
                    if opponent_can_win:
                        break
            if opponent_can_win:
                break
        if not opponent_can_win:
            return f"{r+1},{c+1},{q},{d}"

    # 3. Fallback: Heuristic - prefer moves closest to center
    if moves:
        center_list = [(min(r, 5-r) + min(c, 5-c), r, c, q, d) for r, c, q, d in moves]
        center_list.sort()  # Smallest distance first
        r, c, q, d = center_list[0][1:]
        return f"{r+1},{c+1},{q},{d}"

    # Though unlikely, this should never happen
    return None
