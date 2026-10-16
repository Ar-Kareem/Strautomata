
import sys
from typing import List, Tuple

# Precompute all 49 winning lines
LINES = []

# Axis-aligned lines (27 total)
for i in range(3):
    for j in range(3):
        LINES.append([(i, j, k) for k in range(3)])  # Vary k
for i in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for j in range(3)])  # Vary j
for j in range(3):
    for k in range(3):
        LINES.append([(i, j, k) for i in range(3)])  # Vary i

# Face diagonals (18 total)
for i in range(3):
    LINES.append([(i, 0, 0), (i, 1, 1), (i, 2, 2)])
    LINES.append([(i, 0, 2), (i, 1, 1), (i, 2, 0)])
for j in range(3):
    LINES.append([(0, j, 0), (1, j, 1), (2, j, 2)])
    LINES.append([(0, j, 2), (1, j, 1), (2, j, 0)])
for k in range(3):
    LINES.append([(0, 0, k), (1, 1, k), (2, 2, k)])
    LINES.append([(0, 2, k), (1, 1, k), (2, 0, k)])

# Space diagonals (4 total)
LINES.append([(0, 0, 0), (1, 1, 1), (2, 2, 2)])
LINES.append([(0, 0, 2), (1, 1, 1), (2, 2, 0)])
LINES.append([(0, 2, 0), (1, 1, 1), (2, 0, 2)])
LINES.append([(2, 0, 0), (1, 1, 1), (0, 2, 2)])

# Map each cell to the lines that pass through it
LINES_THROUGH_CELL: dict[Tuple[int, int, int], list] = {}
for i in range(3):
    for j in range(3):
        for k in range(3):
            LINES_THROUGH_CELL[(i, j, k)] = []
for idx, line in enumerate(LINES):
    for cell in line:
        LINES_THROUGH_CELL[cell].append(idx)

INF = 10**9

def cell_centrality(cell: Tuple[int, int, int]) -> int:
    """Return centrality score: center=13, corner=7, face=5, edge=4"""
    i, j, k = cell
    if i == 1 and j == 1 and k == 1:
        return 13
    if i in (0, 2) and j in (0, 2) and k in (0, 2):
        return 7
    # Face centers have exactly two coordinates equal to 1 and one equal to 0 or 2
    if (i == 1 and j == 1 and k in (0, 2)) or \
       (i == 1 and k == 1 and j in (0, 2)) or \
       (j == 1 and k == 1 and i in (0, 2)):
        return 5
    return 4

# Static move ordering by centrality (descending)
CELL_ORDER = sorted([(i, j, k) for i in range(3) for j in range(3) for k in range(3)],
                    key=cell_centrality, reverse=True)

def is_win_fast(board: List[List[List[int]]], player: int, cell: Tuple[int, int, int]) -> bool:
    """Check if player won by placing a stone at cell (only checks lines through cell)"""
    for line_idx in LINES_THROUGH_CELL[cell]:
        a, b, c = LINES[line_idx]
        if board[a[0]][a[1]][a[2]] == player and \
           board[b[0]][b[1]][b[2]] == player and \
           board[c[0]][c[1]][c[2]] == player:
            return True
    return False

def evaluate(board: List[List[List[int]]]) -> int:
    """Heuristic evaluation from perspective of player 1 (positive = good for 1)"""
    score = 0
    for line in LINES:
        c1 = 0
        c_1 = 0
        for (i, j, k) in line:
            val = board[i][j][k]
            if val == 1:
                c1 += 1
            elif val == -1:
                c_1 += 1
        if c1 == 3:
            return INF
        if c_1 == 3:
            return -INF
        if c1 == 2 and c_1 == 0:
            score += 100  # Winning threat
        elif c_1 == 2 and c1 == 0:
            score -= 100  # Must block
        elif c1 == 1 and c_1 == 0:
            score += 10
        elif c_1 == 1 and c1 == 0:
            score -= 10
    return score

def minimax(board: List[List[List[int]]], depth: int, alpha: int, beta: int, maximizing: bool) -> int:
    """Minimax with alpha-beta pruning"""
    # Get empty cells in static order
    empty = [c for c in CELL_ORDER if board[c[0]][c[1]][c[2]] == 0]
    
    if not empty or depth == 0:
        return evaluate(board)
    
    if maximizing:
        max_eval = -INF
        for cell in empty:
            i, j, k = cell
            board[i][j][k] = 1
            if is_win_fast(board, 1, cell):
                board[i][j][k] = 0
                return INF
            eval = minimax(board, depth - 1, alpha, beta, False)
            board[i][j][k] = 0
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = INF
        for cell in empty:
            i, j, k = cell
            board[i][j][k] = -1
            if is_win_fast(board, -1, cell):
                board[i][j][k] = 0
                return -INF
            eval = minimax(board, depth - 1, alpha, beta, True)
            board[i][j][k] = 0
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def is_blocking_move(board: List[List[List[int]]], cell: Tuple[int, int, int]) -> bool:
    """Check if placing at cell blocks an opponent's immediate win"""
    i, j, k = cell
    for line_idx in LINES_THROUGH_CELL[cell]:
        line = LINES[line_idx]
        c_1 = 0
        c_0 = 0
        for (x, y, z) in line:
            val = board[x][y][z]
            if val == -1:
                c_1 += 1
            elif val == 0:
                c_0 += 1
        if c_1 == 2 and c_0 == 1:  # This cell is the empty one completing opponent's line
            return True
    return False

def policy(board: List[List[List[int]]]) -> Tuple[int, int, int]:
    """Return the next move as (i, j, k)"""
    # Collect empty cells
    empty_cells = [(i, j, k) for i in range(3) for j in range(3) for k in range(3) if board[i][j][k] == 0]
    
    if not empty_cells:
        # Should not happen in a valid game, but return center as fallback
        return (1, 1, 1)
    
    if len(empty_cells) == 1:
        return empty_cells[0]
    
    # Check for immediate winning move
    for cell in empty_cells:
        i, j, k = cell
        board[i][j][k] = 1
        if is_win_fast(board, 1, cell):
            board[i][j][k] = 0
            return cell
        board[i][j][k] = 0
    
    # Determine search depth based on game stage
    if len(empty_cells) <= 8:
        search_depth = 6
    elif len(empty_cells) <= 12:
        search_depth = 5
    else:
        search_depth = 4
    
    # Sort candidates: blocking moves first, then by centrality
    def sort_key(cell):
        block = 1 if is_blocking_move(board, cell) else 0
        cent = cell_centrality(cell)
        return (-block, -cent)  # Higher block (1) comes first, then higher centrality
    
    candidates = sorted(empty_cells, key=sort_key)
    
    best_move = candidates[0]
    best_score = -INF
    
    for cell in candidates:
        i, j, k = cell
        board[i][j][k] = 1
        score = minimax(board, search_depth - 1, -INF, INF, False)
        board[i][j][k] = 0
        
        if score > best_score:
            best_score = score
            best_move = cell
            if score == INF:  # Found a forced win
                break
    
    return best_move
