
import time
import math
from typing import Dict, List, Tuple

# Piece values (midgame)
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
CENTER_BONUS = 30
SEMI_CENTER_BONUS = 15

# Precomputed move offsets
KNIGHT_MOVES = [(-2,-1), (-2,1), (-1,-2), (-1,2), (1,-2), (1,2), (2,-1), (2,1)]
KING_MOVES = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]

def sq_to_xy(sq: str) -> Tuple[int, int]:
    """Convert square string 'e4' to coordinates (4,3)"""
    return ord(sq[0]) - 97, int(sq[1]) - 1

def xy_to_sq(x: int, y: int) -> str:
    """Convert coordinates (4,3) to square string 'e4'"""
    return chr(97 + x) + str(y + 1)

def in_board(x: int, y: int) -> bool:
    """Check if coordinates are within board bounds"""
    return 0 <= x < 8 and 0 <= y < 8

def init_board(pieces: Dict[str, str]) -> List[List[str]]:
    """Initialize 8x8 board from pieces dictionary"""
    board = [['.' for _ in range(8)] for _ in range(8)]
    for sq, piece in pieces.items():
        x, y = sq_to_xy(sq)
        board[y][x] = piece
    return board

def copy_board(board: List[List[str]]) -> List[List[str]]:
    """Create a fast copy of the board"""
    return [row[:] for row in board]

def find_king(board: List[List[str]], color: str) -> str:
    """Find the king square for given color"""
    target = ('w' if color == 'white' else 'b') + 'K'
    for y in range(8):
        for x in range(8):
            if board[y][x] == target:
                return xy_to_sq(x, y)
    # Fallback (should never happen)
    return 'e1' if color == 'white' else 'e8'

def is_attacked(board: List[List[str]], sq: str, attacker_color: str) -> bool:
    """Check if a square is attacked by given color"""
    tx, ty = sq_to_xy(sq)
    
    # Knight attacks
    for dx, dy in KNIGHT_MOVES:
        x, y = tx + dx, ty + dy
        if in_board(x, y):
            p = board[y][x]
            if p != '.' and p[0] == attacker_color and p[1] == 'N':
                return True
    
    # King attacks
    for dx, dy in KING_MOVES:
        x, y = tx + dx, ty + dy
        if in_board(x, y):
            p = board[y][x]
            if p != '.' and p[0] == attacker_color and p[1] == 'K':
                return True
    
    # Pawn attacks
    direction = -1 if attacker_color == 'w' else 1
    for dx in (-1, 1):
        x, y = tx + dx, ty + direction
        if in_board(x, y):
            p = board[y][x]
            if p != '.' and p[0] == attacker_color and p[1] == 'P':
                return True
    
    # Sliding pieces (diagonals for B/Q)
    for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
        x, y = tx + dx, ty + dy
        while in_board(x, y):
            p = board[y][x]
            if p != '.':
                if p[0] == attacker_color and p[1] in ('B', 'Q'):
                    return True
                break
            x += dx
            y += dy
    
    # Sliding pieces (horizontal/vertical for R/Q)
    for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
        x, y = tx + dx, ty + dy
        while in_board(x, y):
            p = board[y][x]
            if p != '.':
                if p[0] == attacker_color and p[1] in ('R', 'Q'):
                    return True
                break
            x += dx
            y += dy
    
    return False

def in_check(board: List[List[str]], color: str) -> bool:
    """Check if the given color's king is in check"""
    king_sq = find_king(board, color)
    opp_color = 'b' if color == 'white' else 'w'
    return is_attacked(board, king_sq, opp_color)

def move_score(board: List[List[str]], move: str) -> int:
    """Score moves for ordering (captures first)"""
    to_sq = move[2:4]
    tx, ty = sq_to_xy(to_sq)
    target = board[ty][tx]
    return PIECE_VALUES.get(target[1], 0) if target != '.' else 0

