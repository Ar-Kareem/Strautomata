
import math
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # 1. Setup Constants and Helpers
    color = 'w' if to_play == 'white' else 'b'
    enemy_color = 'b' if color == 'w' else 'w'
    
    files = 'abcdefgh'
    ranks = '12345678'
    
    # Piece values
    values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    def parse_sq(sq):
        return files.index(sq[0]), ranks.index(sq[1])
    
    # Build 8x8 Board
    board = [[None] * 8 for _ in range(8)]
    my_piece_locs = [] # Store locations of my pieces for move matching
    
    for sq, p_code in pieces.items():
        f, r = parse_sq(sq)
        board[r][f] = p_code
        if p_code[0] == color:
            my_piece_locs.append((f, r, p_code[1]))

    # Helper: Check if a square is attacked by a specific color
    def is_square_attacked(b, f, r, by_c):
        # Pawn attacks
        # Attack comes from direction of pawn movement relative to "by_c"
        # If checking if White attacks (f,r), White pawns are at r-1
        # If checking if Black attacks (f,r), Black pawns are at r+1
        p_row = r - 1 if by_c == 'w' else r + 1
        if 0 <= p_row < 8:
            for df in [-1, 1]:
                if 0 <= f + df < 8:
                    p = b[p_row][f+df]
                    if p and p == by_c + 'P': return True, 100

        # Knight attacks
        for dx, dy in [(1,2), (1,-2), (-1,2), (-1,-2), (2,1), (2,-1), (-2,1), (-2,-1)]:
            nx, ny = f+dx, r+dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                p = b[ny][nx]
                if p and p == by_c + 'N': return True, 320
        
        # King attacks
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0: continue
                nx, ny = f+dx, r+dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    p = b[ny][nx]
                    if p and p == by_c + 'K': return True, 20000
        
        # Sliding attacks (Rook/Queen)
        for dx, dy in [(1,0), (-1,0), (0,1), (0,-1)]:
            cx, cy = f, r
            while True:
                cx += dx; cy += dy
                if not (0 <= cx < 8 and 0 <= cy < 8): break
                p = b[cy][cx]
                if p:
                    if p[0] == by_c and p[1] in 'RQ': return True, values[p[1]]
                    break
        
        # Sliding attacks (Bishop/Queen)
        for dx, dy in [(1,1), (1,-1), (-1,1), (-1,-1)]:
            cx, cy = f, r
            while True:
                cx += dx; cy += dy
                if not (0 <= cx < 8 and 0 <= cy < 8): break
                p = b[cy][cx]
                if p:
                    if p[0] == by_c and p[1] in 'BQ': return True, values[p[1]]
                    break
        
        return False, 0

    # Helper: Evaluation Function
    def evaluate_board(b):
        score = 0
        for r in range(8):
            for f in range(8):
                p = b[r][f]
                if not p: continue
                
                c_owner, p_type = p[0], p[1]
                val = values[p_type]
                
                # Positional Heuristics
                # Central control
                if p_type in 'NBQ':
                    if 2 <= r <= 5 and 2 <= f <= 5: val += 10
                # Pawn advancement
                if p_type == 'P':
                    rank_bonus = r if c_owner == 'w' else (7-r)
                    val += rank_bonus * 5
                
                if c_owner == color: score += val
                else: score -= val
        return score

    # Helper: Get moves for a piece type at f,r (for source matching)
    def can_piece_move_pseudo(f, r, target_f, target_r, p_type, c_owner):
        df, dr = target_f - f, target_r - r
        if p_type == 'N':
            return abs(df) * abs(dr) == 2
        if p_type == 'B':
            return abs(df) == abs(dr) # Obstruction unchecked here, relying on SAN validity
        if p_type == 'R':
            return df == 0 or dr == 0
        if p_type == 'Q':
            return df == 0 or dr == 0 or abs(df) == abs(dr)
        if p_type == 'K':
            return abs(df) <= 1 and abs(dr) <= 1
        if p_type == 'P':
            direction = 1 if c_owner == 'w' else -1
            # Capture
            if abs(df) == 1 and dr == direction: return True
            # Push
            if df == 0:
                if dr == direction: return True
                if (r == 1 and c_owner == 'w' and dr == 2) or (r == 6 and c_owner == 'b' and dr == -2): return True
        return False

    best_move = legal_moves[0]
    best_score = -float('inf')

    # Main Loop
    for move_str in legal_moves:
        # Clone board
        new_b = [row[:] for row in board]
        
        clean_move = move_str.replace('+', '').replace('#', '')
        
        moved_val = 0
        target_coords = None
        
        # Handle Castling
        if clean_move == 'O-O':
            row = 0 if color == 'w' else 7
            new_b[row][4] = None; new_b[row][7] = None
            new_b[row][6] = color + 'K'; new_b[row][5] = color + 'R'
            target_coords = (6, row)
            moved_val = values['K']
        elif clean_move == 'O-O-O':
            row = 0 if color == 'w' else 7
            new_b[row][4] = None; new_b[row][0] = None
            new_b[row][2] = color + 'K'; new_b[row][3] = color + 'R'
            target_coords = (2, row)
            moved_val = values['K']
        else:
            # Parse SAN
            # Regex groups: 1=Type, 2=FileHint, 3=RankHint, 4=x, 5=Target, 6=Prom
            regex = r'^([NBRQK])?([a-h])?([1-8])?(x)?([a-h][1-8])(=[NBRQ])?$'
            match = re.match(regex, clean_move)
            if not match: continue
            
            ptype, f_hint, r_hint, is_capture, target_sq, prom = match.groups()
            ptype = ptype if ptype else 'P'
            
            tf, tr = parse_sq(target_sq)
            target_coords = (tf, tr)
            
            # Identify source piece
            candidates = []
            for (sf, sr, st) in my_piece_locs:
                if st != ptype: continue
                if f_hint and files[sf] != f_hint: continue
                if r_hint and ranks[sr] != r_hint: continue
                
                # Verify geometry
                if can_piece_move_pseudo(sf, sr, tf, tr, ptype, color):
                    # For pawns, distinguish capture vs push based on file change
                    if ptype == 'P':
                        is_diag = abs(sf - tf) == 1
                        is_capture_move = (is_capture is not None)
                        # SAN 'x' corresponds to diag move. 
                        # If x is present, move must be diag. If not, must be straight.
                        if is_capture_move != is_diag: continue
                    
                    # For sliders, strictly we should check path clear, but SAN implies legality
                    # With valid SAN, usually only one piece fits hints+geometry
                    candidates.append((sf, sr))
            
            if not candidates: continue
            sf, sr = candidates[0] # Assume valid SAN resolves ambiguity
            
            # Apply Move
            piece_atom = color + (prom[1] if prom else ptype)
            moved_val = values[prom[1] if prom else ptype]
            
            # En Passant handling
            if ptype == 'P' and is_capture and new_b[tr][tf] is None:
                # Captured pawn is behind target
                ep_r = tr - (1 if color == 'w' else -1)
                new_b[ep_r][tf] = None
            
            new_b[sr][sf] = None
            new_b[tr][tf] = piece_atom
        
        # Evaluate Position
        score = evaluate_board(new_b)
        
        # Safety Penalty: If I moved a piece to a square attacked by enemy
        # and my piece is worth more than the attacker (e.g. Q on square attacked by P)
        if target_coords:
            tx, ty = target_coords
            attacked, attacker_val = is_square_attacked(new_b, tx, ty, enemy_color)
            if attacked:
                # If we hang a piece (value > attacker), penalize
                # Logic: Score already accounts for capture gains. 
                # If we lose the piece next turn, we lose 'moved_val'.
                # We assume favorable trades (taking Q with R) are good, 
                # unfavorable (Q takes P protected) are bad.
                trade_deficit = moved_val - attacker_val
                if trade_deficit > 0:
                    score -= trade_deficit

        if score > best_score:
            best_score = score
            best_move = move_str
            
    return best_move
