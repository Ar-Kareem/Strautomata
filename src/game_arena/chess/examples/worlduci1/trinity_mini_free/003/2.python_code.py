
import numpy as np

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Helper function to check if a square is under attack
    def is_attacked(square, pieces, to_play):
        color = 'w' if to_play == 'white' else 'b'
        opp_color = 'b' if color == 'w' else 'w'
        # Check all possible attacks from opponent pieces
        for sq, piece in pieces.items():
            if piece[0] == opp_color:
                # Check knight moves
                if piece[1] == 'N':
                    for move in [(2,1), (1,2), (-1,2), (-2,1), (-2,-1), (-1,-2), (1,-2), (2,-1)]:
                        if (ord(sq[0]) + move[0], int(sq[1]) + move[1]) == (ord(square[0]), int(square[1])):
                            return True
                # Check sliding pieces (queen, rook, bishop)
                elif piece[1] in 'QRB':
                    directions = {'R': [(1,0), (-1,0), (0,1), (0,-1)],
                                  'B': [(1,1), (1,-1), (-1,1), (-1,-1)],
                                  'Q': [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)]}
                    for dx, dy in directions[piece[1]]:
                        x, y = ord(square[0]) + dx, int(square[1]) + dy
                        while 1 <= x <= 8 and 1 <= y <= 8:
                            target = chr(x) + str(y)
                            if target not in pieces:
                                continue
                            if pieces[target][0] == color:
                                break
                            if pieces[target][0] == opp_color:
                                if piece[1] in 'RB' and (dx,dy) in [(1,0), (-1,0), (0,1), (0,-1)]:
                                    return True
                                if piece[1] == 'Q' and (abs(dx) == abs(dy) or dx == 0 or dy == 0):
                                    return True
                                break
                            x += dx
                            y += dy
        return False

    # Helper function to check if king is in checkmate
    def is_checkmate(pieces, to_play):
        color = 'w' if to_play == 'white' else 'b'
        opp_color = 'b' if color == 'w' else 'w'
        king_sq = None
        # Find the king's square
        for sq, piece in pieces.items():
            if piece[0] == color and piece[1] == 'K':
                king_sq = sq
                break
        if not king_sq:
            return False
        # Check if king is in check
        if not is_attacked(king_sq, pieces, to_play):
            return False
        # Check if all king's moves are blocked or captured
        king_moves = [(king_sq[0], int(king_sq[1]) + 1), (king_sq[0], int(king_sq[1]) - 1),
                      (chr(ord(king_sq[0]) + 1), king_sq[1]), (chr(ord(king_sq[0]) - 1), king_sq[1]),
                      (chr(ord(king_sq[0]) + 1), str(int(king_sq[1]) + 1)), (chr(ord(king_sq[0]) + 1), str(int(king_sq[1]) - 1)),
                      (chr(ord(king_sq[0]) - 1), str(int(king_sq[1]) + 1)), (chr(ord(king_sq[0]) - 1), str(int(king_sq[1]) - 1))]
        for move in king_moves:
            if 1 <= int(move[1]) <= 8 and 'a' <= move[0] <= 'h':
                target = move[0] + move[1]
                if target not in pieces or pieces[target][0] == color:
                    continue
                # Check if moving to target is safe
                if not is_attacked(target, pieces, to_play):
                    return False
       