
#!/usr/bin/env python3
# Chess move selection policy
# Implements policy(pieces: dict[str,str], to_play: str) -> str
# Tries to use python-chess for legal move generation and evaluation.
# Falls back to a simple move generator if python-chess is not present.

from typing import Dict
import math
import random

# Deterministic randomness
_random = random.Random(1234567)

# Piece values for evaluation (centipawns)
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000
}

FILES = 'abcdefgh'
RANKS = '12345678'

def policy(pieces: Dict[str, str], to_play: str) -> str:
    """
    Return a single UCI move string representing the chosen move.
    pieces: mapping square->piece code like 'wK', 'bQ', etc.
    to_play: 'white' or 'black'
    """
    # Try to use python-chess for correct legal move generation and evaluation
    try:
        import chess
    except Exception:
        chess = None

    if chess is not None:
        try:
            # Create empty board and place pieces
            try:
                board = chess.Board.empty()
            except Exception:
                board = chess.Board()
                board.clear()

            for sq, code in pieces.items():
                if len(code) != 2:
                    continue
                color_char, ptype = code[0], code[1]
                color = chess.WHITE if color_char == 'w' else chess.BLACK
                pmap = {'K': chess.KING, 'Q': chess.QUEEN, 'R': chess.ROOK, 'B': chess.BISHOP, 'N': chess.KNIGHT, 'P': chess.PAWN}
                if ptype not in pmap:
                    continue
                piece = chess.Piece(pmap[ptype], color)
                try:
                    sqi = chess.parse_square(sq)
                except Exception:
                    continue
                board.set_piece_at(sqi, piece)

            board.turn = (to_play == 'white')

            legal_moves = list(board.legal_moves)
            if not legal_moves:
                # No legal moves: fallback simple move or return a dummy move if none
                return _fallback_move(pieces, to_play)

            # Evaluation function returns score from White perspective
            def eval_board(bd: chess.Board) -> int:
                score = 0
                for sqi, pc in bd.piece_map().items():
                    # pc.symbol() returns 'P', 'p' etc
                    sym = pc.symbol()
                    color = chess.WHITE if sym.isupper() else chess.BLACK
                    pcode = sym.upper()
                    val = PIECE_VALUES.get(pcode, 0)
                    if color == chess.WHITE:
                        score += val
                    else:
                        score -= val
                return score

            # Choose best move by 1-ply lookahead
            best_move = None
            best_score = -10**9
            perspective = 1 if to_play == 'white' else -1

            for mv in legal_moves:
                board.push(mv)
                mat = eval_board(board)
                # mobility: number of legal replies (smaller is often worse for opponent)
                try:
                    mobility = board.legal_moves.count()
                except Exception:
                    # Some versions may not support count(); convert to list (costly but fine)
                    mobility = len(list(board.legal_moves))
                # Compute bonuses
                score = perspective * mat
                # Encourage checks
                if board.is_check():
                    score += 50
                # Encourage promotions explicitly (if move is a promotion)
                if mv.promotion is not None:
                    # promotion value relative
                    score += PIECE_VALUES.get('Q', 900)
                # Mobility heuristic: prefer giving the opponent fewer moves (i.e., smaller mobility)
                # We'll subtract small fraction of opponent mobility
                score -= 2 * mobility
                # Slight tie-breaker prefer captures (captured material already in mat diff, but add small incentive)
                if board.is_capture(mv):
                    score += 10
                board.pop()

                # Deterministic tie breaking: prefer lexicographically smaller uci
                u = mv.uci()
                if score > best_score or (score == best_score and (best_move is None or u < best_move.uci())):
                    best_score = score
                    best_move = mv

            if best_move is None:
                return _fallback_move(pieces, to_play)
            return best_move.uci()
        except Exception:
            # If anything goes wrong with python-chess usage, fall back
            return _fallback_move(pieces, to_play)
    else:
        # No chess library available: fallback to a simple generator that produces a plausible legal-format move.
        return _fallback_move(pieces, to_play)

