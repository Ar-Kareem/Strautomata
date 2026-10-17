
import itertools
import random

# Precompute all winning lines (list of lists of (x,y,z) tuples)
def generate_lines():
    lines = []
    # axis-aligned lines
    for y in range(3):
        for z in range(3):
            lines.append([(x, y, z) for x in range(3)])
    for x in range(3):
        for z in range(3):
            lines.append([(x, y, z) for y in range(3)])
    for x in range(3):
        for y in range(3):
            lines.append([(x, y, z) for z in range(3)])
    # 2D diagonals in xy planes (fixed z)
    for z in range(3):
        lines.append([(i, i, z) for i in range(3)])      # main diagonal
        lines.append([(i, 2-i, z) for i in range(3)])   # anti-diagonal
    # 2D diagonals in xz planes (fixed y)
    for y in range(3):
        lines.append([(i, y, i) for i in range(3)])
        lines.append([(i, y, 2-i) for i in range(3)])
    # 2D diagonals in yz planes (fixed x)
    for x in range(3):
        lines.append([(x, i, i) for i in range(3)])
        lines.append([(x, i, 2-i) for i in range(3)])
    # 3D space diagonals (4 lines)
    lines.append([(i, i, i) for i in range(3)])
    lines.append([(i, i, 2-i) for i in range(3)])
    lines.append([(i, 2-i, i) for i in range(3)])
    lines.append([(i, 2-i, 2-i) for i in range(3)])
    return lines

ALL_LINES = generate_lines()

def winner(board):
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    for line in ALL_LINES:
        values = [board[x][y][z] for (x,y,z) in line]
        if values[0] == values[1] == values[2] != 0:
            return values[0]
    return 0

def evaluate(board):
    """Heuristic evaluation of the board from player 1's perspective."""
    score = 0
    for line in ALL_LINES:
        cells = [board[x][y][z] for (x,y,z) in line]
        count1 = cells.count(1)
        countm1 = cells.count(-1)
        if count1 == 3:
            score += 10000
        elif countm1 == 3:
            score -= 10000
        elif count1 == 2 and countm1 == 0:
            score += 100
        elif countm1 == 2 and count1 == 0:
            score -= 100
        elif count1 == 1 and countm1 == 0:
            score += 1
        elif countm1 == 1 and count1 == 0:
            score -= 1
    # Encourage center occupancy
    if board[1][1][1] == 1:
        score += 10
    elif board[1][1][1] == -1:
        score -= 10
    return score

def get_moves(board):
    moves = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    moves.append((x,y,z))
    return moves

def order_moves(board, moves, player):
    """Order moves by heuristic of the board after making the move."""
    scored = []
    for (x,y,z) in moves:
        # make move
        board[x][y][z] = player
        # evaluate from player 1 perspective
        if player == 1:
            score = evaluate(board)
        else:
            # opponent's move: negate evaluation because we evaluate for player 1
            score = -evaluate(board)
        board[x][y][z] = 0
        scored.append((score, (x,y,z)))
    # sort descending for player 1 (maximizer), ascending for player -1 (minimizer)
    scored.sort(key=lambda t: t[0], reverse=(player==1))
    return [move for _, move in scored]

def minimax(board, player, depth, alpha, beta):
    """Return the best score for the current player (1 or -1) using alpha-beta."""
    w = winner(board)
    if w != 0:
        return w * 1000000  # big number, positive for us win, negative for opponent
    if depth == 0:
        return evaluate(board)
    moves = get_moves(board)
    if not moves:
        return 0  # draw
    # order moves
    ordered_moves = order_moves(board, moves, player)
    if player == 1:  # maximizing player (us)
        value = -float('inf')
        for (x,y,z) in ordered_moves:
            board[x][y][z] = player
            value = max(value, minimax(board, -player, depth-1, alpha, beta))
            board[x][y][z] = 0
            if value >= beta:
                break
            alpha = max(alpha, value)
        return value
    else:  # minimizing player (opponent)
        value = float('inf')
        for (x,y,z) in ordered_moves:
            board[x][y][z] = player
            value = min(value, minimax(board, -player, depth-1, alpha, beta))
            board[x][y][z] = 0
            if value <= alpha:
                break
            beta = min(beta, value)
        return value

def policy(board):
    """Return the next move (x,y,z) for player 1."""
    # Check for immediate win
    moves = get_moves(board)
    for (x,y,z) in moves:
        board[x][y][z] = 1
        if winner(board) == 1:
            board[x][y][z] = 0
            return (x,y,z)
        board[x][y][z] = 0
    # Check for immediate loss (block opponent)
    for (x,y,z) in moves:
        board[x][y][z] = -1
        if winner(board) == -1:
            board[x][y][z] = 0
            return (x,y,z)
        board[x][y][z] = 0
    # If center is free, take it (good heuristic)
    if board[1][1][1] == 0:
        return (1,1,1)
    # Use minimax with depth 4 (2 moves ahead for each side)
    best_move = None
    best_value = -float('inf')
    depth = 4
    # order moves for player 1
    ordered_moves = order_moves(board, moves, 1)
    for (x,y,z) in ordered_moves:
        board[x][y][z] = 1
        value = minimax(board, -1, depth-1, -float('inf'), float('inf'))
        board[x][y][z] = 0
        if value > best_value:
            best_value = value
            best_move = (x,y,z)
    # fallback: if no move chosen, pick first available
    if best_move is None and moves:
        best_move = moves[0]
    return best_move
