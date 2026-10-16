
import copy

def check_win(board, player):
    # Check horizontal
    for r in range(6):
        line = board[r]
        for start in range(2):
            if all(line[start + i] == player for i in range(5)):
                return True
    # Check vertical
    for c in range(6):
        line = [board[r][c] for r in range(6)]
        for start in range(2):
            if all(line[start + i] == player for i in range(5)):
                return True
    # Check diagonal (top-left to bottom-right)
    for sr in range(2):
        diag = [board[sr + i][sr + i] for i in range(5)]
        if all(diag[i] == player for i in range(5)):
            return True
    # Check diagonal (top-right to bottom-left)
    for sr in range(2):
        sc = 4 - sr
        diag = [board[sr + i][sc - i] for i in range(5)]
        if all(diag[i] == player for i in range(5)):
            return True
    return False

def rotate_quad(board, quad, direction):
    qs = [(0, 3, 0, 3), (0, 3, 3, 6), (3, 6, 0, 3), (3, 6, 3, 6)][quad]
    sr, er, sc, ec = qs
    sub = [[board[r][c] for c in range(sc, ec)] for r in range(sr, er)]
    if direction == 'L':
        rotated = [[sub[2 - c][r] for c in range(3)] for r in range(3)]
    else:  # 'R'
        rotated = [[sub[c][2 - r] for c in range(3)] for r in range(3)]
    for r in range(3):
        for c in range(3):
            board[sr + r][sc + c] = rotated[r][c]

def policy(you, opponent):
    # Build the board: 0 = empty, 1 = you (player), 2 = opponent
    board = [[(1 if you[r][c] else (2 if opponent[r][c] else 0)) for c in range(6)] for r in range(6)]
    
    # First pass: Try to find a winning move
    for r in range(1, 7):
        for c in range(1, 7):
            r0, c0 = r - 1, c - 1
            if board[r0][c0] != 0:
                continue
            for quad in range(4):
                for direction in ['L', 'R']:
                    b = copy.deepcopy(board)
                    b[r0][c0] = 1  # Place marble
                    rotate_quad(b, quad, direction)
                    if check_win(b, 1):
                        return f"{r},{c},{quad},{direction}"
    
    # Second pass: Try to find a move that blocks opponent's immediate win
    for r in range(1, 7):
        for c in range(1, 7):
            r0, c0 = r - 1, c - 1
            if board[r0][c0] != 0:
                continue
            for quad in range(4):
                for direction in ['L', 'R']:
                    b = copy.deepcopy(board)
                    b[r0][c0] = 1  # Place marble
                    rotate_quad(b, quad, direction)
                    # Check if opponent can win in response
                    opponent_can_win = False
                    for r2 in range(6):
                        for c2 in range(6):
                            if b[r2][c2] != 0:
                                continue
                            for q2 in range(4):
                                for d2 in ['L', 'R']:
                                    bb = copy.deepcopy(b)
                                    bb[r2][c2] = 2  # Opponent places
                                    rotate_quad(bb, q2, d2)
                                    if check_win(bb, 2):
                                        opponent_can_win = True
                                        break
                                if opponent_can_win:
                                    break
                            if opponent_can_win:
                                break
                        if opponent_can_win:
                            break
                    if not opponent_can_win:
                        return f"{r},{c},{quad},{direction}"
    
    # Fallback: Return the first legal move
    for r in range(1, 7):
        for c in range(1, 7):
            r0, c0 = r - 1, c - 1
            if board[r0][c0] == 0:
                return f"{r},{c},0,L"  # Guaranteed empty cell exists
