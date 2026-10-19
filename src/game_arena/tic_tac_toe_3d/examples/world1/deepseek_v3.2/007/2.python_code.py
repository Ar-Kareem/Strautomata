
import itertools
import math

# Precompute all winning lines
LINES = []

# Rows: fixed z and y, varying x
for z in range(3):
    for y in range(3):
        LINES.append([(z, y, x) for x in range(3)])

# Columns: fixed z and x, varying y
for z in range(3):
    for x in range(3):
        LINES.append([(z, y, x) for y in range(3)])

# Pillars: fixed y and x, varying z
for y in range(3):
    for x in range(3):
        LINES.append([(z, y, x) for z in range(3)])

# Layer diagonals
for z in range(3):
    LINES.append([(z, 0, 0), (z, 1, 1), (z, 2, 2)])
    LINES.append([(z, 0, 2), (z, 1, 1), (z, 2, 0)])

# Space diagonals (triagonals)
LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
LINES.append([(0, 2, 2), (1, 1, 1), (2, 0, 0)])

def copy_board(board):
    """Return a deep copy of the board."""
    return [[[board[z][y][x] for x in range(3)] for y in range(3)] for z in range(3)]

def check_winner(board):
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    for line in LINES:
        a, b, c = line
        az, ay, ax = a
        bz, by, bx = b
        cz, cy, cx = c
        val = board[az][ay][ax]
        if val != 0 and val == board[bz][by][bx] == board[cz][cy][cx]:
            return val
    return 0

def evaluate(board):
    """
    Heuristic evaluation of the board from the perspective of player 1.
    Higher score means better for player 1.
    """
    score = 0
    for line in LINES:
        counts = {1: 0, -1: 0}
        for (z, y, x) in line:
            val = board[z][y][x]
            if val != 0:
                counts[val] += 1
        if counts[1] == 3:
            return 10000  # already caught by check_winner, but just in case
        if counts[-1] == 3:
            return -10000
        if counts[1] > 0 and counts[-1] == 0:
            # line only has our pieces
            score += (counts[1] - counts[-1]) * (10 ** counts[1])
        elif counts[-1] > 0 and counts[1] == 0:
            # line only has opponent pieces
            score += (counts[1] - counts[-1]) * (10 ** counts[-1])
        else:
            # line has both, subtract opponent's threat
            score += (counts[1] - counts[-1]) * (10 ** max(counts[1], counts[-1]))
    # Center bonus
    if board[1][1][1] == 1:
        score += 50
    elif board[1][1][1] == -1:
        score -= 50
    return score

def minimax(board, depth, alpha, beta, maximizing_player):
    """
    Minimax with alpha-beta pruning.
    Returns a score for the board state.
    """
    winner = check_winner(board)
    if winner != 0:
        return winner * (10000 - depth)  # prefer faster win / slower loss
    if depth == 0:
        return evaluate(board)
    empty_cells = [(z, y, x) for z in range(3) for y in range(3) for x in range(3) if board[z][y][x] == 0]
    if not empty_cells:
        return 0  # draw
    if maximizing_player:
        value = -math.inf
        for (z, y, x) in empty_cells:
            new_board = copy_board(board)
            new_board[z][y][x] = 1
            value = max(value, minimax(new_board, depth - 1, alpha, beta, False))
            alpha = max(alpha, value)
            if value >= beta:
                break
        return value
    else:
        value = math.inf
        for (z, y, x) in empty_cells:
            new_board = copy_board(board)
            new_board[z][y][x] = -1
            value = min(value, minimax(new_board, depth - 1, alpha, beta, True))
            beta = min(beta, value)
            if value <= alpha:
                break
        return value

def policy(board):
    """
    Determine the next move for player 1 (you) on the given 3D board.
    Returns a tuple (z, y, x) with indices 0–2.
    """
    # List all empty cells
    empty_cells = [(z, y, x) for z in range(3) for y in range(3) for x in range(3) if board[z][y][x] == 0]
    if not empty_cells:
        return (0, 0, 0)  # no move possible, return arbitrary

    # Check for immediate winning move
    for (z, y, x) in empty_cells:
        new_board = copy_board(board)
        new_board[z][y][x] = 1
        if check_winner(new_board) == 1:
            return (z, y, x)

    # Check for immediate blocking move
    for (z, y, x) in empty_cells:
        new_board = copy_board(board)
        new_board[z][y][x] = -1
        if check_winner(new_board) == -1:
            return (z, y, x)

    # Use minimax with depth 4 to choose the best move
    best_move = None
    best_value = -math.inf
    depth = 4  # adjustable
    for (z, y, x) in empty_cells:
        new_board = copy_board(board)
        new_board[z][y][x] = 1
        move_value = minimax(new_board, depth - 1, -math.inf, math.inf, False)
        if move_value > best_value:
            best_value = move_value
            best_move = (z, y, x)
        # Tie-break: prefer center if score is close (within 10)
        elif move_value == best_value and best_move is not None:
            if (z, y, x) == (1, 1, 1):
                best_move = (z, y, x)

    if best_move is None:
        # Fallback: choose first empty cell (should not happen)
        best_move = empty_cells[0]

    return best_move
