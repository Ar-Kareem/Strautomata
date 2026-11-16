
def policy(state, role):
    # Parse the state into a board dictionary: (x,y) -> color
    board = {}
    for prop in state:
        if prop[0] == "cell":
            x, y, color = int(prop[1]), int(prop[2]), prop[3]
            board[(x, y)] = color
    
    # Generate all legal moves for the current role
    moves = generate_moves(board, role)
    
    if not moves:
        return "noop"  # Should not happen in a valid game state
    
    # Check for immediate winning move
    for move in moves:
        if is_winning_move(move, role):
            return format_move(move)
    
    # Alpha-beta search with depth 4
    best_move = moves[0]
    best_score = -float('inf')
    
    # Sort moves for better pruning (captures and advanced moves first)
    sorted_moves = sort_moves(moves, board, role)
    
    for move in sorted_moves:
        new_board = apply_move(board, move, role)
        score = -alphabeta(new_board, opponent(role), 4, -float('inf'), float('inf'), role)
        if score > best_score:
            best_score = score
            best_move = move
    
    return format_move(best_move)


def generate_moves(board, role):
    """Generate all legal moves for the given role."""
    moves = []
    if role == "white":
        directions = [(0, 1), (-1, 1), (1, 1)]  # forward, diag-left, diag-right
    else:
        directions = [(0, -1), (-1, -1), (1, -1)]  # forward, diag-left, diag-right
    
    for (x, y), color in board.items():
        if color != role:
            continue
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 1 <= nx <= 8 and 1 <= ny <= 8:
                target = board.get((nx, ny))
                if dx == 0:  # Straight forward - must be empty
                    if target is None:
                        moves.append((x, y, nx, ny))
                else:  # Diagonal - can be empty or capture opponent
                    if target is None or target != role:
                        moves.append((x, y, nx, ny))
    return moves


def apply_move(board, move, role):
    """Return new board after applying move."""
    x1, y1, x2, y2 = move
    new_board = dict(board)
    del new_board[(x1, y1)]
    new_board[(x2, y2)] = role
    return new_board


def is_winning_move(move, role):
    """Check if move reaches the opposite end."""
    x1, y1, x2, y2 = move
    if role == "white" and y2 == 8:
        return True
    if role == "black" and y2 == 1:
        return True
    return False


def opponent(role):
    return "black" if role == "white" else "white"


def format_move(move):
    return f"move({move[0]},{move[1]},{move[2]},{move[3]})"


def alphabeta(board, role, depth, alpha, beta, perspective):
    """Alpha-beta search from perspective of original role."""
    # Check terminal conditions
    if has_won(board, "white"):
        return 100000 if perspective == "white" else -100000
    if has_won(board, "black"):
        return 100000 if perspective == "black" else -100000
    
    if depth == 0:
        return evaluate(board, perspective)
    
    moves = generate_moves(board, role)
    if not moves:
        return -100000  # No moves is a loss
    
    for move in moves:
        new_board = apply_move(board, move, role)
        value = -alphabeta(new_board, opponent(role), depth - 1, -beta, -alpha, perspective)
        if value >= beta:
            return beta
        if value > alpha:
            alpha = value
    return alpha


def has_won(board, role):
    """Check if role has any piece on the goal row."""
    if role == "white":
        for (x, y), color in board.items():
            if color == "white" and y == 8:
                return True
    else:
        for (x, y), color in board.items():
            if color == "black" and y == 1:
                return True
    return False


def evaluate(board, perspective):
    """Evaluate board from perspective of given role."""
    white_adv = 0
    black_adv = 0
    white_count = 0
    black_count = 0
    
    for (x, y), color in board.items():
        if color == "white":
            white_count += 1
            white_adv += y  # Higher row is better for white
        else:
            black_count += 1
            black_adv += (9 - y)  # Lower row (higher 9-y) is better for black
    
    if perspective == "white":
        score = (white_count - black_count) * 1000 + white_adv - black_adv
    else:
        score = (black_count - white_count) * 1000 + black_adv - white_adv
    
    return score


def sort_moves(moves, board, role):
    """Sort moves to improve alpha-beta pruning."""
    def move_priority(m):
        x1, y1, x2, y2 = m
        score = 0
        # Prioritize captures
        if (x2, y2) in board and board[(x2, y2)] != role:
            score += 1000
        # Prioritize forward progress
        if role == "white":
            score += y2 * 10
        else:
            score += (9 - y2) * 10
        return -score  # Negative for descending sort
    
    return sorted(moves, key=move_priority)
