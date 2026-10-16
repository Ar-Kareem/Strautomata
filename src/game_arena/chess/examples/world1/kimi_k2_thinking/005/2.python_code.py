
# -------------------------------------------------------------
#  Minimal chess engine – quiescence search + piece‑square tables
# -------------------------------------------------------------
try:
    import chess
    import numpy as np
except ImportError:                     # fallback if chess is unavailable
    chess = None
    np = None

if chess is not None:
    # ---------------------------------------------------------
    #  Evaluation parameters (piece values & piece‑square tables)
    # ---------------------------------------------------------
    PIECE_VALUES = {
        chess.PAWN:   100,
        chess.KNIGHT: 300,
        chess.BISHOP: 300,
        chess.ROOK:   500,
        chess.QUEEN:  900,
        chess.KING:     0,
    }

    # Piece‑square tables (Sunfish‑style, centipawn‑scale)
    # Index 0 = a1, 63 = h8 (same as python‑chess)
    PST_PAWN = [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0,
    ]

    PST_KNIGHT = [
        -50, -40, -40, -40, -40, -40, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -40, 0, 10, 15, 15, 10, 0, -40,
        -40, 5, 15, 20, 20, 15, 5, -40,
        -40, 0, 15, 20, 20, 15, 0, -40,
        -40, 5, 10, 15, 15, 10, 5, -40,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -40, -40, -40, -40, -40, -50,
    ]

    PST_BISHOP = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 10, 5, 5, 5, 5, 10, -10,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20,
    ]

    PST_ROOK = [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, 10, 10, 10, 10, 5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        0, 0, 0, 5, 5, 0, 0, 0,
    ]

    PST_QUEEN = [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20,
    ]

    PST_KING = [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20,
    ]

    # Map piece type to its table
    PSQT = {
        chess.PAWN:   PST_PAWN,
        chess.KNIGHT: PST_KNIGHT,
        chess.BISHOP: PST_BISHOP,
        chess.ROOK:   PST_ROOK,
        chess.QUEEN:  PST_QUEEN,
        chess.KING:   PST_KING,
    }

    def evaluate(board, perspective):
        """
        Return a centipawn score from the point of view of *perspective*
        (chess.WHITE or chess.BLACK).  Higher numbers are better for
        the perspective side.
        """
        score = 0
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if piece is None:
                continue
            # material value
            value = PIECE_VALUES[piece.piece_type]
            # piece‑square bonus (mirrored for black)
            if piece.color == chess.WHITE:
                psq = PSQT[piece.piece_type][sq]
            else:
                psq = PSQT[piece.piece_type][chess.square_mirror(sq)]
            total = value + psq
            if piece.color == perspective:
                score += total
            else:
                score -= total
        return score

# -------------------------------------------------------------
#  Policy entry point
# -------------------------------------------------------------
def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str]) -> str:
    """
    Return a single legal move for the side to play.
    """
    # -------------------------------------------------------------
    #  No chess library – fall back to a very simple heuristic
    # -------------------------------------------------------------
    if chess is None:
        # Prefer any capture, otherwise the first move.
        for m in legal_moves:
            if 'x' in m:
                return m  # arbitrary capture
        # No capture – return the first legal move.
        return legal_moves[0]

    # -------------------------------------------------------------
    #  Build a python‑chess board from the provided description
    # -------------------------------------------------------------
    board = chess.Board(empty=True)                 # start with an empty board
    for sq, pc in pieces.items():
        # pc is a two‑character string like "wP" or "bN"
        color = chess.WHITE if pc[0] == 'w' else chess.BLACK
        # piece symbol is the second character (lowercase for python‑chess)
        symbol = pc[1].lower()
        # map symbol to piece type
        typ = {
            'p': chess.PAWN,
            'n': chess.KNIGHT,
            'b': chess.BISHOP,
            'r': chess.ROOK,
            'q': chess.QUEEN,
            'k': chess.KING,
        }[symbol]
        piece = chess.Piece(typ, color)
        board.set_piece_at(chess.parse_square(sq), piece)

    board.turn = chess.WHITE if to_play == 'white' else chess.BLACK
    original_side = board.turn                     # side that we are playing

    # -------------------------------------------------------------
    #  Search for the best move (quiescence‑search depth = 2)
    # -------------------------------------------------------------
    best_move = None
    best_score = -float('inf')

    for move_san in legal_moves:
        # ---- parse SAN (handles disambiguation, promotions, checks, mates) ----
        try:
            move = board.parse_san(move_san)
        except Exception:
            # skip malformed moves – should never happen
            continue

        # ---- apply the move -------------------------------------------------
        board_after = board.copy()
        board_after.push(move)

        # ---- if the move mates the opponent, return it immediately ----------
        if board_after.is_checkmate():
            return move_san

        # ---- static evaluation after our move --------------------------------
        score_after = evaluate(board_after, original_side)

        # ---- opponent's best capture reply (worst case for us) -------------
        worst_score = float('inf')
        # board.turn is already flipped to opponent after push()
        for opp_move in board_after.legal_moves:
            if not board_after.is_capture(opp_move):
                continue            # only consider captures (quiescence)
            board_cap = board_after.copy()
            board_cap.push(opp_move)      # after the capture it's our turn again
            sc = evaluate(board_cap, original_side)
            if sc < worst_score:          # opponent tries to minimise our score
                worst_score = sc

        # if opponent had no capture, the evaluation stays as after our move
        if worst_score == float('inf'):
            effective_score = score_after
        else:
            effective_score = worst_score

        # keep the move with the highest guaranteed score
        if effective_score > best_score:
            best_score = effective_score
            best_move = move_san

    # -------------------------------------------------------------
    #  Fallback – should never happen, but keep the first move
    # -------------------------------------------------------------
    if best_move is None:
        best_move = legal_moves[0]

    return best_move
