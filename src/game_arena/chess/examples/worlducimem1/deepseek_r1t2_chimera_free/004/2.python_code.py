
import numpy as np

def square_to_pos(square):
    file = ord(square[0]) - ord('a')
    rank = int(square[1]) - 1
    return (file, rank)

def pos_to_square(pos):
    file, rank = pos
    return chr(file + ord('a')) + str(rank + 1)

def is_square_attacked(board, pos, by_color):
    x, y = pos
    # Check knights
    knight_moves = [(2,1), (1,2), (-1,2), (-2,1), (-2,-1), (-1,-2), (1,-2), (2,-1)]
    for dx, dy in knight_moves:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            piece = board[ny][nx]
            if piece and piece[0] == by_color and piece[1] == 'N':
                return True
    
    # Check diagonal and straight lines
    directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while 0 <= nx < 8 and 0 <= ny < 8:
            piece = board[ny][nx]
            if piece:
                if piece[0] == by_color:
                    piece_type = piece[1]
                    if (dx == 0 or dy == 0):  # Rook or Queen direction
                        if piece_type in ['R', 'Q']:
                            return True
                    else:  # Bishop or Queen direction
                        if piece_type in ['B', 'Q']:
                            return True
                    break  # Blocked by a piece
                else:
                    break  # Friendly piece blocks vision
            nx += dx
            ny += dy
    
    # Check pawn attacks
    if by_color == 'w':
        for dx in [-1, 1]:
            ax, ay = x + dx, y - 1
            if 0 <= ax < 8 and 0 <= ay < 8:
                piece = board[ay][ax]
                if piece == 'wP':
                    return True
    else:
        for dx in [-1, 1]:
            ax, ay = x + dx, y + 1
            if 0 <= ax < 8 and 0 <= ay < 8:
                piece = board[ay][ax]
                if piece == 'bP':
                    return True
    
    # Check king attacks
    king_moves = [(dx, dy) for dx in [-1,0,1] for dy in [-1,0,1] if (dx, dy) != (0,0)]
    for dx, dy in king_moves:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            piece = board[ny][nx]
            if piece and piece[0] == by_color and piece[1] == 'K':
                return True
                
    return False

def generate_pawn_moves(board, pos, color):
    moves = []
    x, y = pos
    direction = 1 if color == 'w' else -1
    start_rank = 1 if color == 'w' else 6
    
    # Forward moves
    if board[y + direction][x] is None:
        moves.append((x, y + direction))
        if y == start_rank and board[y + 2*direction][x] is None:
            moves.append((x, y + 2*direction))
    
    # Captures
    for dx in [-1, 1]:
        nx, ny = x + dx, y + direction
        if 0 <= nx < 8 and 0 <= ny < 8:
            target = board[ny][nx]
            if target and target[0] != color:
                moves.append((nx, ny))
    
    return moves

def generate_knight_moves(board, pos, color):
    moves = []
    x, y = pos
    deltas = [(2,1), (1,2), (-1,2), (-2,1), (-2,-1), (-1,-2), (1,-2), (2,-1)]
    for dx, dy in deltas:
        nx, ny = x + dx, y + dy
        if 0 <= nx < 8 and 0 <= ny < 8:
            target = board[ny][nx]
            if not target or target[0] != color:
                moves.append((nx, ny))
    return moves

def generate_sliding_moves(board, pos, color, directions):
    moves = []
    x, y = pos
    for dx, dy in directions:
        nx, ny = x + dx, y + dy
        while 0 <= nx < 8 and 0 <= ny < 8:
            target = board[ny][nx]
            if target:
                if target[0] != color:
                    moves.append((nx, ny))
                break  # Blocked by any piece
            moves.append((nx, ny))
            nx += dx
            ny += dy
    return moves

