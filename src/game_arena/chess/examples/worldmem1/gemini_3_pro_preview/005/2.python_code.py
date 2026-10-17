
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    A strong greedy chess policy that evaluates moves based on material, safety, and centrality.
    """
    
    # 1. Setup Constants and Board
    color_map = {'white': 'w', 'black': 'b'}
    my_color = color_map[to_play]
    opp_color = 'b' if my_color == 'w' else 'w'
    
    # Piece Values
    values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    files = 'abcdefgh'
    
    # Board representation 8x8: board[rank_idx][file_idx]
    board = [[None for _ in range(8)] for _ in range(8)]
    my_pieces = []
    
    def to_coords(sq_str):
        f = files.index(sq_str[0])
        r = int(sq_str[1]) - 1
        return f, r

    for sq, p_code in pieces.items():
        f, r = to_coords(sq)
        board[r][f] = p_code
        if p_code[0] == my_color:
            my_pieces.append((sq, p_code[1], f, r))

    # 2. Helper Functions for Geometry and Safety
    
    def is_path_clear(x1, y1, x2, y2):
        """Checks if the path between two squares is empty (for sliding pieces)."""
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        if steps == 0: return True
        sx = 0 if dx == 0 else dx // abs(dx)
        sy = 0 if dy == 0 else dy // abs(dy)
        for i in range(1, steps):
            if board[y1 + i*sy][x1 + i*sx] is not None:
                return False
        return True

    def get_attackers(tx, ty, aggressor_color):
        """Returns a sorted list of piece values of aggressor_color attacking (tx, ty)."""
        attackers = []
        pawn_dir = 1 if aggressor_color == 'w' else -1
        
        for y in range(8):
            for x in range(8):
                p = board[y][x]
                if p and p[0] == aggressor_color:
                    pt = p[1]
                    dx, dy = abs(tx - x), abs(ty - y)
                    is_hit = False
                    
                    if pt == 'P':
                        # Pawn attacks diagonally forward
                        if dx == 1 and (ty - y) == pawn_dir: 
                            is_hit = True
                    elif pt == 'N':
                        if (dx, dy) in [(1, 2), (2, 1)]: is_hit = True
                    elif pt == 'K':
                        if dx <= 1 and dy <= 1: is_hit = True
                    elif pt == 'B':
                        if dx == dy and is_path_clear(x, y, tx, ty): is_hit = True
                    elif pt == 'R':
                        if (dx == 0 or dy == 0) and is_path_clear(x, y, tx, ty): is_hit = True
                    elif pt == 'Q':
                        if (dx == dy or dx == 0 or dy == 0) and is_path_clear(x, y, tx, ty): is_hit = True
                    
                    if is_hit:
                        attackers.append(values[pt])
        return sorted(attackers)

    def can_reach_pseudo(ptype, fx, fy, tx, ty, capture):
        """Checks if a piece type can geometrically move from source to dest."""
        dx = abs(tx - fx)
        dy = abs(ty - fy)
        
        if ptype == 'N': return (dx, dy) in [(1, 2), (2, 1)]
        if ptype == 'B': return dx == dy and is_path_clear(fx, fy, tx, ty)
        if ptype == 'R': return (dx == 0 or dy == 0) and is_path_clear(fx, fy, tx, ty)
        if ptype == 'Q': return (dx == dy or dx == 0 or dy == 0) and is_path_clear(fx, fy, tx, ty)
        if ptype == 'K': return dx <= 1 and dy <= 1
        if ptype == 'P':
            d = 1 if my_color == 'w' else -1
            if capture:
                # Diagonal capture
                return dx == 1 and (ty - fy) == d
            else:
                # Push
                if dx == 0 and (ty - fy) == d: return True
                # Double Push
                if dx == 0 and (ty - fy) == 2*d:
                    start_rank = 1 if my_color == 'w' else 6
                    return fy == start_rank and is_path_clear(fx, fy, tx, ty)
        return False

    # 3. Evaluate Moves
    best_move = random.choice(legal_moves) if legal_moves else ''
    best_score = -float('inf')

    # Quick checkmate detection
    for move in legal_moves:
        if '#' in move: return move, memory

    for move in legal_moves:
        score = 0.0
        
        # --- Parsing SAN ---
        clean = move.replace('+', '').replace('#', '')
        
        # Handle Castling
        if clean == 'O-O':
            score += 25
            fx, fy = (-1, -1) # Dummy, logic handled via bonus
        elif clean == 'O-O-O':
            score += 25
            fx, fy = (-1, -1)
        else:
            # Handle Promotion
            promo_val = 0
            if '=' in clean:
                parts = clean.split('=')
                clean = parts[0]
                promo_char = parts[1]
                promo_val = values.get(promo_char, 0) - 100 # Gain over pawn
            score += promo_val
            
            # Destination Square
            dest_str = clean[-2:]
            tf, tr = to_coords(dest_str)
            
            # Identify Move Type
            is_capture = 'x' in clean
            if clean[0] in 'NBRQK':
                ptype = clean[0]
                prefix = clean[1:-2]
            else:
                ptype = 'P'
                prefix = clean[:-2]
            
            if 'x' in prefix: prefix = prefix.replace('x', '')
            
            # Disambiguation hints
            hint_f = -1
            hint_r = -1
            for c in prefix:
                if c in files: hint_f = files.index(c)
                elif c in '12345678': hint_r = int(c) - 1
            
            # Find Source Square (fx, fy)
            fx, fy = -1, -1
            for sq, p, pf, pr in my_pieces:
                if p != ptype: continue
                # Match hints
                if hint_f != -1 and pf != hint_f: continue
                if hint_r != -1 and pr != hint_r: continue
                # Match geometric possibility
                if can_reach_pseudo(ptype, pf, pr, tf, tr, is_capture):
                    fx, fy = pf, pr
                    break
            
            # --- Evaluation ---
            if fx != -1:
                # 1. Material
                dest_piece = board[tr][tf]
                cap_val = 0
                if dest_piece:
                    cap_val = values.get(dest_piece[1], 0)
                elif is_capture and ptype == 'P':
                    cap_val = 100 # En passant assumption
                
                score += cap_val
                
                # 2. Positional (Center Control)
                # Manhattan distance to center (3.5, 3.5)
                old_dist = abs(3.5 - fx) + abs(3.5 - fy)
                new_dist = abs(3.5 - tf) + abs(3.5 - tr)
                score += (old_dist - new_dist) * 3.0
                
                # 3. Safety / Trade Logic
                opp_attackers = get_attackers(tf, tr, opp_color)
                
                if opp_attackers:
                    lowest_attacker = opp_attackers[0]
                    my_val = values[ptype]
                    
                    # Check if square is defended by us (Static check)
                    defenders = get_attackers(tf, tr, my_color)
                    is_defended = len(defenders) > 0

                    if not is_defended:
                        # Hanging piece
                        score -= my_val
                    else:
                        # Defended
                        # If we move a high value piece to a square attacked by lower value
                        # we likely lose material in the trade.
                        if lowest_attacker < my_val:
                            # Penalty is roughly the loss in value overlap
                            score -= (my_val - lowest_attacker)
        
        # Random noise to break ties
        score += random.uniform(0, 5)
        
        if score > best_score:
            best_score = score
            best_move = move

    return best_move, memory
