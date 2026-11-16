
import time
from typing import List, Tuple, Set

# Game constants
MAN_VALUE = 100
KING_VALUE = 160
CENTER_VALUE = 10
TIME_LIMIT = 0.9

def is_valid_square(r: int, c: int) -> bool:
    """Check if a square is valid (on board and dark)"""
    return 0 <= r < 8 and 0 <= c < 8 and (r + c) % 2 == 1

def get_directions(is_king: bool, color: str) -> List[Tuple[int, int]]:
    """Get movement directions based on piece type and color"""
    if is_king:
        return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    return [(-1, -1), (-1, 1)] if color == 'b' else [(1, -1), (1, 1)]

def generate_captures(my_men: Set, my_kings: Set, opp_men: Set, opp_kings: Set, 
                     color: str) -> List[Tuple]:
    """Generate all capturing moves (single jump for speed)"""
    captures = []
    occupied = my_men | my_kings | opp_men | opp_kings
    opp_pieces = opp_men | opp_kings
    
    # Men captures (forward only)
    for r, c in my_men:
        for dr, dc in get_directions(False, color):
            mid_r, mid_c = r + dr, c + dc
            land_r, land_c = r + 2*dr, c + 2*dc
            
            if (is_valid_square(mid_r, mid_c) and (mid_r, mid_c) in opp_pieces and
                is_valid_square(land_r, land_c) and (land_r, land_c) not in occupied):
                captures.append(((r, c), (land_r, land_c)))
    
    # King captures (any direction)
    for r, c in my_kings:
        for dr, dc in get_directions(True, color):
            step = 1
            while True:
                mid_r, mid_c = r + step*dr, c + step*dc
                if not is_valid_square(mid_r, mid_c) or (mid_r, mid_c) in occupied:
                    if (mid_r, mid_c) in opp_pieces:
                        land_step = step + 1
                        while True:
                            land_r, land_c = r + land_step*dr, c + land_step*dc
                            if not is_valid_square(land_r, land_c) or (land_r, land_c) in occupied:
                                break
                            captures.append(((r, c), (land_r, land_c)))
                            land_step += 1
                    break
                step += 1
    
    return captures

def generate_all_moves(my_men: Set, my_kings: Set, opp_men: Set, opp_kings: Set, 
                      color: str) -> List[Tuple]:
    """Generate all legal moves (prioritizing captures)"""
    captures = generate_captures(my_men, my_kings, opp_men, opp_kings, color)
    if captures:
        return captures
    
    # Regular moves
    moves = []
    occupied = my_men | my_kings | opp_men | opp_kings
    
    # Men moves (forward only)
    for r, c in my_men:
        for dr, dc in get_directions(False, color):
            new_r, new_c = r + dr, c + dc
            if is_valid_square(new_r, new_c) and (new_r, new_c) not in occupied:
                moves.append(((r, c), (new_r, new_c)))
    
    # King moves (any distance)
    for r, c in my_kings:
        for dr, dc in get_directions(True, color):
            step = 1
            while True:
                new_r, new_c = r + step*dr, c + step*dc
                if not is_valid_square(new_r, new_c) or (new_r, new_c) in occupied:
                    break
                moves.append(((r, c), (new_r, new_c)))
                step += 1
    
    return moves

def evaluate_position(my_men: Set, my_kings: Set, opp_men: Set, opp_kings: Set,
                     color: str) -> int:
    """Evaluate board position (higher is better)"""
    # Material advantage
    score = (len(my_men) - len(opp_men)) * MAN_VALUE
    score += (len(my_kings) - len(opp_kings)) * KING_VALUE
    
    # Position bonuses for men
    for r, c in my_men:
        if color == 'b':
            score += (7 - r) * 2  # Closer to promotion (row 0)
        else:
            score += r * 2  # Closer to promotion (row 7)
        
        # Center control
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += CENTER_VALUE
    
    # Centralize kings
    for r, c in my_kings:
        if 2 <= r <= 5 and 2 <= c <= 5:
            score += CENTER_VALUE
    
    return score

