
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    BOARD_SIZE = 15
    
    # Initialize board
    board = np.full((BOARD_SIZE, BOARD_SIZE), -1, dtype=int)
    occupied = set()
    for r, c in me:
        board[r, c] = 0
        occupied.add((r, c))
    for r, c in opp:
        board[r, c] = 1
        occupied.add((r, c))
    
    # Get valid moves
    valid_moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if valid_mask[r, c] and (r, c) not in occupied:
                valid_moves.append((r, c))
    
    if not valid_moves:
        return (7, 7)  # Fallback
    
    # Check for immediate win
    for move in valid_moves:
        r, c = move
        board[r, c] = 0
        if check_win(board, 0):
            return move
        board[r, c] = -1
    
    # Check for block
    for move in valid_moves:
        r, c = move
        board[r, c] = 1
        if check_win(board, 1):
            board[r, c] = -1
            return move
        board[r, c] = -1
    
    # Generate candidate moves
    if me:
        candidates = generate_candidate_moves(board, occupied, valid_mask, BOARD_SIZE)
    else:
        candidates = valid_moves
    
    # Select best move
    best_move = None
    best_score = float('-inf')
    
    for move in candidates:
        r, c = move
        score = evaluate_move(board, move, 0)
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is not None:
        return best_move
    
    return (7, 7)

def get_neighbors(r, c, BOARD_SIZE):
    """Get valid neighbor positions on hex grid"""
    neighbors = []
    # Same column
    for dr in [-1, 1]:
        nr, nc = r + dr, c
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            neighbors.append((nr, nc))
    # Left and right columns
    if c % 2 == 0:  # Even column
        left_offsets = [(-1, -1), (0, -1)]
        right_offsets = [(0, 1), (1, 1)]
    else:  # Odd column
        left_offsets = [(0, -1), (1, -1)]
        right_offsets = [(-1, 1), (0, 1)]
    for dr, dc in left_offsets:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            neighbors.append((nr, nc))
    for dr, dc in right_offsets:
        nr, nc = r + dr, c + dc
        if 0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE:
            neighbors.append((nr, nc))
    return neighbors

def generate_candidate_moves(board, occupied, valid_mask, BOARD_SIZE):
    """Generate candidate moves near existing stones using BFS"""
    candidates = set()
    if not occupied:
        return [(7, 7)]
    frontier = list(occupied)
    visited = set(occupied)
    distance = 0
    while frontier and distance < 2:
        next_frontier = []
        for r, c in frontier:
            for nr, nc in get_neighbors(r, c, BOARD_SIZE):
                if (nr, nc) not in visited and valid_mask[nr, nc]:
                    candidates.add((nr, nc))
                    visited.add((nr, nc))
                    next_frontier.append((nr, nc))
        frontier = next_frontier
        distance += 1
    return list(candidates)

def check_win(board, player):
    """Check if player has won"""
    me = []
    opp = []
    for r in range(15):
        for c in range(15):
            if board[r, c] == player:
                me.append((r, c))
            elif board[r, c] == 1 - player:
                opp.append((r, c))
    
    groups = get_connected_groups(board)
    for group in groups:
        if group['player'] == player:
            # Check for ring
            if has_ring(board, group):
                return True
            # Check for fork (3+ edges)
            edges = count_edges(board, group)
            if edges >= 3:
                return True
            # Check for bridge (2+ corners)
            corners = count_corners(group)
            if corners >= 2:
                return True
    return False

def get_connected_groups(board):
    """Get all connected groups of stones"""
    BOARD_SIZE = 15
    visited = set()
    groups = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if board[r, c] != -1 and (r, c) not in visited:
                player = board[r, c]
                group = {'player': player, 'cells': set(), 'corners': set(), 'edges': 0}
                queue = [(r, c)]
                visited.add((r, c))
                while queue:
                    cr, cc = queue.pop(0)
                    group['cells'].add((cr, cc))
                    for nr, nc in get_neighbors(cr, cc, BOARD_SIZE):
                        if board[nr, nc] == player and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
                # Count corners
                for cell in group['cells']:
                    corners = get_corners_touched(cell)
                    group['corners'].update(corners)
                groups.append(group)
    return groups

