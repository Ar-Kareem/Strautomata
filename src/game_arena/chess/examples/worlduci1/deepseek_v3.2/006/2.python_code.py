
import numpy as np
import time

PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (midgame) from simplified PeSTO
PAWN_TABLE = [
    0,   0,   0,   0,   0,   0,  0,   0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,   5, 10, 25, 25, 10,  5,  5,
    0,   0,  0, 20, 20,  0,  0,  0,
    5,  -5,-10,  0,  0,-10, -5,  5,
    5,  10, 10,-20,-20, 10, 10,  5,
    0,   0,  0,  0,  0,  0,  0,  0
]

KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]

BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]

ROOK_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    0,  0,  0,  5,  5,  0,  0,  0
]

QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -5,  0,  5,  5,  5,  5,  0, -5,
    0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

KING_TABLE_MID = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
    20, 20,  0,  0,  0,  0, 20, 20,
    20, 30, 10,  0,  0, 10, 30, 20
]

KING_TABLE_END = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

def square_to_index(sq):
    file_ord = ord(sq[0]) - ord('a')
    rank = int(sq[1]) - 1
    return rank * 8 + file_ord

def index_to_square(idx):
    rank = idx // 8
    file_ = idx % 8
    return chr(ord('a') + file_) + str(rank + 1)

