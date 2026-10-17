
import copy
from typing import Dict, Tuple, List, Optional

# piece values for simple material evaluation
PIECE_VALUE = {
    'P': 1,
    'N': 3,
    'B': 3,
    'R': 5,
    'Q': 9,
    'K': 0,
}

# offsets for sliding pieces
DIRS = {
    'N': [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)],
    'K': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
    'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    'R': [(-1, 0), (1, 0), (0, -1), (0, 1)],
    'Q': [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)],
}

FILE_TO_IDX = {c: i for i, c in enumerate('abcdefgh')}
IDX_TO_FILE = {i: c for c, i in FILE_TO_IDX.items()}


def sq_to_idx(sq: str) -> int:
    """a1 -> 0, h8 -> 63"""
    file = FILE_TO_IDX[sq[0]]
    rank = int(sq[1]) - 1
    return rank * 8 + file


def idx_to_sq(idx: int) -> str:
    rank, file = divmod(idx, 8)
    return IDX_TO_FILE[file] + str(rank + 1)


def in_board(r: int, f: int) -> bool:
    return 0 <= r < 8 and 0 <= f < 8


def generate_moves(board: List[Optional[str]], color: str) -> List[Tuple[int, int, Optional[str]]]:
    """Return list of (src_idx, dst_idx, promotion_piece_type or None)."""
    moves = []
    opponent = 'b' if color == 'w' else 'w'
    pawn_dir = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    promotion_rank = 7 if color == 'w' else 0

    for src, piece in enumerate(board):
        if piece is None or piece[0] != color:
            continue
        p_type = piece[1]
        r, f = divmod(src, 8)

        if p_type == 'P':
            # single forward
            nr = r + pawn_dir
            if in_board(nr, f) and board[nr * 8 + f] is None:
                # promotion?
                if nr == promotion_rank:
                    for promo in ('q', 'r', 'b', 'n'):
                        moves.append((src, nr * 8 + f, promo.upper()))
                else:
                    moves.append((src, nr * 8 + f, None))
                # double forward from start rank
                if r == start_rank:
                    nr2 = nr + pawn_dir
                    if in_board(nr2, f) and board[nr2 * 8 + f] is None:
                        moves.append((src, nr2 * 8 + f, None))
            # captures
            for df in (-1, 1):
                nc = f + df
                if in_board(nr, nc):
                    target = board[nr * 8 + nc]
                    if target is not None and target[0] == opponent:
                        if nr == promotion_rank:
                            for promo in ('q', 'r', 'b', 'n'):
                                moves.append((src, nr * 8 + nc, promo.upper()))
                        else:
                            moves.append((src, nr * 8 + nc, None))
            # En‑passant omitted

        elif p_type == 'N':
            for dr, df in DIRS['N']:
                nr, nf = r + dr, f + df
                if not in_board(nr, nf):
                    continue
                dst = nr * 8 + nf
                target = board[dst]
                if target is None or target[0] == opponent:
                    moves.append((src, dst, None))

        elif p_type in ('B', 'R', 'Q'):
            dirs = DIRS[p_type]
            for dr, df in dirs:
                nr, nf = r + dr, f + df
                while in_board(nr, nf):
                    dst = nr * 8 + nf
                    target = board[dst]
                    if target is None:
                        moves.append((src, dst, None))
                    else:
                        if target[0] == opponent:
                            moves.append((src, dst, None))
                        break
                    nr += dr
                    nf += df

        elif p_type == 'K':
            for dr, df in DIRS['K']:
                nr, nf = r + dr, f + df
                if not in_board(nr, nf):
                    continue
                dst = nr * 8 + nf
                target = board[dst]
                if target is None or target[0] == opponent:
                    moves.append((src, dst, None))
            # Castling omitted (king moves only one square)

    return moves


