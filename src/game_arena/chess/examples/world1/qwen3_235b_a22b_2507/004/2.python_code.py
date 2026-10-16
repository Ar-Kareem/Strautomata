
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Piece values (in pawns)
    VALUE = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}  # King has no material value
    
    # Determine player color
    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if color == 'w' else 'w'

    # Utility: convert square to (file, rank) = (col, row)
    def sq2fr(square: str):
        return square[0], int(square[1])

    # Evaluate material on the board
    def evaluate_material():
        total = 0
        for sq, piece in pieces.items():
            c, p = piece[0], piece[1]
            v = VALUE[p]
            if c == color:
                total += v
            else:
                total -= v
        return total

    # Get opponent's legal moves by simulating all moves (rough threat detection)
    # Since we don't have a full engine, we do basic capture detection
    def get_attacked_squares(opp_color):
        attacked = set()
        for sq, piece in pieces.items():
            pcolor, ptype = piece[0], piece[1]
            if pcolor != opp_color:
                continue
            file, rank = sq2fr(sq)
            col = ord(file) - ord('a')
            # Pawn attacks
            if ptype == 'P':
                pf = 1 if opp_color == 'b' else -1
                for df in [-1, 1]:
                    nf = col + df
                    nr = rank + pf
                    if 0 <= nf < 8 and 1 <= nr <= 8:
                        n_square = chr(ord('a') + nf) + str(nr)
                        attacked.add(n_square)
            # Knight
            elif ptype == 'N':
                for dx, dy in [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]:
                    nf = col + dx
                    nr = rank + dy
                    if 0 <= nf < 8 and 1 <= nr <= 8:
                        n_square = chr(ord('a') + nf) + str(nr)
                        attacked.add(n_square)
            # King
            elif ptype == 'K':
                for dx in [-1,0,1]:
                    for dy in [-1,0,1]:
                        if dx == 0 and dy == 0:
                            continue
                        nf = col + dx
                        nr = rank + dy
                        if 0 <= nf < 8 and 1 <= nr <= 8:
                            n_square = chr(ord('a') + nf) + str(nr)
                            attacked.add(n_square)
            # Rook, Queen: horizontal/vertical
            if ptype in 'RQ':
                for (dx, dy) in [(0,1),(0,-1),(1,0),(-1,0)]:
                    for i in range(1,8):
                        nf = col + i*dx
                        nr = rank + i*dy
                        if 0 <= nf < 8 and 1 <= nr <= 8:
                            n_square = chr(ord('a') + nf) + str(nr)
                            attacked.add(n_square)
                            # Stop at first piece (but include the capture square)
                            if n_square in pieces:
                                break
                        else:
                            break
            # Bishop, Queen: diagonal
            if ptype in 'BQ':
                for (dx, dy) in [(1,1),(1,-1),(-1,1),(-1,-1)]:
                    for i in range(1,8):
                        nf = col + i*dx
                        nr = rank + i*dy
                        if 0 <= nf < 8 and 1 <= nr <= 8:
                            n_square = chr(ord('a') + nf) + str(nr)
                            attacked.add(n_square)
                            if n_square in pieces:
                                break
                        else:
                            break
        return attacked

    # Precompute current material and attack maps
    current_material = evaluate_material()
    opp_attacked = get_attacked_squares(opp_color)

    # Move scoring
    best_score = -np.inf
    best_move = legal_moves[0]  # fallback

    for move in legal_moves:
        score = 0.0
        
        # Simulate the move and compute consequences
        # We don't fully update the board, but extract info from move string
        src, dst = None, None
        captured = None
        is_capture = 'x' in move
        is_promotion = '=' in move
        is_castle = 'O' in move
        gives_check = '+' in move
        gives_mate = '#' in move or '++' in move  # rare, but for safety

        # Parse move
        cleaned = move.replace('x', '').replace('+', '').replace('#', '')
        if cleaned == 'O-O' or cleaned == 'O-O-O':
            if to_play == 'white':
                src = 'e1'
                dst = 'g1' if cleaned == 'O-O' else 'c1'
            else:
                src = 'e8'
                dst = 'g8' if cleaned == 'O-O' else 'c8'
        else:
            # Last part is always the destination square
            dst = cleaned[-2:]
            # Promotion: check if last part has =Q etc.
            if is_promotion:
                promoted_piece = move.split('=')[1][0]
                score += VALUE[promoted_piece]  # Big incentive
            # Determine src piece by current pieces[dst] after move
            # We can reverse by checking what piece could move there
            # But easier: if it's a capture, the captured piece is on dst before
            # But we don't know src. However, we can infer if a capture happened
            # and what was captured
            if is_capture:
                if len(cleaned) >= 5 and cleaned[-3] not in 'O':  # e.g. Bxc4, Nxc4, Rc4, cxd5
                    # The character before 'x' may be disambiguation
                    # But the captured piece is on dst before the move
                    if dst in pieces:
                        captured = pieces[dst]
                        score += VALUE[captured[1]]  # gain material
                else:
                    # e.g. 'cxd5': pawn from c-file captures on d5
                    # or 'fxe5': pawn capture
                    # We know the destination, and it's a capture
                    if dst in pieces:
                        captured = pieces[dst]
                        score += VALUE[captured[1]]
            # Determine if it's a pawn move or piece move
            # First char may be piece letter if not pawn
            first_char = move[0]
            if first_char in 'KQRBN':
                # Piece move
                piece_type = first_char
                # Try to find src: it's any piece of this color and type that can move to dst
                # But without full move gen, assume it's not losing unless captured?
                # For simplicity, just use destination
                # But we want to penalize moving king unnecessarily
                if piece_type == 'K' and not is_castle:
                    score -= 0.5  # Avoid king moves unless castling
                # Bonus for developing knights and bishops early
                # Rough heuristic: if early in game (few captures or many back-row pieces), reward N/B moves
            else:
                # Must be a pawn move (no piece letter)
                # e.g. 'e4', 'exd5', 'e8=Q'
                piece_type = 'P'

        # Promotions: already scored above
        if is_promotion:
            # Score already includes the new piece value
            # But we must subtract the pawn that is lost
            score -= VALUE['P']
            # Prefer queen promotion
            if '=Q' in move:
                score += 0.5
            # Avoid bad promotions
        else:
            # Normal move: piece moves from src to dst
            # We need to figure out what piece is moving
            # Try to infer from destination and move syntax
            # If the move starts with a piece letter (K,Q,R,B,N), that's the piece
            # Otherwise, it's a pawn
            if move[0] in 'KQRBN':
                moving_piece = move[0]
            else:
                moving_piece = 'P'
            
            # Find the source square by checking which piece of that type/color can move there
            # But we don't have full move generation.
            # Instead, we check: if destination is empty, then src is where a piece of this type was
            # But this is too complex. Instead, we rely on captures for material.
            # We can at least detect if the moving piece is lost (captured)
            # But we don't simulate the board.
            # Instead, we detect if the moving piece would be under attack after the move
            # by checking if dst is in opp_attacked
            # But only if it's not capturing a high-value piece

            # However, we do know: if the move is a capture, and dst has a piece
            if is_capture and captured:
                # Gain material
                captured_value = VALUE[captured[1]]
                # But if we're recapturing, this might be equal
                # Try to find what piece we're using to capture
                # It's a simplification
                attacker_value = VALUE[moving_piece]
                # Gain: captured_value - attacker_value (if we lose the attacker)
                # But we don't know for sure
                # Instead, just add captured_value, but penalize if we use high-value piece
                score += captured_value
                if moving_piece in 'QR' and captured_value < 5:
                    score -= 2  # discourage trading high for low
                if moving_piece == 'N' and captured_value > 3:
                    score += 0.5  # knight takes big piece
                if moving_piece == 'B' and captured_value > 3:
                    score += 0.5
            # Check if the destination is attacked by opponent
            if dst in opp_attacked:
                # We are moving into attack
                if not is_capture or (is_capture and VALUE[moving_piece] <= VALUE[captured[1]]):
                    # Not capturing or capturing equal/less, but moving into danger
                    # Only allow if it's checkmate or check
                    if gives_mate:
                        score += 100
                    elif gives_check:
                        score += 0.5
                    else:
                        score -= 0.5  # discourage moving into capture

        # Give high priority to checkmate
        if gives_mate:
            score += 1000
        elif gives_check:
            score += 0.2

        # Castling bonus: king safety
        if is_castle:
            score += 0.8

        # Encourage early development of minor pieces
        # If it's a knight or bishop move and not a capture, give small bonus early
        if move[0] in 'NB' and not is_capture and len(move) <= 3:  # simple Nf3, Bb4 etc.
            # Give small bonus if not in endgame
            if current_material > 10:  # rough early/mid game
                score += 0.1

        # Pawn moves forward: slight encouragement
        if move[0] not in 'KQRBN' and not is_capture and move[1:].isalnum():
            score += 0.05

        # Prefer central control: e4, d4, e5, d5, etc.
        central_squares = ['d4', 'd5', 'e4', 'e5', 'c4', 'c5', 'f4', 'f5']
        if dst in central_squares:
            score += 0.05
            if move[0] in 'NBP':  # minor or pawn
                score += 0.05

        # Ensure score is float
        score = float(score)

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    # Always return a legal move
    return best_move
