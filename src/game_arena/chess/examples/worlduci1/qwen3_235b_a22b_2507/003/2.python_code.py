
import random
from typing import Dict, List, Tuple

def policy(pieces: Dict[str, str], to_play: str) -> str:
    # Define piece values (positive for material counting)
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
    
    # Piece-square tables: better positions get higher bonuses
    # Indexed by piece type and color (we'll mirror for black)
    # Here we provide simplified tables favoring center control and development
    PAWN_TABLE = [
         0,   0,   0,   0,   0,   0,   0,   0,
       50,  50,  50,  50,  50,  50,  50,  50,
       10,  10,  20,  30,  30,  20,  10,  10,
        5,   5,  10,  25,  25,  10,   5,   5,
        0,   0,   0,  20,  20,   0,   0,   0,
        5,  -5, -10,   0,   0, -10,  -5,   5,
        5,  10,  10, -20, -20,  10,  10,   5,
         0,   0,   0,   0,   0,   0,   0,   0
    ]
    
    KNIGHT_TABLE = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,   0,   0,   0,   0, -20, -40,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -30,   5,  15,  20,  20,  15,   5, -30,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -30,   5,  10,  15,  15,  10,   5, -30,
        -40, -20,   0,   5,   5,   0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ]
    
    BISHOP_TABLE = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,  10,  10,   5,   0, -10,
        -10,   5,   5,  10,  10,   5,   5, -10,
        -10,   0,  10,  10,  10,  10,   0, -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,   5,   0,   0,   0,   0,   5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ]
    
    ROOK_TABLE = [
          0,   0,   0,   0,   0,   0,   0,   0,
          5,  10,  10,  10,  10,  10,  10,   5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
         -5,   0,   0,   0,   0,   0,   0,  -5,
          0,   0,   0,   5,   5,   0,   0,   0
    ]
    
    QUEEN_TABLE = [
        -20, -10, -10,  -5,  -5, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,   5,   5,   5,   0, -10,
         -5,   0,   5,   5,   5,   5,   0,  -5,
          0,   0,   5,   5,   5,   5,   0,  -5,
        -10,   5,   5,   5,   5,   5,   0, -10,
        -10,   0,   5,   0,   0,   0,   0, -10,
        -20, -10, -10,  -5,  -5, -10, -10, -20
    ]
    
    KING_TABLE_MIDDLEGAME = [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
         20,  20,   0,   0,   0,   0,  20,  20,
         20,  30,  10,   0,   0,  10,  30,  20
    ]
    
    KING_TABLE_ENDGAME = [
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10,   0,   0, -10, -20, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -30,   0,   0,   0,   0, -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50
    ]

    # Helper: convert square string to index 0-63
    def square_to_index(sq: str) -> int:
        file = ord(sq[0]) - ord('a')
        rank = int(sq[1]) - 1
        return rank * 8 + file

    # Helper: get piece color and type
    def get_piece_color_type(piece: str) -> Tuple[str, str]:
        return piece[0], piece[1]

    # Evaluate current board position from perspective of current player
    def evaluate(pieces: Dict[str, str], to_play: str) -> float:
        score = 0.0
        w_king_sq = None
        b_king_sq = None
        total_material = 0

        # First pass: count material and find kings
        for sq, piece in pieces.items():
            color, ptype = get_piece_color_type(piece)
            val = PIECE_VALUES[ptype]
            total_material += val
            if ptype == 'K':
                if color == 'w':
                    w_king_sq = sq
                else:
                    b_king_sq = sq

        # Determine game phase (based on queens and material)
        w_queens = sum(1 for p in pieces.values() if p == 'wQ')
        b_queens = sum(1 for p in pieces.values() if p == 'bQ')
        endgame = (w_queens == 0 and b_queens == 0) or total_material < 2500

        # Second pass: evaluate material and positional bonus
        for sq, piece in pieces.items():
            color, ptype = get_piece_color_type(piece)
            val = PIECE_VALUES[ptype]
            idx = square_to_index(sq)
            
            # Apply piece-square bonuses
            if ptype == 'P':
                bonus = PAWN_TABLE[idx]
            elif ptype == 'N':
                bonus = KNIGHT_TABLE[idx]
            elif ptype == 'B':
                bonus = BISHOP_TABLE[idx]
            elif ptype == 'R':
                bonus = ROOK_TABLE[idx]
            elif ptype == 'Q':
                bonus = QUEEN_TABLE[idx]
            elif ptype == 'K':
                bonus = KING_TABLE_ENDGAME[idx] if endgame else KING_TABLE_MIDDLEGAME[idx]
            else:
                bonus = 0

            # Reverse bonus for black
            if color == 'b':
                bonus = -bonus

            # Add or subtract based on color
            if (color == 'w') == (to_play == 'white'):
                score += val + bonus
            else:
                score -= val + bonus

        # Encourage king safety: penalize if own king is exposed
        king_sq = w_king_sq if to_play == 'white' else b_king_sq
        if king_sq:
            kidx = square_to_index(king_sq)
            # Simple: if king is in center in opening, penalize (unless in endgame)
            rank, file = int(king_sq[1]), king_sq[0]
            if not endgame and 3 <= rank <= 6 and 'c' <= file <= 'f':
                score -= 30 if to_play == 'white' else 30  # symmetric: actually depends on perspective

        return score

    # Simulate move: apply move to pieces and return new pieces dict
    def make_move(pieces: Dict[str, str], move: str) -> Dict[str, str]:
        # Create a deep copy of pieces
        new_pieces = {k: v for k, v in pieces.items()}
        from_sq = move[:2]
        to_sq = move[2:4]
        # Promotion handling
        promotion = None
        if len(move) > 4:
            promotion = move[4]

        # Remove captured piece
        if to_sq in new_pieces:
            del new_pieces[to_sq]

        # Move piece
        if from_sq in new_pieces:
            piece = new_pieces[from_sq]
            del new_pieces[from_sq]
            # Handle promotion
            if promotion and piece[1] == 'P':
                piece = piece[0] + promotion.upper()
            new_pieces[to_sq] = piece
        return new_pieces

    # Check if a king is under attack (naive version: check all opponent moves)
    def is_check(pieces: Dict[str, str], to_play: str) -> bool:
        opp_color = 'w' if to_play == 'black' else 'b'
        my_king_sq = None
        for sq, piece in pieces.items():
            if piece[1] == 'K' and piece[0] == ('w' if to_play == 'white' else 'b'):
                my_king_sq = sq
                break
        if not my_king_sq:
            return False  # Should not happen

        # Generate all opponent pseudo-legal moves (simplified attack check)
        for sq, piece in pieces.items():
            if piece[0] == opp_color:
                moves = generate_pseudo_legal_moves(pieces, sq)
                if my_king_sq in [m[2:4] for m in moves]:
                    return True
        return False

    # Generate pseudo-legal moves for a piece (simplified)
    def generate_pseudo_legal_moves(pieces: Dict[str, str], sq: str) -> List[str]:
        piece = pieces.get(sq)
        if not piece:
            return []
        color, ptype = get_piece_color_type(piece)
        moves = []
        file, rank = ord(sq[0]) - ord('a'), int(sq[1]) - 1

        def valid_pos(f, r):
            return 0 <= f < 8 and 0 <= r < 8

        def pos_to_sq(f, r):
            return chr(ord('a') + f) + str(r + 1)

        if ptype == 'P':
            # Assume all are non-ambiguous pawns
            dir = 1 if color == 'w' else -1
            # Forward
            if valid_pos(file, rank + dir) and pos_to_sq(file, rank + dir) not in pieces:
                moves.append(sq + pos_to_sq(file, rank + dir))
                # Double move from start
                if (rank == 1 and color == 'w') or (rank == 6 and color == 'b'):
                    if valid_pos(file, rank + 2 * dir) and pos_to_sq(file, rank + 2 * dir) not in pieces:
                        moves.append(sq + pos_to_sq(file, rank + 2 * dir))
            # Capture
            for df in [-1, 1]:
                nf, nr = file + df, rank + dir
                if valid_pos(nf, nr):
                    n_sq = pos_to_sq(nf, nr)
                    if n_sq in pieces and pieces[n_sq][0] != color:
                        # Promotion?
                        if (color == 'w' and nr == 7) or (color == 'b' and nr == 0):
                            for promo in 'qrbn':
                                moves.append(sq + n_sq + promo)
                        else:
                            moves.append(sq + n_sq)

        elif ptype == 'N':
            knight_moves = [(-1,-2), (-2,-1), (-2,1), (-1,2), (1,2), (2,1), (2,-1), (1,-2)]
            for df, dr in knight_moves:
                nf, nr = file + df, rank + dr
                if valid_pos(nf, nr):
                    n_sq = pos_to_sq(nf, nr)
                    if n_sq not in pieces or pieces[n_sq][0] != color:
                        moves.append(sq + n_sq)

        elif ptype == 'B':
            for df, dr in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                nf, nr = file + df, rank + dr
                while valid_pos(nf, nr):
                    n_sq = pos_to_sq(nf, nr)
                    if n_sq not in pieces:
                        moves.append(sq + n_sq)
                    else:
                        if pieces[n_sq][0] != color:
                            moves.append(sq + n_sq)
                        break
                    nf, nr = nf + df, nr + dr

        elif ptype == 'R':
            for df, dr in [(-1,0), (1,0), (0,-1), (0,1)]:
                nf, nr = file + df, rank + dr
                while valid_pos(nf, nr):
                    n_sq = pos_to_sq(nf, nr)
                    if n_sq not in pieces:
                        moves.append(sq + n_sq)
                    else:
                        if pieces[n_sq][0] != color:
                            moves.append(sq + n_sq)
                        break
                    nf, nr = nf + df, nr + dr

        elif ptype == 'Q':
            # Combine rook and bishop
            for df, dr in [(-1,-1), (-1,1), (1,-1), (1,1), (-1,0), (1,0), (0,-1), (0,1)]:
                nf, nr = file + df, rank + dr
                while valid_pos(nf, nr):
                    n_sq = pos_to_sq(nf, nr)
                    if n_sq not in pieces:
                        moves.append(sq + n_sq)
                    else:
                        if pieces[n_sq][0] != color:
                            moves.append(sq + n_sq)
                        break
                    nf, nr = nf + df, nr + dr

        elif ptype == 'K':
            for df in [-1, 0, 1]:
                for dr in [-1, 0, 1]:
                    if df == 0 and dr == 0:
                        continue
                    nf, nr = file + df, rank + dr
                    if valid_pos(nf, nr):
                        n_sq = pos_to_sq(nf, nr)
                        if n_sq not in pieces or pieces[n_sq][0] != color:
                            moves.append(sq + n_sq)

        return moves

    # Get all legal moves for current player (from global state)
    def get_legal_moves(pieces: Dict[str, str], to_play: str) -> List[str]:
        color = 'w' if to_play == 'white' else 'b'
        legal_moves = []
        for sq, piece in pieces.items():
            if piece[0] == color:
                moves = generate_pseudo_legal_moves(pieces, sq)
                # Only keep moves that don't leave king in check (very basic)
                for move in moves:
                    sim_pieces = make_move(pieces, move)
                    if not is_check(sim_pieces, to_play):
                        # Promotion handling: always prefer queen unless specified
                        if len(move) == 5 and move[4] in 'qrbn':
                            # Convert lowercase to uppercase
                            legal_moves.append(move[:4] + move[4].lower())
                        else:
                            legal_moves.append(move)
        return legal_moves

    # First, evaluate immediate captures and checkmates
    def is_capture(move: str) -> bool:
        to_sq = move[2:4]
        return to_sq in pieces

    def is_promotion(move: str) -> bool:
        return len(move) > 4

    def is_checkmate_attempt(move: str, pieces: Dict[str, str], to_play: str) -> bool:
        # Extremely simplified: simulate and see if opponent has no legal moves
        new_pieces = make_move(pieces, move)
        opp_color = 'black' if to_play == 'white' else 'white'
        opp_moves = get_legal_moves(new_pieces, opp_color)
        return len(opp_moves) == 0 and is_check(new_pieces, opp_color)

    # Get moves from input (we assume legal_moves is globally provided)
    # But we must rely on environment passing legal_moves — we are not given it!
    # Wait: legal_moves is not in function signature! We must deduce from state?
    # However, the problem says: "Return exactly ONE move string that is an element of legal_moves"
    # But legal_moves is not passed to policy(). This means in the arena, it is implied that policy has access?
    # But it's not. There's a bug.
    #
    # Correction: The problem implies legal_moves is available, but not passed. This is ambiguous.
    # However, the example includes: "Example format of legal_moves you might receive"
    # But function signature has only `pieces` and `to_play`.
    #
    # This suggests the system will somehow inject legal_moves into the scope or pass it.
    # But it's not in the signature.
    #
    # Re-reading: "You will be disqualified if you do not return a legal move string."
    # But we have no access to legal_moves? That can't be.
    #
    # Important: The user prompt says "move selection from provided legal moves" but the API only takes `pieces` and `to_play`.
    #
    # This seems to be a flaw in the problem statement.
    #
    # However, the example output shows: `Example format of legal_moves you might receive:` after the API.
    #
    # Therefore, I suspect the actual API call includes legal_moves, but it's omitted in the signature.
    # But the user explicitly says: "implement the following API: def policy(pieces: dict[str, str], to_play: str) -> str"
    #
    # This is contradictory.
    #
    # Given the constraints, I must assume that `legal_moves` is available in the global scope or passed.
    # But it's not. So I must regenerate legal_moves from the current board state.
    #
    # Therefore, we define:
    legal_moves = get_legal_moves(pieces, to_play)

    if not legal_moves:
        # Fallback: return a random move (should not happen)
        return 'e1e1'

    # First priority: check for checkmate
    for move in legal_moves:
        if is_checkmate_attempt(move, pieces, to_play):
            return move

    # Second priority: check for captures and promotions
    candidate_moves = []
    for move in legal_moves:
        new_pieces = make_move(pieces, move)
        current_score = evaluate(pieces, to_play)
        new_score = evaluate(new_pieces, 'black' if to_play == 'white' else 'white')
        # Material gain
        delta = new_score - current_score
        # Boost for captures and promotions
        if is_capture(move):
            captured = pieces.get(move[2:4])
            if captured:
                delta += PIECE_VALUES[captured[1]]
        if is_promotion(move):
            delta += PIECE_VALUES['Q'] - PIECE_VALUES['P']  # Net gain

        # Bonus for pawn advances in center?
        piece = pieces.get(move[:2])
        if piece and piece[1] == 'P':
            to_rank = int(move[3])
            if (to_play == 'white' and to_rank > int(move[1])) or (to_play == 'black' and to_rank < int(move[1])):
                # Pawn advanced
                delta += 10

        candidate_moves.append((delta, random.random(), move))  # random tiebreak

    # Sort by delta (descending)
    candidate_moves.sort(reverse=True)

    # Select best move based on greedy evaluation
    best_move = candidate_moves[0][2]

    # Optional: look one move ahead (minimax with depth 1)
    if len(candidate_moves) > 1:
        best_score = float('-inf')
        final_move = best_move
        for _, _, move in candidate_moves[:10]:  # consider top 10
            # Simulate move
            new_pieces = make_move(pieces, move)
            # If opponent has no move, we win
            opp_moves = get_legal_moves(new_pieces, 'black' if to_play == 'white' else 'white')
            if not opp_moves:
                return move
            # Find best opponent response
            opp_best_score = float('-inf')
            for opp_move in opp_moves[:10]:  # top 10 responses
                opp_new_pieces = make_move(new_pieces, opp_move)
                # Evaluate from our perspective (after two moves)
                score = evaluate(opp_new_pieces, to_play)
                if score < opp_best_score:
                    opp_best_score = score
            # But we want moves that maximize our min score
            # However, our evaluation is from our side, so higher is better
            # So we want max(min(score after opponent best move))
            if opp_best_score > best_score:
                best_score = opp_best_score
                final_move = move
        return final_move

    return best_move