def apply_move(move: Tuple, my_men: Set, my_kings: Set, opp_men: Set, opp_kings: Set,
              color: str) -> Tuple[Set, Set, Set, Set]:
    """Apply a move and return new board state"""
    from_pos, to_pos = move
    fr, fc = from_pos
    tr, tc = to_pos
    
    new_my_men = my_men.copy()
    new_my_kings = my_kings.copy()
    new_opp_men = opp_men.copy()
    new_opp_kings = opp_kings.copy()
    opp_pieces = new_opp_men | new_opp_kings
    
    # Remove captured piece if jump
    if abs(fr - tr) == 2:
        mid_r, mid_c = (fr + tr) // 2, (fc + tc) // 2
        if (mid_r, mid_c) in opp_pieces:
            if (mid_r, mid_c) in new_opp_men:
                new_opp_men.remove((mid_r, mid_c))
            else:
                new_opp_kings.remove((mid_r, mid_c))
    
    # Move the piece
    if from_pos in new_my_men:
        new_my_men.remove(from_pos)
        # Promote if reaching last row
        if (color == 'b' and tr == 0) or (color == 'w' and tr == 7):
            new_my_kings.add(to_pos)
        else:
            new_my_men.add(to_pos)
    elif from_pos in new_my_kings:
        new_my_kings.remove(from_pos)
        new_my_kings.add(to_pos)
    
    return new_my_men, new_my_kings, new_opp_men, new_opp_kings

def minimax_search(my_men: Set, my_kings: Set, opp_men: Set, opp_kings: Set,
           color: str, depth: int, alpha: float, beta: float,
           maximizing: bool, start_time: float) -> Tuple:
    """Alpha-beta minimax search"""
    if time.time() - start_time > TIME_LIMIT:
        return None, None
    
    moves = generate_all_moves(my_men, my_kings, opp_men, opp_kings, color)
    
    if not moves:
        return (-10000 if maximizing else 10000), None
    
    if depth == 0:
        return evaluate_position(my_men, my_kings, opp_men, opp_kings, color), None
    
    opp_color = 'w' if color == 'b' else 'b'
    
    if maximizing:
        best_value = -float('inf')
        best_move = None
        
        for move in moves:
            new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
                move, my_men, my_kings, opp_men, opp_kings, color
            )
            
            value, _ = minimax_search(
                new_opp_men, new_opp_kings, new_my_men, new_my_kings,
                opp_color, depth-1, alpha, beta, False, start_time
            )
            
            if value is None:
                return None, None
            
            if value > best_value:
                best_value = value
                best_move = move
            
            alpha = max(alpha, value)
            if alpha >= beta:
                break
        
        return best_value, best_move
    else:
        best_value = float('inf')
        best_move = None
        
        for move in moves:
            new_my_men, new_my_kings, new_opp_men, new_opp_kings = apply_move(
                move, my_men, my_kings, opp_men, opp_kings, color
            )
            
            value, _ = minimax_search(
                new_opp_men, new_opp_kings, new_my_men, new_my_kings,
                opp_color, depth-1, alpha, beta, True, start_time
            )
            
            if value is None:
                return None, None
            
            if value < best_value:
                best_value = value
                best_move = move
            
            beta = min(beta, value)
            if alpha >= beta:
                break
        
        return best_value, best_move

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
          opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
          color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Select the best move using iterative deepening alpha-beta search.
    Always returns a legal move.
    """
    start_time = time.time()
    
    # Use sets for O(1) lookups
    my_men_set = set(my_men)
    my_kings_set = set(my_kings)
    opp_men_set = set(opp_men)
    opp_kings_set = set(opp_kings)
    
    # Generate all legal moves
    moves = generate_all_moves(my_men_set, my_kings_set, opp_men_set, opp_kings_set, color)
    
    # Safety fallback (should never trigger in valid games)
    if not moves:
        if my_men:
            pos = next(iter(my_men_set))
            dr = -1 if color == 'b' else 1
            return (pos, (pos[0] + dr, pos[1]))
        return ((0, 0), (0, 0))
    
    # Trivial case
    if len(moves) == 1:
        return moves[0]
    
    # Iterative deepening: increase depth until time runs out
    best_move = moves[0]
    for depth in range(1, 10):  # Max depth 9
        try:
            _, move = minimax_search(
                my_men_set, my_kings_set, opp_men_set, opp_kings_set,
                color, depth, -float('inf'), float('inf'), True, start_time
            )
            
            if move is not None:
                best_move = move
            else:
                break  # Time limit exceeded
        except:
            break  # Any error: use last best move
    
    return best_move
