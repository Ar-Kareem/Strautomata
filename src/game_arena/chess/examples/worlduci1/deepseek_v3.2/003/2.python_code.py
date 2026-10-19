
import copy
import time
from typing import Dict, List, Optional, Tuple

PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (from white's perspective, flipped for black)
PIECE_SQUARE_TABLES = {
    'P': [  # Pawn
         0,  0,  0,  0,  0,  0,  0,  0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
         5,  5, 10, 25, 25, 10,  5,  5,
         0,  0,  0, 20, 20,  0,  0,  0,
         5, -5,-10,  0,  0,-10, -5,  5,
         5, 10, 10,-20,-20, 10, 10,  5,
         0,  0,  0,  0,  0,  0,  0,  0
    ],
    'N': [  # Knight
        -50,-40,-30,-30,-30,-30,-40,-50,
        -40,-20,  0,  0,  0,  0,-20,-40,
        -30,  0, 10, 15, 15, 10,  0,-30,
        -30,  5, 15, 20, 20, 15,  5,-30,
        -30,  0, 15, 20, 20, 15,  0,-30,
        -30,  5, 10, 15, 15, 10,  5,-30,
        -40,-20,  0,  5,  5,  0,-20,-40,
        -50,-40,-30,-30,-30,-30,-40,-50
    ],
    'B': [  # Bishop
        -20,-10,-10,-10,-10,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5, 10, 10,  5,  0,-10,
        -10,  5,  5, 10, 10,  5,  5,-10,
        -10,  0, 10, 10, 10, 10,  0,-10,
        -10, 10, 10, 10, 10, 10, 10,-10,
        -10,  5,  0,  0,  0,  0,  5,-10,
        -20,-10,-10,-10,-10,-10,-10,-20
    ],
    'R': [  # Rook
         0,  0,  0,  0,  0,  0,  0,  0,
         5, 10, 10, 10, 10, 10, 10,  5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
        -5,  0,  0,  0,  0,  0,  0, -5,
         0,  0,  0,  5,  5,  0,  0,  0
    ],
    'Q': [  # Queen
        -20,-10,-10, -5, -5,-10,-10,-20,
        -10,  0,  0,  0,  0,  0,  0,-10,
        -10,  0,  5,  5,  5,  5,  0,-10,
         -5,  0,  5,  5,  5,  5,  0, -5,
          0,  0,  5,  5,  5,  5,  0, -5,
        -10,  5,  5,  5,  5,  5,  0,-10,
        -10,  0,  5,  0,  0,  0,  0,-10,
        -20,-10,-10, -5, -5,-10,-10,-20
    ],
    'K': [  # King (midgame)
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -30,-40,-40,-50,-50,-40,-40,-30,
        -20,-30,-30,-40,-40,-30,-30,-20,
        -10,-20,-20,-20,-20,-20,-20,-10,
         20, 20,  0,  0,  0,  0, 20, 20,
         20, 30, 10,  0,  0, 10, 30, 20
    ],
    'K_endgame': [  # King (endgame)
        -50,-40,-30,-20,-20,-30,-40,-50,
        -30,-20,-10,  0,  0,-10,-20,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 30, 40, 40, 30,-10,-30,
        -30,-10, 20, 30, 30, 20,-10,-30,
        -30,-30,  0,  0,  0,  0,-30,-30,
        -50,-30,-30,-30,-30,-30,-30,-50
    ]
}

def square_index(sq: str) -> int:
    """Convert algebraic square to index 0-63 (a8=0, h1=63)."""
    file = ord(sq[0]) - ord('a')
    rank = 8 - int(sq[1])
    return rank * 8 + file

class ChessState:
    def __init__(self, pieces: Dict[str, str], to_play: str):
        self.pieces = pieces.copy()
        self.to_play = to_play
        self._legal_moves_cache = None
        self._is_checkmate_cache = None
        self._is_stalemate_cache = None

    def copy(self):
        return ChessState(self.pieces, self.to_play)

    def get_legal_moves(self) -> List[str]:
        if self._legal_moves_cache is not None:
            return self._legal_moves_cache

        moves = []
        for sq, piece in self.pieces.items():
            if piece[0] != ('w' if self.to_play == 'white' else 'b'):
                continue
            piece_type = piece[1]
            moves.extend(self._moves_for_piece(sq, piece_type))
        self._legal_moves_cache = moves
        return moves

    def _moves_for_piece(self, sq: str, piece_type: str) -> List[str]:
        moves = []
        r, f = 8 - int(sq[1]), ord(sq[0]) - ord('a')
        directions = []
        if piece_type == 'P':
            pawn_dir = -1 if self.to_play == 'white' else 1
            start_rank = 6 if self.to_play == 'white' else 1
            # Single push
            new_r = r + pawn_dir
            if 0 <= new_r < 8:
                new_sq = chr(f + ord('a')) + str(8 - new_r)
                if new_sq not in self.pieces:
                    if new_r == 0 or new_r == 7:  # promotion
                        for prom in ['q', 'r', 'b', 'n']:
                            moves.append(sq + new_sq + prom)
                    else:
                        moves.append(sq + new_sq)
                    # Double push from starting rank
                    if r == start_rank:
                        new_r2 = r + 2*pawn_dir
                        new_sq2 = chr(f + ord('a')) + str(8 - new_r2)
                        if new_sq2 not in self.pieces and new_sq not in self.pieces:
                            moves.append(sq + new_sq2)
            # Captures
            for df in [-1, 1]:
                new_f = f + df
                new_r = r + pawn_dir
                if 0 <= new_f < 8 and 0 <= new_r < 8:
                    new_sq = chr(new_f + ord('a')) + str(8 - new_r)
                    target = self.pieces.get(new_sq)
                    if target and target[0] != ('w' if self.to_play == 'white' else 'b'):
                        if new_r == 0 or new_r == 7:  # promotion capture
                            for prom in ['q', 'r', 'b', 'n']:
                                moves.append(sq + new_sq + prom)
                        else:
                            moves.append(sq + new_sq)
        elif piece_type == 'N':
            knight_moves = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
            for dr, df in knight_moves:
                new_r, new_f = r+dr, f+df
                if 0 <= new_r < 8 and 0 <= new_f < 8:
                    new_sq = chr(new_f + ord('a')) + str(8 - new_r)
                    target = self.pieces.get(new_sq)
                    if not target or target[0] != ('w' if self.to_play == 'white' else 'b'):
                        moves.append(sq + new_sq)
        elif piece_type == 'B':
            directions = [(-1,-1),(-1,1),(1,-1),(1,1)]
            moves.extend(self._slide_moves(sq, directions))
        elif piece_type == 'R':
            directions = [(-1,0),(1,0),(0,-1),(0,1)]
            moves.extend(self._slide_moves(sq, directions))
        elif piece_type == 'Q':
            directions = [(-1,-1),(-1,1),(1,-1),(1,1),(-1,0),(1,0),(0,-1),(0,1)]
            moves.extend(self._slide_moves(sq, directions))
        elif piece_type == 'K':
            king_moves = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]
            for dr, df in king_moves:
                new_r, new_f = r+dr, f+df
                if 0 <= new_r < 8 and 0 <= new_f < 8:
                    new_sq = chr(new_f + ord('a')) + str(8 - new_r)
                    target = self.pieces.get(new_sq)
                    if not target or target[0] != ('w' if self.to_play == 'white' else 'b'):
                        moves.append(sq + new_sq)
            # Castling (simplified: assumes no checks/intermediate squares occupied)
            if sq == ('e1' if self.to_play == 'white' else 'e8'):
                # Kingside
                rook_sq = ('h1' if self.to_play == 'white' else 'h8')
                if rook_sq in self.pieces and self.pieces[rook_sq][1] == 'R' and self.pieces[rook_sq][0] == ('w' if self.to_play == 'white' else 'b'):
                    if all(inter not in self.pieces for inter in (['f1','g1'] if self.to_play == 'white' else ['f8','g8'])):
                        moves.append(sq + ('g1' if self.to_play == 'white' else 'g8'))
                # Queenside
                rook_sq = ('a1' if self.to_play == 'white' else 'a8')
                if rook_sq in self.pieces and self.pieces[rook_sq][1] == 'R' and self.pieces[rook_sq][0] == ('w' if self.to_play == 'white' else 'b'):
                    if all(inter not in self.pieces for inter in (['b1','c1','d1'] if self.to_play == 'white' else ['b8','c8','d8'])):
                        moves.append(sq + ('c1' if self.to_play == 'white' else 'c8'))
        return moves

    def _slide_moves(self, sq: str, directions: List[Tuple[int,int]]) -> List[str]:
        moves = []
        r, f = 8 - int(sq[1]), ord(sq[0]) - ord('a')
        my_color = 'w' if self.to_play == 'white' else 'b'
        for dr, df in directions:
            cr, cf = r+dr, f+df
            while 0 <= cr < 8 and 0 <= cf < 8:
                new_sq = chr(cf + ord('a')) + str(8 - cr)
                target = self.pieces.get(new_sq)
                if not target:
                    moves.append(sq + new_sq)
                elif target[0] != my_color:
                    moves.append(sq + new_sq)
                    break
                else:
                    break
                cr += dr
                cf += df
        return moves

    def make_move(self, move: str) -> 'ChessState':
        new_state = self.copy()
        if len(move) == 5:  # promotion
            src, dst, prom = move[:2], move[2:4], move[4]
            new_state.pieces[dst] = ('w' if self.to_play == 'white' else 'b') + prom.upper()
            del new_state.pieces[src]
        else:
            src, dst = move[:2], move[2:]
            # handle castling: move rook too
            if src == ('e1' if self.to_play == 'white' else 'e8') and dst in [('g1','c1') if self.to_play == 'white' else ('g8','c8')]:
                if dst == ('g1' if self.to_play == 'white' else 'g8'):
                    rook_src = ('h1' if self.to_play == 'white' else 'h8')
                    rook_dst = ('f1' if self.to_play == 'white' else 'f8')
                else:
                    rook_src = ('a1' if self.to_play == 'white' else 'a8')
                    rook_dst = ('d1' if self.to_play == 'white' else 'd8')
                new_state.pieces[rook_dst] = new_state.pieces[rook_src]
                del new_state.pieces[rook_src]
            new_state.pieces[dst] = new_state.pieces[src]
            del new_state.pieces[src]
        new_state.to_play = 'black' if self.to_play == 'white' else 'white'
        new_state._legal_moves_cache = None
        return new_state

    def is_checkmate(self) -> bool:
        if self._is_checkmate_cache is not None:
            return self._is_checkmate_cache
        moves = self.get_legal_moves()
        if not moves and self.is_in_check():
            self._is_checkmate_cache = True
            return True
        self._is_checkmate_cache = False
        return False

    def is_stalemate(self) -> bool:
        if self._is_stalemate_cache is not None:
            return self._is_stalemate_cache
        moves = self.get_legal_moves()
        if not moves and not self.is_in_check():
            self._is_stalemate_cache = True
            return True
        self._is_stalemate_cache = False
        return False

    def is_in_check(self) -> bool:
        # find my king
        my_color = 'w' if self.to_play == 'white' else 'b'
        king_sq = None
        for sq, piece in self.pieces.items():
            if piece[0] == my_color and piece[1] == 'K':
                king_sq = sq
                break
        if not king_sq:
            return False
        # switch perspective temporarily to see if any opponent piece attacks king
        temp_state = self.copy()
        temp_state.to_play = 'black' if self.to_play == 'white' else 'white'
        opp_moves = temp_state.get_legal_moves()
        for move in opp_moves:
            if move[2:4] == king_sq:
                return True
        return False

    def evaluate(self) -> float:
        """Evaluate position from current player's perspective."""
        if self.is_checkmate():
            return -100000  # opponent delivered checkmate
        if self.is_stalemate():
            return 0

        total = 0
        my_color = 'w' if self.to_play == 'white' else 'b'
        piece_count = len(self.pieces)
        endgame = piece_count <= 12

        for sq, piece in self.pieces.items():
            value = PIECE_VALUES[piece[1]]
            # piece-square table
            idx = square_index(sq)
            if piece[0] == 'b':
                idx = 63 - idx  # flip for black
            table = PIECE_SQUARE_TABLES[piece[1]]
            if piece[1] == 'K' and endgame:
                table = PIECE_SQUARE_TABLES['K_endgame']
            value += table[idx]
            if piece[0] == my_color:
                total += value
            else:
                total -= value

        # bonus for center control
        center_squares = ['d4','e4','d5','e5']
        for sq in center_squares:
            if sq in self.pieces and self.pieces[sq][0] == my_color:
                total += 20
            elif sq in self.pieces:
                total -= 20

        # penalty for king safety (simplified: pawn shield)
        king_sq = None
        for sq, piece in self.pieces.items():
            if piece[0] == my_color and piece[1] == 'K':
                king_sq = sq
                break
        if king_sq:
            r, f = 8 - int(king_sq[1]), ord(king_sq[0]) - ord('a')
            pawn_dir = 1 if my_color == 'w' else -1
            shield = 0
            for df in [-1,0,1]:
                new_r = r + pawn_dir
                new_f = f + df
                if 0 <= new_r < 8 and 0 <= new_f < 8:
                    sq2 = chr(new_f + ord('a')) + str(8 - new_r)
                    if sq2 in self.pieces and self.pieces[sq2][0] == my_color and self.pieces[sq2][1] == 'P':
                        shield += 1
            total += shield * 10

        return total

    def order_moves(self, moves: List[str]) -> List[str]:
        """Order moves for better alpha-beta performance."""
        scored = []
        for move in moves:
            score = 0
            # MVV-LVA for captures
            if len(move) >= 4:
                dst = move[2:4]
                if dst in self.pieces:
                    victim = self.pieces[dst][1]
                    aggressor = self.pieces[move[:2]][1]
                    score += 10 * PIECE_VALUES.get(victim, 0) - PIECE_VALUES.get(aggressor, 0)
            # promotions
            if len(move) == 5 and move[4] == 'q':
                score += 900
            # checks (simplified: we don't compute here)
            # center moves
            if dst in ['d4','e4','d5','e5']:
                score += 20
            scored.append((score, move))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

