
import numpy as np

def policy(pieces, to_play, memory):
    # Convert pieces to board representation
    board = [[None for _ in range(8)] for _ in range(8)]
    for square, piece in pieces.items():
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        board[rank][file] = piece

    current_player = 'w' if to_play == 'white' else 'b'
    opponent = 'b' if current_player == 'w' else 'w'
    
    # Piece values
    piece_values = {'P': 1, 'N': 3, 'B': 3, 'R': 5, 'Q': 9, 'K': 0}
    
    # Simple piece-square tables (centralization bonuses)
    pawn_table = np.array([
        [0, 0, 0, 0, 0, 0, 0, 0],
        [50,50,50,50,50,50,50,50],
        [10,10,20,30,30,20,10,10],
        [5, 5,10,25,25,10, 5, 5],
        [0, 0, 0,20,20, 0, 0, 0],
        [5,-5,-10,0,0,-10,-5,5],
        [5,10,10,-20,-20,10,10,5],
        [0, 0, 0, 0, 0, 0, 0, 0]
    ])
    
    knight_table = np.array([
        [-50,-40,-30,-30,-30,-30,-40,-50],
        [-40,-20,  0,  0,  0,  0,-20,-40],
        [-30,  0, 10, 15, 15, 10,  0,-30],
        [-30,  5, 15, 20, 20, 15,  5,-30],
        [-30,  0, 15, 20, 20, 15,  0,-30],
        [-30,  5, 10, 15, 15, 10,  5,-30],
        [-40,-20,  0,  5,  5,  0,-20,-40],
        [-50,-40,-30,-30,-30,-30,-40,-50]
    ])
    
    king_table = np.array([
        [20,30,10, 0, 0,10,30,20],
        [20,20, 0, 0, 0, 0,20,20],
        [-10,-20,-20,-20,-20,-20,-20,-10],
        [-20,-30,-30,-40,-40,-30,-30,-20],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30],
        [-30,-40,-40,-50,-50,-40,-40,-30]
    ])
    
    def to_coords(square):
        file = ord(square[0]) - ord('a')
        rank = int(square[1]) - 1
        return (rank, file)
        
    def from_coords(rank, file):
        return chr(file + ord('a')) + str(rank + 1)
    
    # Generate pseudo-legal moves
    def generate_moves(board, player):
        moves = []
        for rank in range(8):
            for file in range(8):
                piece = board[rank][file]
                if piece and piece[0] == player:
                    piece_type = piece[1]
                    if piece_type == 'P':
                        # Pawn moves
                        direction = 1 if player == 'w' else -1
                        start_rank = 1 if player == 'w' else 6
                        # Forward moves
                        if 0 <= rank + direction < 8 and not board[rank + direction][file]:
                            moves.append(from_coords(rank, file) + from_coords(rank + direction, file))
                            if rank == start_rank and not board[rank + 2*direction][file]:
                                moves.append(from_coords(rank, file) + from_coords(rank + 2*direction, file))
                        # Captures
                        for df in [-1, 1]:
                            if 0 <= file + df < 8 and 0 <= rank + direction < 8:
                                target = board[rank + direction][file + df]
                                if target and target[0] != player:
                                    moves.append(from_coords(rank, file) + from_coords(rank + direction, file + df))
                    elif piece_type == 'N':
                        # Knight moves
                        for dr, df in [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]:
                            nr, nf = rank + dr, file + df
                            if 0 <= nr < 8 and 0 <= nf < 8:
                                target = board[nr][nf]
                                if not target or target[0] != player:
                                    moves.append(from_coords(rank, file) + from_coords(nr, nf))
                    elif piece_type == 'K':
                        # King moves
                        for dr in [-1,0,1]:
                            for df in [-1,0,1]:
                                if dr == 0 and df == 0:
                                    continue
                                nr, nf = rank + dr, file + df
                                if 0 <= nr < 8 and 0 <= nf < 8:
                                    target = board[nr][nf]
                                    if not target or target[0] != player:
                                        moves.append(from_coords(rank, file) + from_coords(nr, nf))
                    else:
                        # Directions for Q/R/B
                        directions = []
                        if piece_type in ['Q', 'R']:
                            directions += [(0,1), (1,0), (0,-1), (-1,0)]
                        if piece_type in ['Q', 'B']:
                            directions += [(1,1), (1,-1), (-1,1), (-1,-1)]
                        for dr, df in directions:
                            r, f = rank + dr, file + df
                            while 0 <= r < 8 and 0 <= f < 8:
                                target = board[r][f]
                                if not target or target[0] != player:
                                    moves.append(from_coords(rank, file) + from_coords(r, f))
                                    if target and target[0] != player:
                                        break
                                else:
                                    break
                                r += dr
                                f += df
        return moves
    
    # Remove moves that leave king in check
    def is_in_check(board, player):
        # Find king
        king_pos = None
        for rank in range(8):
            for file in range(8):
                piece = board[rank][file]
                if piece and piece[0] == player and piece[1] == 'K':
                    king_pos = (rank, file)
                    break
            if king_pos:
                break
        if not king_pos:
            return False
        
        # Check if attacked
        opponent = 'b' if player == 'w' else 'w'
        for rank in range(8):
            for file in range(8):
                piece = board[rank][file]
                if piece and piece[0] == opponent:
                    moves = generate_moves(board, opponent)
                    for move in moves:
                        _, dest = to_coords(move[0:2]), to_coords(move[2:4])
                        if dest == king_pos:
                            return True
        return False
    
    def legal_moves(board, player):
        pseudo_moves = generate_moves(board, player)
        legal = []
        for move in pseudo_moves:
            # Make move on copy
            b_copy = [row[:] for row in board]
            src, dest = to_coords(move[0:2]), to_coords(move[2:4])
            piece = b_copy[src[0]][src[1]]
            b_copy[dest[0]][dest[1]] = piece
            b_copy[src[0]][src[1]] = None
            
            if not is_in_check(b_copy, player):
                legal.append(move)
        return legal
    
    def evaluate_move(move, board):
        src, dest = to_coords(move[0:2]), to_coords(move[2:4])
        piece = board[src[0]][src[1]]
        piece_type = piece[1]
        
        # Material gain
        captured_piece = board[dest[0]][dest[1]]
        material = piece_values[captured_piece[1]] if captured_piece else 0
        
        # Positional bonus
        positional = 0
        if piece_type == 'P':
            if piece[0] == 'w':
                positional = pawn_table[dest[0]][dest[1]]
            else:
                positional = pawn_table[7 - dest[0]][dest[1]]
        elif piece_type == 'N':
            positional = knight_table[dest[0]][dest[1]]
        elif piece_type == 'K':
            positional = king_table[dest[0]][dest[1]] if (dest[0] <= 1 or dest[0] >= 6) else 0
        
        # Penalize moving to attacked squares
        safety = 0
        for rank in range(8):
            for file in range(8):
                p = board[rank][file]
                if p and p[0] != current_player:
                    # Simulate captures
                    if move[2:4] in generate_moves(board, p[0]):
                        safety -= piece_values[piece[1]] / 2
        
        return material * 100 + positional + safety
    
    # Get legal moves and evaluate
    moves = legal_moves(board, current_player)
    if not moves:
        return ("0000", memory)  # Shouldn't happen
    
    # Sort moves by immediate evaluation
    scored = []
    for move in moves:
        score = evaluate_move(move, board)
        # Bonus for checks
        b_copy = [row[:] for row in board]
        src, dest = to_coords(move[0:2]), to_coords(move[2:4])
        piece = b_copy[src[0]][src[1]]
        b_copy[dest[0]][dest[1]] = piece
        b_copy[src[0]][src[1]] = None
        if is_in_check(b_copy, opponent):
            score += 50
        scored.append((score, move))
    
    # Return move with highest score
    scored.sort(reverse=True, key=lambda x: x[0])
    best_move = scored[0][1]
    return (best_move, memory)
