
#!/usr/bin/env python3
# Chess move selection policy
# Implements: policy(pieces: dict[str, str], to_play: str) -> str
# Tries to use python-chess for accurate legal move generation and evaluation.
# Falls back to using a global `legal_moves` list if python-chess is not available.

from typing import Dict

def policy(pieces: Dict[str, str], to_play: str) -> str:
    """
    Return a single UCI move string for the side to play.
    - pieces: dict mapping squares like 'e4' to piece codes like 'wK', 'bq', etc.
    - to_play: 'white' or 'black'
    """
    # Material values for heuristics
    PIECE_VALUE = {'P': 1.0, 'N': 3.0, 'B': 3.0, 'R': 5.0, 'Q': 9.0, 'K': 0.0}
    color_to_bool = {'white': True, 'black': False}

    # Try to use python-chess for correctness and stronger evaluation
    try:
        import chess
        # Create an empty board and place pieces
        board = chess.Board.empty()
        board.clear()
        # Place pieces from the pieces dict
        piece_map = {
            'P': chess.PAWN, 'N': chess.KNIGHT, 'B': chess.BISHOP,
            'R': chess.ROOK, 'Q': chess.QUEEN, 'K': chess.KING
        }
        for sq, code in pieces.items():
            if not sq or len(code) != 2:
                continue
            col = code[0]
            p = code[1].upper()
            if p not in piece_map:
                continue
            try:
                sqi = chess.parse_square(sq)
            except Exception:
                continue
            piece = chess.Piece(piece_map[p], True if col == 'w' else False)
            board.set_piece_at(sqi, piece)
        # Set turn
        board.turn = color_to_bool.get(to_play, True)
        # Clear castling rights and en passant (we don't know them)
        board.castling_rights = 0
        board.ep_square = None
        board.halfmove_clock = 0
        board.fullmove_number = 1

        legal = list(board.legal_moves)
        if not legal:
            # No legal moves: return a dummy legal string if possible from provided moves in globals
            # As a last resort, attempt to pull a provided global legal_moves
            gm = globals().get('legal_moves')
            if isinstance(gm, (list, tuple)) and gm:
                return gm[0]
            # If absolutely no moves, return a safe fallback (shouldn't usually happen)
            return "a1a1"

        # Helper to compute material score (white - black)
        def material_score(b: chess.Board) -> float:
            score = 0.0
            for sqi, pc in b.piece_map().items():
                val = PIECE_VALUE.get(pc.symbol().upper(), 0.0)
                score += val if pc.color == chess.WHITE else -val
            return score

        best_move = None
        best_score = -10**9
        us_is_white = board.turn == chess.WHITE
        sign = 1 if us_is_white else -1

        # Evaluate each legal move
        for mv in legal:
            # Immediate capture/promotion/check bonuses (from original position view)
            capture_bonus = 0.0
            if board.is_capture(mv):
                # If capturing, add captured piece value if we can find it
                # Use target square in current board
                to_sq = mv.to_square
                captured = board.piece_at(to_sq)
                if captured is not None:
                    capture_bonus += PIECE_VALUE.get(captured.symbol().upper(), 0.0) * 100.0
                else:
                    # en-passant capture case: assume pawn capture value
                    capture_bonus += PIECE_VALUE['P'] * 100.0
            if mv.promotion:
                # Big bonus for promotion (prefer queen)
                promo_val = 9.0 if mv.promotion == chess.QUEEN else PIECE_VALUE.get(chess.Piece(mv.promotion, True).symbol().upper(), 0.0)
                capture_bonus += promo_val * 120.0

            # Make move and evaluate resultant position
            board.push(mv)
            # Immediate mate detection
            if board.is_checkmate():
                board.pop()
                return mv.uci()
            mat = material_score(board)
            # Mobility for the side to move (opponent), we prefer to reduce opponent mobility
            opp_mobility = board.legal_moves.count()
            # Also check if we give check after the move
            check_bonus = 50.0 if board.is_check() else 0.0
            board.pop()

            # Combine scores. material is white-black; convert to perspective of player to move
            score = sign * mat * 100.0 - opp_mobility * 1.5 + capture_bonus + check_bonus
            # Slight tie-breaker: prefer captures/promotion (already boosted), else prefer move ordering by UCI
            if score > best_score:
                best_score = score
                best_move = mv

        if best_move is None:
            # Fallback to first legal move
            return legal[0].uci()
        return best_move.uci()

    except Exception:
        # Fallback path: use a provided global legal_moves list (if available) and choose best by heuristic.
        gm = globals().get('legal_moves')
        if not gm:
            # As a last fallback, try to synthesize a trivial move. This is unlikely in evaluation contexts
            # Build a naive move: find any pawn of our color and try to advance it one square
            mycol = 'w' if to_play == 'white' else 'b'
            # Try single-step pawn moves
            files = 'abcdefgh'
            ranks = '12345678'
            for sq, code in pieces.items():
                if code == mycol + 'P':
                    f = sq[0]; r = sq[1]
                    if mycol == 'w':
                        nr = str(int(r) + 1) if r != '8' else None
                    else:
                        nr = str(int(r) - 1) if r != '1' else None
                    if nr:
                        candidate = f + r + f + nr
                        # if candidate not legal it's still the best we can do without move list
                        return candidate
            # If none found, pick any from-to by moving first piece to same square (invalid but placeholder)
            # Try to find some move that looks syntactically valid
            if pieces:
                from_sq = next(iter(pieces.keys()))
                # try move one rank forward if possible
                f = from_sq[0]; r = from_sq[1]
                try:
                    nr = str(min(8, int(r) + 1))
                    return from_sq + f + nr
                except Exception:
                    pass
            # Last resort
            return "a1a1"
        # gm expected to be a list of UCI move strings
        legal_moves = [m for m in gm if isinstance(m, str) and len(m) >= 4]
        if not legal_moves:
            # nothing to do
            return "a1a1"
        # Heuristic scoring for fallback: promotions and captures prioritized
        def piece_at(sq):
            return pieces.get(sq)

        def score_move(mv: str) -> float:
            # mv like 'e2e4' or 'a7a8q'
            frm = mv[:2]; to = mv[2:4]
            promo = mv[4] if len(mv) >= 5 else None
            s = 0.0
            # capture if destination contains opponent piece
            dst_piece = piece_at(to)
            if dst_piece:
                if dst_piece[0] != ('w' if to_play == 'white' else 'b'):
                    # captured opponent piece
                    val = PIECE_VALUE.get(dst_piece[1].upper(), 0.0)
                    s += val * 100.0
            if promo:
                # promotion desirability
                prom_val = {'q': 9.0, 'r': 5.0, 'b': 3.0, 'n': 3.0}
                s += prom_val.get(promo.lower(), 0.0) * 120.0
            # prefer center squares
            center = set(['d4','d5','e4','e5','c4','c5','f4','f5'])
            if to in center:
                s += 5.0
            # prefer moves that move pieces (non-pawn moves slightly deprioritized)
            from_piece = piece_at(frm)
            if from_piece:
                if from_piece[1].upper() == 'P':
                    s += 0.5
                else:
                    s += 1.0
            return s

        best = max(legal_moves, key=score_move)
        return best