def quiescence(state: ChessState, alpha: float, beta: float, depth: int) -> float:
    """Quiescence search to avoid horizon effect."""
    stand_pat = state.evaluate()
    if stand_pat >= beta:
        return beta
    if alpha < stand_pat:
        alpha = stand_pat

    if depth <= 0:
        return stand_pat

    # only consider captures
    moves = state.get_legal_moves()
    capture_moves = []
    for move in moves:
        if len(move) >= 4 and move[2:4] in state.pieces:
            capture_moves.append(move)
    capture_moves = state.order_moves(capture_moves)

    for move in capture_moves:
        new_state = state.make_move(move)
        score = -quiescence(new_state, -beta, -alpha, depth-1)
        if score >= beta:
            return beta
        if score > alpha:
            alpha = score
    return alpha

def alpha_beta(state: ChessState, depth: int, alpha: float, beta: float, start_time: float, max_time: float) -> Tuple[float, Optional[str]]:
    """Alpha-beta search with iterative deepening cutoff."""
    if depth == 0 or state.is_checkmate() or state.is_stalemate():
        return quiescence(state, alpha, beta, 3), None

    moves = state.get_legal_moves()
    if not moves:
        return state.evaluate(), None

    moves = state.order_moves(moves)
    best_move = moves[0]
    for move in moves:
        new_state = state.make_move(move)
        score, _ = alpha_beta(new_state, depth-1, -beta, -alpha, start_time, max_time)
        score = -score
        if score >= beta:
            return beta, move
        if score > alpha:
            alpha = score
            best_move = move
        if time.time() - start_time > max_time:
            break
    return alpha, best_move

def iterative_deepening(state: ChessState, max_time: float) -> str:
    """Perform iterative deepening search within time limit."""
    start_time = time.time()
    best_move = state.get_legal_moves()[0]
    depth = 1
    while time.time() - start_time < max_time * 0.8:  # leave some margin
        _, move = alpha_beta(state, depth, -float('inf'), float('inf'), start_time, max_time)
        if move:
            best_move = move
        depth += 1
        if depth > 6:  # cap depth for safety
            break
    return best_move

def policy(pieces: Dict[str, str], to_play: str) -> str:
    state = ChessState(pieces, to_play)
    moves = state.get_legal_moves()
    if not moves:
        return ""  # should not happen

    # Immediate checkmate
    for move in moves:
        new_state = state.make_move(move)
        if new_state.is_checkmate():
            return move

    # Search for best move
    return iterative_deepening(state, max_time=0.95)  # leave 0.05s margin
