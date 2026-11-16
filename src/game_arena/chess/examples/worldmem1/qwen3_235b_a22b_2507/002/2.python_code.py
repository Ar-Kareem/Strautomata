
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Piece values
    PIECE_VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Invert color for opponent
    color_key = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if to_play == 'white' else 'w'
    
    # Check if we're in endgame (few pieces), but not used yet
    total_pieces = len(pieces)
    
    # Score each legal move
    best_score = float('-inf')
    best_move = legal_moves[0]  # fallback

    # Retrieve memory: track if castled or move count
    move_count = memory.get('move_count', 0)
    memory['move_count'] = move_count + 1

    for move in legal_moves:
        score = 0

        # 1. Detect checkmate (ends with # or similar; check for '+', '++', '#')
        if '#' in move or move.endswith('++') or move.endswith('#'):
            score += 10000
            if score > best_score:
                best_score = score
                best_move = move
                continue  # Don't evaluate further

        # 2. Promotion
        if '=Q' in move:
            score += PIECE_VALUES['Q']
        elif '=R' in move:
            score += PIECE_VALUES['R']
        elif '=B' in move:
            score += PIECE_VALUES['B']
        elif '=N' in move:
            score += PIECE_VALUES['N']

        # 3. Capture
        if 'x' in move:
            # Extract destination square (after 'x')
            match = re.search(r'x([a-h][1-8])', move)
            if match:
                target_sq = match.group(1)
                if target_sq in pieces:
                    captured = pieces[target_sq]
                    # Ensure opponent piece
                    if captured[0] == opp_color:
                        score += PIECE_VALUES[captured[1]]

        # 4. Check bonus
        if move.endswith('+') or '+' in move:
            score += 0.5

        # 5. Castling bonus
        if move == 'O-O' or move == 'O-O-O':
            score += 1.0  # encourage castling

        # 6. Prefer developing knights and bishops early
        if move.startswith('N') and len(move) <= 3 and move[1] not in 'x=':
            # Simple knight move (like Nf3, not Nxe5 or Nbc3)
            if move_count < 10:  # early game
                score += 0.5

        if move.startswith('B') and len(move) <= 3 and move[1] not in 'x=':
            if move_count < 10:
                score += 0.5

        # 7. Penalize pawn moves that retreat or do nothing (rare)
        if move.startswith('b') and move[1] in '1234' and color_key == 'w':
            score -= 0.1
        if move.startswith('g') and move[1] in '5678' and color_key == 'b':
            score -= 0.1

        # 8. Slightly prefer central pawn pushes (e.g. e4, d4, e5, d5)
        if re.fullmatch(r'[e,d][4,5]', move) and move[0] in 'ed':
            score += 0.2

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    return best_move, memory