def generate_king_moves(board, pos, color):
    moves = []
    x, y = pos
    for dx in [-1,0,1]:
        for dy in [-1,0,1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if 0 <= nx < 8 and 0 <= ny < 8:
                target = board[ny][nx]
                if not target or target[0] != color:
                    moves.append((nx, ny))
    return moves

def policy(pieces, to_play, memory):
    current_color = 'w' if to_play == 'white' else 'b'
    opponent_color = 'b' if current_color == 'w' else 'w'
    
    # Initialize board from pieces dict
    board = [[None for _ in range(8)] for _ in range(8)]
    for square, piece in pieces.items():
        file, rank = square_to_pos(square)
        board[rank][file] = piece
    
    # Generate all possible moves
    all_moves = []
    for square, piece in pieces.items():
        if piece[0] != current_color:
            continue
        x, y = square_to_pos(square)
        piece_type = piece[1]
        
        if piece_type == 'P':
            moves = generate_pawn_moves(board, (x, y), current_color)
        elif piece_type == 'N':
            moves = generate_knight_moves(board, (x, y), current_color)
        elif piece_type == 'B':
            moves = generate_sliding_moves(board, (x, y), current_color, [(-1,-1), (-1,1), (1,-1), (1,1)])
        elif piece_type == 'R':
            moves = generate_sliding_moves(board, (x, y), current_color, [(0,-1), (0,1), (-1,0), (1,0)])
        elif piece_type == 'Q':
            moves = generate_sliding_moves(board, (x, y), current_color, 
                                         [(0,-1), (0,1), (-1,0), (1,0), (-1,-1), (-1,1), (1,-1), (1,1)])
        elif piece_type == 'K':
            moves = generate_king_moves(board, (x, y), current_color)
        else:
            continue
        
        for (nx, ny) in moves:
            from_sq = pos_to_square((x, y))
            to_sq = pos_to_square((nx, ny))
            move_str = from_sq + to_sq
            # Handle pawn promotion (simplified to queen)
            if piece_type == 'P' and (ny == 7 or ny == 0):
                move_str += 'q'
            all_moves.append(move_str)
    
    # Filter to only legal moves (king not in check)
    legal_moves = []
    for move in all_moves:
        # Make a copy of the board
        temp_board = [row[:] for row in board]
        from_sq = move[:2]
        to_sq = move[2:4]
        
        from_file, from_rank = square_to_pos(from_sq)
        to_file, to_rank = square_to_pos(to_sq)
        
        # Move the piece
        moving_piece = temp_board[from_rank][from_file]
        temp_board[from_rank][from_file] = None
        # Capture handling
        temp_board[to_rank][to_file] = moving_piece
        
        # Find the king's position
        king_pos = None
        for r in range(8):
            for f in range(8):
                p = temp_board[r][f]
                if p == current_color + 'K':
                    king_pos = (f, r)
                    break
            if king_pos:
                break
        
        # Check if king is under attack
        if not is_square_attacked(temp_board, king_pos, opponent_color):
            legal_moves.append(move)
    
    if not legal_moves:
        # If no legal moves (shouldn't happen but safe guard)
        return "a1a1", memory
    
    # Evaluate moves using material and position
    piece_values = {'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1, 'K': 0}
    best_move = None
    best_score = -10000
    for move in legal_moves:
        score = 0
        from_sq = move[:2]
        to_sq = move[2:4]
        
        # Capture
        to_x, to_y = square_to_pos(to_sq)
        captured_piece = board[to_y][to_x]
        if captured_piece and captured_piece[0] != current_color:
            score += piece_values.get(captured_piece[1], 0)
        
        # Promotion
        if len(move) == 5 and move[4] == 'q':
            score += 9
        
        # Center control for knights and bishops
        moving_piece_type = pieces[from_sq][1]
        if moving_piece_type in ['N', 'B']:
            center = {(3,3), (3,4), (4,3), (4,4)}
            if (to_x, to_y) in center:
                score += 1
        
        # Check if move gives check (not implemented due to complexity)
        
        if score > best_score:
            best_score = score
            best_move = move
        elif score == best_score:
            # Tiebreaker: Pick randomly (or prefer non-captures)
            if np.random.rand() > 0.5:
                best_move = move
    
    return best_move, memory
