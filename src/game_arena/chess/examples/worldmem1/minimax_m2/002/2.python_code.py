
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    def get_destination(move, to_play):
        if move.startswith('O-O'):
            return 'g1' if to_play == 'white' else 'g8'
        elif move.startswith('O-O-O'):
            return 'c1' if to_play == 'white' else 'c8'
        else:
            for i in range(len(move)-1, 0, -1):
                if move[i-1] in 'abcdefgh' and move[i] in '12345678':
                    return move[i-1:i+1]
            return None
    
    scored_moves = []
    for move in legal_moves:
        score = 0
        if move.endswith('#'):
            score += 1000000
        elif move.endswith('+'):
            score += 10000
        
        if 'x' in move:
            dest = get_destination(move, to_play)
            captured_piece = pieces.get(dest)
            if captured_piece is not None:
                piece_type = captured_piece[1]
                value = piece_values.get(piece_type, 0)
                score += value * 100
        
        if move.startswith('O-O') or move.startswith('O-O-O'):
            score += 1000
        else:
            dest = get_destination(move, to_play)
            if dest is not None:
                file_char = dest[0]
                rank_char = dest[1]
                x = ord(file_char) - ord('a')
                y = int(rank_char) - 1
                dist = ((x - 3.5)**2 + (y - 3.5)**2)**0.5
                bonus = 100 - dist * 10
                if bonus < 0:
                    bonus = 0
                score += bonus
        
        scored_moves.append((score, move))
    
    scored_moves.sort(key=lambda x: x[0], reverse=True)
    chosen_move = scored_moves[0][1]
    return chosen_move, {}