def gen_pseudo_moves(board: List[List[str]], color: str, last_move: str) -> List[str]:
    """Generate pseudo-legal moves (may leave king in check)"""
    moves = []
    my_color = 'w' if color == 'white' else 'b'
    
    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece == '.' or piece[0] != my_color:
                continue
            
            from_sq = xy_to_sq(x, y)
            ptype = piece[1]
            
            if ptype == 'P':
                direction = 1 if my_color == 'w' else -1
                start_rank = 1 if my_color == 'w' else 6
                
                # Forward one square
                ty = y + direction
                if in_board(x, ty) and board[ty][x] == '.':
                    if ty == 0 or ty == 7:  # Promotion
                        for promo in ['q', 'r', 'b', 'n']:
                            moves.append(from_sq + xy_to_sq(x, ty) + promo)
                    else:
                        moves.append(from_sq + xy_to_sq(x, ty))
                        # Two squares from start
                        if y == start_rank:
                            ty2 = y + 2 * direction
                            if in_board(x, ty2) and board[ty2][x] == '.':
                                moves.append(from_sq + xy_to_sq(x, ty2))
                
                # Captures
                for dx in (-1, 1):
                    tx, ty = x + dx, y + direction
                    if in_board(tx, ty):
                        target = board[ty][tx]
                        if target != '.' and target[0] != my_color:
                            if ty == 0 or ty == 7:  # Promotion
                                for promo in ['q', 'r', 'b', 'n']:
                                    moves.append(from_sq + xy_to_sq(tx, ty) + promo)
                            else:
                                moves.append(from_sq + xy_to_sq(tx, ty))
                
                # En passant
                if last_move and len(last_move) == 4:
                    from_x, from_y = sq_to_xy(last_move[:2])
                    to_x, to_y = sq_to_xy(last_move[2:4])
                    if abs(from_y - to_y) == 2 and board[to_y][to_x] == ('b' if my_color == 'w' else 'w') + 'P':
                        if abs(to_x - x) == 1 and to_y == y:
                            cap_y = to_y + direction
                            if in_board(to_x, cap_y):
                                moves.append(from_sq + xy_to_sq(to_x, cap_y))
            
            elif ptype == 'N':
                for dx, dy in KNIGHT_MOVES:
                    tx, ty = x + dx, y + dy
                    if in_board(tx, ty):
                        target = board[ty][tx]
                        if target == '.' or target[0] != my_color:
                            moves.append(from_sq + xy_to_sq(tx, ty))
            
            elif ptype == 'B':
                for dx, dy in [(-1,-1), (-1,1), (1,-1), (1,1)]:
                    tx, ty = x + dx, y + dy
                    while in_board(tx, ty):
                        target = board[ty][tx]
                        if target == '.':
                            moves.append(from_sq + xy_to_sq(tx, ty))
                        else:
                            if target[0] != my_color:
                                moves.append(from_sq + xy_to_sq(tx, ty))
                            break
                        tx += dx
                        ty += dy
            
            elif ptype == 'R':
                for dx, dy in [(-1,0), (1,0), (0,-1), (0,1)]:
                    tx, ty = x + dx, y + dy
                    while in_board(tx, ty):
                        target = board[ty][tx]
                        if target == '.':
                            moves.append(from_sq + xy_to_sq(tx, ty))
                        else:
                            if target[0] != my_color:
                                moves.append(from_sq + xy_to_sq(tx, ty))
                            break
                        tx += dx
                        ty += dy
            
            elif ptype == 'Q':
                for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                    tx, ty = x + dx, y + dy
                    while in_board(tx, ty):
                        target = board[ty][tx]
                        if target == '.':
                            moves.append(from_sq + xy_to_sq(tx, ty))
                        else:
                            if target[0] != my_color:
                                moves.append(from_sq + xy_to_sq(tx, ty))
                            break
                        tx += dx
                        ty += dy
            
            elif ptype == 'K':
                for dx, dy in KING_MOVES:
                    tx, ty = x + dx, y + dy
                    if in_board(tx, ty):
                        target = board[ty][tx]
                        if target == '.' or target[0] != my_color:
                            moves.append(from_sq + xy_to_sq(tx, ty))
                
                # Castling (simplified - assumes rights exist if pieces on original squares)
                if my_color == 'w' and from_sq == 'e1' and not in_check(board, 'white'):
                    if board[0][5] == '.' and board[0][6] == '.' and board[0][7] == 'wR':
                        if not is_attacked(board, 'f1', 'b') and not is_attacked(board, 'g1', 'b'):
                            moves.append('e1g1')
                    if board[0][1] == '.' and board[0][2] == '.' and board[0][3] == '.' and board[0][0] == 'wR':
                        if not is_attacked(board, 'd1', 'b') and not is_attacked(board, 'c1', 'b'):
                            moves.append('e1c1')
                
                elif my_color == 'b' and from_sq == 'e8' and not in_check(board, 'black'):
                    if board[7][5] == '.' and board[7][6] == '.' and board[7][7] == 'bR':
                        if not is_attacked(board, 'f8', 'w') and not is_attacked(board, 'g8', 'w'):
                            moves.append('e8g8')
                    if board[7][1] == '.' and board[7][2] == '.' and board[7][3] == '.' and board[7][0] == 'bR':
                        if not is_attacked(board, 'd8', 'w') and not is_attacked(board, 'c8', 'w'):
                            moves.append('e8c8')
    
    return moves

