
import numpy as np

# Piece-square table encoding strategic square values
PIECE_SQUARE_TABLE = np.array([
    [100, -20, 10, 5, 5, 10, -20, 100],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [10, -2, 1, 1, 1, 1, -2, 10],
    [5, -2, 1, 1, 1, 1, -2, 5],
    [5, -2, 1, 1, 1, 1, -2, 5],
    [10, -2, 1, 1, 1, 1, -2, 10],
    [-20, -50, -2, -2, -2, -2, -50, -20],
    [100, -20, 10, 5, 5, 10, -20, 100]
])

DIRECTIONS = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
CORNERS = {"a1", "a8", "h1", "h8"}
X_SQUARES = {"b2", "b7", "g2", "g7"}
C_SQUARES = {"a2", "a7", "h2", "h7", "b1", "b8", "g1", "g8"}

def policy(you: np.ndarray, opponent: np.ndarray) -> str:
    """Main policy: returns the best move using heuristic evaluation."""
    legal_moves = get_legal_moves(you, opponent)
    if not legal_moves:
        return "pass"
    
    # Always prioritize corners
    corner_moves = [m for m in legal_moves if m in CORNERS]
    if corner_moves:
        return corner_moves[0]
    
    # Categorize moves by risk
    safe_moves, risky_moves, very_risky_moves = [], [], []
    for move in legal_moves:
        if move in X_SQUARES:
            (safe_moves if leads_to_corner(move, you, opponent) else very_risky_moves).append(move)
        elif move in C_SQUARES:
            (safe_moves if leads_to_corner(move, you, opponent) else risky_moves).append(move)
        else:
            safe_moves.append(move)
    
    # Evaluate moves from safest category available
    moves_to_consider = safe_moves or risky_moves or very_risky_moves
    best_move = moves_to_consider[0]
    best_score = float('-inf')
    
    for move in moves_to_consider:
        score = evaluate_move(move, you, opponent)
        if move in C_SQUARES and move not in safe_moves:
            score -= 3000
        elif move in X_SQUARES and move not in safe_moves:
            score -= 5000
        
        if score > best_score:
            best_score, best_move = score, move
    
    return best_move

def leads_to_corner(move: str, you: np.ndarray, opponent: np.ndarray) -> bool:
    """Check if move is adjacent to an empty corner."""
    adjacent = {
        "b2": (0,0), "a2": (0,0), "b1": (0,0),
        "b7": (7,0), "a7": (7,0), "b8": (7,0),
        "g2": (0,7), "h2": (0,7), "g1": (0,7),
        "g7": (7,7), "h7": (7,7), "g8": (7,7)
    }
    if move in adjacent:
        r, c = adjacent[move]
        return you[r][c] == 0 and opponent[r][c] == 0
    return False

def get_legal_moves(you: np.ndarray, opponent: np.ndarray) -> list:
    """Get all legal moves in algebraic notation."""
    moves = []
    for r in range(8):
        for c in range(8):
            if you[r][c] == 0 and opponent[r][c] == 0 and is_legal_move(r, c, you, opponent):
                moves.append(convert_to_algebraic(r, c))
    return moves

def is_legal_move(r: int, c: int, you: np.ndarray, opponent: np.ndarray) -> bool:
    """Check if a move at (r, c) flips any opponent discs."""
    for dr, dc in DIRECTIONS:
        if can_flip_in_direction(r, c, dr, dc, you, opponent):
            return True
    return False

def can_flip_in_direction(r: int, c: int, dr: int, dc: int, you: np.ndarray, opponent: np.ndarray) -> bool:
    """Check if any discs flip in direction (dr, dc)."""
    r_curr, c_curr = r + dr, c + dc
    if not (0 <= r_curr < 8 and 0 <= c_curr < 8 and opponent[r_curr][c_curr] == 1):
        return False
    
    while 0 <= r_curr < 8 and 0 <= c_curr < 8:
        if you[r_curr][c_curr] == 1:
            return True
        if opponent[r_curr][c_curr] == 0:
            return False
        r_curr += dr
        c_curr += dc
    return False

def convert_to_algebraic(r: int, c: int) -> str:
    """Convert (r, c) to algebraic notation (e.g., 'd3')."""
    return f"{chr(ord('a') + c)}{r + 1}"

def convert_from_algebraic(move: str) -> tuple:
    """Convert algebraic notation to (r, c)."""
    return int(move[1]) - 1, ord(move[0]) - ord('a')

def evaluate_move(move: str, you: np.ndarray, opponent: np.ndarray) -> float:
    """Evaluate move by simulating it and scoring the resulting position."""
    r, c = convert_from_algebraic(move)
    new_you, new_opponent = simulate_move(r, c, you, opponent)
    score = evaluate_position(new_you, new_opponent)
    
    # Edge bonus for non-corners
    if (r in {0, 7} or c in {0, 7}) and move not in CORNERS:
        score += 1000
    
    return score

def evaluate_position(you: np.ndarray, opponent: np.ndarray) -> float:
    """Score a board position using multiple heuristics."""
    # Piece-square values
    score = np.sum(you * PIECE_SQUARE_TABLE) - np.sum(opponent * PIECE_SQUARE_TABLE)
    
    # Corner occupation bonus
    for r, c in [(0,0), (0,7), (7,0), (7,7)]:
        if you[r][c]:
            score += 500
        if opponent[r][c]:
            score -= 500
    
    # Mobility difference
    our_moves = len(get_legal_moves(you, opponent))
    opp_moves = len(get_legal_moves(opponent, you))
    score += (our_moves - opp_moves) * 50
    
    # Late-game disc maximization
    if np.sum(you) + np.sum(opponent) > 50:
        score += (np.sum(you) - np.sum(opponent)) * 20
    
    return score

def simulate_move(r: int, c: int, you: np.ndarray, opponent: np.ndarray) -> tuple:
    """Simulate placing a disc at (r, c) and flipping discs."""
    new_you = you.copy()
    new_opponent = opponent.copy()
    new_you[r][c] = 1
    
    for dr, dc in DIRECTIONS:
        for flip_r, flip_c in get_discs_to_flip(r, c, dr, dc, you, opponent):
            new_you[flip_r][flip_c] = 1
            new_opponent[flip_r][flip_c] = 0
    
    return new_you, new_opponent

def get_discs_to_flip(r: int, c: int, dr: int, dc: int, you: np.ndarray, opponent: np.ndarray) -> list:
    """Get opponent discs that would be flipped in direction (dr, dc)."""
    discs = []
    r_curr, c_curr = r + dr, c + dc
    
    while 0 <= r_curr < 8 and 0 <= c_curr < 8:
        if opponent[r_curr][c_curr] == 0:
            return []
        if you[r_curr][c_curr] == 1:
            return discs
        discs.append((r_curr, c_curr))
        r_curr += dr
        c_curr += dc
    
    return []
