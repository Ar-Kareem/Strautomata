
import random

def policy(pieces: dict[str, str], to_play: str) -> str:
    # 1. Generate Legal Moves (Internal Logic)
    # Note: In the actual arena, legal_moves would be provided or derived.
    # Since we must return a move from the board state, we implement 
    # a basic move generator for standard pieces.
    
    piece_values = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    color_mult = 1 if to_play == 'white' else -1
    us = 'w' if to_play == 'white' else 'b'
    them = 'b' if to_play == 'white' else 'w'

    def get_eval(board):
        score = 0
        for sq, p in board.items():
            val = piece_values.get(p[1], 0)
            # Basic central control bonus
            file_idx = ord(sq[0]) - ord('a')
            rank_idx = int(sq[1]) - 1
            centrality = (3.5 - abs(3.5 - file_idx)) + (3.5 - abs(3.5 - rank_idx))
            if p[0] == 'w':
                score += val + centrality * 2
            else:
                score -= val + centrality * 2
        return score * color_mult

    def get_pseudo_legal_moves(board, color):
        moves = []
        for sq, p in board.items():
            if p[0] != color: continue
            f, r = ord(sq[0]) - ord('a'), int(sq[1])
            # Simplified move generation for choosing among possibilities
            # This logic mimics standard UCI format generation
            # (In the arena environment, the engine typically receives a move list)
            # Here we simulate the move selection assuming legal_moves are detectable
            pass
        return moves

    # Because 'legal_moves' is typically provided by the environment 
    # but not explicitly passed in the function signature provided in the prompt, 
    # we must deduce them or handle the piece dictionary.
    
    # Strategy: Find a move that captures the highest value piece or improves position.
    
    best_move = None
    best_score = -float('inf')

    # Simulation of move calculation
    # We iterate through pieces and look for "obvious" good moves (captures/advancements)
    possible_moves = []
    files = 'abcdefgh'
    ranks = '12345678'
    
    for start_sq, p in pieces.items():
        if p[0] != us: continue
        pt = p[1]
        sf, sr = ord(start_sq[0]) - ord('a'), int(start_sq[1])
        
        # Directions for pieces
        dirs = []
        if pt == 'N':
            dirs = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]
        elif pt == 'B':
            dirs = [(1,1), (1,-1), (-1,1), (-1,-1)]
        elif pt == 'R':
            dirs = [(0,1), (0,-1), (1,0), (-1,0)]
        elif pt == 'Q' or pt == 'K':
            dirs = [(0,1), (0,-1), (1,0), (-1,0), (1,1), (1,-1), (-1,1), (-1,-1)]
        elif pt == 'P':
            step = 1 if us == 'w' else -1
            # Push
            target_r = sr + step
            if 1 <= target_r <= 8:
                tsq = f"{start_sq[0]}{target_r}"
                if tsq not in pieces:
                    possible_moves.append(start_sq + tsq)
            # Captures
            for df in [-1, 1]:
                tf = sf + df
                if 0 <= tf <= 7:
                    tsq = f"{files[tf]}{sr + step}"
                    if tsq in pieces and pieces[tsq][0] == them:
                        possible_moves.append(start_sq + tsq)

        for df, dr in dirs:
            for dist in range(1, 9):
                tf, tr = sf + df * dist, sr + dr * dist
                if 0 <= tf <= 7 and 1 <= tr <= 8:
                    tsq = f"{files[tf]}{tr}"
                    if tsq not in pieces:
                        possible_moves.append(start_sq + tsq)
                        if pt in 'NK': break
                    elif pieces[tsq][0] == them:
                        possible_moves.append(start_sq + tsq)
                        break
                    else: break
                else: break

    # Add promotion 'q' to pawn moves reaching the end
    final_moves = []
    for m in possible_moves:
        if pieces[m[:2]][1] == 'P' and (m[3] == '8' or m[3] == '1'):
            final_moves.append(m + 'q')
        else:
            final_moves.append(m)

    if not final_moves:
        return "e2e4" # Fallback (should not happen in legal state)

    # Evaluate moves
    for move in final_moves:
        f, t = move[:2], move[2:4]
        score = 0
        # Capture weight
        if t in pieces:
            score += 10 * piece_values.get(pieces[t][1], 0)
        # Position weight
        score += (3.5 - abs(3.5 - (ord(t[0]) - ord('a'))))
        score += (3.5 - abs(3.5 - (int(t[1]) - 1)))
        
        if score > best_score:
            best_score = score
            best_move = move

    return best_move if best_move else final_moves[0]
