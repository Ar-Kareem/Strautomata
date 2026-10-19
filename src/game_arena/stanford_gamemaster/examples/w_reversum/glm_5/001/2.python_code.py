
def policy(state: list[list[object]], role: str) -> str:
    # Parse the state
    board = {}
    for prop in state:
        if prop[0] == "cell":
            row, col, color = int(prop[1]), int(prop[2]), prop[3]
            board[(row, col)] = color
    
    my_color = role
    opp_color = "blue" if role == "red" else "red"
    
    # Find all legal moves
    legal_moves = find_legal_moves(board, my_color, opp_color)
    
    if not legal_moves:
        # Fallback: return any empty cell
        for row in range(1, 7):
            for col in range(1, 7):
                if (row, col) not in board:
                    return f"move({row},{col})"
        return "move(1,1)"
    
    # Select best move
    best = select_move(board, legal_moves, my_color, opp_color)
    return f"move({best[0]},{best[1]})"


def get_flips(board, row, col, my_color, opp_color):
    """Get all pieces that would flip if we place at (row, col)."""
    flips = []
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for dr, dc in directions:
        r, c = row + dr, col + dc
        line = []
        while (r, c) in board and board[(r, c)] == opp_color:
            line.append((r, c))
            r += dr
            c += dc
        if line and (r, c) in board and board[(r, c)] == my_color:
            flips.extend(line)
    
    return flips


def find_legal_moves(board, my_color, opp_color):
    """Find all legal moves for the current player."""
    moves = []
    for row in range(1, 7):
        for col in range(1, 7):
            if (row, col) not in board:
                flips = get_flips(board, row, col, my_color, opp_color)
                if flips:
                    moves.append((row, col, flips))
    return moves


def select_move(board, legal_moves, my_color, opp_color):
    """Select the best move using positional weights and mobility."""
    # Positional weights for 6x6 Reversi board
    weights = [
        [120, -20,  20,  20, -20, 120],
        [-20, -40,  -5,  -5, -40, -20],
        [ 20,  -5,  15,  15,  -5,  20],
        [ 20,  -5,  15,  15,  -5,  20],
        [-20, -40,  -5,  -5, -40, -20],
        [120, -20,  20,  20, -20, 120]
    ]
    
    corners = {(1,1), (1,6), (6,1), (6,6)}
    
    # Find corners that are empty - adjacent cells are dangerous
    dangerous = set()
    corner_adj = {(1,1): [(1,2),(2,1),(2,2)], (1,6): [(1,5),(2,5),(2,6)],
                  (6,1): [(5,1),(5,2),(6,2)], (6,6): [(5,5),(5,6),(6,5)]}
    for corner, adj in corner_adj.items():
        if corner not in board:
            for a in adj:
                dangerous.add(a)
    
    total_pieces = len(board)
    is_endgame = total_pieces >= 30
    
    best_move = None
    best_score = -float('inf')
    
    for row, col, flips in legal_moves:
        score = weights[row-1][col-1]
        
        # Corner bonus
        if (row, col) in corners:
            score += 200
        
        # Danger penalty for cells near empty corners
        if (row, col) in dangerous:
            score -= 100
        
        # Flip count (more valuable in endgame)
        flip_value = 10 if is_endgame else 3
        score += len(flips) * flip_value
        
        # Mobility evaluation
        new_board = dict(board)
        new_board[(row, col)] = my_color
        for fr, fc in flips:
            new_board[(fr, fc)] = my_color
        
        my_moves = len(find_legal_moves(new_board, my_color, opp_color))
        opp_moves = len(find_legal_moves(new_board, opp_color, my_color))
        
        score += (my_moves - opp_moves) * 8
        
        # Prefer fewer flips early game (fewer pieces = more mobility)
        if total_pieces < 15:
            score -= len(flips) * 2
        
        if score > best_score:
            best_score = score
            best_move = (row, col)
    
    return best_move