def is_attacked(board: List[Optional[str]], square: int, attacker_color: str) -> bool:
    """Return True if square is attacked by any piece of attacker_color."""
    opponent = attacker_color
    r, f = divmod(square, 8)

    # pawn attacks
    pawn_dir = 1 if opponent == 'w' else -1
    for df in (-1, 1):
        nr, nf = r - pawn_dir, f + df  # pawn attacks opposite direction of movement
        if in_board(nr, nf):
            idx = nr * 8 + nf
            piece = board[idx]
            if piece is not None and piece[0] == opponent and piece[1] == 'P':
                return True

    # knight attacks
    for dr, df in DIRS['N']:
        nr, nf = r + dr, f + df
        if in_board(nr, nf):
            idx = nr * 8 + nf
            piece = board[idx]
            if piece is not None and piece[0] == opponent and piece[1] == 'N':
                return True

    # sliding pieces
    for d in DIRS['B']:
        nr, nf = r + d[0], f + d[1]
        while in_board(nr, nf):
            idx = nr * 8 + nf
            piece = board[idx]
            if piece is not None:
                if piece[0] == opponent and piece[1] in ('B', 'Q'):
                    return True
                break
            nr += d[0]
            nf += d[1]

    for d in DIRS['R']:
        nr, nf = r + d[0], f + d[1]
        while in_board(nr, nf):
            idx = nr * 8 + nf
            piece = board[idx]
            if piece is not None:
                if piece[0] == opponent and piece[1] in ('R', 'Q'):
                    return True
                break
            nr += d[0]
            nf += d[1]

    # king attacks (adjacent squares)
    for dr, df in DIRS['K']:
        nr, nf = r + dr, f + df
        if in_board(nr, nf):
            idx = nr * 8 + nf
            piece = board[idx]
            if piece is not None and piece[0] == opponent and piece[1] == 'K':
                return True

    return False


def king_position(board: List[Optional[str]], color: str) -> int:
    """Return index of the king of given color."""
    target = color + 'K'
    for i, p in enumerate(board):
        if p == target:
            return i
    raise ValueError("King not found")


def apply_move(board: List[Optional[str]],
               src: int,
               dst: int,
               promo: Optional[str]) -> List[Optional[str]]:
    """Return a new board after making the move (including promotion)."""
    new_board = board.copy()
    piece = new_board[src]
    if piece is None:
        return new_board
    # move piece
    new_piece = piece
    if promo is not None:
        new_piece = piece[0] + promo  # promote
    new_board[dst] = new_piece
    new_board[src] = None
    return new_board


def legal_moves(board: List[Optional[str]], color: str) -> List[Tuple[int, int, Optional[str]]]:
    """All pseudo‑legal moves filtered by king‑safety."""
    cand = generate_moves(board, color)
    legal = []
    for src, dst, promo in cand:
        new_board = apply_move(board, src, dst, promo)
        king_idx = king_position(new_board, color)
        if not is_attacked(new_board, king_idx, 'b' if color == 'w' else 'w'):
            legal.append((src, dst, promo))
    return legal


def move_to_uci(src: int, dst: int, promo: Optional[str]) -> str:
    uci = idx_to_sq(src) + idx_to_sq(dst)
    if promo is not None:
        uci += promo.lower()
    return uci


def policy(pieces: dict, to_play: str, memory: dict) -> Tuple[str, dict]:
    """
    Choose a move based on a simple material‑centric heuristic.
    pieces : dict {square_str: 'wP', ...}
    to_play : 'white' or 'black'
    memory  : unused (kept for API compatibility)
    Returns (uci_move_string, updated_memory)
    """
    # Build board array
    board = [None] * 64
    for sq, code in pieces.items():
        board[sq_to_idx(sq)] = code

    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if color == 'w' else 'w'

    # Generate all legal moves
    legs = legal_moves(board, color)
    if not legs:
        # No legal moves (checkmate or stalemate). Choose a random pseudo‑legal move to stay legal.
        # Fallback: generate pseudo‑legal moves without king‑safety filter.
        pseudo = generate_moves(board, color)
        if pseudo:
            src, dst, promo = pseudo[0]
            return move_to_uci(src, dst, promo), memory
        else:
            # Completely dead position – return a dummy move (should never happen)
            return 'a1a1', memory

    # Separate captures
    captures = []
    for src, dst, promo in legs:
        target = board[dst]
        # promotion captures are already counted, treat promotion as capture of queen value
        if target is not None and target[0] == opp_color:
            captures.append((src, dst, promo, PIECE_VALUE[target[1]]))
        elif promo is not None:
            # promotion without capture, treat as modest gain
            captures.append((src, dst, promo, PIECE_VALUE[promo]))
    if captures:
        # Choose capture with highest captured piece value (or promotion value)
        captures.sort(key=lambda x: x[3], reverse=True)
        src, dst, promo, _ = captures[0]
        return move_to_uci(src, dst, promo), memory

    # No capture – pick the first legal move (could be improved later)
    src, dst, promo = legs[0]
    return move_to_uci(src, dst, promo), memory
