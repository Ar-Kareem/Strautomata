
import numpy as np

# Precomputed lines for 3x3x3 Tic Tac Toe
LINES = []

def initialize_lines():
    global LINES
    if LINES:
        return
    # 3x3x3 grid points
    points = [(x, y, z) for x in range(3) for y in range(3) for z in range(3)]
    
    # Helper: check if three points are collinear and equally spaced in 3D
    def collinear(p1, p2, p3):
        # vectors
        v1 = (p2[0]-p1[0], p2[1]-p1[1], p2[2]-p1[2])
        v2 = (p3[0]-p1[0], p3[1]-p1[1], p3[2]-p1[2])
        cross = (v1[1]*v2[2] - v1[2]*v2[1],
                 v1[2]*v2[0] - v1[0]*v2[2],
                 v1[0]*v2[1] - v1[1]*v2[0])
        if cross != (0,0,0):
            return False
        # Check integer multiples (1:2 or 2:1 ratio) to avoid non-adjacent collinear points
        # In 3x3x3 lines are of length 3, so any collinear points with max coordinate diff 2 are valid lines
        # We just need to ensure they form a line of length 3 exactly
        # All three points should be distinct and max pairwise diff in each dimension <= 2
        return True
    
    lines_set = set()
    for i in range(len(points)):
        for j in range(i+1, len(points)):
            for k in range(j+1, len(points)):
                if collinear(points[i], points[j], points[k]):
                    # verify they are evenly spaced (adjacent or with step)
                    # simple: check if middle point is the average
                    p1, p2, p3 = points[i], points[j], points[k]
                    # Check all orderings
                    triples = [(p1,p2,p3), (p1,p3,p2), (p2,p1,p3), (p2,p3,p1), (p3,p1,p2), (p3,p2,p1)]
                    valid = False
                    for a,b,c in triples:
                        if (2*b[0] == a[0]+c[0] and 2*b[1] == a[1]+c[1] and 2*b[2] == a[2]+c[2]):
                            valid = True
                            break
                    if valid:
                        lines_set.add(tuple(sorted([points[i], points[j], points[k]])))
    LINES = [list(line) for line in lines_set]

initialize_lines()

def evaluate(board):
    score = 0
    for line in LINES:
        cells = [board[x][y][z] for (x,y,z) in line]
        s = sum(cells)
        if s == 3:
            return 1000
        elif s == -3:
            return -1000
        elif s == 2 and 0 in cells:
            score += 10
        elif s == -2 and 0 in cells:
            score -= 10
        elif s == 1 and cells.count(0)==2:
            score += 1
        elif s == -1 and cells.count(0)==2:
            score -= 1
    return score

def is_terminal(board):
    for line in LINES:
        cells = [board[x][y][z] for (x,y,z) in line]
        if sum(cells) == 3 or sum(cells) == -3:
            return True
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    return False
    return True

def minimax(board, depth, alpha, beta, maximizing_player):
    if depth == 0 or is_terminal(board):
        return evaluate(board), None
    
    moves = []
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] == 0:
                    moves.append((x,y,z))
    
    if maximizing_player:
        max_eval = -float('inf')
        best_move = moves[0]
        for move in moves:
            x,y,z = move
            board[x][y][z] = 1
            eval, _ = minimax(board, depth-1, alpha, beta, False)
            board[x][y][z] = 0
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = moves[0]
        for move in moves:
            x,y,z = move
            board[x][y][z] = -1
            eval, _ = minimax(board, depth-1, alpha, beta, True)
            board[x][y][z] = 0
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

def policy(board):
    """
    Returns the best move for the current player (player 1).
    """
    board_np = board
    # Determine current depth by counting empty cells
    empty_count = sum(1 for x in range(3) for y in range(3) for z in range(3) if board_np[x][y][z]==0)
    if empty_count == 27:
        # First move: play center
        return (1,1,1)
    # Set depth for search: go deeper when fewer pieces on board
    if empty_count > 15:
        depth = 2
    elif empty_count > 10:
        depth = 4
    else:
        depth = 6
    
    _, move = minimax(board_np, depth, -float('inf'), float('inf'), True)
    return move
