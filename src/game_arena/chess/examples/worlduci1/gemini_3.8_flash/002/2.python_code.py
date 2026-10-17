
import math
import random
from typing import Dict, List, Optional, Tuple

# Piece values
PIECE_VALUES = {
    'P': 100,
    'N': 320,
    'B': 330,
    'R': 500,
    'Q': 900,
    'K': 20000,
}

# Piece-Square Tables (White perspective, rank 1 to rank 8)
PAWN_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
      0,  0,  0,  0,  0,  0,  0,  0,
      5, 10, 10, 10, 10, 10, 10,  5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
     -5,  0,  0,  0,  0,  0,  0, -5,
      0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

PST = {
    'P': PAWN_TABLE,
    'N': KNIGHT_TABLE,
    'B': BISHOP_TABLE,
    'R': ROOK_TABLE,
    'Q': QUEEN_TABLE,
    'K': KING_TABLE,
}


def sq_to_coords(sq: str) -> Tuple[int, int]:
    return ord(sq[0]) - ord('a'), int(sq[1]) - 1


def coords_to_sq(c: int, r: int) -> str:
    return chr(ord('a') + c) + str(r + 1)


def evaluate_board(pieces: Dict[str, str], my_color_char: str) -> int:
    score = 0
    opp_color_char = 'b' if my_color_char == 'w' else 'w'
    has_my_king = False
    has_opp_king = False

    for sq, p in pieces.items():
        color, ptype = p[0], p[1]
        c, r = sq_to_coords(sq)
        if color == 'w':
            table_idx = (7 - r) * 8 + c
        else:
            table_idx = r * 8 + c

        val = PIECE_VALUES.get(ptype, 0)
        table = PST.get(ptype)
        if table:
            val += table[table_idx]

        if color == my_color_char:
            score += val
            if ptype == 'K':
                has_my_king = True
        else:
            score -= val
            if ptype == 'K':
                has_opp_king = True

    if not has_opp_king:
        return 99999
    if not has_my_king:
        return -99999
    return score


def apply_move(pieces: Dict[str, str], move: str) -> Dict[str, str]:
    new_pieces = pieces.copy()
    src = move[:2]
    dst = move[2:4]
    promo = move[4:].upper() if len(move) > 4 else None

    moving_piece = new_pieces.pop(src, None)
    if not moving_piece:
        return new_pieces

    color = moving_piece[0]
    ptype = moving_piece[1]

    # Castling king side or queen side rook movement
    if ptype == 'K':
        if src == 'e1' and dst == 'g1':
            rook = new_pieces.pop('h1', None)
            if rook:
                new_pieces['f1'] = rook
        elif src == 'e1' and dst == 'c1':
            rook = new_pieces.pop('a1', None)
            if rook:
                new_pieces['d1'] = rook
        elif src == 'e8' and dst == 'g8':
            rook = new_pieces.pop('h8', None)
            if rook:
                new_pieces['f8'] = rook
        elif src == 'e8' and dst == 'c8':
            rook = new_pieces.pop('a8', None)
            if rook:
                new_pieces['d8'] = rook

    if promo:
        new_pieces[dst] = color + promo
    else:
        new_pieces[dst] = moving_piece

    return new_pieces


