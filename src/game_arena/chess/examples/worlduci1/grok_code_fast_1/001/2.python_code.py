
import random
import copy
from typing import Dict, List, Tuple

# Constants
PIECE_VALUES = {'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000}
PIECE_TYPES = {'K': 'K', 'Q': 'Q', 'R': 'R', 'B': 'B', 'N': 'N', 'P': 'P'}
DIRECTIONS = {'R': [(-1, 0), (1, 0), (0, -1), (0, 1)], 'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)], 'Q': [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (-1, 1), (1, -1), (1, 1)]}
KNIGHT_MOVES = [(-2, -1), (-2, 1), (2, -1), (2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2)]

# Piece-square tables (simplified, symmetric for black by flipping)
PST = {
    'P': [0,  0,  0,  0,  0,  0,  0,  0,
         50, 50, 50, 50, 50, 50, 50, 50,
         10, 10, 20, 30, 30, 20, 10, 10,
          5,  5, 10, 25, 25, 10,  5,  5,
          0,  0,  0, 20, 20,  0,  0,  0,
          5, -5,-10,  0,  0,-10, -5,  5,
          5, 10, 10,-20,-20, 10, 10,  5,
          0,  0,  0,  0,  0,  0,  0,  0],
    'N': [-50,-40,-30,-30,-30,-30,-40,-50,
         -40,-20,  0,  0,  0,  0,-20,-40,
         -30,  0, 10, 15, 15, 10,  0,-30,
         -30,  5, 15, 20, 20, 15,  5,-30,
         -30,  0, 15, 20, 20, 15,  0,-30,
         -30,  5, 10, 15, 15, 10,  5,-30,
         -40,-20,  0,  5,  5,  0,-20,-40,
         -50,-40,-30,-30,-30,-30,-40,-50],
    'B': [-20,-10,-10,-10,-10,-10,-10,-20,
         -10,  0,  0,  0,  0,  0,  0,-10,
         -10,  0,  5, 10, 10,  5,  0,-10,
         -10,  5,  5, 10, 10,  5,  5,-10,
         -10,  0, 10, 10, 10, 10,  0,-10,
         -10, 10, 10, 10, 10, 10, 10,-10,
         -10,  5,  0,  0,  0,  0,  5,-10,
         -20,-10,-10,-10,-10,-10,-10,-20],
    'R': [0,  0,  0,  0,  0,  0,  0,  0,
          5, 10, 10, 10, 10, 10, 10,  5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
         -5,  0,  0,  0,  0,  0,  0, -5,
          0,  0,  0,  5,  5,  0,  0,  0],
    'Q': [-20,-10,-10, -5, -5,-10,-10,-20,
         -10,  0,  0,  0,  0,  0,  0,-10,
         -10,  0,  5,  5,  5,  5,  0,-10,
          -5,  0,  5,  5,  5,  5,  0, -5,
          -5,  0,  5,  5,  5,  5,  0, -5,
         -10,  5,  5,  5,  5,  5,  0,-10,
         -10,  0,  5,  0,  0,  0,  0,-10,
         -20,-10,-10, -5, -5,-10,-10,-20],
    'K': [-30,-40,-40,-50,-50,-40,-40,-30,
         -30,-40,-40,-50,-50,-40,-40,-30,
         -30,-40,-40,-50,-50,-40,-40,-30,
         -30,-40,-40,-50,-50,-40,-40,-30,
         -20,-30,-30,-40,-40,-30,-30,-20,
         -10,-20,-20,-20,-20,-20,-20,-10,
          20, 20,  0,  0,  0,  0, 20, 20,
          20, 30, 10,  0,  0, 10, 30, 20]
}

def to_index(square: str) -> int:
    file, rank = square
    return (ord(file) - ord('a')) + (int(rank) - 1) * 8

def to_square(index: int) -> str:
    file = chr(ord('a') + index % 8)
    rank = str(index // 8 + 1)
    return file + rank

def make_board(pieces: Dict[str, str]) -> List[List[str]]:
    board = [[''] * 8 for _ in range(8)]
    for sq, piece in pieces.items():
        idx = to_index(sq)
        board[idx // 8][idx % 8] = piece
    return board

def is_in_check(board: List[List[str]], color: str) -> bool:
    king_pos = None
    enemy_color = 'b' if color == 'w' else 'w'
    for i in range(8):
        for j in range(8):
            if board[i][j] == f'{color}K':
                king_pos = (i, j)
                break
        if king_pos:
            break
    if not king_pos:
        return False
    return is_under_attack(board, king_pos, enemy_color)

def is_under_attack(board: List[List[str]], pos: Tuple[int, int], attacker_color: str) -> bool:
    # Check knights
    for dx, dy in KNIGHT_MOVES:
        nx, ny = pos[0] + dx, pos[1] + dy
        if 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == f'{attacker_color}N':
            return True
    # Check sliding pieces
    for piece in ['Q', 'R', 'B']:
        for dx, dy in DIRECTIONS[piece]:
            x, y = pos[0] + dx, pos[1] + dy
            while 0 <= x < 8 and 0 <= y < 8:
                if board[x][y]:
                    if board[x][y][0] == attacker_color and board[x][y][1] == piece:
                        return True
                    break
                x += dx
                y += dy
    # Check pawns
    pawn_dir = -1 if attacker_color == 'w' else 1
    for dy in [-1, 1]:
        nx, ny = pos[0] + pawn_dir, pos[1] + dy
        if 0 <= nx < 8 and 0 <= ny < 8 and board[nx][ny] == f'{attacker_color}P':
            return True
    return False

def generate_moves(board: List[List[str]], color: str) -> List[str]:
    moves = []
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece and piece[0] == color:
                piece_type = piece[1]
                if piece_type == 'P':
                    moves.extend(generate_pawn_moves(board, i, j, color))
                elif piece_type == 'N':
                    moves.extend(generate_knight_moves(board, i, j, color))
                elif piece_type == 'B':
                    moves.extend(generate_sliding_moves(board, i, j, color, 'B'))
                elif piece_type == 'R':
                    moves.extend(generate_sliding_moves(board, i, j, color, 'R'))
                elif piece_type == 'Q':
                    moves.extend(generate_sliding_moves(board, i, j, color, 'Q'))
                elif piece_type == 'K':
                    moves.extend(generate_king_moves(board, i, j, color))
    return moves

def generate_pawn_moves(board: List[List[str]], i: int, j: int, color: str) -> List[str]:
    moves = []
    dir = -1 if color == 'w' else 1
    # Move forward
    if not board[i + dir][j]:
        moves.append(to_uci((i, j), (i + dir, j), color, 'P'))
        # Double move from rank 2/7
        if (color == 'w' and i == 6) or (color == 'b' and i == 1):
            if not board[i + 2 * dir][j]:
                moves.append(to_uci((i, j), (i + 2 * dir, j), color, 'P'))
    # Captures
    for dj in [-1, 1]:
        ni, nj = i + dir, j + dj
        if 0 <= ni < 8 and 0 <= nj < 8 and board[ni][nj] and board[ni][nj][0] != color:
            moves.append(to_uci((i, j), (ni, nj), color, 'P'))
    return moves

def generate_knight_moves(board: List[List[str]], i: int, j: int, color: str) -> List[str]:
    moves = []
    for dx, dy in KNIGHT_MOVES:
        ni, nj = i + dx, j + dy
        if 0 <= ni < 8 and 0 <= nj < 8 and (not board[ni][nj] or board[ni][nj][0] != color):
            moves.append(to_uci((i, j), (ni, nj), color, 'N'))
    return moves

def generate_sliding_moves(board: List[List[str]], i: int, j: int, color: str, piece: str) -> List[str]:
    moves = []
    for dx, dy in DIRECTIONS[piece]:
        x, y = i + dx, j + dy
        while 0 <= x < 8 and 0 <= y < 8:
            if not board[x][y]:
                moves.append(to_uci((i, j), (x, y), color, piece))
            elif board[x][y][0] != color:
                moves.append(to_uci((i, j), (x, y), color, piece))
                break
            else:
                break
            x += dx
            y += dy
    return moves

def generate_king_moves(board: List[List[str]], i: int, j: int, color: str) -> List[str]:
    moves = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            ni, nj = i + dx, j + dy
            if 0 <= ni < 8 and 0 <= nj < 8 and (not board[ni][nj] or board[ni][nj][0] != color):
                moves.append(to_uci((i, j), (ni, nj), color, 'K'))
    return moves  # Note: No castling in this simplified version for speed

def to_uci(from_pos: Tuple[int, int], to_pos: Tuple[int, int], color: str, piece: str) -> str:
    prom = ''
    if piece == 'P' and ((color == 'w' and to_pos[0] == 0) or (color == 'b' and to_pos[0] == 7)):
        prom = 'q'  # Default promotion
    return to_square(from_pos[0] * 8 + from_pos[1]) + to_square(to_pos[0] * 8 + to_pos[1]) + prom

def filter_legal_moves(board: List[List[str]], moves: List[str], color: str) -> List[str]:
    legal = []
    for move in moves:
        board_copy = copy.deepcopy(board)
        make_move(board_copy, move, color)
        if not is_in_check(board_copy, color):
            legal.append(move)
    return legal

def make_move(board: List[List[str]], move: str, color: str):
    from_sq = move[:2]
    to_sq = move[2:4]
    prom = move[4:] if len(move) > 4 else ''
    f_idx = to_index(from_sq)
    t_idx = to_index(to_sq)
    fi, fj = f_idx // 8, f_idx % 8
    ti, tj = t_idx // 8, t_idx % 8
    piece = board[fi][fj]
    new_piece = piece if not prom else f'{color}{prom.upper()}'
    board[fi][fj] = ''
    board[ti][tj] = new_piece

def evaluate(board: List[List[str]], color: str) -> int:
    score = 0
    for i in range(8):
        for j in range(8):
            piece = board[i][j]
            if piece:
                sign = 1 if piece[0] == color else -1
                ptype = piece[1]
                isz = i * 8 + j if piece[0] == 'w' else (7 - i) * 8 + j
                score += sign * (PIECE_VALUES[ptype] + PST[ptype][isz])
    return score

def quiescence(board: List[List[str]], depth: int, alpha: int, beta: int, color: str, max_depth: int = 3) -> int:
    if depth > max_depth:
        return evaluate(board, color)
    all_moves = generate_moves(board, color)
    legal_moves = filter_legal_moves(board, all_moves, color)
    captures = [m for m in legal_moves if len(m) == 4 and board[to_index(m[2:4]) // 8][to_index(m[2:4]) % 8]]
    if not captures:
        return evaluate(board, color)
    for move in captures:
        board_copy = copy.deepcopy(board)
        make_move(board_copy, move, color)
        if not is_in_check(board_copy, color):
            score = -quiescence(board_copy, depth + 1, -beta, -alpha, 'b' if color == 'w' else 'w', max_depth)
            if score >= beta:
                return beta
            alpha = max(alpha, score)
    return alpha

def minimax(board: List[List[str]], depth: int, alpha: int, beta: int, color: str, max_depth: int = 3) -> Tuple[int, str]:
    if depth >= max_depth:
        return quiescence(board, 0, alpha, beta, color), None

    all_moves = generate_moves(board, color)
    legal_moves = filter_legal_moves(board, all_moves, color)
    if not legal_moves:
        return evaluate(board, color), None  # May be checkmate, but no handling

    best_move = random.choice(legal_moves)  # Fallback
    for move in legal_moves:
        board_copy = copy.deepcopy(board)
        make_move(board_copy, move, color)
        score, _ = minimax(board_copy, depth + 1, -beta, -alpha, 'b' if color == 'w' else 'w', max_depth)
        score = -score
        if score > alpha:
            alpha = score
            best_move = move
        if alpha >= beta:
            break
    return alpha, best_move

def policy(pieces: Dict[str, str], to_play: str) -> str:
    board = make_board(pieces)
    color = 'w' if to_play == 'white' else 'b'
    _, move = minimax(board, 0, float('-inf'), float('inf'), color)
    return move if move else random.choice(filter_legal_moves(board, generate_moves(board, color), color))