def gen_legal_moves(board: List[List[str]], color: str, last_move: str) -> List[str]:
    """Generate only legal moves (pseudo-legal -> filter checks)"""
    pseudo = gen_pseudo_moves(board, color, last_move)
    legal = []
    
    # Sort by move score for better alpha-beta pruning
    pseudo.sort(key=lambda m: move_score(board, m), reverse=True)
    
    for move in pseudo:
        new_board = copy_board(board)
        from_sq, to_sq = move[:2], move[2:4]
        
        # Execute move
        if len(move) > 4:  # Promotion
            new_board[sq_to_xy(to_sq)[1]][sq_to_xy(to_sq)[0]] = new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]][0] + move[4].upper()
            new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]] = '.'
        else:
            # Normal move or capture
            new_board[sq_to_xy(to_sq)[1]][sq_to_xy(to_sq)[0]] = new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]]
            new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]] = '.'
        
        # Check if move leaves own king in check
        if not in_check(new_board, color):
            legal.append(move)
    
    return legal

def evaluate(board: List[List[str]], color: str) -> float:
    """Evaluate position from perspective of color"""
    score = 0
    
    # Material and center control
    for y in range(8):
        for x in range(8):
            piece = board[y][x]
            if piece == '.':
                continue
            
            ptype = piece[1]
            value = PIECE_VALUES[ptype]
            
            # Material count
            if piece[0] == 'w':
                score += value
            else:
                score -= value
            
            # Center control bonus
            if (x, y) in [(3,3), (3,4), (4,3), (4,4)]:
                mult = 1.5 if ptype in 'QBNR' else 1.0
                if piece[0] == 'w':
                    score += CENTER_BONUS * mult
                else:
                    score -= CENTER_BONUS * mult
    
    # Endgame: king activity
    piece_count = sum(1 for row in board for p in row if p != '.' and p[1] != 'K')
    if piece_count < 12:
        own_king = find_king(board, color)
        opp_king = find_king(board, 'black' if color == 'white' else 'white')
        kx, ky = sq_to_xy(own_king)
        okx, oky = sq_to_xy(opp_king)
        
        # Encourage own king to center, opponent king to edge
        own_dist = abs(3.5 - kx) + abs(3.5 - ky)
        opp_dist = abs(3.5 - okx) + abs(3.5 - oky)
        
        if color == 'white':
            score -= own_dist * 5
            score += opp_dist * 5
        else:
            score += own_dist * 5
            score -= opp_dist * 5
    
    return score if color == 'white' else -score

