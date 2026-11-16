
import math
from typing import List, Tuple

# Precompute all winning lines in a 3x3x3 cube
def generate_lines():
    lines = []
    # Lines within each layer (z constant)
    for z in range(3):
        # Rows (y constant)
        for y in range(3):
            lines.append([(z, y, x) for x in range(3)])
        # Columns (x constant)
        for x in range(3):
            lines.append([(z, y, x) for y in range(3)])
        # Diagonals in layer
        lines.append([(z, y, y) for y in range(3)])  # main diagonal
        lines.append([(z, y, 2 - y) for y in range(3)])  # anti-diagonal
    
    # Vertical lines (x,y constant, z varies)
    for x in range(3):
        for y in range(3):
            lines.append([(z, y, x) for z in range(3)])
    
    # Space diagonals (through cube corners)
    lines.append([(i, i, i) for i in range(3)])  # from (0,0,0) to (2,2,2)
    lines.append([(i, i, 2 - i) for i in range(3)])  # from (0,0,2) to (2,2,0)
    lines.append([(i, 2 - i, i) for i in range(3)])  # from (0,2,0) to (2,0,2)
    lines.append([(i, 2 - i, 2 - i) for i in range(3)])  # from (0,2,2) to (2,0,0)
    
    # Face diagonals? Actually those are already covered by layer diagonals and vertical combinations.
    # However, there are diagonals that go through layers but not space corners? For example, from (0,0,1) to (2,2,1) is not a straight line because x changes, y changes, z changes but not proportionally. Wait, in 3D, a line must have constant direction ratios. So the above covers all.
    return lines

ALL_LINES = generate_lines()

def check_winner(board):
    """Return 1 if player 1 wins, -1 if player -1 wins, 0 otherwise."""
    for line in ALL_LINES:
        values = [board[z][y][x] for (z, y, x) in line]
        if values[0] == values[1] == values[2] and values[0] != 0:
            return values[0]
    return 0

def get_empty_cells(board):
    empty = []
    for z in range(3):
        for y in range(3):
            for x in range(3):
                if board[z][y][x] == 0:
                    empty.append((z, y, x))
    return empty

def evaluate(board):
    """Heuristic evaluation of board from player 1's perspective."""
    score = 0
    for line in ALL_LINES:
        marks = [board[z][y][x] for (z, y, x) in line]
        p1 = marks.count(1)
        p2 = marks.count(-1)
        if p1 > 0 and p2 == 0:
            # line still possible for player 1
            score += 10 ** p1  # exponential bonus for more marks
        elif p2 > 0 and p1 == 0:
            # line still possible for opponent
            score -= 10 ** p2
        # if both have marks, line is dead, contribute 0
    return score

def minimax(board, depth, alpha, beta, maximizing_player, player):
    """Return (score, move) for the current player."""
    winner = check_winner(board)
    if winner != 0:
        return (winner * 10000, None)  # large win/loss score
    empty = get_empty_cells(board)
    if not empty:
        return (0, None)  # draw
    if depth == 0:
        return (evaluate(board), None)
    
    if maximizing_player:
        best_score = -math.inf
        best_move = None
        for (z, y, x) in empty:
            board[z][y][x] = player
            score, _ = minimax(board, depth - 1, alpha, beta, False, -player)
            board[z][y][x] = 0  # undo
            if score > best_score:
                best_score = score
                best_move = (z, y, x)
            alpha = max(alpha, best_score)
            if beta <= alpha:
                break
        return (best_score, best_move)
    else:
        best_score = math.inf
        best_move = None
        for (z, y, x) in empty:
            board[z][y][x] = -player  # opponent is -player
            score, _ = minimax(board, depth - 1, alpha, beta, True, player)
            board[z][y][x] = 0
            if score < best_score:
                best_score = score
                best_move = (z, y, x)
            beta = min(beta, best_score)
            if beta <= alpha:
                break
        return (best_score, best_move)

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    # Determine if we are player 1 or -1? According to spec, we are always player 1.
    # The opponent is -1.
    # Check current turn: count moves? Actually board may have any number of moves.
    # We assume it's our turn.
    player = 1
    
    # First, check if we can win immediately
    empty = get_empty_cells(board)
    for (z, y, x) in empty:
        board[z][y][x] = player
        if check_winner(board) == player:
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0
    
    # Check if opponent can win immediately (block)
    for (z, y, x) in empty:
        board[z][y][x] = -player
        if check_winner(board) == -player:
            board[z][y][x] = 0
            return (z, y, x)
        board[z][y][x] = 0
    
    # Use minimax with depth limit
    # Adjust depth based on number of empty cells to keep response fast
    depth = 4
    if len(empty) <= 6:
        depth = 6  # deeper near endgame
    elif len(empty) >= 20:
        depth = 3  # shallower early
    
    _, best_move = minimax(board, depth, -math.inf, math.inf, True, player)
    if best_move is not None:
        return best_move
    
    # Fallback: first empty cell
    return empty[0]

