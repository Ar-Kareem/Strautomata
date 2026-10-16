
import re
from typing import Dict, List, Tuple

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str], memory: Dict) -> Tuple[str, Dict]:
    # Material values
    VALUES = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Determine player color
    color = 'w' if to_play == 'white' else 'b'
    opp_color = 'b' if color == 'w' else 'w'
    
    # Extract piece positions for both sides
    my_pieces = {sq: pc for sq, pc in pieces.items() if pc[0] == color}
    opp_pieces = {sq: pc for sq, pc in pieces.items() if pc[0] == opp_color}
    
    # Increment move counter in memory
    if 'move_count' not in memory:
        memory['move_count'] = 0
    memory['move_count'] += 1
    
    # Utility: parse move
    def parse_move(move: str) -> Dict[str, str]:
        m = {'original': move, 'capture': False, 'check': False, 'mate': False, 'promo': None, 'castling': None, 'from': None, 'to': None, 'piece': 'P'}
        if move == 'O-O':
            m['castling'] = 'kingside'
            m['piece'] = 'K'
        elif move == 'O-O-O':
            m['castling'] = 'queenside'
            m['piece'] = 'K'
        else:
            if 'x' in move:
                m['capture'] = True
            if '+' in move:
                m['check'] = True
            if '#' in move:
                m['mate'] = True
            if '=Q' in move:
                m['promo'] = 'Q'
            elif '=R' in move:
                m['promo'] = 'R'
            elif '=B' in move:
                m['promo'] = 'B'
            elif '=N' in move:
                m['promo'] = 'N'

            # Extract piece
            if move[0].isupper() and move[0] != 'O':
                m['piece'] = move[0]
            # Find destination square
            sq_match = re.search(r'[a-h][1-8](?=[+#]?(\=[QRBN])?$)', move)
            if sq_match:
                m['to'] = sq_match.group(0)
            # Try to infer source (simplified)
            # This is incomplete, but we can try to reverse-engineer based on what piece moved
            # For now, we'll avoid complex disambiguation and focus on captures and known actions
        return m

    # Evaluate what piece is on a square (or None)
    def piece_at(sq: str) -> str:
        return pieces.get(sq, None)

    # Get opponent attacks on a square (simplified: only direct captures)
    def is_attacked_by_opponent(sq: str) -> bool:
        piece = piece_at(sq)
        # Check if any opponent piece can capture on sq
        for pos, pc in opp_pieces.items():
            ptype = pc[1]
            pcolor = pc[0]
            from_file, from_rank = pos[0], int(pos[1])
            to_file, to_rank = sq[0], int(sq[1])
            df, dr = ord(to_file) - ord(from_file), to_rank - from_rank
            adf, adr = abs(df), abs(dr)
            if ptype == 'P':
                # Pawn captures: diagonal forward one
                forward = 1 if pcolor == 'w' else -1
                if df in [-1, 1] and dr == forward:
                    return True
            elif ptype == 'N':
                if (adf == 2 and adr == 1) or (adf == 1 and adr == 2):
                    return True
            elif ptype == 'B':
                if adf == adr and adf > 0:
                    return True
            elif ptype == 'R':
                if adf == 0 or adr == 0:
                    return True
            elif ptype == 'Q':
                if adf == adr or adf == 0 or adr == 0:
                    return True
            elif ptype == 'K':
                if adf <= 1 and adr <= 1:
                    return True
        return False

    # Score move
    best_score = -1000000
    best_move = legal_moves[0]  # fallback

    for move in legal_moves:
        score = 0
        m = parse_move(move)

        # Priority 1: Checkmate
        if m['mate']:
            return move, memory

        # Priority 2: Check
        if m['mate']:
            score += 10000
        elif m['check']:
            score += 50  # incentive, but not as high as mate

        # Priority 3: Castling
        if m['castling']:
            score += 80

        # Priority 4: Promotion
        if m['promo']:
            promo_value = VALUES[m['promo']]
            score += promo_value * 10
            # Avoid underpromotion unless knight check? (simplified: prefer Q)
            if m['promo'] != 'Q':
                score -= 5  # slight penalty for underpromotion

        # Evaluate captures
        if m['capture'] and m['to']:
            captured_piece = piece_at(m['to'])
            if captured_piece:
                cap_color, cap_type = captured_piece[0], captured_piece[1]
                if cap_color != color:  # valid capture
                    value_gained = VALUES[cap_type]
                    value_lost = VALUES[m['piece']] if m['piece'] else 1  # assume pawn
                    net_gain = value_gained - value_lost
                    score += net_gain * 10

                    # Penalize if we hang the capturing piece immediately (simplified)
                    if is_attacked_by_opponent(m['to']):
                        # But if we gain material, it might be worth it
                        score -= value_gained * 5  # risk penalty

        # Penalize moving king early unless castling or necessary
        if m['piece'] == 'K':
            if memory['move_count'] < 10 and not m['castling']:
                score -= 40

        # Encourage knight and bishop development in opening
        if memory['move_count'] < 10:
            if m['piece'] in ['N', 'B']:
                # Developing to central squares
                if m['to'] in ['e4', 'd4', 'e5', 'd5', 'c6', 'f6', 'c3', 'f3']:
                    score += 20
            # Avoid moving same piece twice
            if memory.get(f"moved_{m['piece']}_count", 0) > 1:
                score -= 10

        # Prefer forward pawn moves (in opening) or captures
        if m['piece'] == 'P':
            if m['capture']:
                score += 10
            else:
                # Pushing pawn forward (central or flank)
                to_rank = int(m['to'][1])
                if (color == 'w' and to_rank > 2) or (color == 'b' and to_rank < 7):
                    score += 5  # slight encouragement

        # Avoid moves that leave a piece hanging (if we move and our piece on another square is attacked)
        # Simplified: if we move a piece, does it expose the king or lose another piece?
        # Instead: focus on if the moved piece ends up on a square that is attacked and not defended (simplified below)

        # Only basic: if move is not a capture and moves to a square attacked by opponent, penalize
        if m['to'] and not m['capture'] and m['piece'] != 'K' and m['castling'] is None:
            if is_attacked_by_opponent(m['to']):
                # Is that piece defended? (crude approximation)
                # For now, assume knight/bishop are less defended
                piece_type = m['piece']
                if piece_type in ['N', 'B', 'R', 'Q']:
                    score -= VALUES[piece_type] * 5  # high penalty for hanging piece

        # Update memory for piece moves (for development tracking)
        if m['piece'] in ['N', 'B', 'Q', 'R']:
            key = f"moved_{color}_{m['piece']}_count"
            memory[key] = memory.get(key, 0) + 1

        # Update best move
        if score > best_score:
            best_score = score
            best_move = move

    return best_move, memory
