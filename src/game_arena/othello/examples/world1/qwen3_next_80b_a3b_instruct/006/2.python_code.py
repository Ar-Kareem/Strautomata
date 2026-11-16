
import numpy as np
import time

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    # Define board size and coordinate mapping
    BOARD_SIZE = 8
    COLS = "abcdefgh"
    
    # Combine board state
    board = you + opponent
    empty = (board == 0)
    
    # Get all legal moves
    legal_moves = get_legal_moves(you, opponent)
    
    # If no legal moves, pass
    if len(legal_moves) == 0:
        return "pass"
    
    # If only one move, return it immediately
    if len(legal_moves) == 1:
        move = legal_moves[0]
        return COLS[move[1]] + str(move[0] + 1)
    
    # Time budget
    start_time = time.time()
    timeout = 0.9  # Leave 0.1s for safety

    # Evaluate moves with minimax + alpha-beta pruning
    # Sort moves: prioritize corners, then edges, then others
    move_scores = {}
    for move in legal_moves:
        r, c = move
        score = 0
        if (r == 0 or r == 7) and (c == 0 or c == 7):
            score = 10000  # Corner
        elif r == 0 or r == 7 or c == 0 or c == 7:
            score = 1000   # Edge
        else:
            score = 100    # Interior
        # Add heuristic that favors moves that don't enable opponent to take corner
        move_scores[move] = score
    
    # Sort moves by priority
    sorted_moves = sorted(legal_moves, key=lambda m: move_scores[m], reverse=True)
    
    # Start minimax search
    best_move = sorted_moves[0]
    best_score = float('-inf')
    
    # Depth: start with 5, if time allows go deeper
    depth = 5
    try:
        for move in sorted_moves:
            if time.time() - start_time > timeout:
                break
            # Make temporary move
            new_you, new_opponent = make_move(you, opponent, move)
            # Evaluate move
            score = -minimax(new_opponent, new_you, depth-1, float('-inf'), float('inf'), start_time, timeout)
            if score > best_score:
                best_score = score
                best_move = move
    except Exception:
        pass  # If any issue, return the best move found so far

    # Return the best move in algebraic notation
    r, c = best_move
    return COLS[c] + str(r + 1)

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> list:
    """Return list of (row, col) that are legal moves for 'you'."""
    legal_moves = []
    board = you + opponent
    empty = (board == 0)
    
    for r in range(8):
        for c in range(8):
            if empty[r][c] and is_legal_move(you, opponent, r, c):
                legal_moves.append((r, c))
    return legal_moves

def is_legal_move(you: np.ndarray, opponent: np.ndarray, r: int, c: int) -> bool:
    """Check if placing a disc at (r, c) is legal."""
    if you[r][c] or opponent[r][c]:
        return False
    
    # 8 directions: dr, dc
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        found_opponent = False
        while 0 <= nr < 8 and 0 <= nc < 8:
            if opponent[nr][nc]:
                found_opponent = True
            elif you[nr][nc] and found_opponent:
                return True
            else:
                break  # empty or own disc without bracketing
            nr += dr
            nc += dc
    return False

def make_move(you: np.ndarray, opponent: np.ndarray, move: tuple) -> tuple:
    """Return new (you, opponent) after making move."""
    r, c = move
    new_you = you.copy()
    new_opponent = opponent.copy()
    
    new_you[r][c] = 1  # Place own disc
    
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        flip_list = []
        while 0 <= nr < 8 and 0 <= nc < 8:
            if opponent[nr][nc]:
                flip_list.append((nr, nc))
            elif new_you[nr][nc] and flip_list:
                # Flip all discs in flip_list
                for fr, fc in flip_list:
                    new_you[fr][fc] = 1
                    new_opponent[fr][fc] = 0
                break
            else:
                break
            nr += dr
            nc += dc
    
    return new_you, new_opponent

def count_discs(you: np.ndarray) -> int:
    return np.sum(you)

def mobility(you: np.ndarray, opponent: np.ndarray) -> int:
    """Return difference in number of legal moves between you and opponent."""
    your_moves = len(get_legal_moves(you, opponent))
    opponent_moves = len(get_legal_moves(opponent, you))
    return your_moves - opponent_moves

