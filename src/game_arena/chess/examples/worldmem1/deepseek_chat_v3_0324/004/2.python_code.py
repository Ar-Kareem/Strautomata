
import random
import numpy as np

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize memory if first move
    if not memory:
        memory = {
            'move_count': 0,
            'castling_rights': {'white': {'kingside': True, 'queenside': True},
                              'black': {'kingside': True, 'queenside': True}},
            'last_moves': []
        }
    
    color = to_play[0]  # 'w' or 'b'
    opponent_color = 'b' if color == 'w' else 'w'
    memory['move_count'] += 1
    
    # Piece values
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    
    def evaluate_move(move):
        # Check for checkmate
        if move.endswith('#'):
            return 1000
        
        # Check for checks
        if move.endswith('+'):
            score = 50
        else:
            score = 0
            
        # Evaluate captures
        if 'x' in move:
            captured_piece = None
            target_square = move.split('x')[1][:2]
            if target_square in pieces:
                captured_piece = pieces[target_square][1]
                score += piece_values.get(captured_piece, 0) * 10
            
            # Subtract value of capturing piece if it's a trade
            moving_piece = move[0] if move[0].isupper() else 'P'
            if moving_piece == 'P' and 'x' in move:
                moving_piece = move[0].upper()  # Handle pawn captures like 'dxe4'
            score -= piece_values.get(moving_piece, 0) * 0.5
        
        # Promote pawns
        if '=Q' in move:
            score += 8
        elif '=R' in move:
            score += 4
        elif '=B' in move or '=N' in move:
            score += 2
            
        # Castling
        if move == 'O-O' or move == 'O-O-O':
            score += 2
            
        # Central control
        dest_square = move[-2:] if '=' not in move else move[-4:-2]
        if len(dest_square) == 2:
            file, rank = dest_square[0], dest_square[1]
            center_files = ['d', 'e']
            center_ranks = ['4', '5']
            if file in center_files and rank in center_ranks:
                score += 1
        
        # Development (knights and bishops early)
        if memory['move_count'] < 10:
            if move.startswith('N') or move.startswith('B'):
                score += 1
        
        return score
    
    # Sort moves by evaluation
    scored_moves = [(move, evaluate_move(move)) for move in legal_moves]
    scored_moves.sort(key=lambda x: -x[1])
    
    # Update castling rights
    king_moved = any(move.startswith('K') for move in memory.get('last_moves', [])[-2:])
    rook_moves = [move for move in memory.get('last_moves', [])[-2:] if move.startswith('R')]
    
    # Choose best move with some randomness among top choices
    top_score = scored_moves[0][1]
    best_moves = [move for move, score in scored_moves if score >= top_score * 0.9]
    
    # Update memory
    chosen_move = random.choice(best_moves)
    memory['last_moves'] = memory.get('last_moves', [])[-9:] + [chosen_move]  # Keep last 10 moves
    
    # Update castling rights if king or rook moved
    if chosen_move == 'O-O' or chosen_move == 'O-O-O':
        memory['castling_rights'][to_play]['kingside'] = False
        memory['castling_rights'][to_play]['queenside'] = False
    elif chosen_move.startswith('K'):
        memory['castling_rights'][to_play]['kingside'] = False
        memory['castling_rights'][to_play]['queenside'] = False
    elif chosen_move.startswith('Ra') or chosen_move.startswith('Rh'):
        # Simplistic rook move detection
        memory['castling_rights'][to_play]['queenside'] = False
    
    return chosen_move, memory
