
from typing import Dict, List

def simulate_move(pieces: Dict, move: str, to_play: str):
    new_pieces = {k: v for k, v in pieces.items()}
    
    # Handle castling
    if move == 'O-O':
        if to_play == 'white':
            new_pieces['g1'] = 'wK'
            del new_pieces['e1']
            if 'h1' in new_pieces:
                new_pieces['f1'] = 'wR'
                del new_pieces['h1']
        else:
            new_pieces['g8'] = 'bK'
            del new_pieces['e8']
            if 'h8' in new_pieces:
                new_pieces['f8'] = 'bR'
                del new_pieces['h8']
    elif move == 'O-O-O':
        if to_play == 'white':
            new_pieces['c1'] = 'wK'
            del new_pieces['e1']
            if 'a1' in new_pieces:
                new_pieces['d1'] = 'wR'
                del new_pieces['a1']
        else:
            new_pieces['c8'] = 'bK'
            del new_pieces['e8']
            if 'a8' in new_pieces:
                new_pieces['d8'] = 'bR'
                del new_pieces['a8']
    else:
        # Capture or pawn move
        if 'x' in move:
            parts = move.split('x', 1)
            origin, dest = parts[0], parts[1]
            dest_sq = dest
        else:
            # Pawn move or other non-capture
            # Assume move is in the format [piece][square] or [square]
            if len(move) >= 4:
                # Piece move: 'Nbd2'
                origin = move[1:3]
                dest_sq = move[-2:]
            else:
                # Pawn move: 'e4'
                dest_sq = move
                origin = None
        
        # Remove captured piece
        if 'x' in move:
            dest_sq = move.split('x', 1)[1]
            if dest_sq in new_pieces:
                del new_pieces[dest_sq]
        
        # Move the piece
        piece_type = None
        if len(move) >= 2:
            piece_type = move[0]
            if piece_type in ['R', 'B', 'Q', 'N']:
                origin_sq = move[1:3]
                if origin_sq in new_pieces:
                    piece = new_pieces[origin_sq]
                    if piece[0] == ('w' if to_play == 'white' else 'b'):
                        new_pieces[dest_sq] = piece
                        del new_pieces[origin_sq]
        
        # Handle pawn promotion
        if len(move) >= 3 and move[-2:] in ['e8', 'h8', 'e1', 'h1']:
            if color == 'white':
                promotion = move[-1]
                if promotion in ['Q', 'R', 'B', 'N']:
                    new_pieces[dest_sq] = to_play + promotion
            else:
                promotion = move[-1]
                if promotion in ['Q', 'R', 'B', 'N']:
                    new_pieces[dest_sq] = color + promotion if to_play == 'black' else 'b' + promotion
    
    return new_pieces

def piece_value(piece: str) -> int:
    if piece[1] == 'Q':
        return 9
    elif piece[1] == 'R':
        return 5
    elif piece[1] in ['B', 'N']:
        return 3
    elif piece[1] == 'P':
        return 1
    else:
        return 0  # King

def is_checkmate(board: Dict, check_square: str, check_color: str) -> bool:
    # Check if king is in check
    # Then check if any escape is possible
    # This is a simplified version
    return False  # Placeholder for full checkmate detection

def policy(pieces: Dict, to_play: str, legal_moves: List[str]) -> str:
    max_val = 0
    best_move = legal_moves[0]

    # Priority list: checkmate > queen > rook > knight/bishop > castling
    for move in legal_moves:
        # Simulate move
        new_board = simulate_move(pieces, move, to_play)
        color_opponent = 'b' if to_play == 'white' else 'w'
        king_sq = next((sq for sq in new_board if new_board[sq][0] == color_opponent and new_board[sq][1] == 'K'), None)
        if king_sq:
            checkmate = is_checkmate(new_board, king_sq, color_opponent)
            if checkmate:
                max_val = 1000
                best_move = move
                break
        # Check for captures
        if 'x' in move:
            captured_square = move.split('x', 1)[1]
            if captured_square in new_board:
                captured_val = piece_value(new_board[captured_square])
                if captured_val > max_val:
                    max_val = captured_val
                    best_move = move

    # If no checkmate found, prioritize captures
    if max_val == 1000:
        return best_move
    else:
        return best_move
