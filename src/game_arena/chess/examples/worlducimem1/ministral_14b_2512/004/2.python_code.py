
import sys
from collections import defaultdict

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Parse the current board state
    board = Board(pieces, to_play)
    legal_moves = memory.get('legal_moves', [])

    if not legal_moves:
        return ("", memory)  # Should not happen per problem constraints

    # Generate candidate moves (sorted by evaluation)
    candidates = []
    for move in legal_moves:
        new_pieces = board.apply_move(move)
        new_board = Board(new_pieces, to_play)
        score = evaluate_position(new_board, to_play)
        candidates.append((move, score))

    # Sort by score (descending for white, ascending for black)
    candidates.sort(key=lambda x: x[1] * (-1 if to_play == 'white' else 1), reverse=True)

    # Select the best move (or first if no clear winner)
    best_move = candidates[0][0]

    # Update memory with legal moves for next call (optional)
    memory['legal_moves'] = legal_moves
    return (best_move, memory)

class Board:
    def __init__(self, pieces, to_play):
        self.pieces = pieces
        self.to_play = to_play
        self.king_pos = None
        self.find_king()

    def find_king(self):
        for square, piece in self.pieces.items():
            if piece.endswith('K'):
                self.king_pos = square
                break

    def apply_move(self, move):
        new_pieces = self.pieces.copy()
        from_sq = move[:2]
        to_sq = move[2:4]

        # Handle pawn promotion (5-char moves)
        if len(move) == 5:
            piece = move[4]
            new_pieces[to_sq] = self.to_play[0].upper() + piece
            del new_pieces[from_sq]
            return new_pieces

        # Move the piece
        piece = new_pieces[from_sq]
        new_pieces[to_sq] = piece
        del new_pieces[from_sq]

        # Handle castling (e.g., e1g1)
        if piece.endswith('K') and abs(ord(to_sq[0]) - ord(from_sq[0])) == 2:
            rook_from = 'h1' if to_sq == 'g1' else 'a1' if to_sq == 'c1' else 'h8' if to_sq == 'g8' else 'a8'
            rook_to = 'f1' if to_sq == 'g1' else 'd1' if to_sq == 'c1' else 'f8' if to_sq == 'g8' else 'd8'
            new_pieces[rook_to] = new_pieces[rook_from]
            del new_pieces[rook_from]

        return new_pieces

def evaluate_position(board, to_play):
    # Material evaluation (piece-square tables could be added for depth)
    material = 0
    for piece in board.pieces.values():
        color = piece[0]
        value = piece[1]
        if color == to_play[0]:
            material += piece_value(value)
        else:
            material -= piece_value(value)

    # Mobility (number of legal moves for each piece)
    mobility = 0
    for square, piece in board.pieces.items():
        if piece[0] == to_play[0]:
            mobility += count_moves(board, square, piece)

    # King safety (distance to enemy pieces)
    king_safety = king_safety_score(board, to_play)

    # Pawn structure (bonus for passed pawns, penalty for weaknesses)
    pawn_structure = pawn_structure_score(board, to_play)

    # Combine evaluations (weights can be tuned)
    total = (
        material * 100 +
        mobility * 5 +
        king_safety * 20 +
        pawn_structure * 10
    )

    return total

def piece_value(piece):
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    return values.get(piece, 0)

def count_moves(board, square, piece):
    # Simplified: count all possible moves (no legal move generation here)
    # In a real implementation, generate legal moves for the piece
    return 1  # Placeholder

def king_safety_score(board, to_play):
    king_sq = None
    for sq, p in board.pieces.items():
        if p.endswith('K') and p[0] == to_play[0]:
            king_sq = sq
            break

    if not king_sq:
        return 0

    # Penalize if king is in the center or near enemy pieces
    center_distance = abs(ord(king_sq[0]) - ord('d')) + abs(int(king_sq[1]) - 5)
    enemy_pieces_near = 0

    for sq, p in board.pieces.items():
        if p[0] != to_play[0] and abs(ord(sq[0]) - ord(king_sq[0])) <= 1 and abs(int(sq[1]) - int(king_sq[1])) <= 1:
            enemy_pieces_near += 1

    return center_distance - enemy_pieces_near * 2

def pawn_structure_score(board, to_play):
    score = 0
    for sq, p in board.pieces.items():
        if p[0] == to_play[0] and p[1] == 'P':
            # Bonus for passed pawns (simplified)
            if not any(
                board.pieces.get(f"{chr(ord(sq[0]) + dx)}{int(sq[1]) + dy}", None)
                for dx in [-1, 0, 1]
                for dy in [1]
            ):
                score += 1
            # Penalty for doubled pawns
            file = sq[0]
            pawns_on_file = sum(1 for s, piece in board.pieces.items() if piece[0] == to_play[0] and piece[1] == 'P' and s[0] == file)
            if pawns_on_file > 1:
                score -= 0.5
    return score
