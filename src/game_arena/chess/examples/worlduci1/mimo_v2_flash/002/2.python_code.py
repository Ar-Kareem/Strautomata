
def policy(pieces: dict[str, str], to_play: str) -> str:
    import random

    # Map files and ranks
    files = 'abcdefgh'
    ranks = '12345678'

    # Helper to get neighbors for Knights
    knight_offsets = [(1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1)]

    # Helper to get directions for Sliding pieces
    directions = {
        'B': [(1, 1), (1, -1), (-1, 1), (-1, -1)],
        'R': [(1, 0), (-1, 0), (0, 1), (0, -1)],
        'Q': [(1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)]
    }

    # Color multiplier: 1 for White (up the board), -1 for Black (down the board)
    # White pawns move +1 rank, Black -1 rank.
    # We will use "forward" relative to side.
    # White: forward direction = 1 (rank increases)
    # Black: forward direction = -1 (rank decreases)
    color_mult = 1 if to_play == 'white' else -1

    def get_square_coords(square):
        return files.index(square[0]), ranks.index(square[1])

    def get_square_from_coords(f, r):
        if 0 <= f < 8 and 0 <= r < 8:
            return files[f] + ranks[r]
        return None

    def get_piece_at(square, p_dict):
        return p_dict.get(square)

    # Check if a square is under attack by the opponent
    def is_attacked(square, p_dict, my_color):
        opp_color = 'w' if my_color == 'b' else 'b'
        f, r = get_square_coords(square)

        # 1. Pawn attacks
        # Opponent pawns attack from "behind" their move direction
        # If my_color is white, opp is black, who moves -1 rank.
        # So black pawns attack from r+1 (one rank back from where they land).
        # Wait, simpler: check where pawns could be to attack this square.
        # If I am white (moving up), opp is black (moving down).
        # Black pawns at (f-1, r-1) or (f+1, r-1) attack me at (f, r).
        # Correct: Black pawns are "below".
        # So if I am White: attack comes from (f-1, r-1) and (f+1, r-1).
        # If I am Black: attack comes from (f-1, r+1) and (f+1, r+1).
        attack_rank_dirs = (-1, 1) if my_color == 'w' else (1, -1)
        # Let's re-verify.
        # White pawn moves (0, 1). Attacks (1, 1) and (-1, 1).
        # Black pawn moves (0, -1). Attacks (1, -1) and (-1, -1).
        # If I am White, I care if Black attacks me.
        # Black attacks (x+1, y-1) and (x-1, y-1).
        # So check (f-1, r+1) and (f+1, r+1).
        # If I am Black, I care if White attacks me.
        # White attacks (x+1, y+1) and (x-1, y+1).
        # So check (f-1, r-1) and (f+1, r-1).

        pf1, pf2 = (f-1, f+1) 
        if my_color == 'w':
            # Check for Black pawns
            for pf in [f-1, f+1]:
                sq = get_square_from_coords(pf, r+1)
                if sq and p_dict.get(sq) == 'bP':
                    return True
        else:
            # Check for White pawns
            for pf in [f-1, f+1]:
                sq = get_square_from_coords(pf, r-1)
                if sq and p_dict.get(sq) == 'wP':
                    return True

        # 2. Knight attacks
        for df, dr in knight_offsets:
            nf, nr = f + df, r + dr
            sq = get_square_from_coords(nf, nr)
            if sq:
                p = p_dict.get(sq)
                if p and p[0] == opp_color and p[1] == 'N':
                    return True

        # 3. King attacks
        for df in [-1, 0, 1]:
            for dr in [-1, 0, 1]:
                if df == 0 and dr == 0: continue
                nf, nr = f + df, r + dr
                sq = get_square_from_coords(nf, nr)
                if sq:
                    p = p_dict.get(sq)
                    if p and p[0] == opp_color and p[1] == 'K':
                        return True

        # 4. Sliding attacks (R, B, Q)
        for piece_type in ['R', 'B', 'Q']:
            dirs = directions[piece_type]
            for df, dr in dirs:
                nf, nr = f + df, r + dr
                while True:
                    sq = get_square_from_coords(nf, nr)
                    if not sq: break
                    p = p_dict.get(sq)
                    if p:
                        if p[0] == opp_color and p[1] in ['Q', piece_type]: # Q covers both R and B lines
                            return True
                        break # Blocked
                    nf += df
                    nr += dr
        return False

    def get_king_square(my_color, p_dict):
        target = my_color + 'K'
        for sq, p in p_dict.items():
            if p == target:
                return sq
        return None

    def is_square_empty(square, p_dict):
        return square not in p_dict

    def generate_moves(p_dict, turn_color):
        moves = []
        # Identify pieces for the current turn
        # Determine promotion rank
        promote_rank = '8' if turn_color == 'white' else '1'
        home_rank_pawn = '2' if turn_color == 'white' else '7'
        
        # King side/Queen side rook squares for castling checks (simplified)
        # We assume standard chess starting pos is irrelevant here, we only care about current state.
        # Castling rights are NOT given. We must detect if the move is valid.
        # Rule: King cannot move through check. King cannot be in check.
        # Rook and King must not have moved. (We can't know if they moved, but we assume we can castle if path is clear and safe?).
        # Since we don't have history, we usually only consider castling if:
        # 1. King is at e1/e8
        # 2. Rook is at h1/h8 or a1/a8
        # 3. Path is clear
        # 4. Squares are not attacked
        # This is hard without history, but we can try to guess.
        # Actually, the prompt implies a simple environment. Let's implement castling only if explicitly safe and pieces are there.
        
        # Let's find all pieces of the current color
        for sq, p in p_dict.items():
            if p[0] != turn_color:
                continue
            
            f, r = get_square_coords(sq)
            p_type = p[1]

            if p_type == 'P':
                # Pawn
                # Forward move
                target_r = r + color_mult
                if 0 <= target_r < 8:
                    # Single push
                    target_sq = get_square_from_coords(f, target_r)
                    if target_sq and target_sq not in p_dict:
                        # Promotion?
                        if ranks[target_r] == promote_rank:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(sq + target_sq + promo)
                        else:
                            moves.append(sq + target_sq)
                        
                        # Double push
                        if r == ranks.index(home_rank_pawn):
                            double_r = r + 2 * color_mult
                            target_sq2 = get_square_from_coords(f, double_r)
                            if target_sq2 and target_sq2 not in p_dict:
                                moves.append(sq + target_sq2)
                
                # Captures
                for df in [-1, 1]:
                    nf = f + df
                    nr = r + color_mult
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        target_sq = get_square_from_coords(nf, nr)
                        if target_sq:
                            target_p = p_dict.get(target_sq)
                            # Standard capture
                            if target_p and target_p[0] != turn_color:
                                if ranks[nr] == promote_rank:
                                    for promo in ['q', 'r', 'b', 'n']:
                                        moves.append(sq + target_sq + promo)
                                else:
                                    moves.append(sq + target_sq)
                            # En passant? We have no history, so we cannot detect EP.
                            # We skip EP for safety (don't return illegal move).

            elif p_type in ['N']:
                for df, dr in knight_offsets:
                    nf, nr = f + df, r + dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        target_sq = get_square_from_coords(nf, nr)
                        if target_sq:
                            target_p = p_dict.get(target_sq)
                            if target_p is None or target_p[0] != turn_color:
                                moves.append(sq + target_sq)

            elif p_type in ['B', 'R', 'Q']:
                dirs = directions[p_type]
                for df, dr in dirs:
                    nf, nr = f + df, r + dr
                    while 0 <= nf < 8 and 0 <= nr < 8:
                        target_sq = get_square_from_coords(nf, nr)
                        target_p = p_dict.get(target_sq)
                        if target_p is None:
                            moves.append(sq + target_sq)
                        elif target_p[0] != turn_color:
                            moves.append(sq + target_sq)
                            break # Capture
                        else:
                            break # Blocked by own piece
                        nf += df
                        nr += dr

            elif p_type == 'K':
                # Normal King moves
                for df in [-1, 0, 1]:
                    for dr in [-1, 0, 1]:
                        if df == 0 and dr == 0: continue
                        nf, nr = f + df, r + dr
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            target_sq = get_square_from_coords(nf, nr)
                            if target_sq:
                                target_p = p_dict.get(target_sq)
                                if target_p is None or target_p[0] != turn_color:
                                    moves.append(sq + target_sq)
                
                # Castling (Heuristic: only consider if it looks like start position and path clear)
                # We must check if King is in check. This is handled by the filtering logic in the main part.
                # We only generate "potential" castles here if the squares are empty and we see a rook.
                # White: e1 (f=4, r=0). Kingside: h1 (f=7). Queenside: a1 (f=0).
                if turn_color == 'white' and sq == 'e1':
                    # Kingside: f1, g1 empty. h1 is R.
                    if get_square_from_coords(5, 0) not in p_dict and get_square_from_coords(6, 0) not in p_dict:
                        if p_dict.get('h1') == 'wR':
                            # Generate g1
                            moves.append('e1g1')
                    # Queenside: d1, c1, b1 empty. a1 is R.
                    if get_square_from_coords(3, 0) not in p_dict and get_square_from_coords(2, 0) not in p_dict and get_square_from_coords(1, 0) not in p_dict:
                        if p_dict.get('a1') == 'wR':
                            # Generate c1
                            moves.append('e1c1')
                
                # Black: e8 (f=4, r=7).
                if turn_color == 'black' and sq == 'e8':
                    # Kingside: f8, g8 empty. h8 is R.
                    if get_square_from_coords(5, 7) not in p_dict and get_square_from_coords(6, 7) not in p_dict:
                        if p_dict.get('h8') == 'bR':
                            moves.append('e8g8')
                    # Queenside: d8, c8, b8 empty. a8 is R.
                    if get_square_from_coords(3, 7) not in p_dict and get_square_from_coords(2, 7) not in p_dict and get_square_from_coords(1, 7) not in p_dict:
                        if p_dict.get('a8') == 'bR':
                            moves.append('e8c8')

        return moves

    # 1. Generate all legal moves (filtering checks)
    legal_moves = generate_moves(pieces, to_play)
    
    # Filter for checks
    # We must simulate. This is the slow part.
    # Optimization: If the king is not currently in check, we don't need to simulate every move.
    # Only moves that expose the king to check need checking.
    # But it's easier and safer to just simulate all moves (given 1 sec limit and board size).
    
    final_legal_moves = []
    king_sq = get_king_square(to_play, pieces)
    opp_color = 'w' if to_play == 'b' else 'b'

    # If no king found (shouldn't happen), return random
    if not king_sq:
        if legal_moves:
            return random.choice(legal_moves)
        return ""

    for move in legal_moves:
        # Simulate move
        start = move[:2]
        end = move[2:4]
        moving_piece = pieces[start]
        
        # Create a temp board
        temp_pieces = pieces.copy()
        del temp_pieces[start]
        
        # Handle capture
        if end in temp_pieces:
            del temp_pieces[end]
            
        # Handle promotion (technically the piece type changes, but for check detection,
        # a Queen is usually worst-case for blocking, but we replaced the pawn).
        # If promotion, put a Queen for check detection.
        if len(move) == 5:
            promo_type = move[4]
            if promo_type == 'q':
                temp_pieces[end] = to_play[0] + 'Q'
            elif promo_type == 'r':
                temp_pieces[end] = to_play[0] + 'R'
            elif promo_type == 'b':
                temp_pieces[end] = to_play[0] + 'B'
            elif promo_type == 'n':
                temp_pieces[end] = to_play[0] + 'N'
        else:
            temp_pieces[end] = moving_piece
            
        # Update King position if King moved
        new_king_sq = king_sq
        if moving_piece[1] == 'K':
            new_king_sq = end
            
        # Check if new king position is attacked
        if not is_attacked(new_king_sq, temp_pieces, to_play):
            final_legal_moves.append(move)

    if not final_legal_moves:
        # Checkmate/Stalemate - return empty? Policy must return a move.
        # But if no legal moves, we can't return one.
        # The arena handles this. We should try to return something or crash?
        # Let's return a random one from original if filtered list empty (unlikely unless all moves are illegal)
        if legal_moves:
            return random.choice(legal_moves)
        # This is a fail-safe
        return ""

    # --- Evaluation & Selection ---
    
    # Values for material
    vals = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    
    # Center control weights
    center_sqs = ['d4', 'e4', 'd5', 'e5']
    center_bonus = 0.1

    best_moves = []
    max_score = -float('inf')

    for move in final_legal_moves:
        score = 0.0
        start = move[:2]
        end = move[2:4]
        
        # 1. Capture logic
        if end in pieces:
            target_p = pieces[end]
            attacker_p = pieces[start]
            # MVV/LVA (Most Valuable Victim / Least Valuable Attacker)
            # Score = 10 * VictimVal - AttackerVal
            victim_val = vals.get(target_p[1], 0)
            attacker_val = vals.get(attacker_p[1], 0)
            score += (victim_val * 10) - attacker_val
            
            # Slight preferance for capturing with less valuable piece
            if attacker_val < victim_val:
                score += 1

        # 2. Promotion
        if len(move) == 5:
            promo = move[4]
            if promo == 'q':
                score += 9 # Value of queen minus pawn (roughly) + bonus
            elif promo == 'n':
                score += 3 # Knight minus pawn

        # 3. Center Control
        if end in center_sqs:
            score += center_bonus

        # 4. King Safety (Avoid moving King into check - handled by filtering, but avoid central King)
        # Heuristic: If moving King, prefer corners or edges over center in early game
        if pieces[start][1] == 'K':
            f, r = get_square_coords(end)
            # Distance from center (3.5, 3.5)
            dist = abs(f - 3.5) + abs(r - 3.5)
            score -= (4 - dist) * 0.5 # Penalize moving to center

        # 5. Checkmate detection
        # Is this move checkmate?
        # We need to see if opponent has any legal moves in the new position
        # This is expensive (N * N). Let's do a quick check if it's checking the King.
        # If it gives check, we simulate opponent response.
        
        # Check if the move gives check
        # We can use is_attacked.
        # Simulate move to temp_pieces
        temp_pieces = pieces.copy()
        del temp_pieces[start]
        if end in temp_pieces: del temp_pieces[end]
        temp_pieces[end] = pieces[start]
        if len(move) == 5: 
             # Promotion to Queen for worst case check
             temp_pieces[end] = to_play[0] + 'Q'
        
        opp_king_sq = get_king_square(opp_color, temp_pieces)
        
        if opp_king_sq and is_attacked(opp_king_sq, temp_pieces, opp_color):
            score += 50 # Massive bonus for checking
            
            # Can opponent escape?
            # We need to generate opponent moves. This is costly.
            # Let's just hope check score is enough to prefer it.
            # To be smarter: check if check is "mate-like" (no easy escape).
            # Let's skip full mate search to save time and stick to high check bonus.

        if score > max_score:
            max_score = score
            best_moves = [move]
        elif abs(score - max_score) < 0.001:
            best_moves.append(move)

    if not best_moves:
        return random.choice(final_legal_moves)
        
    return random.choice(best_moves)