def generate_pseudo_legal_moves(pieces: Dict[str, str], color_char: str) -> List[str]:
    moves = []
    opp_char = 'b' if color_char == 'w' else 'w'
    pawn_dir = 1 if color_char == 'w' else -1
    start_rank = 1 if color_char == 'w' else 6
    promo_rank = 7 if color_char == 'w' else 0

    knight_offsets = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    king_offsets = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]
    straight_dirs = [(1, 0), (-1, 0), (0, 1), (0, -1)]
    diag_dirs = [(1, 1), (1, -1), (-1, 1), (-1, -1)]

    for sq, p in pieces.items():
        if p[0] != color_char:
            continue
        c, r = sq_to_coords(sq)
        ptype = p[1]

        if ptype == 'P':
            # Forward one step
            nr = r + pawn_dir
            if 0 <= nr <= 7:
                fwd_sq = coords_to_sq(c, nr)
                if fwd_sq not in pieces:
                    if nr == promo_rank:
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(f"{sq}{fwd_sq}{promo}")
                    else:
                        moves.append(f"{sq}{fwd_sq}")
                        # Forward two steps
                        if r == start_rank:
                            fwd2_sq = coords_to_sq(c, r + 2 * pawn_dir)
                            if fwd2_sq not in pieces:
                                moves.append(f"{sq}{fwd2_sq}")

            # Diagonal captures
            for dc in [-1, 1]:
                nc = c + dc
                nr = r + pawn_dir
                if 0 <= nc <= 7 and 0 <= nr <= 7:
                    cap_sq = coords_to_sq(nc, nr)
                    target = pieces.get(cap_sq)
                    if target and target[0] == opp_char:
                        if nr == promo_rank:
                            for promo in ['q', 'r', 'b', 'n']:
                                moves.append(f"{sq}{cap_sq}{promo}")
                        else:
                            moves.append(f"{sq}{cap_sq}")

        elif ptype == 'N':
            for dc, dr in knight_offsets:
                nc, nr = c + dc, r + dr
                if 0 <= nc <= 7 and 0 <= nr <= 7:
                    dest = coords_to_sq(nc, nr)
                    target = pieces.get(dest)
                    if not target or target[0] == opp_char:
                        moves.append(f"{sq}{dest}")

        elif ptype == 'K':
            for dc, dr in king_offsets:
                nc, nr = c + dc, r + dr
                if 0 <= nc <= 7 and 0 <= nr <= 7:
                    dest = coords_to_sq(nc, nr)
                    target = pieces.get(dest)
                    if not target or target[0] == opp_char:
                        moves.append(f"{sq}{dest}")

        elif ptype in ('B', 'R', 'Q'):
            dirs = []
            if ptype in ('B', 'Q'):
                dirs.extend(diag_dirs)
            if ptype in ('R', 'Q'):
                dirs.extend(straight_dirs)

            for dc, dr in dirs:
                step = 1
                while True:
                    nc, nr = c + dc * step, r + dr * step
                    if not (0 <= nc <= 7 and 0 <= nr <= 7):
                        break
                    dest = coords_to_sq(nc, nr)
                    target = pieces.get(dest)
                    if not target:
                        moves.append(f"{sq}{dest}")
                    else:
                        if target[0] == opp_char:
                            moves.append(f"{sq}{dest}")
                        break
                    step += 1

    return moves


def score_move_tactics(pieces: Dict[str, str], move: str) -> int:
    src = move[:2]
    dst = move[2:4]
    promo = move[4:] if len(move) > 4 else None
    victim = pieces.get(dst)
    attacker = pieces.get(src)

    priority = 0
    if victim:
        victim_val = PIECE_VALUES.get(victim[1], 0)
        attacker_val = PIECE_VALUES.get(attacker[1], 0) if attacker else 0
        priority += 1000 + (victim_val * 10 - attacker_val)

    if promo == 'q':
        priority += 900
    elif promo:
        priority += 300

    # Slight center attraction
    dc, dr = sq_to_coords(dst)
    center_dist = abs(3.5 - dc) + abs(3.5 - dr)
    priority -= int(center_dist * 2)

    return priority


def policy(pieces: Dict[str, str], to_play: str, *args, **kwargs) -> str:
    color_char = 'w' if to_play.lower().startswith('w') else 'b'
    opp_char = 'b' if color_char == 'w' else 'w'

    # Retrieve legal_moves from arguments or fallback
    legal_moves: Optional[List[str]] = None
    if 'legal_moves' in kwargs and kwargs['legal_moves']:
        legal_moves = kwargs['legal_moves']
    elif args and isinstance(args[0], list):
        legal_moves = args[0]

    if not legal_moves:
        legal_moves = generate_pseudo_legal_moves(pieces, color_char)

    if not legal_moves:
        return 'e2e4'

    if len(legal_moves) == 1:
        return legal_moves[0]

    # Sort moves by immediate tactical heuristic
    ordered_moves = sorted(legal_moves, key=lambda m: score_move_tactics(pieces, m), reverse=True)

    best_move = ordered_moves[0]
    best_score = -1000000

    for move in ordered_moves:
        b1 = apply_move(pieces, move)

        # Check immediate king capture / game winning move
        opp_king_alive = any(p == opp_char + 'K' for p in b1.values())
        if not opp_king_alive:
            return move

        # 2-ply search: opponent's response
        opp_replies = generate_pseudo_legal_moves(b1, opp_char)
        if not opp_replies:
            # Opponent has no moves, highly favorable
            move_eval = 90000
        else:
            worst_reply_eval = 1000000
            # Check up to top 12 opponent responses
            sorted_opp_replies = sorted(opp_replies, key=lambda m: score_move_tactics(b1, m), reverse=True)[:12]
            for opp_move in sorted_opp_replies:
                b2 = apply_move(b1, opp_move)
                score = evaluate_board(b2, color_char)
                if score < worst_reply_eval:
                    worst_reply_eval = score

            move_eval = worst_reply_eval

        if move_eval > best_score:
            best_score = move_eval
            best_move = move

    return best_move
