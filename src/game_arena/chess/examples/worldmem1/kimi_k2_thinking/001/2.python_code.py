
import random
from typing import Dict, List

def policy(pieces: Dict[str, str], to_play: str, legal_moves: List[str], memory: dict) -> tuple[str, dict]:
    """
    Strategic chess move selection optimized for arena competition.
    
    Decision hierarchy:
    1. Checkmate (ends game)
    2. Queen promotion (massive material gain)
    3. Checks (tactical pressure)
    4. Captures (material advantage)
    5. Castling (king safety)
    6. Development (minor pieces)
    7. Center control (pawn structure)
    8. Random move (avoid predictability)
    
    Guarantees: Always returns a legal move from the list.
    """
    if not legal_moves:
        return ("", memory)
    
    my_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if to_play == 'white' else 'w'
    my_back_rank = '1' if to_play == 'white' else '8'
    
    # --- Tier 1: Forced Wins ---
    # 1. Checkmate
    for move in legal_moves:
        if '#' in move:
            return (move, memory)
    
    # 2. Queen promotion (instant game-winning material)
    queen_promos = [m for m in legal_moves if '=Q' in m]
    if queen_promos:
        return (queen_promos[0], memory)
    
    # --- Tier 2: Material & Tactics ---
    # Evaluate captures by material value
    capture_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 100}
    best_capture = None
    best_capture_value = 0
    
    for move in legal_moves:
        if 'x' in move:
            # Extract destination square from SAN capture notation
            clean_move = move[:-1] if move.endswith('+') else move
            x_pos = clean_move.find('x')
            dest_sq = clean_move[x_pos+1:x_pos+3]
            
            # Verify it's a valid square reference
            if len(dest_sq) == 2 and dest_sq[0] in 'abcdefgh' and dest_sq[1] in '12345678':
                captured_piece = pieces.get(dest_sq)
                if captured_piece and captured_piece[0] == opponent_color:
                    # Calculate capture value
                    value = capture_values.get(captured_piece[1], 0)
                    # Small bonus for checking captures
                    if '+' in move:
                        value += 0.5
                    
                    if value > best_capture_value:
                        best_capture_value = value
                        best_capture = move
    
    # 3. Strong captures (positive material gain)
    if best_capture and best_capture_value >= 1:
        return (best_capture, memory)
    
    # 4. Checks (if no profitable captures)
    checking_moves = [m for m in legal_moves if '+' in m]
    if checking_moves:
        return (checking_moves[0], memory)
    
    # --- Tier 3: Position & Safety ---
    # 5. Castling (king safety and rook activation)
    castle_moves = [m for m in legal_moves if m.startswith('O-O')]
    if castle_moves:
        return (castle_moves[0], memory)
    
    # 6. Minor piece development from back rank
    development_moves = []
    for move in legal_moves:
        # Knights and bishops from starting squares
        if (move.startswith('N') and f'N{my_back_rank}' in move) or \
           (move.startswith('B') and f'B{my_back_rank}' in move):
            development_moves.append(move)
    
    if development_moves:
        return (development_moves[0], memory)
    
    # 7. Central pawn advances
    center_moves = [m for m in legal_moves if m in ['e4', 'd4', 'e3', 'd3', 'e5', 'd5', 'e6', 'd6']]
    if center_moves:
        return (center_moves[0], memory)
    
    # 8. Knight to natural developing squares
    knight_targets = ['f3', 'c3', 'f6', 'c6'] if to_play == 'white' else ['f6', 'c6', 'f3', 'c3']
    knight_moves = [m for m in legal_moves if m.startswith('N') and m[-2:] in knight_targets]
    if knight_moves:
        return (knight_moves[0], memory)
    
    # --- Tier 4: Fallback ---
    # Return random move to avoid deterministic patterns
    return (random.choice(legal_moves), memory)