def _fallback_move(pieces: Dict[str, str], to_play: str) -> str:
    """
    Fallback: generate a plausible move in UCI form from the given pieces.
    This naive generator tries to produce a move that fits piece movement rules and captures,
    but does not guarantee full legality (checks, en-passant, castling).
    """
    # Build board occupancy
    board = {}
    for sq, code in pieces.items():
        board[sq] = code

    color = 'w' if to_play == 'white' else 'b'
    enemy = 'b' if color == 'w' else 'w'

    # Helper to test square inside board
    def in_bounds(f, r):
        return 0 <= f < 8 and 0 <= r < 8

    def idx_to_sq(f, r):
        return FILES[f] + RANKS[r]

    # List all our pieces
    our_pieces = [(sq, code[1]) for sq, code in board.items() if code[0] == color]
    # Prioritize captures
    capture_moves = []
    quiet_moves = []

    for sq, ptype in our_pieces:
        f = FILES.index(sq[0])
        r = RANKS.index(sq[1])
        if ptype == 'P':
            # pawns: forward direction
            dr = 1 if color == 'w' else -1
            # single step
            nf, nr = f, r + dr
            if in_bounds(nf, nr):
                dest = idx_to_sq(nf, nr)
                if dest not in board:
                    # move forward
                    quiet_moves.append(sq + dest)
            # captures
            for df in (-1, 1):
                nf, nr = f + df, r + dr
                if in_bounds(nf, nr):
                    dest = idx_to_sq(nf, nr)
                    if dest in board and board[dest][0] == enemy:
                        capture_moves.append(sq + dest)
            # double step from starting rank
            start_rank = 1 if color == 'w' else 6
            if r == start_rank:
                nf, nr = f, r + 2*dr
                mid = idx_to_sq(f, r + dr)
                dest = idx_to_sq(nf, nr)
                if in_bounds(nf, nr) and dest not in board and mid not in board:
                    quiet_moves.append(sq + dest)
        elif ptype == 'N':
            for df, dr in ((1,2),(2,1),(2,-1),(1,-2),(-1,-2),(-2,-1),(-2,1),(-1,2)):
                nf, nr = f+df, r+dr
                if not in_bounds(nf,nr): continue
                dest = idx_to_sq(nf,nr)
                if dest in board:
                    if board[dest][0] == enemy:
                        capture_moves.append(sq + dest)
                else:
                    quiet_moves.append(sq + dest)
        elif ptype == 'B' or ptype == 'R' or ptype == 'Q':
            directions = []
            if ptype in ('B','Q'):
                directions += [(1,1),(1,-1),(-1,1),(-1,-1)]
            if ptype in ('R','Q'):
                directions += [(1,0),(-1,0),(0,1),(0,-1)]
            for df, dr in directions:
                nf, nr = f+df, r+dr
                while in_bounds(nf,nr):
                    dest = idx_to_sq(nf,nr)
                    if dest in board:
                        if board[dest][0] == enemy:
                            capture_moves.append(sq + dest)
                        break
                    else:
                        quiet_moves.append(sq + dest)
                    nf += df
                    nr += dr
        elif ptype == 'K':
            for df in (-1,0,1):
                for dr in (-1,0,1):
                    if df == 0 and dr == 0: continue
                    nf, nr = f+df, r+dr
                    if not in_bounds(nf,nr): continue
                    dest = idx_to_sq(nf,nr)
                    if dest in board:
                        if board[dest][0] == enemy:
                            capture_moves.append(sq + dest)
                    else:
                        quiet_moves.append(sq + dest)
        else:
            # unknown piece type (shouldn't happen) -> skip
            continue

    # Prefer captures
    candidates = capture_moves + quiet_moves
    if not candidates:
        # No moves found: try random legal-format move a1a1 (illegal but formatted). As last resort we must return something.
        # But better try to move any piece to any square
        all_sqs = [a+b for a in FILES for b in RANKS]
        if our_pieces:
            sq = our_pieces[0][0]
            for dest in all_sqs:
                if dest != sq:
                    return sq + dest
        return 'a1a1'

    # Simple heuristic: prefer captures of higher-value pieces (estimate by enemy piece)
    def score_move(mv):
        src = mv[:2]; dst = mv[2:4]
        sc = 0
        if dst in board and board[dst][0] == enemy:
            # reward capturing
            sc += PIECE_VALUES.get(board[dst][1], 0)
        # prefer center moves slightly
        file_idx = FILES.index(dst[0])
        rank_idx = RANKS.index(dst[1])
        center_dist = abs(file_idx - 3.5) + abs(rank_idx - 3.5)
        sc -= center_dist * 2
        # deterministic tie-breaker
        sc += (_random.random() * 1e-6)
        return sc

    best = max(candidates, key=score_move)
    return best

# If this module is executed as a script, demonstrate a trivial run (not required)
if __name__ == "__main__":
    # Example: simple position
    pieces = {'e1': 'wK', 'e8': 'bK', 'a2': 'wP', 'a7': 'bP', 'b1': 'wN'}
    print(policy(pieces, 'white'))
