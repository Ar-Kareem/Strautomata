
def policy(my_men, my_kings, opp_men, opp_kings, color):
    """
    Checkers AI optimized for competitive arena play.
    Core principles:
    1. Always capture when possible (mandatory)
    2. Maximize material gain (kings > men)
    3. Prioritize king promotion
    4. Control central squares
    5. Advance while avoiding unnecessary risks
    """
    # Convert input to sets for efficient operations
    my_men = set(my_men)
    my_kings = set(my_kings)
    opp_men = set(opp_men)
    opp_kings = set(opp_kings)
    
    # Precompute all piece positions
    all_pieces = my_men | my_kings | opp_men | opp_kings
    
    # Setup color-specific parameters
    if color == 'b':
        regular_dirs = [(-1, -1), (-1, 1)]  # Black moves toward row 0
        promotion_row = 0
        back_row = 7
    else:
        regular_dirs = [(1, -1), (1, 1)]      # White moves toward row 7
        promotion_row = 7
        back_row = 0
    
    king_dirs = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    # Helper: check board bounds
    def in_bounds(r, c):
        return 0 <= r < 8 and 0 <= c < 8
    
    # --- CAPTURE SEQUENCE GENERATION ---
    def generate_capture_sequences(piece_pos, is_king, captured_pieces):
        """
        Recursively find all capture sequences from a starting position.
        Returns list of sequences: [start, cap1, land1, cap2, land2, ...]
        """
        r, c = piece_pos
        dirs = king_dirs if is_king else regular_dirs
        sequences = []
        
        # Try each direction
        for dr, dc in dirs:
            mid = (r + dr, c + dc)
            land = (r + 2*dr, c + 2*dc)
            
            # Check if valid capture
            if (in_bounds(*mid) and in_bounds(*land) and
                mid in (opp_men | opp_kings) and mid not in captured_pieces and
                land not in all_pieces):
                
                # Create new capture sequence
                new_captured = captured_pieces | {mid}
                base_sequence = [piece_pos, mid, land]
                
                # Recurse for multi-captures
                follow_ups = generate_capture_sequences(land, is_king, new_captured)
                
                if follow_ups:
                    # Extend each follow-up sequence
                    for seq in follow_ups:
                        sequences.append(base_sequence + seq[2:])
                else:
                    # No further captures
                    sequences.append(base_sequence)
        
        return sequences
    
    # Find all possible captures
    all_capture_seqs = []
    
    for pos in my_men:
        all_capture_seqs.extend(generate_capture_sequences(pos, False, set()))
    
    for pos in my_kings:
        all_capture_seqs.extend(generate_capture_sequences(pos, True, set()))
    
    # --- CAPTURE SELECTION (MANDATORY) ---
    if all_capture_seqs:
        def capture_score(seq):
            """Score capture sequences: material > length > promotion > position"""
            # Material gain from captured pieces
            captured = seq[1:-1:2]
            score = sum(200 if p in opp_kings else 100 for p in captured)
            
            # Bonus for multiple captures
            score += len(captured) * 50
            
            # Promotion bonus
            if seq[0] in my_men and seq[-1][0] == promotion_row:
                score += 200
            
            # Central landing square bonus
            fr, fc = seq[-1]
            if 2 <= fr <= 5 and 2 <= fc <= 5:
                score += 30
            
            return score
        
        # Select best capture sequence
        best_seq = max(all_capture_seqs, key=capture_score)
        return (best_seq[0], best_seq[-1])
    
    # --- REGULAR MOVE GENERATION ---
    def generate_regular_moves():
        """Generate all non-capture moves"""
        moves = []
        
        # Men moves
        for r, c in my_men:
            for dr, dc in regular_dirs:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in all_pieces:
                    moves.append(((r, c), (nr, nc)))
        
        # King moves
        for r, c in my_kings:
            for dr, dc in king_dirs:
                nr, nc = r + dr, c + dc
                if in_bounds(nr, nc) and (nr, nc) not in all_pieces:
                    moves.append(((r, c), (nr, nc)))
        
        return moves
    
    regular_moves = generate_regular_moves()
    
    if not regular_moves:
        # No legal moves (shouldn't happen in valid game)
        return ((0, 0), (0, 0))
    
    # --- REGULAR MOVE SCORING ---
    def move_score(move):
        """Heuristic evaluation of non-capture moves"""
        from_pos, to_pos = move
        fr, fc = from_pos
        tr, tc = to_pos
        
        score = 0
        
        # Absolute priority: promotion
        if from_pos in my_men and tr == promotion_row:
            return 100000
        
        # Forward advancement for men
        if from_pos in my_men:
            if color == 'b':
                score += (7 - tr) * 8
            else:
                score += tr * 8
        
        # Central position control
        center_dist = max(abs(tr - 3.5), abs(tc - 3.5))
        score += int((4 - center_dist) * 6)
        
        # King centralization
        if from_pos in my_kings:
            score += 20
        
        # Avoid edges for men (reduces mobility)
        if from_pos in my_men and tc in (0, 7):
            score -= 20
        
        # Defensive: maintain back row structure early game
        if fr == back_row and len(my_men) > 4:
            score -= 30
        
        # Bonus for moving away from back row
        if fr == back_row and tr != back_row:
            score += 10
        
        return score
    
    # Select best regular move
    best_move = max(regular_moves, key=move_score)
    return best_move
