
import copy

def get_pieces(board, player):
    """Return list of (r,c) coordinates for player's pieces."""
    return [(r, c) for r in range(8) for c in range(8) if board[r][c] == player]

def count_components(board, player):
    """Count connected components using 8-connectivity."""
    pieces = get_pieces(board, player)
    if not pieces:
        return 0
    pieces_set = set(pieces)
    visited = set()
    components = 0
    for start in pieces:
        if start in visited:
            continue
        components += 1
        stack = [start]
        visited.add(start)
        while stack:
            r, c = stack.pop()
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in pieces_set and (nr, nc) not in visited:
                        visited.add((nr, nc))
                        stack.append((nr, nc))
    return components

def has_won(board, player):
    """Check if all player's pieces form a single connected group."""
    pieces = get_pieces(board, player)
    return len(pieces) > 0 and count_components(board, player) == 1

def get_line_count(board, r, c, dr, dc):
    """Count pieces in the line specified by direction from (r,c)."""
    count = 0
    if dr == 0:  # Horizontal
        for cc in range(8):
            if board[r][cc] != 0:
                count += 1
    elif dc == 0:  # Vertical
        for rr in range(8):
            if board[rr][c] != 0:
                count += 1
    elif dr == dc:  # Diagonal \ (r-c constant)
        diff = r - c
        for rr in range(8):
            cc = rr - diff
            if 0 <= cc < 8 and board[rr][cc] != 0:
                count += 1
    else:  # Diagonal / (r+c constant)
        s = r + c
        for rr in range(8):
            cc = s - rr
            if 0 <= cc < 8 and board[rr][cc] != 0:
                count += 1
    return count

def generate_moves(board, player):
    """Generate all legal moves for player."""
    moves = []
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    my_pieces = get_pieces(board, player)
    opponent = -player
    
    for r, c in my_pieces:
        for dr, dc in directions:
            count = get_line_count(board, r, c, dr, dc)
            if count == 0:
                continue
            nr, nc = r + dr * count, c + dc * count
            if not (0 <= nr < 8 and 0 <= nc < 8):
                continue
            if board[nr][nc] == player:
                continue
            
            # Check for opponent pieces in the path
            blocked = False
            for step in range(1, count):
                cr, cc = r + dr * step, c + dc * step
                if board[cr][cc] == opponent:
                    blocked = True
                    break
            if blocked:
                continue
            
            moves.append((r, c, nr, nc))
    return moves

def apply_move(board, move, player):
    """Return new board after applying move."""
    r, c, nr, nc = move
    new_board = [row[:] for row in board]
    new_board[r][c] = 0
    new_board[nr][nc] = player
    return new_board

def evaluate(board):
    """Evaluate position from perspective of player 1."""
    if has_won(board, 1):
        return 10000
    if has_won(board, -1):
        return -10000
    
    # Component difference: fewer components is better for me, worse for opponent
    my_comp = count_components(board, 1)
    opp_comp = count_components(board, -1)
    score = (opp_comp - my_comp) * 100
    
    # Clustering: lower variance is better for me (pieces close together)
    my_pieces = get_pieces(board, 1)
    opp_pieces = get_pieces(board, -1)
    
    if len(my_pieces) > 1:
        avg_r = sum(r for r, c in my_pieces) / len(my_pieces)
        avg_c = sum(c for r, c in my_pieces) / len(my_pieces)
        var = sum((r - avg_r) ** 2 + (c - avg_c) ** 2 for r, c in my_pieces) / len(my_pieces)
        score -= var * 3
    
    if len(opp_pieces) > 1:
        avg_r = sum(r for r, c in opp_pieces) / len(opp_pieces)
        avg_c = sum(c for r, c in opp_pieces) / len(opp_pieces)
        var = sum((r - avg_r) ** 2 + (c - avg_c) ** 2 for r, c in opp_pieces) / len(opp_pieces)
        score += var * 1.5  # Prefer opponent spread out
    
    return score

def minimax(board, depth, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning."""
    if depth == 0:
        return evaluate(board)
    
    player = 1 if maximizing else -1
    moves = generate_moves(board, player)
    
    if not moves:
        return -10000 if maximizing else 10000
    
    # Check immediate wins
    for move in moves:
        new_board = apply_move(board, move, player)
        if has_won(new_board, player):
            return 10000 if maximizing else -10000
    
    if maximizing:
        max_eval = -float('inf')
        for move in moves:
            new_board = apply_move(board, move, player)
            eval = minimax(new_board, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval)
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for move in moves:
            new_board = apply_move(board, move, player)
            eval = minimax(new_board, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval)
            beta = min(beta, eval)
            if beta <= alpha:
                break
        return min_eval

def policy(board):
    """Return best move string."""
    # Normalize board to list of lists
    if hasattr(board, 'tolist'):
        board = board.tolist()
    else:
        board = [list(row) for row in board]
    
    moves = generate_moves(board, 1)
    if not moves:
        return "0,0:0,0"  # Should not occur in valid game state
    
    # Check for immediate win
    for move in moves:
        new_board = apply_move(board, move, 1)
        if has_won(new_board, 1):
            r, c, nr, nc = move
            return f"{r},{c}:{nr},{nc}"
    
    # Move ordering: captures first, then center proximity
    def move_priority(m):
        r, c, nr, nc = m
        is_capture = board[nr][nc] == -1
        center_dist = abs(nr - 3.5) + abs(nc - 3.5)
        return (-int(is_capture), center_dist)
    
    moves.sort(key=move_priority)
    
    # Determine search depth based on branching factor
    if len(moves) <= 12:
        search_depth = 3
    else:
        search_depth = 2
    
    best_move = moves[0]
    best_score = -float('inf')
    
    for move in moves:
        new_board = apply_move(board, move, 1)
        score = minimax(new_board, search_depth - 1, -float('inf'), float('inf'), False)
        if score > best_score:
            best_score = score
            best_move = move
    
    r, c, nr, nc = best_move
    return f"{r},{c}:{nr},{nc}"
