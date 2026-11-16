
import random
import re

PIECE_VALUE = {
    'K': 0,
    'Q': 9,
    'R': 5,
    'B': 3,
    'N': 3,
    'P': 1,
}

def _strip_suffix(move: str) -> str:
    # remove check/mate annotations
    return move.replace('+','').replace('#','')

def _destination_square(move: str) -> None:
    m = _strip_suffix(move)
    if m in ("O-O", "O-O-O"):
        return None
    # remove promotion part
    if '=' in m:
        m = m.split('=')[0]
    # destination is last two chars
    if len(m) >= 2:
        return m[-2:]
    return None

def _promotion_piece(move: str) -> None:
    if '=' in move:
        part = move.split('=')[1]
        if part:
            # first char after '=' is piece letter
            return part[0]
    return None

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Ensure we always return a legal move
    best_moves = []
    best_score = -10**9

    # determine enemy color
    enemy = 'b' if to_play == 'white' else 'w'

    for move in legal_moves:
        score = 0

        # checkmate
        if '#' in move:
            score += 10000

        # check
        if '+' in move:
            score += 50

        # castling bonus
        if move in ("O-O", "O-O-O"):
            score += 10

        # capture bonus
        if 'x' in move:
            dest = _destination_square(move)
            if dest and dest in pieces and pieces[dest][0] == enemy:
                cap_piece = pieces[dest][1]
                score += PIECE_VALUE.get(cap_piece, 0) * 100

        # promotion bonus
        promo = _promotion_piece(move)
        if promo:
            score += PIECE_VALUE.get(promo, 0) * 100

        # small bonus for quiet development (piece moves to center)
        dest = _destination_square(move)
        if dest:
            file = dest[0]
            rank = dest[1]
            if file in "cded" and rank in "3456":
                score += 1

        if score > best_score:
            best_score = score
            best_moves = [move]
        elif score == best_score:
            best_moves.append(move)

    if not best_moves:
        return legal_moves[0], memory

    return random.choice(best_moves), memory
