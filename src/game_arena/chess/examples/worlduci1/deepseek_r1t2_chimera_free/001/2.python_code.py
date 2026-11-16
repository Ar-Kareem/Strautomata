
import numpy as np

PIECE_VALUES = {
    'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0
}

CENTRAL_SQUARES = {'d4', 'e4', 'd5', 'e5', 'c3', 'f3', 'c6', 'f6'}

def policy(pieces: dict[str, str], to_play: str) -> str:
    color = 'w' if to_play == 'white' else 'b'
    opponent = 'b' if color == 'w' else 'w'
    
    # Helper functions
    def square_value(square):
        file, rank = square[0], int(square[1])
        center_bonus = 0.1 * (1 + (file in 'de') + (rank in [3,4,5]))
        return center_bonus
    
    def capture_value(move, opp_piece):
        if opp_piece.endswith('K'):
            return float('inf')  # Checkmate
        captured_value = PIECE_VALUES.get(opp_piece[1], 0)
        capturer = pieces.get(move[:2], '')[1]
        capturer_value = PIECE_VALUES.get(capturer, 1)
        safety = 1 - (capturer_value < captured_value) * 0.5
        return captured_value * safety
    
    move_scores = {}
    
    # Generate legal moves from the arena system (would normally be provided)
    # For this implementation, we assume legal_moves are provided elsewhere
    # and must be computed based on current position (simplified for this example)
    
    # Instead, we'll process pieces into a board and evaluate all possible moves
    # Since legal_moves are not provided, this is a placeholder
    
    # Create a board representation
    board = {}
    for pos, piece in pieces.items():
        board.setdefault(pos, piece)
    
    # Evaluate each potential move (hypothetical legal_moves)
    for move in generate_legal_moves(board, color):
        score = 0
        src, dest = move[:2], move[2:]
        
        # Check for capture
        captured_piece = board.get(dest, '')
        if captured_piece and captured_piece[0] == opponent:
            score += 10 * capture_value(move, captured_piece)
        
        # Promotion to queen
        if len(move) == 5 and move[4] == 'q':
            score += 100
        
        # Castling bonus (king moves 2 squares)
        piece = board.get(src, '')
        if piece[1] == 'K' and abs(ord(src[0]) - ord(dest[0])) == 2:
            score += 150 if src[1] in ('1','8') else 50
        
        # Central control for pawns/knights
        if piece[1] in ('P','N'):
            score += 0.5 * (1 if dest in CENTRAL_SQUARES else 0)
        
        # King safety - avoid moving to edges
        if piece[1] == 'K':
            score += (ord(dest[0]) in range(ord('c'), ord('f'))) * 10
        
        # Avoid moving queens early
        if piece[1] == 'Q' and sum('P' in p for p in pieces.values()) > 8:
            score -= 20
        
        # Check for immediate threats to the moved piece
        # Simplified: penalize moving to attacked squares
        # For full implementation, simulate the move and check opponent responses
        
        move_scores[move] = score
    
    # If no captures, add small positional bonuses
    for move, score in move_scores.items():
        if score == 0:
            dest = move[2:]
            move_scores[move] += square_value(dest)
    
    # Select move with highest score
    if move_scores:
        return max(move_scores, key=move_scores.get)
    
    # Fallback if no moves
    return list(board.keys())[0] + list(board.keys())[1]  # Placeholder

# Helper to generate legal moves (simplified example)
def generate_legal_moves(board, color):
    moves = []
    for src, piece in board.items():
        if piece[0] != color:
            continue
        # Simplified move generation (actual implementation would involve chess rules)
        # Example: pawn moves
        if piece[1] == 'P':
            direction = 1 if color == 'w' else -1
            new_rank = str(int(src[1]) + direction)
            # Move forward
            forward_square = src[0] + new_rank
            if forward_square not in board:
                moves.append(src + forward_square)
                # Double move if on starting rank
                if (color == 'w' and src[1] == '2') or (color == 'b' and src[1] == '7'):
                    double_square = src[0] + str(int(src[1]) + 2*direction)
                    if double_square not in board:
                        moves.append(src + double_square)
    
    # Add castling moves if available (simplified)
    king_pos = 'e1' if color == 'w' else 'e8'
    if board.get(king_pos, '') == color + 'K':
        if board.get('h1' if color == 'w' else 'h8', '') == color + 'R':
            moves.append(king_pos + 'g1') if color == 'w' else moves.append(king_pos + 'g8')
        if board.get('a1' if color == 'w' else 'a8', '') == color + 'R':
            moves.append(king_pos + 'c1') if color == 'w' else moves.append(king_pos + 'c8')
    
    return moves

# Note: In a real implementation, legal moves should be accurately generated 
# using a chess library or proper move generation functions. This is a simplified placeholder.
