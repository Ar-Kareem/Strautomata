
import random

def policy(pieces, to_play):
    PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
    
    # Piece-Square Tables (simplified)
    PST = {
        'P': [
            0,  0,  0,  0,  0,  0,  0,  0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5,  5, 10, 25, 25, 10,  5,  5,
            0,  0,  0, 20, 20,  0,  0,  0,
            5, -5,-10,  0,  0,-10, -5,  5,
            5, 10, 10,-20,-20, 10, 10,  5,
            0,  0,  0,  0,  0,  0,  0,  0
        ],
        'N': [
            -50,-40,-30,-30,-30,-30,-40,-50,
            -40,-20,  0,  0,  0,  0,-20,-40,
            -30,  0, 10, 15, 15, 10,  0,-30,
            -30,  5, 15, 20, 20, 15,  5,-30,
            -30,  0, 15, 20, 20, 15,  0,-30,
            -30,  5, 10, 15, 15, 10,  5,-30,
            -40,-20,  0,  5,  5,  0,-20,-40,
            -50,-40,-30,-30,-30,-30,-40,-50
        ]
    }

    def get_legal_moves(board, color):
        moves = []
        c = 'w' if color == 'white' else 'b'
        enemy = 'b' if color == 'white' else 'w'
        
        for sq, pc in board.items():
            if pc[0] != c: continue
            f, r = ord(sq[0]) - 97, int(sq[1]) - 1
            pt = pc[1]
            
            if pt == 'P':
                direction = 1 if c == 'w' else -1
                # Forward
                target = f"{chr(f+97)}{r+direction+1}"
                if 0 <= r+direction < 8 and target not in board:
                    if r+direction in [0, 7]:
                        for p in 'qrbn': moves.append(sq + target + p)
                    else: moves.append(sq + target)
                    # Double push
                    if (r == 1 and c == 'w') or (r == 6 and c == 'b'):
                        target2 = f"{chr(f+97)}{r+2*direction+1}"
                        if target2 not in board: moves.append(sq + target2)
                # Captures
                for df in [-1, 1]:
                    if 0 <= f+df < 8:
                        target = f"{chr(f+df+97)}{r+direction+1}"
                        if target in board and board[target][0] == enemy:
                            if r+direction in [0, 7]:
                                for p in 'qrbn': moves.append(sq + target + p)
                            else: moves.append(sq + target)
            
            elif pt in ['N', 'K']:
                deltas = [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)] if pt == 'N' else \
                         [(1,1),(1,0),(1,-1),(0,1),(0,-1),(-1,1),(-1,0),(-1,-1)]
                for df, dr in deltas:
                    nf, nr = f+df, r+dr
                    if 0 <= nf < 8 and 0 <= nr < 8:
                        target = f"{chr(nf+97)}{nr+1}"
                        if target not in board or board[target][0] == enemy:
                            moves.append(sq + target)
            
            elif pt in ['R', 'B', 'Q']:
                dirs = []
                if pt in ['R', 'Q']: dirs += [(0,1),(0,-1),(1,0),(-1,0)]
                if pt in ['B', 'Q']: dirs += [(1,1),(1,-1),(-1,1),(-1,-1)]
                for df, dr in dirs:
                    for i in range(1, 8):
                        nf, nr = f+df*i, r+dr*i
                        if 0 <= nf < 8 and 0 <= nr < 8:
                            target = f"{chr(nf+97)}{nr+1}"
                            if target not in board: moves.append(sq + target)
                            elif board[target][0] == enemy:
                                moves.append(sq + target)
                                break
                            else: break
                        else: break
        return moves

    def evaluate(board):
        score = 0
        for sq, pc in board.items():
            color_mult = 1 if pc[0] == 'w' else -1
            pt = pc[1]
            score += color_mult * PIECE_VALUES.get(pt, 0)
            if pt in PST:
                idx = (ord(sq[0])-97) + (8*(int(sq[1])-1))
                if pc[0] == 'b': idx = 63 - idx
                score += color_mult * PST[pt][idx]
        return score if to_play == 'white' else -score

    def make_move(board, move):
        new_board = board.copy()
        start, end = move[:2], move[2:4]
        piece = new_board.pop(start)
        if len(move) == 5: # Promotion
            piece = piece[0] + move[4].upper()
        new_board[end] = piece
        # Handle Castling (King move of 2 squares)
        if piece[1] == 'K' and abs(ord(start[0]) - ord(end[0])) == 2:
            row = start[1]
            if end[0] == 'g': # Kingside
                new_board[f'f{row}'] = new_board.pop(f'h{row}')
            elif end[0] == 'c': # Queenside
                new_board[f'd{row}'] = new_board.pop(f'a{row}')
        return new_board

    legal_moves = get_legal_moves(pieces, to_play)
    if not legal_moves: return ""

    best_move = legal_moves[0]
    best_score = -999999
    
    # Simulating 1-ply search with a bit of randomness for variety
    random.shuffle(legal_moves)
    for move in legal_moves:
        temp_board = make_move(pieces, move)
        score = -evaluate(temp_board) # Simple heuristic
        # If capture, prioritize
        if move[2:4] in pieces:
            score += PIECE_VALUES.get(pieces[move[2:4]][1], 0)
        
        if score > best_score:
            best_score = score
            best_move = move
            
    return best_move
