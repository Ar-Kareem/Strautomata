
import numpy as np

def policy(pieces, to_play, memory):
    # Helper functions
    def material_score(board):
        score = 0
        for square, piece in board.items():
            if piece[0] == to_play:
                score += PIECES_VALUE[piece[1]]
            else:
                score -= PIECES_VALUE[piece[1]]
        return score

    def king_safety(board, king_pos):
        # Calculate king safety score based on distance to edge and adjacent pieces
        rank = int(king_pos[1])
        file = ord(king_pos[0]) - ord('a')
        safety = 0
        for r in range(max(0, rank-2), min(8, rank+3)):
            for f in range(max(0, file-2), min(8, file+3)):
                sq = chr(f + ord('a')) + str(r)
                if sq in board:
                    piece = board[sq]
                    if piece[0] != to_play and piece[1] in ['N', 'B', 'R', 'Q']:
                        safety -= 1
        return safety

    def evaluate_position(board):
        # Main evaluation function
        material = material_score(board)
        king_pos = next(pos for pos, piece in board.items() if piece == to_play + 'K')
        safety = king_safety(board, king_pos)
        return material + safety

    # Constants
    PIECES_VALUE = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    MAX_DEPTH = 3
    THREAT_THRESHOLD = 5

    # Convert pieces dict to board representation
    board = {}
    for square, piece in pieces.items():
        board[square] = piece

    # Check for immediate checkmate
    for move in legal_moves:
        # Simulate move
        # (Implementation would check if move leads to checkmate)
        pass  # Placeholder for actual implementation

    # Evaluate all legal moves
    best_move = None
    best_score = -float('inf')
    for move in legal_moves:
        # Simulate move
        # (Implementation would check if move is legal and update board)
        pass  # Placeholder for actual implementation

    # Update memory
    memory['last_eval'] = best_score
    memory['last_move'] = best_move

    return best_move, memory
