
import random

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Piece values
    values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}

    def parse_move(move: str):
        mate = move.endswith('#')
        check = move.endswith('+') or mate
        m = move.rstrip('+#')
        promo = None
        if '=' in m:
            base, promo = m.split('=')
        else:
            base = m
        # destination square for non-castling
        dest = None
        if base in ('O-O', 'O-O-O'):
            dest = None
        else:
            if len(base) >= 2:
                dest = base[-2:]
        capture = 'x' in base
        return {
            'mate': mate,
            'check': check,
            'promo': promo,
            'base': base,
            'dest': dest,
            'capture': capture,
            'castle': base in ('O-O', 'O-O-O')
        }

    best_moves = []
    best_score = -10**9

    for mv in legal_moves:
        info = parse_move(mv)
        score = 0
        if info['mate']:
            score += 100000
        if info['check']:
            score += 50
        if info['promo']:
            # promotion value (new piece minus pawn)
            score += (values.get(info['promo'], 0) - 1) * 20 + 30
        if info['capture']:
            if info['dest'] in pieces:
                captured = pieces[info['dest']][1]
                score += values.get(captured, 0) * 15 + 5
            else:
                score += 5  # en passant or unknown
        if info['castle']:
            score += 10  # king safety
        # slight preference for central squares
        if info['dest'] and len(info['dest']) == 2:
            file = info['dest'][0]
            rank = info['dest'][1]
            if file in 'cdef' and rank in '3456':
                score += 2

        if score > best_score:
            best_score = score
            best_moves = [mv]
        elif score == best_score:
            best_moves.append(mv)

    # choose deterministically (or randomly among best)
    action = best_moves[0] if best_moves else legal_moves[0]
    return action, memory