class Board:
    def __init__(self, pieces, to_play):
        self.board = [None] * 64
        self.turn = 0 if to_play == 'white' else 1
        for sq, piece in pieces.items():
            idx = square_to_index(sq)
            self.board[idx] = piece
        self.history = []
        self.calc_material()

    def copy(self):
        b = Board.__new__(Board)
        b.board = self.board[:]
        b.turn = self.turn
        b.history = []
        return b

    def calc_material(self):
        self.material = {0: 0, 1: 0}
        for p in self.board:
            if p is not None:
                col = 0 if p[0] == 'w' else 1
                piece_type = p[1]
                self.material[col] += PIECE_VALUES[piece_type]

    def is_endgame(self):
        total_material = self.material[0] + self.material[1]
        return total_material < 2500

    def piece_at(self, idx):
        return self.board[idx]

    def get_king_pos(self, color):
        for i in range(64):
            p = self.board[i]
            if p is not None and p[0] == ('w' if color == 0 else 'b') and p[1] == 'K':
                return i
        return -1

    def generate_moves(self):
        moves = []
        for i in range(64):
            p = self.board[i]
            if p is not None and p[0] == ('w' if self.turn == 0 else 'b'):
                self._moves_for_piece(i, moves)
        legal_moves = []
        for m in moves:
            bcopy = self.copy()
            bcopy.make_move(m)
            if not bcopy.is_in_check(self.turn):
                legal_moves.append(m)
        return legal_moves

    def _moves_for_piece(self, idx, moves):
        p = self.board[idx]
        piece_type = p[1]
        if piece_type == 'P':
            self._pawn_moves(idx, moves)
        elif piece_type == 'N':
            self._knight_moves(idx, moves)
        elif piece_type == 'B':
            self._bishop_moves(idx, moves)
        elif piece_type == 'R':
            self._rook_moves(idx, moves)
        elif piece_type == 'Q':
            self._bishop_moves(idx, moves)
            self._rook_moves(idx, moves)
        elif piece_type == 'K':
            self._king_moves(idx, moves)

    def _add_move_if_valid(self, moves, from_idx, to_idx, promote=None):
        target = self.board[to_idx]
        if target is None or target[0] != ('w' if self.turn == 0 else 'b'):
            if promote is not None:
                moves.append((from_idx, to_idx, promote))
            else:
                moves.append((from_idx, to_idx, None))

    def _pawn_moves(self, idx, moves):
        color = 0 if self.board[idx][0] == 'w' else 1
        dir = 1 if color == 0 else -1
        rank = idx // 8
        file_ = idx % 8
        start_rank = 1 if color == 0 else 6
        # move forward
        nxt = idx + dir * 8
        if 0 <= nxt < 64 and self.board[nxt] is None:
            if (color == 0 and rank == 6) or (color == 1 and rank == 1):
                for prom in ['Q', 'R', 'B', 'N']:
                    self._add_move_if_valid(moves, idx, nxt, prom)
            else:
                self._add_move_if_valid(moves, idx, nxt)
                # two steps from start rank
                if rank == start_rank:
                    nxt2 = idx + dir * 16
                    if 0 <= nxt2 < 64 and self.board[nxt2] is None:
                        self._add_move_if_valid(moves, idx, nxt2)
        # captures
        for dx in (-1, 1):
            cap = idx + dir * 8 + dx
            if 0 <= cap < 64 and abs((cap % 8) - file_) == 1:
                target = self.board[cap]
                if target is not None and target[0] != ('w' if color == 0 else 'b'):
                    if (color == 0 and rank == 6) or (color == 1 and rank == 1):
                        for prom in ['Q', 'R', 'B', 'N']:
                            self._add_move_if_valid(moves, idx, cap, prom)
                    else:
                        self._add_move_if_valid(moves, idx, cap)

    def _knight_moves(self, idx, moves):
        rank, file_ = divmod(idx, 8)
        offsets = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
        for dr, df in offsets:
            r2, f2 = rank + dr, file_ + df
            if 0 <= r2 < 8 and 0 <= f2 < 8:
                self._add_move_if_valid(moves, idx, r2*8 + f2)

    def _bishop_moves(self, idx, moves):
        dirs = [(1,1),(1,-1),(-1,1),(-1,-1)]
        self._slide_moves(idx, dirs, moves)

    def _rook_moves(self, idx, moves):
        dirs = [(1,0),(0,1),(-1,0),(0,-1)]
        self._slide_moves(idx, dirs, moves)

    def _slide_moves(self, idx, dirs, moves):
        rank, file_ = divmod(idx, 8)
        color = self.board[idx][0]
        for dr, df in dirs:
            r, f = rank + dr, file_ + df
            while 0 <= r < 8 and 0 <= f < 8:
                to_idx = r*8 + f
                target = self.board[to_idx]
                if target is None:
                    self._add_move_if_valid(moves, idx, to_idx)
                else:
                    if target[0] != color:
                        self._add_move_if_valid(moves, idx, to_idx)
                    break
                r += dr
                f += df

    def _king_moves(self, idx, moves):
        rank, file_ = divmod(idx, 8)
        for dr in (-1,0,1):
            for df in (-1,0,1):
                if dr == 0 and df == 0:
                    continue
                r2, f2 = rank + dr, file_ + df
                if 0 <= r2 < 8 and 0 <= f2 < 8:
                    self._add_move_if_valid(moves, idx, r2*8 + f2)

    def make_move(self, move):
        from_idx, to_idx, promote = move
        piece = self.board[from_idx]
        captured = self.board[to_idx]
        self.history.append((from_idx, to_idx, piece, captured, promote))
        self.board[to_idx] = piece
        self.board[from_idx] = None
        if promote is not None:
            color = piece[0]
            self.board[to_idx] = color + promote
        self.turn ^= 1
        self.calc_material()

    def undo_move(self):
        from_idx, to_idx, piece, captured, promote = self.history.pop()
        self.board[from_idx] = piece
        self.board[to_idx] = captured
        self.turn ^= 1
        self.calc_material()

    def is_in_check(self, color):
        king_pos = self.get_king_pos(color)
        if king_pos == -1:
            return False
        opponent = 1 - color
        # check pawns
        dir = -1 if color == 0 else 1
        for dx in (-1, 1):
            cap = king_pos + dir * 8 + dx
            if 0 <= cap < 64:
                target = self.board[cap]
                if target is not None and target[0] == ('w' if opponent == 0 else 'b') and target[1] == 'P':
                    return True
        # knights
        offsets = [(2,1),(1,2),(-1,2),(-2,1),(-2,-1),(-1,-2),(1,-2),(2,-1)]
        rank, file_ = divmod(king_pos, 8)
        for dr, df in offsets:
            r2, f2 = rank + dr, file_ + df
            if 0 <= r2 < 8 and 0 <= f2 < 8:
                target = self.board[r2*8 + f2]
                if target is not None and target[0] == ('w' if opponent == 0 else 'b') and target[1] == 'N':
                    return True
        # sliding pieces
        dirs = [(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]
        for dr, df in dirs:
            r, f = rank + dr, file_ + df
            while 0 <= r < 8 and 0 <= f < 8:
                to_idx = r*8 + f
                target = self.board[to_idx]
                if target is not None:
                    if target[0] == ('w' if opponent == 0 else 'b'):
                        piece_type = target[1]
                        if dr == 0 or df == 0:  # rook/queen dir
                            if piece_type in ('R', 'Q'):
                                return True
                        else:  # bishop/queen dir
                            if piece_type in ('B', 'Q'):
                                return True
                        # king (one step)
                        if piece_type == 'K' and abs(r - rank) <= 1 and abs(f - file_) <= 1:
                            return True
                    break
                r += dr
                f += df
        return False

    def evaluate(self):
        score = 0
        endgame = self.is_endgame()
        for i in range(64):
            p = self.board[i]
            if p is not None:
                col = 0 if p[0] == 'w' else 1
                piece_type = p[1]
                mult = 1 if col == 0 else -1
                score += mult * PIECE_VALUES[piece_type]
                # piece-square tables
                table_idx = i if col == 0 else 63 - i
                if piece_type == 'P':
                    score += mult * PAWN_TABLE[table_idx]
                elif piece_type == 'N':
                    score += mult * KNIGHT_TABLE[table_idx]
                elif piece_type == 'B':
                    score += mult * BISHOP_TABLE[table_idx]
                elif piece_type == 'R':
                    score += mult * ROOK_TABLE[table_idx]
                elif piece_type == 'Q':
                    score += mult * QUEEN_TABLE[table_idx]
                elif piece_type == 'K':
                    if endgame:
                        score += mult * KING_TABLE_END[table_idx]
                    else:
                        score += mult * KING_TABLE_MID[table_idx]
        # mobility
        mob_score = 0
        my_moves = len(self.generate_moves())
        self.turn ^= 1
        opp_moves = len(self.generate_moves())
        self.turn ^= 1
        mob_score = (my_moves - opp_moves) * 2
        score += mob_score
        return score if self.turn == 0 else -score

def move_to_uci(move):
    from_idx, to_idx, promote = move
    uci = index_to_square(from_idx) + index_to_square(to_idx)
    if promote is not None:
        uci += promote.lower()
    return uci

def uci_to_move(uci, board):
    from_sq = uci[:2]
    to_sq = uci[2:4]
    from_idx = square_to_index(from_sq)
    to_idx = square_to_index(to_sq)
    promote = None
    if len(uci) == 5:
        promote = uci[4].upper()
    return (from_idx, to_idx, promote)

def order_moves(moves, board, tt_move=None):
    scored = []
    for m in moves:
        score = 0
        if m == tt_move:
            score += 10000
        target = board.board[m[1]]
        if target is not None:
            score += 10 * PIECE_VALUES[target[1]] - PIECE_VALUES[board.board[m[0]][1]]
        scored.append((score, m))
    scored.sort(reverse=True)
    return [m for _, m in scored]

def quiescence(board, alpha, beta, color):
    stand_pat = board.evaluate()
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat
    captures = []
    for m in board.generate_moves():
        from_idx, to_idx, _ = m
        if board.board[to_idx] is not None:
            captures.append(m)
    for m in order_moves(captures, board):
        board.make_move(m)
        score = -quiescence(board, -beta, -alpha, -color)
        board.undo_move()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def negamax(board, depth, alpha, beta, color, start_time, time_limit, move_history):
    if depth == 0:
        return quiescence(board, alpha, beta, color)
    moves = board.generate_moves()
    if not moves:
        if board.is_in_check(board.turn):
            return -100000 + (50 - len(move_history))
        else:
            return 0
    if time.time() - start_time > time_limit:
        return 0
    best_move = None
    for m in order_moves(moves, board):
        board.make_move(m)
        move_history.append(m)
        score = -negamax(board, depth - 1, -beta, -alpha, -color, start_time, time_limit, move_history)
        move_history.pop()
        board.undo_move()
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
            best_move = m
    return alpha

def policy(pieces, to_play):
    board = Board(pieces, to_play)
    moves = board.generate_moves()
    if not moves:
        return ''
    # Quick mate check
    for m in moves:
        board.make_move(m)
        opp_moves = board.generate_moves()
        board.undo_move()
        if not opp_moves and board.is_in_check(board.turn ^ 1):
            return move_to_uci(m)
    start_time = time.time()
    time_limit = 0.8
    best_move = moves[0]
    best_score = -float('inf')
    for depth in range(1, 5):
        if time.time() - start_time > time_limit:
            break
        alpha = -float('inf')
        beta = float('inf')
        for m in order_moves(moves, board):
            board.make_move(m)
            score = -negamax(board, depth - 1, -beta, -alpha, -1, start_time, time_limit, [m])
            board.undo_move()
            if score > best_score:
                best_score = score
                best_move = m
            alpha = max(alpha, score)
    return move_to_uci(best_move)
