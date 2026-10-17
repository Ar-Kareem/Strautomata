
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    # Define piece values
    value_map = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Determine current color
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    
    # Check if king is in danger: look for exposed king, but keep it fast
    def get_king_square():
        for sq, piece in pieces.items():
            if piece == f'{color}K':
                return sq
        return None

    # Simple check if a square is attacked (used to discourage bad king moves)
    def is_attacked(square: str) -> bool:
        # Check if any opponent piece can move to this square
        # We'll do a simple linear check for sliding and jumping pieces
        file, rank = square[0], square[1]
        f_idx, r_idx = ord(file) - ord('a'), int(rank) - 1

        # Directions: up, down, left, right, up-right, up-left, down-right, down-left
        directions = [
            (0, 1), (0, -1), (-1, 0), (1, 0),  # rook directions
            (1, 1), (1, -1), (-1, 1), (-1, -1)  # bishop directions
        ]
        knight_moves = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
        for k_f, k_r in knight_moves:
            nf, nr = f_idx + k_f, r_idx + k_r
            if 0 <= nf < 8 and 0 <= nr < 8:
                ns = f"{chr(ord('a')+nf)}{nr+1}"
                if ns in pieces and pieces[ns] == f'{opponent_color}N':
                    return True

        # Check for pawns
        k_dir = 1 if color == 'w' else -1  # pawns capture forward (relative to their color)
        for df in [-1, 1]:
            nf, nr = f_idx + df, r_idx + k_dir
            if 0 <= nf < 8 and 0 <= nr < 8:
                ns = f"{chr(ord('a')+nf)}{nr+1}"
                if ns in pieces and pieces[ns] == f'{opponent_color}P':
                    return True

        # Sliding pieces
        for dx, dy in directions:
            for i in range(1, 8):
                nf, nr = f_idx + i*dx, r_idx + i*dy
                if not (0 <= nf < 8 and 0 <= nr < 8):
                    break
                ns = f"{chr(ord('a')+nf)}{nr+1}"
                if ns in pieces:
                    piece = pieces[ns]
                    if piece[0] == color:
                        break
                    ptype = piece[1]
                    # Rooks and queens can attack along straight lines
                    if dx in [0, 0] and dy in [-1,1] and ptype in 'RQ':  # Actually, correct rook moves: only one of dx,dy nonzero and same dir
                        return True
                    # Bishops and queens along diagonals
                    if abs(dx) == abs(dy) and ptype in 'BQ':
                        return True
                    # Otherwise, blocked or not relevant
                    break
        # Finally, check king (in case of king proximity)
        for df in [-1,0,1]:
            for dr in [-1,0,1]:
                if df == 0 and dr == 0:
                    continue
                nf, nr = f_idx + df, r_idx + dr
                if 0 <= nf < 8 and 0 <= nr < 8:
                    ns = f"{chr(ord('a')+nf)}{nr+1}"
                    if ns in pieces and pieces[ns] == f'{opponent_color}K':
                        return True
        return False

    def evaluate_move(move: str) -> int:
        score = 0

        # +1000 for checkmate
        if '#' in move:
            return 10000

        # +50 for promotion
        if '=Q' in move:
            score += 90
        elif '=R' in move or '=B' in move:
            score += 50
        elif '=N' in move:
            score += 30

        # +10 for delivering check
        if '+' in move:
            score += 10

        # +20 for castling
        if move == 'O-O' or move == 'O-O-O':
            score += 20

        # Check for capture
        if 'x' in move:
            # Extract captured square: last two chars before = or + or #
            # Example: Bxf5+ -> f5; b8=Q -> not a capture; cxd8=Q+ -> d8
            capture_match = re.search(r'x([a-h][1-8])', move)
            if capture_match:
                cap_square = capture_match.group(1)
                if cap_square in pieces:
                    captured_piece = pieces[cap_square]
                    if captured_piece[0] != color:  # opponent piece
                        piece_value = value_map[captured_piece[1]]
                        score += piece_value * 10  # Material gain

        # Penalize moving king unnecessarily unless castling
        if move.startswith('K') and 'x' not in move and move not in ['O-O', 'O-O-O']:
            king_sq = get_king_square()
            if king_sq and not is_attacked(king_sq):
                # If king is safe, avoid moving it without capture
                # But if the move puts it under attack, penalize more
                # Simulate: where would king go?
                dest_match = re.search(r'[a-h][1-8](?=[+#]|$)', move)
                if dest_match:
                    dest_sq = dest_match.group(0)
                    if is_attacked(dest_sq):
                        score -= 25  # Don't walk into danger
                    else:
                        score -= 5  # Just discourage unnecessary king moves

        # Encourage developing knights and bishops early (not a long-term plan, but helps)
        # Very simple: if it's a N or B move in the first few moves, give a small boost
        # We can count total material to estimate game phase roughly
        total_material = sum(value_map[p[1]] for p in pieces.values() if p[0] == color)
        if total_material >= 38:  # Roughly full army (1*9 + 2*3 + 2*3 + 2*5 + 1*9 = 39)
            if move.startswith('N') or move.startswith('B'):
                score += 2

        return score

    # Score all legal moves
    scored_moves = [(move, evaluate_move(move)) for move in legal_moves]

    # Choose the move with the highest score
    best_move = max(scored_moves, key=lambda x: x[1])[0]

    return best_move
