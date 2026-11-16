
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    def get_move_value(move: str) -> int:
        if move[0] in ['N', 'B', 'R', 'Q', 'K']:
            piece_type = move[0]
        elif move[0].islower():
            piece_type = 'P'
        elif move and move[0] == 'x':
            piece_type = 'P'
        else:
            piece_type = 'P'
        values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
        return values.get(piece_type, 1)

    def get_destination_square(move: str) -> str:
        if move in ['O-O', 'O-O-O']:
            return None
        if 'x' in move:
            after_x = move.split('x')[-1]
            square = ''
            for ch in after_x:
                if ch.isalpha() or ch.isdigit():
                    square += ch
                    if len(square) == 2:
                        break
            return square
        elif '=' in move:
            return move.split('=')[0][-2:]
        else:
            return move[-2:]

    best_move = legal_moves[0]
    max_score = float('-inf')

    current_color = 'w' if to_play == 'white' else 'b'

    for move in legal_moves:
        score = 0

        if move.endswith('#'):
            score += 1000
        elif move.endswith('+'):
            score += 50

        if '=' in move and not move.endswith('+') and not move.endswith('#'):
            after_equals = move.split('=')[1]
            promoted_piece = after_equals[0]
            if promoted_piece == 'Q':
                score += 50
            elif promoted_piece == 'R':
                score += 40
            elif promoted_piece in ['B', 'N']:
                score += 30

        if 'x' in move:
            dest_square = get_destination_square(move)
            if dest_square in pieces:
                captured_piece = pieces[dest_square]
                captured_color = 'b' if to_play == 'white' else 'w'
                if captured_piece[0] == captured_color:
                    captured_val = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}.get(captured_piece[1], 0)
                    capturer_val = get_move_value(move)
                    score += (captured_val - capturer_val)

        if move in ['O-O', 'O-O-O']:
            score += 20

        if score > max_score:
            max_score = score
            best_move = move

    return (best_move, memory)
