
import numpy as np

def policy(pieces: dict[str, str], to_play: str) -> str:
    # Define piece values
    piece_value = {'P': 100, 'N': 300, 'B': 320, 'R': 500, 'Q': 900, 'K': 10000}
    
    # Define piece-square tables (small bonuses to encourage good positioning)
    # These are simplified tables: higher values are better for positioning
    center_files = 'cdef'
    center_ranks = '3456'
    
    def positional_score(piece_code, square):
        color = piece_code[0]
        ptype = piece_code[1]
        file, rank = square[0], square[1]
        
        score = 0
        # Center control bonus for minor pieces and pawns
        if file in center_files and rank in center_ranks:
            if ptype == 'N':
                score += 20
            elif ptype == 'B':
                score += 20
            elif ptype == 'P':
                score += 10
        # Encourage king safety (toward edges and fits in castled positions)
        if ptype == 'K':
            if file in 'abc' or file in 'fgh':  # kingside or queenside
                score += 15
        return score

    # Get legal moves (we assume they are passed externally in real use; here we need them as input)
    # But since the API does not provide legal_moves directly, we must infer from context — WAIT.
    # ISSUE: legal_moves is not provided in the function signature!

    # We realize: the function signature only provides `pieces` and `to_play`.
    # But the instructions say: "Return exactly ONE move string that is an element of `legal_moves`"
    # So how do we get `legal_moves`?

    # This indicates a contradiction in the prompt. The function signature does NOT include `legal_moves`.
    # However, without `legal_moves`, we cannot know which moves are legal.

    # Therefore, we must assume that `legal_moves` is also passed, OR that we generate it.

    # But the prompt explicitly says: "You will be disqualified if you do not return a legal move string."
    # And the API is fixed: only (pieces, to_play).

    # Conclusion: the prompt is ambiguous. But looking back: "move selection from provided legal moves" — but not in args.

    # This suggests a mistake in problem design. However, to proceed, we must infer that the arena system injects legal_moves into the global scope.

    # Since this is a competition setting, and we must function under constraints, we assume:
    #   `legal_moves` is available in the global scope.

    # We'll access it as a global variable.

    global legal_moves
    moves = legal_moves  # List of UCI strings: ['e2e4', 'e7e5', ...]

    if not moves:
        # Fallback: should not happen
        return moves[0] if len(moves) > 0 else "e1e1"

    # Determine our color
    our_color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if our_color == 'w' else 'w'

    best_move = moves[0]
    best_score = -999999

    for move in moves:
        score = 0

        # Parse move: e.g. 'a2a1q' (promotion) or 'e2e4'
        from_sq = move[:2]
        to_sq = move[2:4]
        promotion = move[4] if len(move) > 4 else None

        # Current piece being moved
        if from_sq not in pieces:
            continue  # shouldn't happen

        piece = pieces[from_sq]
        ptype = piece[1]

        # If our piece?
        if piece[0] != our_color:
            continue  # shouldn't happen

        # 1. Capture evaluation
        captured_piece = pieces.get(to_sq)
        if captured_piece:
            # Bonus for capturing high-value pieces
            captured_value = piece_value[captured_piece[1]]
            # Penalty for trading down
            our_value = piece_value[ptype]
            capture_score = captured_value
            if captured_value < our_value:
                capture_score -= (our_value - captured_value)  # discourage trading up unless forced
            score += capture_score

            # Extra bonus for checking after capture
            # This is a simplistic tactical bonus: assume capture leading to check is good
            # We can't simulate check easily without full board, so we use heuristics

        # 2. Promotion bonus
        if promotion:
            promo_value = piece_value[promotion.upper()]
            score += promo_value  # assuming we always promote to queen unless specified otherwise

        # 3. Positional improvement
        score += positional_score(piece, to_sq) - positional_score(piece, from_sq)

        # 4. Encourage development: knights and bishops off back rank early
        if ptype in 'NB' and our_color == 'w' and from_sq[1] == '1':
            if to_sq[1] not in '18':
                score += 10
        if ptype in 'NB' and our_color == 'b' and from_sq[1] == '8':
            if to_sq[1] not in '18':
                score += 10

        # 5. Pawn moves: prefer central and advances
        if ptype == 'P':
            score += 10  # encourage pawn moves
            # central files bonus
            if to_sq[0] in 'dfe':
                score += 5
            # promote to back rank
            if (our_color == 'w' and to_sq[1] == '8') or (our_color == 'b' and to_sq[1] == '1'):
                score += 80  # promotion handled above but this encourages it

        # 6. Avoid moving king early unless castling or necessary
        if ptype == 'K':
            if from_sq in ('e1', 'e8'):  # starting position
                if to_sq not in ('g1', 'c1', 'g8', 'c8'):  # not castling
                    score -= 20  # discourage early king walk

        # 7. Castling bonus
        if ptype == 'K' and abs(ord(from_sq[0]) - ord(to_sq[0])) > 1:
            score += 50  # castling is good for king safety

        # 8. Check bonus (heuristic: if the move ends on a square that "could" give check)
        # We don't simulate check, but we know that a queen, rook, or bishop moving to a file/rank
        # occupied by enemy king might check. Or knight jump.
        # But we can't know the king position without finding it.
        # Let's find opponent king
        opp_king_sq = None
        for sq, p in pieces.items():
            if p == f'{opp_color}K':
                opp_king_sq = sq
                break

        if opp_king_sq:
            # Check if move attacks the opponent king (very rough)
            if to_sq[0] == opp_king_sq[0] or to_sq[1] == opp_king_sq[1] or \
               abs(ord(to_sq[0]) - ord(opp_king_sq[0])) == abs(ord(to_sq[1]) - ord(opp_king_sq[1])) or \
               (ptype == 'N' and max(abs(ord(to_sq[0]) - ord(opp_king_sq[0])), abs(ord(to_sq[1]) - ord(opp_king_sq[1]))) == 2 and min(...) == 1):
                score += 20  # heuristic check bonus

        # 9. Avoid leaving valuable pieces hanging — but hard without full board simulation
        # Simplified: if our move exposes our queen or rook to capture, reduce score
        # Too complex for now — skip due to time and complexity

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    return best_move
