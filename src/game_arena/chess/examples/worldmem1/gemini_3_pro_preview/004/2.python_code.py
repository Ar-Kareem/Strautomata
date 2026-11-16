
import math

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    """
    Chess policy that evaluates legal moves based on material, heuristic position, and immediate safety (1-ply).
    """

    # --- Constants & Helpers ---
    FILES = 'abcdefgh'
    RANKS = '12345678'
    
    # Piece Values
    VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Directions for movement
    DIAG_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    ORTHO_DIRS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    KNIGHT_DIRS = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]

    # Board representation helpers
    def to_coords(sq):
        return FILES.index(sq[0]), RANKS.index(sq[1])

    def to_sq(c, r):
        if 0 <= c < 8 and 0 <= r < 8:
            return FILES[c] + RANKS[r]
        return None

    def get_piece_at(board, c, r):
        sq = to_sq(c, r)
        return board.get(sq)

    # --- Engine Logic ---

    def get_attacked_squares(board, attacker_color):
        """
        Returns a set of squares attacked by 'attacker_color' given the board state.
        """
        attacked = set()
        
        for sq, piece in board.items():
            if piece[0] != attacker_color:
                continue
            
            ptype = piece[1]
            c, r = to_coords(sq)
            
            if ptype == 'P':
                # Pawn captures are diagonal
                direction = 1 if attacker_color == 'w' else -1
                for dc in [-1, 1]:
                    target = to_sq(c + dc, r + direction)
                    if target: attacked.add(target)
            
            elif ptype == 'N':
                for dc, dr in KNIGHT_DIRS:
                    target = to_sq(c + dc, r + dr)
                    if target: attacked.add(target)
            
            elif ptype == 'K':
                for dc in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if dc == 0 and dr == 0: continue
                        target = to_sq(c + dc, r + dr)
                        if target: attacked.add(target)
            
            else: # Sliding pieces (B, R, Q)
                dirs = []
                if ptype in ['B', 'Q']: dirs.extend(DIAG_DIRS)
                if ptype in ['R', 'Q']: dirs.extend(ORTHO_DIRS)
                
                for dc, dr in dirs:
                    curr_c, curr_r = c, r
                    while True:
                        curr_c += dc
                        curr_r += dr
                        target = to_sq(curr_c, curr_r)
                        if not target:
                            break
                        attacked.add(target)
                        if target in board: # Blocked by any piece
                            break
        return attacked

    def evaluate_state(board, my_color, moved_piece_sq, move_san):
        """
        Static evaluation of the board.
        moved_piece_sq: The destination square of the move we just made.
        """
        opp_color = 'b' if my_color == 'w' else 'w'
        
        # 1. Material Score
        my_mat = 0
        opp_mat = 0
        my_mobility = 0 # Simple count of pieces
        
        for sq, piece in board.items():
            val = VALUES.get(piece[1], 0)
            
            # Simple Centrality Bonus (favors e4, d4, e5, d5)
            c, r = to_coords(sq)
            center_dist = abs(c - 3.5) + abs(r - 3.5)
            # Bonus decreases with distance from center
            pos_bonus = (10 - center_dist) * 2 
            
            if piece[0] == my_color:
                my_mat += val + pos_bonus
                my_mobility += 1
            else:
                opp_mat += val + pos_bonus

        # 2. Safety / Tactics (Blunder Check)
        # Generate squares attacked by opponent
        opp_attacks = get_attacked_squares(board, opp_color)
        
        safety_penalty = 0
        
        # If the piece we just moved is under attack
        if moved_piece_sq in opp_attacks:
            # We treat this as a risk. 
            # If we captured something valuable, we might accept the trade.
            # Determine what we moved
            my_piece = board[moved_piece_sq]
            my_val = VALUES.get(my_piece[1], 100)
            
            # Heuristic: If we moved a Queen to a square attacked by a Pawn, big penalty.
            # We don't have full exchange analysis, so we act conservatively.
            # We assume we lose the piece.
            
            # Did we capture something? (Handled by material score diff).
            # If the material score went up by capturing Q with P, even if P is lost, it's good.
            # But the material score above already accounts for the removed opponent piece.
            # It does NOT account for our piece being removed next turn.
            
            safety_penalty = my_val * 0.8 # Assume we check checks/captures, usually 1-1 trade is okayish
        
        # Checkmate/Check handling provided by valid move parsing (move_san)
        special_bonus = 0
        if '#' in move_san:
            special_bonus = 100000
        elif '+' in move_san:
            special_bonus = 50
        elif 'Q' in move_san and '=' in move_san: # Promotion to Queen
            special_bonus = 800

        score = (my_mat - opp_mat) - safety_penalty + special_bonus
        return score

    def parse_and_simulate(current_board, move_san, color):
        """
        Parses SAN move and returns the new board state.
        Returns None if parsing fails (shouldn't happen on valid inputs).
        """
        clean_move = move_san.replace('+', '').replace('#', '').replace('x', '')
        new_board = current_board.copy()
        
        target_sq = None
        
        # --- Handle Castling ---
        if clean_move == 'O-O':
            rank = '1' if color == 'w' else '8'
            # Move King
            del new_board['e' + rank]
            new_board['g' + rank] = color + 'K'
            # Move Rook
            if 'h' + rank in new_board: del new_board['h' + rank]
            new_board['f' + rank] = color + 'R'
            return new_board, 'g' + rank
            
        if clean_move == 'O-O-O':
            rank = '1' if color == 'w' else '8'
            # Move King
            del new_board['e' + rank]
            new_board['c' + rank] = color + 'K'
            # Move Rook
            if 'a' + rank in new_board: del new_board['a' + rank]
            new_board['d' + rank] = color + 'R'
            return new_board, 'c' + rank

        # --- Handle Promotion ---
        promo_type = None
        if '=' in clean_move:
            parts = clean_move.split('=')
            clean_move = parts[0]
            promo_type = parts[1] # e.g. Q, R...
        
        # --- Parse Standard Move ---
        # Format: [Piece]?[file]?[rank]?[target]
        # Regex-like manual parsing
        
        # Identify Target
        target_sq = clean_move[-2:]
        t_c, t_r = to_coords(target_sq)
        
        # Identify Piece Type
        prefix = clean_move[:-2]
        p_type = 'P'
        if prefix and prefix[0].isupper():
            p_type = prefix[0]
            prefix = prefix[1:] # Discard piece char
        
        # Hints (e.g. 'a', '1', 'bd')
        hint_file = None
        hint_rank = None
        
        for char in prefix:
            if char in FILES: hint_file = FILES.index(char)
            elif char in RANKS: hint_rank = RANKS.index(char)
            
        # Find the source piece
        candidates = []
        for sq, piece in current_board.items():
            if piece == color + p_type:
                sc, sr = to_coords(sq)
                
                # Check hints
                if hint_file is not None and sc != hint_file: continue
                if hint_rank is not None and sr != hint_rank: continue
                
                # Check geometry (Can this piece physically reach target?)
                can_reach = False
                
                if p_type == 'N':
                    for dc, dr in KNIGHT_DIRS:
                        if sc + dc == t_c and sr + dr == t_r:
                            can_reach = True; break
                elif p_type == 'P':
                    # Pawn logic
                    direction = 1 if color == 'w' else -1
                    # Move forward 1
                    if sc == t_c and sr + direction == t_r: can_reach = True
                    # Move forward 2
                    elif sc == t_c and sr + 2*direction == t_r and ((color=='w' and sr==1) or (color=='b' and sr==6)): can_reach = True
                    # Capture
                    elif abs(sc - t_c) == 1 and sr + direction == t_r: can_reach = True
                
                elif p_type == 'K':
                    if abs(sc - t_c) <= 1 and abs(sr - t_r) <= 1: can_reach = True
                    
                else: # R, B, Q - check line of sight
                    dc, dr = t_c - sc, t_r - sr
                    # Check diagonal
                    if abs(dc) == abs(dr) and p_type in ['B', 'Q']:
                        step_c = 1 if dc > 0 else -1
                        step_r = 1 if dr > 0 else -1
                        # Check blocking
                        blocked = False
                        cur_c, cur_r = sc + step_c, sr + step_r
                        while cur_c != t_c or cur_r != t_r:
                            if to_sq(cur_c, cur_r) in current_board:
                                blocked = True; break
                            cur_c += step_c
                            cur_r += step_r
                        if not blocked: can_reach = True
                    
                    # Check orthogonal
                    elif (dc == 0 or dr == 0) and p_type in ['R', 'Q']:
                        step_c = 0 if dc == 0 else (1 if dc > 0 else -1)
                        step_r = 0 if dr == 0 else (1 if dr > 0 else -1)
                        blocked = False
                        cur_c, cur_r = sc + step_c, sr + step_r
                        while cur_c != t_c or cur_r != t_r:
                            if to_sq(cur_c, cur_r) in current_board:
                                blocked = True; break
                            cur_c += step_c
                            cur_r += step_r
                        if not blocked: can_reach = True

                if can_reach:
                    candidates.append(sq)

        # Apply Move
        # If multiple candidates, usually hints resolve it. If not, we just pick the first one 
        # (Assuming legal_moves comes from a validator, ambiguous standard notation implies specific differentiation).
        # In a loose setting, we pick the first valid geometric candidate.
        if candidates:
            src_sq = candidates[0]
            
            # En Passant handling
            # If Pawn moves diagonal and target empty -> EP
            if p_type == 'P' and abs(to_coords(src_sq)[0] - t_c) == 1 and target_sq not in new_board:
                # Remove captured pawn
                ep_row = to_coords(src_sq)[1] # Same rank as source for the victim
                victim_sq = to_sq(t_c, ep_row)
                if victim_sq in new_board: del new_board[victim_sq]

            del new_board[src_sq]
            
            final_piece = color + (promo_type if promo_type else p_type)
            new_board[target_sq] = final_piece
            
            return new_board, target_sq
            
        return current_board, target_sq # Should not happen

    # --- Main Selection Loop ---
    
    my_color = 'w' if to_play == 'white' else 'b'
    best_move = legal_moves[0]
    best_score = -float('inf')
    
    # Priority: Checkmate
    for move in legal_moves:
        if '#' in move:
            return move, memory
    
    for move in legal_moves:
        try:
            next_board, dest_sq = parse_and_simulate(pieces, move, my_color)
            score = evaluate_state(next_board, my_color, dest_sq, move)
        except Exception:
            # Fallback if logic errors
            score = -10000
            
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move, memory
