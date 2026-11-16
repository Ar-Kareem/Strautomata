
import copy
import math

def policy(pieces: dict[str, str], to_play: str, legal_moves: list[str], memory: dict) -> tuple[str, dict]:
    # Initialize memory if empty
    if not memory:
        memory["history"] = []
        memory["repetition_map"] = {}
    
    # Current player's color code ('w' or 'b')
    us = 'w' if to_play == 'white' else 'b'
    them = 'b' if us == 'w' else 'w'
    
    # Board state fingerprint for repetition detection
    board_key = ''.join(sorted([sq + p for sq, p in pieces.items()]))
    memory["history"].append(board_key)
    memory["repetition_map"][board_key] = memory["repetition_map"].get(board_key, 0) + 1
    
    # Material values
    VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 0}
    # Piece-square tables (midgame oriented, from white's perspective)
    PST = {
        'P': [0, 0, 0, 0, 0, 0, 0, 0,
              50, 50, 50, 50, 50, 50, 50, 50,
              10, 10, 20, 30, 30, 20, 10, 10,
              5, 5, 10, 25, 25, 10, 5, 5,
              0, 0, 0, 20, 20, 0, 0, 0,
              5, -5, -10, 0, 0, -10, -5, 5,
              5, 10, 10, -20, -20, 10, 10, 5,
              0, 0, 0, 0, 0, 0, 0, 0],
        'N': [-50, -40, -30, -30, -30, -30, -40, -50,
              -40, -20, 0, 0, 0, 0, -20, -40,
              -30, 0, 10, 15, 15, 10, 0, -30,
              -30, 5, 15, 20, 20, 15, 5, -30,
              -30, 0, 15, 20, 20, 15, 0, -30,
              -30, 5, 10, 15, 15, 10, 5, -30,
              -40, -20, 0, 5, 5, 0, -20, -40,
              -50, -40, -30, -30, -30, -30, -40, -50],
        'B': [-20, -10, -10, -10, -10, -10, -10, -20,
              -10, 0, 0, 0, 0, 0, 0, -10,
              -10, 0, 5, 10, 10, 5, 0, -10,
              -10, 5, 5, 10, 10, 5, 5, -10,
              -10, 0, 10, 10, 10, 10, 0, -10,
              -10, 10, 10, 10, 10, 10, 10, -10,
              -10, 5, 0, 0, 0, 0, 5, -10,
              -20, -10, -10, -10, -10, -10, -10, -20],
        'R': [0, 0, 0, 0, 0, 0, 0, 0,
              5, 10, 10, 10, 10, 10, 10, 5,
              -5, 0, 0, 0, 0, 0, 0, -5,
              -5, 0, 0, 0, 0, 0, 0, -5,
              -5, 0, 0, 0, 0, 0, 0, -5,
              -5, 0, 0, 0, 0, 0, 0, -5,
              -5, 0, 0, 0, 0, 0, 0, -5,
              0, 0, 0, 5, 5, 0, 0, 0],
        'Q': [-20, -10, -10, -5, -5, -10, -10, -20,
              -10, 0, 0, 0, 0, 0, 0, -10,
              -10, 0, 5, 5, 5, 5, 0, -10,
              -5, 0, 5, 5, 5, 5, 0, -5,
              0, 0, 5, 5, 5, 5, 0, -5,
              -10, 5, 5, 5, 5, 5, 0, -10,
              -10, 0, 5, 0, 0, 0, 0, -10,
              -20, -10, -10, -5, -5, -10, -10, -20],
        'K': [-30, -40, -40, -50, -50, -40, -40, -30,
              -30, -40, -40, -50, -50, -40, -40, -30,
              -30, -40, -40, -50, -50, -40, -40, -30,
              -30, -40, -40, -50, -50, -40, -40, -30,
              -20, -30, -30, -40, -40, -30, -30, -20,
              -10, -20, -20, -20, -20, -20, -20, -10,
              20, 20, 0, 0, 0, 0, 20, 20,
              20, 30, 10, 0, 0, 10, 30, 20],
    }
    
    # Helper: square to index
    def sq_index(sq):
        file = ord(sq[0]) - ord('a')
        rank = int(sq[1]) - 1
        return rank * 8 + file
    
    # Helper: generate all possible moves for a side (for mobility)
    def pseudo_moves_for_color(board, color):
        # Simplified: just count squares attacked by pieces of given color
        # For speed, we use a very basic attack map
        attacks = set()
        for sq, pc in board.items():
            if pc[0] != color:
                continue
            ptype = pc[1]
            f = ord(sq[0]) - ord('a')
            r = int(sq[1]) - 1
            if ptype == 'P':
                step = 1 if color == 'w' else -1
                attacks.add((f-1, r+step))
                attacks.add((f+1, r+step))
            elif ptype == 'N':
                for dx, dy in [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]:
                    attacks.add((f+dx, r+dy))
            elif ptype == 'K':
                for dx in (-1,0,1):
                    for dy in (-1,0,1):
                        if dx == dy == 0:
                            continue
                        attacks.add((f+dx, r+dy))
            else: # Q,R,B sliding
                dirs = []
                if ptype in ('Q','R'):
                    dirs += [(1,0),(-1,0),(0,1),(0,-1)]
                if ptype in ('Q','B'):
                    dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
                for dx,dy in dirs:
                    x, y = f, r
                    while True:
                        x += dx; y += dy
                        if not (0 <= x < 8 and 0 <= y < 8):
                            break
                        attacks.add((x, y))
                        if (chr(x+ord('a')) + str(y+1)) in board:
                            break
        # Filter to board bounds
        return {a for a in attacks if 0 <= a[0] < 8 and 0 <= a[1] < 8}
    
    # Evaluate board from perspective of 'us'
    def evaluate(board):
        score = 0
        our_mobility = pseudo_moves_for_color(board, us)
        their_mobility = pseudo_moves_for_color(board, them)
        
        # Material + PST
        for sq, pc in board.items():
            val = VALUES[pc[1]]
            idx = sq_index(sq)
            pst = PST[pc[1]][idx]
            if pc[0] == us:
                score += val + pst
                # Mobility bonus
                score += 0.1 * len([1 for m in our_mobility if (ord(sq[0])-ord('a'), int(sq[1])-1) == m])
            else:
                score -= val + pst
                score -= 0.1 * len([1 for m in their_mobility if (ord(sq[0])-ord('a'), int(sq[1])-1) == m])
        
        # King safety: penalty for being near opponent pieces
        our_king_sq = None
        for sq, pc in board.items():
            if pc == us + 'K':
                our_king_sq = sq
                break
        if our_king_sq:
            kf = ord(our_king_sq[0]) - ord('a')
            kr = int(our_king_sq[1]) - 1
            for sq, pc in board.items():
                if pc[0] == them:
                    f = ord(sq[0]) - ord('a')
                    r = int(sq[1]) - 1
                    dist = max(abs(f-kf), abs(r-kr))
                    if dist <= 2:
                        score -= 20 / dist
        
        # Pawn structure: penalty for doubled pawns
        pawn_files = {sq[0] for sq, pc in board.items() if pc == us + 'P'}
        score -= 10 * (len([sq for sq, pc in board.items() if pc == us + 'P']) - len(pawn_files))
        
        # Endgame: encourage king to center if few pieces left
        piece_count = sum(1 for pc in board.values() if pc[1] != 'K')
        if piece_count <= 6:
            # King centralization bonus
            center_dist = abs(kf - 3.5) + abs(kr - 3.5)
            score += (7 - center_dist) * 10
        
        return score
    
    # Simulate a move on a board copy
    def make_move(board, move_str):
        new_board = copy.copy(board)
        # Castling
        if move_str in ('O-O', 'O-O-O'):
            rank = '1' if us == 'w' else '8'
            if move_str == 'O-O':
                king_from = 'e' + rank
                king_to = 'g' + rank
                rook_from = 'h' + rank
                rook_to = 'f' + rank
            else:
                king_from = 'e' + rank
                king_to = 'c' + rank
                rook_from = 'a' + rank
                rook_to = 'd' + rank
            new_board[king_to] = new_board.pop(king_from)
            new_board[rook_to] = new_board.pop(rook_from)
            return new_board
        
        # Normal move: parse move like 'e4', 'Nf3', 'Rxe4', 'e8=Q'
        # Simplified parser: find piece moving
        if move_str[0] in 'KQRBN':
            piece = move_str[0]
            rest = move_str[1:]
        else:
            piece = 'P'
            rest = move_str
        
        # Remove capture 'x'
        rest = rest.replace('x', '')
        # Remove check '+'
        rest = rest.replace('+', '')
        
        # Find destination
        dest = rest[-2:]
        promo = None
        if '=' in dest:
            dest, promo = dest.split('=')
        if len(dest) != 2:
            dest = rest[-2:]
        
        # Find source square
        src = None
        for sq, pc in board.items():
            if pc[0] == us and pc[1] == piece:
                # Could move to dest? We'll accept any matching piece type for speed
                # We'll just pick the first one that could legally reach dest (simplified)
                if piece == 'P':
                    if src is None:
                        src = sq
                else:
                    if src is None:
                        src = sq
        
        if src is None:
            src = 'a1'  # fallback
        
        # Move piece
        moving_piece = new_board.pop(src)
        if promo:
            moving_piece = us + promo
        new_board[dest] = moving_piece
        return new_board
    
    # Check for immediate checkmate
    for move in legal_moves:
        new_board = make_move(pieces, move)
        # Check if opponent has no legal moves (stub: assume checkmate if their king is attacked and they have no moves)
        # For safety, we'll just pick this move if it captures opponent's king (should not happen in legal moves)
        # Instead, we rely on the evaluator to prefer checks.
        pass
    
    # Evaluate all legal moves
    best_score = -float('inf')
    best_move = legal_moves[0]
    for move in legal_moves:
        new_board = make_move(pieces, move)
        score = evaluate(new_board)
        
        # Penalize moves that lead to immediate repetition if we are winning
        board_key_new = ''.join(sorted([sq + p for sq, p in new_board.items()]))
        rep_count = memory["repetition_map"].get(board_key_new, 0)
        if rep_count >= 2 and score > 0:
            score -= 100
        
        # Bonus for checks
        # Quick check: does move attack opponent's king?
        their_king_sq = None
        for sq, pc in new_board.items():
            if pc == them + 'K':
                their_king_sq = sq
                break
        if their_king_sq:
            # See if any of our pieces attack that square
            attacks = pseudo_moves_for_color(new_board, us)
            king_pos = (ord(their_king_sq[0])-ord('a'), int(their_king_sq[1])-1)
            if king_pos in attacks:
                score += 50  # check bonus
        
        # Bonus for captures
        if 'x' in move:
            score += 30
        
        # Bonus for promotion
        if '=' in move:
            score += 800 if '=Q' in move else 400
        
        if score > best_score:
            best_score = score
            best_move = move
    
    return best_move, memory