def get_corners_touched(cell):
    """Get which corners a cell touches"""
    r, c = cell
    corners = set()
    # Top-left corner
    if r == 0 and c == 0:
        corners.add('TL')
    # Top-right corner
    if r == 0 and c == 14:
        corners.add('TR')
    # Bottom-left corner
    if r == 14 and c == 0:
        corners.add('BL')
    # Bottom-right corner
    if r == 14 and c == 14:
        corners.add('BR')
    # Left edge corners (not top/bottom)
    if c == 0 and 0 < r < 14:
        corners.add('left')
    # Right edge corners (not top/bottom)
    if c == 14 and 0 < r < 14:
        corners.add('right')
    # Top edge corners (not left/right)
    if r == 0 and 0 < c < 14:
        corners.add('top')
    # Bottom edge corners (not left/right)
    if r == 14 and 0 < c < 14:
        corners.add('bottom')
    return corners

def count_corners(group):
    """Count how many corners/edges a group touches"""
    real_corners = {'TL', 'TR', 'BL', 'BR'}
    edge_corners = {'top', 'bottom', 'left', 'right'}
    corners = group['corners']
    corner_count = len(corners & real_corners)
    edge_count = len(corners & edge_corners)
    return corner_count + edge_count

def count_edges(board, group):
    """Count how many edges a group touches"""
    edges = set()
    for r, c in group['cells']:
        # Top edge (not corners)
        if r == 0 and 0 < c < 14:
            edges.add('top')
        # Bottom edge (not corners)
        if r == 14 and 0 < c < 14:
            edges.add('bottom')
        # Left edge (not corners)
        if c == 0 and 0 < r < 14:
            edges.add('left')
        # Right edge (not corners)
        if c == 14 and 0 < r < 14:
            edges.add('right')
    return len(edges)

def has_ring(board, group):
    """Check if group forms a ring"""
    BOARD_SIZE = 15
    empty_cells = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                   if board[r, c] == -1]
    
    for empty in empty_cells:
        if is_enclosed(board, group, empty):
            return True
    return False

def is_enclosed(board, group, empty_cell):
    """Check if empty cell is enclosed by group"""
    BOARD_SIZE = 15
    er, ec = empty_cell
    visited = set()
    queue = [(er, ec)]
    visited.add((er, ec))
    
    while queue:
        r, c = queue.pop(0)
        # If we reach edge, not enclosed
        if r == 0 or r == BOARD_SIZE - 1 or c == 0 or c == BOARD_SIZE - 1:
            return False
        for nr, nc in get_neighbors(r, c, BOARD_SIZE):
            if (nr, nc) not in visited:
                if board[nr, nc] == -1:  # Empty
                    visited.add((nr, nc))
                    queue.append((nr, nc))
                elif nr in group['cells']:  # Part of ring
                    visited.add((nr, nc))
    return True

def evaluate_move(board, move, player):
    """Evaluate move score based on potential winning structures"""
    r, c = move
    board[r, c] = player
    
    score = 0
    
    # Check if this move wins
    if check_win(board, player):
        board[r, c] = -1
        return 1000000
    
    # Check structures after move
    groups = get_connected_groups(board)
    for group in groups:
        if group['player'] == player:
            # Ring potential
            if has_ring(board, group):
                score += 50000
            # Fork potential (3+ edges)
            edges = count_edges(board, group)
            if edges >= 2:
                score += 10000 * edges
            # Bridge potential (2+ corners)
            corners = count_corners(group)
            if corners >= 1:
                score += 5000 * corners
    
    board[r, c] = -1
    return score