def get_search_depth(board: List[List[str]]) -> int:
    """Determine search depth based on remaining pieces"""
    piece_count = sum(1 for row in board for p in row if p != '.')
    if piece_count > 20:
        return 3  # Opening: shallow search
    elif piece_count > 12:
        return 4  # Middlegame: medium search
    return 5     # Endgame: deep search

def minimax(board: List[List[str]], color: str, depth: int, alpha: float, beta: float, last_move: str) -> Tuple[float, str]:
    """Alpha-beta minimax search"""
    if depth == 0:
        return evaluate(board, color), ""
    
    legal_moves = gen_legal_moves(board, color, last_move)
    
    if not legal_moves:
        # Checkmate or stalemate
        if in_check(board, color):
            return (-20000 if color == 'white' else 20000), ""
        return 0, ""
    
    best_move = legal_moves[0]
    
    if color == 'white':
        max_eval = -math.inf
        for move in legal_moves:
            new_board = copy_board(board)
            from_sq, to_sq = move[:2], move[2:4]
            
            # Execute move
            if len(move) > 4:  # Promotion
                new_board[sq_to_xy(to_sq)[1]][sq_to_xy(to_sq)[0]] = 'w' + move[4].upper()
                new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]] = '.'
            else:
                new_board[sq_to_xy(to_sq)[1]][sq_to_xy(to_sq)[0]] = new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]]
                new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]] = '.'
            
            eval, _ = minimax(new_board, 'black', depth-1, alpha, beta, move)
            
            if eval > max_eval:
                max_eval = eval
                best_move = move
            
            alpha = max(alpha, eval)
            if beta <= alpha:
                break
        
        return max_eval, best_move
    
    else:
        min_eval = math.inf
        for move in legal_moves:
            new_board = copy_board(board)
            from_sq, to_sq = move[:2], move[2:4]
            
            # Execute move
            if len(move) > 4:  # Promotion
                new_board[sq_to_xy(to_sq)[1]][sq_to_xy(to_sq)[0]] = 'b' + move[4].upper()
                new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]] = '.'
            else:
                new_board[sq_to_xy(to_sq)[1]][sq_to_xy(to_sq)[0]] = new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]]
                new_board[sq_to_xy(from_sq)[1]][sq_to_xy(from_sq)[0]] = '.'
            
            eval, _ = minimax(new_board, 'white', depth-1, alpha, beta, move)
            
            if eval < min_eval:
                min_eval = eval
                best_move = move
            
            beta = min(beta, eval)
            if beta <= alpha:
                break
        
        return min_eval, best_move

def select_move(board: List[List[str]], color: str, last_move: str, time_limit: float) -> str:
    """Select best move using iterative deepening"""
    start_time = time.time()
    legal_moves = gen_legal_moves(board, color, last_move)
    
    if not legal_moves:
        return ''  # Should not happen
    
    if len(legal_moves) == 1:
        return legal_moves[0]
    
    best_move = legal_moves[0]
    depth_limit = get_search_depth(board)
    
    for depth in range(1, depth_limit + 1):
        if time.time() - start_time > time_limit * 0.8:
            break
        
        _, move = minimax(board, color, depth, -math.inf, math.inf, last_move)
        if move:
            best_move = move
        
        # Stop early if checkmate found
        if _ == 20000 or _ == -20000:
            break
    
    return best_move

def policy(pieces: Dict[str, str], to_play: str, memory: Dict) -> Tuple[str, Dict]:
    """Main policy function - returns best move and updated memory"""
    board = init_board(pieces)
    last_move = memory.get('last_move', '')
    
    # Use slightly less than 1 second for safety
    time_limit = 0.95
    
    # Select the best move
    move = select_move(board, to_play, last_move, time_limit)
    
    # Update memory with last move
    memory['last_move'] = move
    return move, memory