def stability(you: np.ndarray, opponent: np.ndarray) -> int:
    """Estimate stability of discs (hard to flip)."""
    # A simple heuristic: count discs that are adjacent to corners or on edges with neighbors
    # This is very simplified; full stability is complex but expensive.
    stable_count = 0
    for r in range(8):
        for c in range(8):
            if you[r][c]:
                # Corner discs are always stable
                if (r == 0 or r == 7) and (c == 0 or c == 7):
                    stable_count += 1
                # Edge disc with stable neighbor
                elif r == 0 or r == 7 or c == 0 or c == 7:
                    # Check if at least one adjacent disc is yours and not on an edge
                    neighbors = [(r+dr, c+dc) for dr in [-1,0,1] for dc in [-1,0,1] if (dr,dc) != (0,0)]
                    for nr, nc in neighbors:
                        if 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc]:
                            # This is a crude proxy for stability
                            stable_count += 0.5
                            break
                # Interior disc with at least two neighbors
                else:
                    neighbors = [(r+dr, c+dc) for dr in [-1,0,1] for dc in [-1,0,1] if (dr,dc) != (0,0)]
                    your_neighbors = sum(1 for nr, nc in neighbors if 0 <= nr < 8 and 0 <= nc < 8 and you[nr][nc])
                    if your_neighbors >= 3:  # Well surrounded
                        stable_count += 1
    return stable_count

def evaluate(you: np.ndarray, opponent: np.ndarray) -> float:
    """Evaluation function for board state."""
    # Weights for evaluation components
    CORNER_WEIGHT = 1000
    EDGE_WEIGHT = 100
    MOBILITY_WEIGHT = 10
    STABILITY_WEIGHT = 50
    DISC_WEIGHT = 1
    
    # Corner control
    corners = [(0,0), (0,7), (7,0), (7,7)]
    your_corners = sum(1 for r, c in corners if you[r][c])
    opp_corners = sum(1 for r, c in corners if opponent[r][c])
    corner_diff = your_corners - opp_corners
    
    # Edge control (non-corner edges)
    edges = [(0,i) for i in range(1,7)] + [(7,i) for i in range(1,7)] + [(i,0) for i in range(1,7)] + [(i,7) for i in range(1,7)]
    your_edges = sum(1 for r, c in edges if you[r][c])
    opp_edges = sum(1 for r, c in edges if opponent[r][c])
    edge_diff = your_edges - opp_edges
    
    # Total discs
    your_discs = count_discs(you)
    opp_discs = count_discs(opponent)
    disc_diff = your_discs - opp_discs
    
    # Mobility
    mob_diff = mobility(you, opponent)
    
    # Stability
    stab_diff = stability(you, opponent) - stability(opponent, you)
    
    # Combine
    score = (CORNER_WEIGHT * corner_diff +
             EDGE_WEIGHT * edge_diff +
             MOBILITY_WEIGHT * mob_diff +
             STABILITY_WEIGHT * stab_diff +
             DISC_WEIGHT * disc_diff)
    
    return score

def minimax(you: np.ndarray, opponent: np.ndarray, depth: int, alpha: float, beta: float, start_time: float, timeout: float) -> float:
    """Minimax with alpha-beta pruning."""
    if time.time() - start_time > timeout:
        raise TimeoutError("Timeout")
    
    # Terminal conditions
    your_moves = get_legal_moves(you, opponent)
    opp_moves = get_legal_moves(opponent, you)
    
    if depth == 0 or (len(your_moves) == 0 and len(opp_moves) == 0):
        return evaluate(you, opponent)
    
    # If no moves for current player, let opponent move (pass)
    if len(your_moves) == 0:
        return -minimax(opponent, you, depth, -beta, -alpha, start_time, timeout)
    
    # Maximize current player's score
    best_value = float('-inf')
    # Try each legal move
    for move in your_moves:
        new_you, new_opponent = make_move(you, opponent, move)
        try:
            value = -minimax(new_opponent, new_you, depth - 1, -beta, -alpha, start_time, timeout)
            best_value = max(best_value, value)
            alpha = max(alpha, best_value)
            if alpha >= beta:
                break  # Beta cutoff
        except TimeoutError:
            raise  # Propagate timeout
    
    return best_value
