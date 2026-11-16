
import numpy as np
from typing import Dict, List, Tuple

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str], memory: Dict) -> Tuple[str, Dict]:
    # --- Initialize memory if empty ---
    if not memory:
        memory = {
            'castling_rights': {'white': {'K': True, 'Q': True}, 'black': {'K': True, 'Q': True}},
            'en_passant': None,
            'halfmove_clock': 0,
            'fullmove_number': 1,
            'king_pos': {'white': None, 'black': None},
            'material': {'white': 0, 'black': 0},
            'phase': 'opening'  # Can be 'opening', 'middlegame', 'endgame
        }

    # --- Update memory with current state ---
    color = 'w' if to_play == 'white' else 'b'
    king_pos = [sq for sq, pc in pieces.items() if pc.endswith('K') and pc.startswith(color)][0]
    memory['king_pos'][color] = king_pos

    # --- Material evaluation (standard piece-square values) ---
    material = {'w': 0, 'b': 0}
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    for sq, pc in pieces.items():
        if pc.startswith(color):
            material[color] += piece_values[pc[1]]

    memory['material'][color] = material[color]

    # --- Check for checkmate ---
    for move in legal_moves:
        if move.endswith('#'):
            return (move, memory)

    # --- Check for immediate threats (checks or captures) ---
    opponent = 'b' if color == 'w' else 'w'
    opponent_king = [sq for sq, pc in pieces.items() if pc.startswith(opponent) and pc.endswith('K')][0]

    # --- Evaluate captures (highest material gain first) ---
    captures = [move for move in legal_moves if 'x' in move]
    if captures:
        # Sort captures by material gain (simplified: higher value captured first)
        def capture_score(move):
            capturing_piece = move[0]
            captured_piece = move[2] if 'x' in move else move[1]
            if captured_piece == 'K':  # Shouldn't happen in legal moves
                return 100
            return piece_values[captured_piece] - piece_values[capturing_piece[1]]

        captures.sort(key=capture_score, reverse=True)
        best_capture = captures[0]

        # --- If capture gives check, prioritize it ---
        if '+' in best_capture or '#' in best_capture:
            return (best_capture, memory)

        # --- If capture is safe (no opponent attacks target square) ---
        # (Simplified: assume all captures are safe unless king is in danger)
        return (best_capture, memory)

    # --- Check for checks ---
    checks = [move for move in legal_moves if move.endswith('+')]
    if checks:
        # Sort checks by material gain (if check also captures)
        def check_score(move):
            if 'x' in move:
                captured_piece = move[2]
                return piece_values[captured_piece] - piece_values[move[0][1]]
            return 0  # Pure check

        checks.sort(key=check_score, reverse=True)
        return (checks[0], memory)

    # --- Check for promotions ---
    promotions = [move for move in legal_moves if '=' in move]
    if promotions:
        # Sort promotions by piece value (Queen > Rook > Bishop > Knight)
        def promotion_score(move):
            return {'Q': 9, 'R': 5, 'B': 3, 'N': 3}[move[-1]]

        promotions.sort(key=promotion_score, reverse=True)
        return (promotions[0], memory)

    # --- King safety evaluation (distance to opponent's pieces) ---
    def king_safety(sq):
        x, y = ord(sq[0]) - ord('a'), int(sq[1]) - 1
        distances = np.zeros((8, 8))
        for (i, j), pc in pieces.items():
            if pc.startswith(opponent):
                distances[x, y] += 1 / (abs(i - x) + abs(j - y))  # Inverse distance
        return distances[x, y]

    king_safety_scores = {move: king_safety(move[-2:]) for move in legal_moves if move[0] == 'K'}
    if king_safety_scores:
        # Prefer moves that keep king safe (lower score = better)
        best_king_move = min(king_safety_scores, key=king_safety_scores.get)
        return (best_king_move, memory)

    # --- Positional heuristics (center control, development) ---
    center_squares = {'d4', 'd5', 'e4', 'e5'}
    center_moves = [move for move in legal_moves if move[-2:] in center_squares]

    if center_moves and memory['phase'] == 'opening':
        # Prefer moves that control center (simplified: just pick first)
        return (center_moves[0], memory)

    # --- Fallback: pick a move with highest material gain ---
    def move_score(move):
        if 'x' in move:
            captured_piece = move[2]
            return piece_values[captured_piece] - piece_values[move[0][1]]
        return 0  # Non-capturing move

    legal_moves.sort(key=move_score, reverse=True)
    return (legal_moves[0], memory)
