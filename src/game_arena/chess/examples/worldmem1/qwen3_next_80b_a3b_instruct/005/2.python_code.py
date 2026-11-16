
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Define piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 1000}
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    # Check for checkmate moves immediately
    for move in legal_moves:
        if '+' in move and '++' not in move:  # Single check, not checkmate
            continue
        # Check for checkmate: if move ends with '#', or we infer it's checkmate by context
        # But note: checkmate may not be marked in some systems — we can't simulate, so we rely on presence of '#'
        # However, the problem says legal_moves are given correctly — so if it's checkmate, the move might have '+'
        # But official chess notation uses '#' for checkmate. Since the example doesn't show '#', we assume standard:
        # The arena's legal_moves might not include '#', only '+' for check.
        # We need a better heuristic: if a move results in checkmate, we don't know unless the system marks it.
        # But the problem says: "prioritize checkmate if available", implying we can detect it.
        # However, we are not given board state beyond pieces, and cannot simulate.
        # So we must assume that if a move is in legal_moves and leads to checkmate, it's still just a string.
        # We cannot detect checkmate without a full board simulator — and we are constrained to 1s.
        
        # Since we are not allowed to simulate, we cannot reliably detect checkmate.
        # Alternative: some systems append '#', others use '++'. We'll check for '#' or '++'
        if '#' in move or '++' in move:
            return move, memory
    
    # If no obvious checkmate, let's score moves by material gain and safety
    best_move = legal_moves[0]
    best_score = float('-inf')
    
    # Precompute opponent threats: check if any opponent piece can capture our king next turn
    # We cannot simulate fully, so we skip complex threat detection unless we can infer from positions
    
    for move in legal_moves:
        score = 0.0
        
        # Check if it's a capture
        if 'x' in move:
            # Extract the destination square
            if '=' in move:  # promotion with capture
                dest = move.split('x')[1].split('=')[0]
            else:
                dest = move.split('x')[1]
                if len(dest) == 2:  # normal capture
                    pass
                else:  # disambiguated capture like "Nfxe5"
                    # We need to extract destination properly
                    # Example: Nfxe5 -> remove 'Nf' and 'xe5' -> 'e5'
                    for i, c in enumerate(move):
                        if c == 'x':
                            dest = move[i+1:]
                            break
            # Check if destination square has an opponent piece
            if dest in pieces and pieces[dest].startswith(opponent_color):
                captured_piece = pieces[dest][1]  # e.g., 'Q' for 'bQ'
                score += 10 * piece_values[captured_piece]  # Bonus for capturing valuable pieces
        
        # Promotion to Queen is best unless specified otherwise
        if '=' in move:
            if '=Q' in move:
                score += 8  # Promote to Queen: big bonus
            elif '=R' in move:
                score += 5
            elif '=B' in move or '=N' in move:
                score += 3  # Sometimes knight is better to avoid stalemate, but we don't know — assume Queen always
        
        # Check if move is castling
        if move in ['O-O', 'O-O-O']:
            score += 4  # Castling is valuable for king safety and development
        
        # Positional bonus: control center
        center_squares = {'d4', 'd5', 'e4', 'e5'}
        if len(move) >= 2:  # It's a move to a square
            # Extract destination: handle disambiguation, captures, promotions
            dest_square = extract_destination(move)
            if dest_square in center_squares:
                score += 1.5
        
        # Penalty for moving king into danger or making king unstable
        if move.startswith('K'):  # King move
            # Check if king move exposes the king? We can't fully simulate, so penalize if move is to edge
            # Or check if it's on the 1st/8th rank or a/h file
            dest_square = extract_destination(move)
            if dest_square in ['a1','a2','a3','a4','a5','a6','a7','a8',
                               'h1','h2','h3','h4','h5','h6','h7','h8',
                               'a1','b1','c1','d1','e1','f1','g1','h1',
                               'a8','b8','c8','d8','e8','f8','g8','h8']:
                score -= 2  # King on edge is dangerous
            
            # Also, if king moves, we assume it might have castling already done, so less bonus
        
        # If this move puts opponent in check
        if '+' in move:
            score += 3  # Check is good
        
        # Avoid moves that leave pieces hanging (we can't simulate, so skip)
        
        # Avoid moves that remove defense of own king/pieces? No info to judge
        
        # Choose move with best score
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory

def extract_destination(move: str) -> str:
    # Extract the destination square from a move string
    # Handle cases: 'e4', 'Nf3', 'Bxe5', 'Qh8=', 'Rac1', 'O-O', 'b8=Q'
    if move in ['O-O', 'O-O-O']:
        return ''  # Special cases, no square
    
    # Promotion case
    if '=' in move:
        move = move.split('=')[0]
    
    if 'x' in move:
        # Extract after 'x'
        dest = move.split('x')[-1]
        return dest
    else:
        # Normal move: find last two characters that are a valid square (file and rank)
        # Only valid files: a-h, ranks: 1-8
        # Look for last two chars
        if len(move) >= 2:
            last_two = move[-2:]
            if len(last_two) == 2 and last_two[0] in 'abcdefgh' and last_two[1] in '12345678':
                return last_two
        # Could be longer disambiguation: e.g., "Nec3" → "c3"
        # We go backwards until we find a valid square
        for i in range(len(move)-2, -1, -1):
            sq = move[i:i+2]
            if len(sq) == 2 and sq[0] in 'abcdefgh' and sq[1] in '12345678':
                return sq
    # Fallback: if nothing found, try the last two characters
    if len(move) >= 2:
        return move[-2:]
    else:
        return move  # unlikely
