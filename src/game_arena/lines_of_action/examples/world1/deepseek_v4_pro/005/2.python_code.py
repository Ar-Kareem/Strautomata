
import numpy as np
import time

DIRECTIONS = [
    (0, 1),   # horizontal right
    (0, -1),  # horizontal left
    (1, 0),   # vertical down
    (-1, 0),  # vertical up
    (1, 1),   # diagonal down-right
    (1, -1),  # diagonal down-left
    (-1, 1),  # diagonal up-right
    (-1, -1), # diagonal up-left
]

def count_pieces_in_line(board, r, c, dr, dc):
    """Count total pieces (both colors) in the line starting from (r,c) along direction (dr,dc)."""
    count = 1  # current piece
    # Forward direction
    nr, nc = r + dr, c + dc
    while 0 <= nr < 8 and 0 <= nc < 8:
        if board[nr, nc] != 0:
            count += 1
        nr += dr
        nc += dc
    # Backward direction
    nr, nc = r - dr, c - dc
    while 0 <= nr < 8 and 0 <= nc < 8:
        if board[nr, nc] != 0:
            count += 1
        nr -= dr
        nc -= dc
    return count

def get_legal_moves(board, player):
    """Generate all legal moves for the given player."""
    moves = []
    pieces = np.argwhere(board == player)
    for r, c in pieces:
        for dr, dc in DIRECTIONS:
            steps = count_pieces_in_line(board, r, c, dr, dc)
            nr = r + steps * dr
            nc = c + steps * dc
            # Check bounds
            if 0 <= nr < 8 and 0 <= nc < 8:
                # Check no enemy pieces in between
                valid = True
                for i in range(1, steps):
                    cr = r + i * dr
                    cc = c + i * dc
                    if board[cr, cc] == -player:
                        valid = False
                        break
                if not valid:
                    continue
                # Cannot land on own piece
                if board[nr, nc] == player:
                    continue
                moves.append(((r, c), (nr, nc)))
    return moves

def apply_move(board, move, player):
    """Return new board after applying move."""
    new_board = board.copy()
    (r1, c1), (r2, c2) = move
    new_board[r1, c1] = 0
    new_board[r2, c2] = player
    return new_board

def find_groups(board, player):
    """Find all connected components for the given player using 8-connectivity."""
    visited = np.zeros((8, 8), dtype=bool)
    groups = []
    pieces = np.argwhere(board == player)
    for r, c in pieces:
        if not visited[r, c]:
            group = []
            stack = [(r, c)]
            visited[r, c] = True
            while stack:
                cr, cc = stack.pop()
                group.append((cr, cc))
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = cr + dr, cc + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and not visited[nr, nc] and board[nr, nc] == player:
                            visited[nr, nc] = True
                            stack.append((nr, nc))
            groups.append(group)
    return groups

def heuristic(board, player):
    """Evaluate board from perspective of player."""
    opp = -player
    
    # Count pieces
    my_pieces = np.sum(board == player)
    opp_pieces = np.sum(board == opp)
    
    if my_pieces == 0:
        return -100000
    if opp_pieces == 0:
        return 100000
    
    # Find groups
    my_groups = find_groups(board, player)
    opp_groups = find_groups(board, opp)
    
    my_max_group_size = max(len(g) for g in my_groups) if my_groups else 0
    opp_max_group_size = max(len(g) for g in opp_groups) if opp_groups else 0
    
    # Win condition
    if my_max_group_size == my_pieces:
        return 100000
    if opp_max_group_size == opp_pieces:
        return -100000
    
    # Heuristic components
    score = 0
    
    # Primary: maximize my connectivity, minimize opponent's
    my_connectivity = my_max_group_size / my_pieces if my_pieces > 0 else 0
    opp_connectivity = opp_max_group_size / opp_pieces if opp_pieces > 0 else 0
    score += 2000 * (my_connectivity - opp_connectivity)
    
    # Number of my groups (fewer is better)
    score -= 500 * len(my_groups)
    score += 400 * len(opp_groups)
    
    # Center control and mobility
    center_weight = np.array([[4,3,2,1,1,2,3,4],
                              [3,2,1,0,0,1,2,3],
                              [2,1,0,0,0,0,1,2],
                              [1,0,0,0,0,0,0,1],
                              [1,0,0,0,0,0,0,1],
                              [2,1,0,0,0,0,1,2],
                              [3,2,1,0,0,1,2,3],
                              [4,3,2,1,1,2,3,4]])
    my_center_score = np.sum(center_weight[board == player])
    opp_center_score = np.sum(center_weight[board == opp])
    score += 10 * (my_center_score - opp_center_score)
    
    # Mobility: more legal moves is good
    my_moves = len(get_legal_moves(board, player))
    # Simulate opponent moves for mobility (just count quickly if not too many pieces)
    if opp_pieces < 10:
        opp_moves = len(get_legal_moves(board, opp))
    else:
        opp_moves = my_moves  # estimate
    score += 5 * (my_moves - opp_moves)
    
    return score

def minimax(board, depth, alpha, beta, maximizing, player, start_time, time_limit=0.95):
    """Minimax with alpha-beta pruning and time limit."""
    if time.time() - start_time > time_limit:
        raise TimeoutError()
    
    if depth == 0:
        return heuristic(board, player), None
    
    opp = -player
    current_player = player if maximizing else opp
    
    moves = get_legal_moves(board, current_player)
    if not moves:
        # No moves -> skip turn? In LOA, if no moves, game ends? 
        # Usually pass, but for heuristic just evaluate.
        return heuristic(board, player), None
    
    best_move = None
    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_player)
            eval, _ = minimax(new_board, depth-1, alpha, beta, False, player, start_time, time_limit)
            if eval > max_eval:
                max_eval = eval
                best_move = move
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval, best_move
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = apply_move(board, move, current_player)
            eval, _ = minimax(new_board, depth-1, alpha, beta, True, player, start_time, time_limit)
            if eval < min_eval:
                min_eval = eval
                best_move = move
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval, best_move

class TimeoutError(Exception):
    pass

def policy(board) -> str:
    board = np.array(board, dtype=np.int8)
    player = 1  # We are always player 1 in this API
    
    start_time = time.time()
    best_move = None
    depth = 1
    
    # Get all legal moves, if only one, return it immediately
    moves = get_legal_moves(board, player)
    if len(moves) == 1:
        r1, c1 = moves[0][0]
        r2, c2 = moves[0][1]
        return f"{r1},{c1}:{r2},{c2}"
    
    # Iterative deepening
    while True:
        try:
            eval, move = minimax(board, depth, -float('inf'), float('inf'), True, player, start_time, time_limit=0.9)
            if move is not None:
                best_move = move
            depth += 1
            if depth > 4:  # Reasonable limit given time constraints
                break
        except TimeoutError:
            break
        except Exception:
            break
    
    # Fallback: if no move found (should not happen), return first legal move
    if best_move is None and moves:
        best_move = moves[0]
    
    r1, c1 = best_move[0]
    r2, c2 = best_move[1]
    return f"{r1},{c1}:{r2},{c2}"
