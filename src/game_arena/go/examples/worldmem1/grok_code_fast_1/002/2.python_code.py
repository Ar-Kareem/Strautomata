
import copy
import random  # Not used but imported for potential future extensions

def find_group(board, r, c, player, visited):
    """Find connected group and its liberties."""
    direction = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    group = []
    liberties = set()
    queue = [(r, c)]
    visited.add((r, c))
    while queue:
        cr, cc = queue.pop(0)
        group.append((cr, cc))
        for dr, dc in direction:
            nr, nc = cr + dr, cc + dc
            if board[nr][nc] == 0:
                liberties.add((nr, nc))
            elif board[nr][nc] == player and (nr, nc) not in visited:
                visited.add((nr, nc))
                queue.append((nr, nc))
    return group, liberties

def find_liberties(board, r, c, player):
    """Get liberties of the group containing (r,c)."""
    visited = set()
    group, liberties = find_group(board, r, c, player, visited)
    return liberties

def is_self_capture(board, r, c):
    """Check if placing at (r,c) for player 1 is suicidal."""
    temp_board = copy.deepcopy(board)
    temp_board[r][c] = 1
    return len(find_liberties(temp_board, r, c, 1)) == 0

def is_legal(board, r, c):
    """Check if move at (r,c) is legal (empty and not suicidal)."""
    return board[r][c] == 0 and not is_self_capture(board, r, c)

def simulate_captures(board, r, c):
    """Simulate placing at (r,c), remove captured groups, return capture count."""
    temp_board = copy.deepcopy(board)
    temp_board[r][c] = 1
    captures = 0
    # Check opponent's groups for capture
    visited = set()
    for i in range(1, 20):
        for j in range(1, 20):
            if temp_board[i][j] == 2 and (i, j) not in visited:
                group, liberties = find_group(temp_board, i, j, 2, visited)
                if len(liberties) == 0:
                    for gr, gc in group:
                        temp_board[gr][gc] = 0
                    captures += len(group)
    return captures

def policy(me, opp, memory):
    # Initialize board: 21x21, borders -1, empty 0, me 1, opp 2
    board = [[-1] * 21 for _ in range(21)]
    for i in range(1, 20):
        for j in range(1, 20):
            board[i][j] = 0
    for r, c in me:
        board[r][c] = 1
    for r, c in opp:
        board[r][c] = 2
    
    # Find all legal moves
    legal_moves = []
    for r in range(1, 20):
        for c in range(1, 20):
            if is_legal(board, r, c):
                legal_moves.append((r, c))
    
    if not legal_moves:
        # Should not happen, but pass if somehow no moves
        return ((0, 0), memory)
    
    # Evaluate captures for each legal move
    best_move = None
    best_captures = -1
    for r, c in legal_moves:
        cap = simulate_captures(board, r, c)
        if cap > best_captures:
            best_captures = cap
            best_move = (r, c)
        elif cap == best_captures and (best_move is None or r < best_move[0] or (r == best_move[0] and c < best_move[1])):
            best_move = (r, c)
    
    if best_captures > 0:
        return (best_move, memory)
    
    # No captures: Play adjacent to opponent
    adjacent_moves = []
    direction = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    for r in range(1, 20):
        for c in range(1, 20):
            if board[r][c] == 0:  # Only consider empty spots
                for dr, dc in direction:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19 and board[nr][nc] == 2:  # Adjacent to opp
                        adjacent_moves.append((r, c))
                        break
    
    if adjacent_moves:
        # Select the one closest to top-left for determinism
        best_move = min(adjacent_moves, key=lambda x: (x[0], x[1]))
        return (best_move, memory)
    
    # No adjacent: Shuffle to make it aggressive in center-ish area
    # Play in a semi-central area, e.g., rows/cols 5-15
    central_moves = [m for m in legal_moves if 5 <= m[0] <= 15 and 5 <= m[1] <= 15]
    if central_moves:
        best_move = min(central_moves, key=lambda x: (x[0], x[1]))
        return (best_move, memory)
    
    # Fallback to any legal, top-left first
    best_move = min(legal_moves, key=lambda x: (x[0], x[1]))
    return (best_move, memory)
