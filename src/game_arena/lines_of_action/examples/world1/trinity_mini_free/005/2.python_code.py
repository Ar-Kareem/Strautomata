
import numpy as np

def policy(board):
    """
    Returns the optimal move for the current player using minimax with alpha-beta pruning.
    """
    # Generate all legal moves
    moves = generate_legal_moves(board)
    if not moves:
        return None  # No moves available (should not occur in valid games)
    
    # Initialize minimax parameters
    best_move = moves[0]
    best_score = -float('inf')
    alpha = -float('inf')
    beta = float('inf')
    
    # Evaluate each move
    for move in moves:
        new_board = make_move(board, move)
        score = minimax(new_board, depth=3, alpha=alpha, beta=beta, maximizing=True)
        if score > best_score:
            best_score = score
            best_move = move
    return best_move

def generate_legal_moves(board):
    """Generate all legal moves for the current player."""
    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:  # Current player's piece
                for dr, dc in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                    # Calculate target position
                    steps = 0
                    tr, tc = r + dr, c + dc
                    while 0 <= tr < 8 and 0 <= tc < 8:
                        steps += 1
                        # Count pieces in the line
                        if board[tr][tc] == 1:
                            # Valid move if steps match piece count
                            if steps == 1:
                                moves.append(f"{r},{c}:{tr},{tc}")
                            elif steps > 1:
                                # Check path for enemy pieces
                                path_clear = True
                                for i in range(1, steps):
                                    pi, pj = r + i*dr, c + i*dc
                                    if board[pi][pj] == -1:
                                        path_clear = False
                                        break
                                if path_clear:
                                    moves.append(f"{r},{c}:{tr},{tc}")
                        elif board[tr][tc] == -1:
                            break  # Enemy piece blocks further movement
                        tr += dr
                        tc += dc
    return moves

def make_move(board, move):
    """Apply a move to the board and capture enemy pieces."""
    r1, c1, r2, c2 = parse_move(move)
    board = np.copy(board)
    board[r1][c1] = 0  # Clear source
    board[r2][c2] = 1  # Move piece
    # Capture enemy pieces in the target row/col
    for r in range(8):
        if board[r][c2] == -1:
            board[r][c2] = 0
        if board[r1][r] == -1:
            board[r1][r] = 0
    return board

def parse_move(move):
    """Parse move string into coordinates."""
    r1, c1, r2, c2 = map(int, move.split(':'))
    return r1, c1, r2, c2

def minimax(board, depth, alpha, beta, maximizing):
    """Minimax with alpha-beta pruning."""
    if depth == 0 or is_terminal(board):
        return evaluate(board)
    
    if maximizing:
        value = -float('inf')
        for move in generate_legal_moves(board):
            new_board = make_move(board, move)
            value = max(value, minimax(new_board, depth-1, alpha, beta, False))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = float('inf')
        for move in generate_legal_moves(board):
            new_board = make_move(board, move)
            value = min(value, minimax(new_board, depth-1, alpha, beta, True))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value

def evaluate(board):
    """Evaluate board state using connectivity, mobility, and safety."""
    # Check for win/loss
    if is_win(board):
        return 1000 if board[0][0] == 1 else -1000
    
    # Count connected components
    comp_count = count_components(board)
    # Mobility score (higher is better)
    my_moves = len(generate_legal_moves(board))
    opp_moves = len(generate_legal_moves(np.copy(board) * -1))
    mobility = my_moves - opp_moves
    
    # Safety score (lower is better)
    safety = 0
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1:
                # Check for enemy pieces that can capture this piece
                for dr, dc in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                    tr, tc = r + dr, c + dc
                    while 0 <= tr < 8 and 0 <= tc < 8:
                        if board[tr][tc] == -1:
                            safety += 1
                        tr += dr
                        tc += dc
    
    # Weighted evaluation
    return (comp_count * -10) + (mobility * 5) - (safety * 2)

def is_win(board):
    """Check if all player's pieces are connected."""
    # Find all player pieces
    pieces = [(r, c) for r in range(8) for c in range(8) if board[r][c] == 1]
    if not pieces:
        return False
    
    # BFS to check connectivity
    start = pieces[0]
    visited = set()
    queue = [start]
    visited.add(start)
    
    while queue:
        r, c = queue.pop(0)
        for dr, dc in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
            tr, tc = r + dr, c + dc
            if 0 <= tr < 8 and 0 <= tc < 8 and board[tr][tc] == 1 and (tr, tc) not in visited:
                visited.add((tr, tc))
                queue.append((tr, tc))
    
    return len(visited) == len(pieces)

def count_components(board):
    """Count connected components of player's pieces."""
    visited = set()
    components = 0
    
    for r in range(8):
        for c in range(8):
            if board[r][c] == 1 and (r, c) not in visited:
                components += 1
                # BFS to mark connected pieces
                queue = [(r, c)]
                visited.add((r, c))
                while queue:
                    tr, tc = queue.pop(0)
                    for dr, dc in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
                        nr, nc = tr + dr, tc + dc
                        if 0 <= nr < 8 and 0 <= nc < 8 and board[nr][nc] == 1 and (nr, nc) not in visited:
                            visited.add((nr, nc))
                            queue.append((nr, nc))
    return components
