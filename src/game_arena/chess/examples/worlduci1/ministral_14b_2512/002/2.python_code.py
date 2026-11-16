
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    # --- Helper Functions ---
    def get_piece_value(piece):
        """Returns the value of a piece (in pawn units)."""
        if piece[1] == 'P': return 1
        elif piece[1] == 'N': return 3
        elif piece[1] == 'B': return 3
        elif piece[1] == 'R': return 5
        elif piece[1] == 'Q': return 9
        elif piece[1] == 'K': return 0  # King is not directly valued in captures
        else: return 0

    def is_pawn_on_8th_rank(square):
        """Checks if a pawn is on the 8th rank (for promotion)."""
        return square[1] == '8'

    def is_king_in_check(pieces, color):
        """Checks if the king is in check (simplified heuristic)."""
        king_square = None
        opponent_pieces = {sq: pc for sq, pc in pieces.items() if pc[0] != color}
        for sq, pc in pieces.items():
            if pc[0] == color and pc[1] == 'K':
                king_square = sq
                break
        if not king_square:
            return False  # No king found (invalid position)

        # Check if any opponent piece attacks the king
        # (Simplified: Assume rooks/bishops attack along ranks/files, knights to L-shaped squares)
        king_file, king_rank = king_square[0], king_square[1]
        for sq, pc in opponent_pieces.items():
            file, rank = sq[0], sq[1]
            if pc[1] == 'R':
                if file == king_file or rank == king_rank:  # Rook attacks along rank/file
                    return True
            elif pc[1] == 'B':
                if abs(ord(file) - ord(king_file)) == abs(int(rank) - int(king_rank)):  # Bishop diagonal
                    return True
            elif pc[1] == 'Q':
                if file == king_file or rank == king_rank or abs(ord(file) - ord(king_file)) == abs(int(rank) - int(king_rank)):
                    return True
            elif pc[1] == 'N':
                if (abs(ord(file) - ord(king_file)) == 2 and abs(int(rank) - int(king_rank)) == 1) or \
                   (abs(ord(file) - ord(king_file)) == 1 and abs(int(rank) - int(king_rank)) == 2):
                    return True
            elif pc[1] == 'P':
                # Pawn attacks (black pawns attack forward-right, white forward-left)
                if color == 'white' and rank == '7' and file in ['b', 'c', 'd', 'e', 'f', 'g', 'h']:
                    if file == 'b' and king_file == 'a' or \
                       file == 'c' and king_file == 'b' or \
                       file == 'd' and king_file == 'c' or \
                       file == 'e' and king_file == 'd' or \
                       file == 'f' and king_file == 'e' or \
                       file == 'g' and king_file == 'f' or \
                       file == 'h' and king_file == 'g':
                        return True
                elif color == 'black' and rank == '2' and file in ['b', 'c', 'd', 'e', 'f', 'g', 'h']:
                    if file == 'b' and king_file == 'a' or \
                       file == 'c' and king_file == 'b' or \
                       file == 'd' and king_file == 'c' or \
                       file == 'e' and king_file == 'd' or \
                       file == 'f' and king_file == 'e' or \
                       file == 'g' and king_file == 'f' or \
                       file == 'h' and king_file == 'g':
                        return True
        return False

    def evaluate_move(move, pieces, to_play):
        """Evaluates a move based on material gain, king safety, and pawn promotion."""
        from_sq, to_sq = move[:2], move[2:4]
        piece = pieces[from_sq]
        color = piece[0]

        # Check if the move is a capture (and evaluate material gain)
        if to_sq in pieces:
            captured_piece = pieces[to_sq]
            if captured_piece[0] != color:  # Opponent's piece
                material_gain = get_piece_value(piece) - get_piece_value(captured_piece)
            else:  # Friendly piece (en passant or underpromotion)
                material_gain = 0
        else:
            material_gain = 0

        # Check if the move is a pawn promotion
        is_promotion = len(move) > 4
        if is_promotion:
            promotion_value = 9  # Queen promotion is default (max value)
        else:
            promotion_value = 0

        # Check if the move puts the opponent's king in check
        puts_opponent_in_check = False
        if not is_pawn_on_8th_rank(to_sq):  # Not a pawn promotion (since promotions don't put king in check)
            # Simulate the move (temporarily update pieces)
            temp_pieces = pieces.copy()
            del temp_pieces[from_sq]
            temp_pieces[to_sq] = piece
            puts_opponent_in_check = is_king_in_check(temp_pieces, 'w' if color == 'b' else 'b')

        # Check if the move improves king safety (e.g., castling or moving king away from danger)
        king_safety_improvement = 0
        if piece[1] == 'K':
            # If castling, assume safety improvement
            if from_sq == 'e1' and to_sq in ['g1', 'c1']: king_safety_improvement = 5
            elif from_sq == 'e8' and to_sq in ['g8', 'c8']: king_safety_improvement = 5
            else:
                # Simple heuristic: Moving king to a lower rank (closer to center) is safer
                old_rank = int(from_sq[1])
                new_rank = int(to_sq[1])
                if color == 'white' and new_rank < old_rank: king_safety_improvement = 1
                elif color == 'black' and new_rank > old_rank: king_safety_improvement = 1

        # Check if the move develops a knight or bishop
        develops_piece = 0
        if piece[1] in ['N', 'B']:
            # Knights/bishops moving toward center (e3, e4, d4, d5) are good
            center_files = {'d', 'e'}
            center_ranks = {'4', '5'} if color == 'white' else {'3', '4'}
            if to_sq[0] in center_files and to_sq[1] in center_ranks:
                develops_piece = 2
            else:
                develops_piece = 1  # Still counts as development

        # Check if the move is a pawn push (e.g., e4, d4)
        is_pawn_push = piece[1] == 'P' and not is_pawn_on_8th_rank(to_sq)
        if is_pawn_push:
            # Prioritize central pawn pushes
            if to_sq[0] in ['d', 'e'] and to_sq[1] in ['3', '4', '5']:
                develops_piece += 1  # Bonus for central pawn pushes

        # Score the move (higher is better)
        score = material_gain * 10 + (1 if puts_opponent_in_check else 0) * 100 + \
                king_safety_improvement * 20 + promotion_value * 20 + \
                develops_piece * 10

        return score

    def is_castling_move(move):
        """Checks if the move is castling (e.g., e1g1)."""
        return move[0] == 'e' and move[2] in ['g', 'c'] and move[1] == move[3]

    # --- Main Policy Logic ---
    color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if color == 'w' else 'w'

    # Check if opponent's king is in check (if so, prioritize moves that escape or capture)
    opponent_king_in_check = is_king_in_check(pieces, opponent_color)

    # Filter legal moves based on strategy
    best_move = None
    best_score = -float('inf')

    for move in legal_moves:
        # Prioritize checkmate moves (if any)
        if not opponent_king_in_check:
            from_sq, to_sq = move[:2], move[2:4]
            if to_sq in pieces and pieces[to_sq][0] == opponent_color and pieces[to_sq][1] == 'K':
                # Check if this move captures the opponent's king (simplified)
                # In real chess, this would require deeper analysis, but for this arena, we assume it's a checkmate
                return move  # Return immediately if checkmate is found

        # Evaluate all legal moves
        score = evaluate_move(move, pieces, to_play)

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    # --- Fallback Rules (if no strong move is found) ---
    # 1. If opponent's king is in check, pick a random legal move (simplified)
    if opponent_king_in_check:
        return random.choice(legal_moves)

    # 2. If no strong move, prefer pawn pushes or knight/bishop development
    pawn_moves = [move for move in legal_moves if pieces[move[:2]][1] == 'P']
    knight_bishop_moves = [move for move in legal_moves if pieces[move[:2]][1] in ['N', 'B']]

    if pawn_moves and best_move not in pawn_moves:
        # Prefer central pawn pushes (e.g., e4, d4)
        central_pawn_moves = [move for move in pawn_moves if move[2] in ['d', 'e'] and move[3] in ['3', '4', '5']]
        if central_pawn_moves:
            return random.choice(central_pawn_moves)
        else:
            return random.choice(pawn_moves)
    elif knight_bishop_moves and best_move not in knight_bishop_moves:
        return random.choice(knight_bishop_moves)

    # Default: Return the highest-scoring move
    return best_move
