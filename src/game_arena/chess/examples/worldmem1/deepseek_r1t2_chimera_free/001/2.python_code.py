
import re

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    my_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if my_color == 'w' else 'w'
    
    # Initialize memory for move count and opening book
    if 'move_count' not in memory:
        memory['move_count'] = 0
    move_count = memory['move_count']
    memory['move_count'] = move_count + 1
    
    # Predefined opening moves for white/black (simplified Italian Game)
    if 'opening_moves' not in memory:
        memory['opening_moves'] = {
            'white': ['e4', 'Nf3', 'Bc4', 'O-O', 'd3', 'Nc3'],
            'black': ['e5', 'Nc6', 'Bc5', 'O-O', 'd6', 'Nf6']
        }
        memory['opening_index'] = 0
    
    # Try to follow opening moves if possible
    if memory['opening_index'] < len(memory['opening_moves'][to_play]):
        next_opening_move = memory['opening_moves'][to_play][memory['opening_index']]
        if next_opening_move in legal_moves:
            memory['opening_index'] += 1
            return (next_opening_move, memory)
    
    best_move = legal_moves[0]
    best_score = -float('inf')
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Helper to extract destination square from move string
    def get_destination(move):
        squares = re.findall(r'[a-h][1-8]', move)
        return squares[-1] if squares else None
    
    for move in legal_moves:
        score = 0
        dest = get_destination(move)
        
        # Handle castling early
        if move == 'O-O' or move == 'O-O-O':
            score += 200 if move_count < 10 else 50  # Strong early bonus
            if score > best_score:
                best_score, best_move = score, move
            continue
        
        # Determine moving piece type
        if not dest:  # Fallback if regex fails
            continue
        piece_type = 'P'  # Default to pawn
        if move[0] in 'KQRBN':
            piece_type = move[0]
        elif move.startswith('O-O'):
            piece_type = 'K'
        
        # Material gain from captures
        if dest in pieces and pieces[dest][0] == opponent_color:
            captured_value = piece_values.get(pieces[dest][1], 0)
            score += captured_value * 2  # Prioritize captures
        
        # Promotion bonus
        if '=Q' in move:
            score += 8  # Queen promotion is best
        elif '=R' in move:
            score += 4
        elif '=B' in move or '=N' in move:
            score += 2
        
        # Check bonus
        if move.endswith('+'):
            score += 50
        
        # Positional scoring
        file, rank = dest[0], int(dest[1])
        central_files = ['d', 'e']
        central_ranks = [3, 4, 5, 6]
        
        if file in central_files and rank in central_ranks:
            score += 1  # Central control
            if piece_type in ['N', 'B']:
                score += 2  # Extra for minor pieces
        
        # Pawn advancement
        if piece_type == 'P':
            advancement = rank - 2 if my_color == 'w' else 7 - rank - 1
            score += advancement * 0.2
        
        # Early development bonus (first 15 moves)
        if move_count < 15 and piece_type in ['N', 'B']:
            score += 1
        
        # Avoid moving king unnecessarily
        if move_count < 10 and piece_type == 'K':
            score -= 3
        
        # Update best move
        if score > best_score:
            best_score, best_move = score, move
    
    return (best_move, memory)
