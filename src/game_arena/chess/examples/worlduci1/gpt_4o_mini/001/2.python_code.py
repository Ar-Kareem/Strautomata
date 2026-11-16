
def policy(pieces: dict[str, str], to_play: str) -> str:
    def is_checkmate(pieces, king_position):
        for move in legal_moves:
            # Simulate the move
            target_position = move[2:4]  # the destination of the move
            temp_pieces = pieces.copy()
            temp_pieces[target_position] = temp_pieces.pop(move[:2])  # Move the piece
            if not is_in_check(temp_pieces, king_position):
                return False
        return True

    def is_in_check(pieces, king_position):
        for pos, piece in pieces.items():
            if piece[0] != to_play[0]:  # Only check opponent's pieces
                if can_attack(piece, pos, king_position, pieces):
                    return True
        return False

    def can_attack(piece, from_pos, to_pos, pieces):
        # Implement basic attacking logic based on piece type
        row_diff = abs(ord(to_pos[0]) - ord(from_pos[0]))
        col_diff = abs(int(to_pos[1]) - int(from_pos[1]))
        
        if piece[1] == 'K':
            return (row_diff <= 1 and col_diff <= 1)
        elif piece[1] == 'Q':
            return (row_diff == col_diff or from_pos[0] == to_pos[0] or from_pos[1] == to_pos[1])
        elif piece[1] == 'R':
            return (from_pos[0] == to_pos[0] or from_pos[1] == to_pos[1])
        elif piece[1] == 'B':
            return (row_diff == col_diff)
        elif piece[1] == 'N':
            return (row_diff == 1 and col_diff == 2) or (row_diff == 2 and col_diff == 1)
        elif piece[1] == 'P':
            direction = 1 if piece[0] == 'w' else -1
            if row_diff == 1 and col_diff == 1:
                return (int(to_pos[1]) - int(from_pos[1])) == direction
        return False

    legal_moves = get_legal_moves(pieces, to_play)  # Assume there's a function to fetch legal moves
    king_position = None

    for pos, piece in pieces.items():
        if piece == (to_play[0] + 'K'):
            king_position = pos
    
    # Prioritize checkmate
    for move in legal_moves:
        if is_checkmate(pieces, king_position):
            return move
    
    # Return the first available legal move as a default action if no other better move is found
    return legal_moves[0]

def get_legal_moves(pieces, player):
    # Placeholder for the function that generates legal moves based on the given pieces and player
    return []
