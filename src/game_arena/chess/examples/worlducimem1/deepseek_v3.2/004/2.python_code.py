
import numpy as np
import time
from collections import defaultdict

PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000
}

# Piece-square tables (from white's perspective, flipped for black)
PIECE_SQUARE_TABLES = {
    'P': [ # Pawn
         0,   0,   0,   0,   0,   0,   0,   0,
        50,  50,  50,  50,  50,  50,  50,  50,
        10,  10,  20,  30,  30,  20,  10,  10,
         5,   5,  10,  25,  25,  10,   5,   5,
         0,   0,   0,  20,  20,   0,   0,   0,
         5,  -5, -10,   0,   0, -10,  -5,   5,
         5,  10,  10, -20, -20,  10,  10,   5,
         0,   0,   0,   0,   0,   0,   0,   0
    ],
    'N': [ # Knight
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20,   0,   0,   0,   0, -20, -40,
        -30,   0,  10,  15,  15,  10,   0, -30,
        -30,   5,  15,  20,  20,  15,   5, -30,
        -30,   0,  15,  20,  20,  15,   0, -30,
        -30,   5,  10,  15,  15,  10,   5, -30,
        -40, -20,   0,   5,   5,   0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ],
    'B': [ # Bishop
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,  10,  10,   5,   0, -10,
        -10,   5,   5,  10,  10,   5,   5, -10,
        -10,   0,  10,  10,  10,  10,   0, -10,
        -10,  10,  10,  10,  10,  10,  10, -10,
        -10,   5,   0,   0,   0,   0,   5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ],
    'R': [ # Rook
         0,   0,   0,   0,   0,   0,   0,   0,
         5,  10,  10,  10,  10,  10,  10,   5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
        -5,   0,   0,   0,   0,   0,   0,  -5,
         0,   0,   0,   5,   5,   0,   0,   0
    ],
    'Q': [ # Queen
        -20, -10, -10,  -5,  -5, -10, -10, -20,
        -10,   0,   0,   0,   0,   0,   0, -10,
        -10,   0,   5,   5,   5,   5,   0, -10,
         -5,   0,   5,   5,   5,   5,   0,  -5,
          0,   0,   5,   5,   5,   5,   0,  -5,
        -10,   5,   5,   5,   5,   5,   0, -10,
        -10,   0,   5,   0,   0,   0,   0, -10,
        -20, -10, -10,  -5,  -5, -10, -10, -20
    ],
    'K': [ # King (middle game)
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
         20,  20,   0,   0,   0,   0,  20,  20,
         20,  30,  10,   0,   0,  10,  30,  20
    ],
    'K_END': [ # King (endgame)
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10,   0,   0, -10, -20, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  30,  40,  40,  30, -10, -30,
        -30, -10,  20,  30,  30,  20, -10, -30,
        -30, -30,   0,   0,   0,   0, -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50
    ]
}

class ChessBoard:
    def __init__(self, pieces, to_play):
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.to_play = 1 if to_play == 'white' else -1
        self.castling_rights = {'K': True, 'Q': True, 'k': True, 'q': True}
        self.en_passant = None
        self.halfmove_clock = 0
        self.fullmove_number = 1
        
        for square, piece in pieces.items():
            col = ord(square[0]) - ord('a')
            row = int(square[1]) - 1
            self.board[row][col] = piece
        
        self.material_balance = self._calculate_material()
    
    def _calculate_material(self):
        score = 0
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    value = PIECE_VALUES[piece[1]]
                    if piece[0] == 'w':
                        score += value
                    else:
                        score -= value
        return score
    
    def get_piece_at(self, square):
        col = ord(square[0]) - ord('a')
        row = int(square[1]) - 1
        return self.board[row][col]
    
    def make_move(self, move_str):
        # Parse UCI move
        from_sq = move_str[:2]
        to_sq = move_str[2:4]
        promotion = move_str[4:] if len(move_str) > 4 else None
        
        from_col = ord(from_sq[0]) - ord('a')
        from_row = int(from_sq[1]) - 1
        to_col = ord(to_sq[0]) - ord('a')
        to_row = int(to_sq[1]) - 1
        
        piece = self.board[from_row][from_col]
        captured = self.board[to_row][to_col]
        
        # Create new board
        new_board = [row[:] for row in self.board]
        new_board[from_row][from_col] = None
        new_board[to_row][to_col] = piece
        
        if promotion:
            new_board[to_row][to_col] = piece[0] + promotion.upper()
        
        # Update castling rights
        new_castling = self.castling_rights.copy()
        if piece[1] == 'K':
            new_castling['K'] = new_castling['Q'] = False
        elif piece[1] == 'R':
            if from_sq == 'h1':
                new_castling['K'] = False
            elif from_sq == 'a1':
                new_castling['Q'] = False
        
        new_to_play = -self.to_play
        
        new_board_obj = ChessBoard({}, 'white' if new_to_play == 1 else 'black')
        new_board_obj.board = new_board
        new_board_obj.to_play = new_to_play
        new_board_obj.castling_rights = new_castling
        new_board_obj.material_balance = self.material_balance
        
        # Update material balance
        if captured:
            value = PIECE_VALUES[captured[1]]
            if captured[0] == 'w':
                new_board_obj.material_balance -= value
            else:
                new_board_obj.material_balance += value
        
        return new_board_obj
    
    def generate_legal_moves(self):
        moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and ((piece[0] == 'w' and self.to_play == 1) or 
                            (piece[0] == 'b' and self.to_play == -1)):
                    from_sq = chr(col + ord('a')) + str(row + 1)
                    moves.extend(self._get_moves_for_piece(from_sq, piece))
        return moves
    
    def _get_moves_for_piece(self, square, piece):
        moves = []
        col = ord(square[0]) - ord('a')
        row = int(square[1]) - 1
        piece_type = piece[1]
        color = piece[0]
        
        directions = []
        if piece_type == 'P':
            # Pawn moves
            forward = -1 if color == 'w' else 1
            start_row = 6 if color == 'w' else 1
            if 0 <= row + forward < 8:
                # Single push
                if not self.board[row + forward][col]:
                    moves.append(square + chr(col + ord('a')) + str(row + forward + 1))
                    # Double push from starting position
                    if row == start_row and not self.board[row + 2*forward][col]:
                        moves.append(square + chr(col + ord('a')) + str(row + 2*forward + 1))
                # Captures
                for dc in [-1, 1]:
                    if 0 <= col + dc < 8:
                        target = self.board[row + forward][col + dc]
                        if target and target[0] != color:
                            moves.append(square + chr(col + dc + ord('a')) + str(row + forward + 1))
        
        elif piece_type == 'N':
            # Knight moves
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                           (1, -2), (1, 2), (2, -1), (2, 1)]
            for dr, dc in knight_moves:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = self.board[new_row][new_col]
                    if not target or target[0] != color:
                        moves.append(square + chr(new_col + ord('a')) + str(new_row + 1))
        
        elif piece_type in ['B', 'R', 'Q']:
            # Sliding pieces
            if piece_type == 'B':
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            elif piece_type == 'R':
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            else:  # Queen
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),
                             (-1, 0), (1, 0), (0, -1), (0, 1)]
            
            for dr, dc in directions:
                for i in range(1, 8):
                    new_row, new_col = row + i*dr, col + i*dc
                    if not (0 <= new_row < 8 and 0 <= new_col < 8):
                        break
                    target = self.board[new_row][new_col]
                    if not target:
                        moves.append(square + chr(new_col + ord('a')) + str(new_row + 1))
                    elif target[0] != color:
                        moves.append(square + chr(new_col + ord('a')) + str(new_row + 1))
                        break
                    else:
                        break
        
        elif piece_type == 'K':
            # King moves
            king_moves = [(-1, -1), (-1, 0), (-1, 1), (0, -1),
                         (0, 1), (1, -1), (1, 0), (1, 1)]
            for dr, dc in king_moves:
                new_row, new_col = row + dr, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = self.board[new_row][new_col]
                    if not target or target[0] != color:
                        moves.append(square + chr(new_col + ord('a')) + str(new_row + 1))
            
            # Castling (simplified)
            if color == 'w' and row == 0 and col == 4:
                if self.castling_rights.get('K'):
                    moves.append('e1g1')
                if self.castling_rights.get('Q'):
                    moves.append('e1c1')
        
        return moves
    
    def evaluate(self):
        score = self.material_balance
        game_phase = self._get_game_phase()
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    value = self._get_piece_square_value(piece, row, col, game_phase)
                    if piece[0] == 'w':
                        score += value
                    else:
                        score -= value
        
        # Add bonuses for positional factors
        score += self._evaluate_mobility() * 0.1
        score += self._evaluate_center_control() * 0.5
        score += self._evaluate_pawn_structure() * 0.3
        score += self._evaluate_king_safety() * 0.8
        
        return score * self.to_play
    
    def _get_game_phase(self):
        # Determine if we're in opening, middlegame, or endgame
        total_material = abs(self.material_balance)
        if total_material < 2000:
            return 2  # Endgame
        elif total_material < 6000:
            return 1  # Middlegame
        return 0  # Opening
    
    def _get_piece_square_value(self, piece, row, col, game_phase):
        piece_type = piece[1]
        color = piece[0]
        
        if color == 'b':
            row = 7 - row
        
        if piece_type == 'K' and game_phase == 2:
            table = PIECE_SQUARE_TABLES['K_END']
        else:
            table = PIECE_SQUARE_TABLES.get(piece_type, [0]*64)
        
        index = row * 8 + col
        return table[index]
    
    def _evaluate_mobility(self):
        mobility = 0
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    moves = len(self._get_moves_for_piece(
                        chr(col + ord('a')) + str(row + 1), piece))
                    if piece[0] == 'w':
                        mobility += moves
                    else:
                        mobility -= moves
        return mobility
    
    def _evaluate_center_control(self):
        center_squares = [(3, 3), (3, 4), (4, 3), (4, 4)]
        control = 0
        for row, col in center_squares:
            piece = self.board[row][col]
            if piece:
                if piece[0] == 'w':
                    control += 1
                else:
                    control -= 1
        return control
    
    def _evaluate_pawn_structure(self):
        score = 0
        pawn_files_white = defaultdict(int)
        pawn_files_black = defaultdict(int)
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece[1] == 'P':
                    if piece[0] == 'w':
                        pawn_files_white[col] += 1
                        # Pawn advancement bonus
                        score += (row - 1) * 5
                    else:
                        pawn_files_black[col] += 1
                        score -= (6 - row) * 5
        
        # Penalize doubled pawns
        for count in pawn_files_white.values():
            if count > 1:
                score -= 20 * (count - 1)
        for count in pawn_files_black.values():
            if count > 1:
                score += 20 * (count - 1)
        
        return score
    
    def _evaluate_king_safety(self):
        score = 0
        white_king_pos = None
        black_king_pos = None
        
        # Find kings
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece[1] == 'K':
                    if piece[0] == 'w':
                        white_king_pos = (row, col)
                    else:
                        black_king_pos = (row, col)
        
        # Penalize king in center during opening/middlegame
        if white_king_pos:
            row, col = white_king_pos
            if 2 <= row <= 5 and 2 <= col <= 5:
                score -= 30
        if black_king_pos:
            row, col = black_king_pos
            if 2 <= row <= 5 and 2 <= col <= 5:
                score += 30
        
        return score

class ChessAI:
    def __init__(self):
        self.transposition_table = {}
        self.nodes_searched = 0
        self.start_time = None
        self.time_limit = 0.95  # 95% of 1 second
        
    def minimax(self, board, depth, alpha, beta, maximizing_player):
        self.nodes_searched += 1
        
        # Time management
        if self.nodes_searched % 1000 == 0 and time.time() - self.start_time > self.time_limit:
            return 0, None
        
        if depth == 0:
            return board.evaluate(), None
        
        moves = board.generate_legal_moves()
        
        if not moves:
            # Checkmate or stalemate
            return -10000 if maximizing_player else 10000, None
        
        # Move ordering
        moves = self.order_moves(board, moves)
        
        best_move = None
        
        if maximizing_player:
            max_eval = -float('inf')
            for move in moves:
                new_board = board.make_move(move)
                eval_score, _ = self.minimax(new_board, depth-1, alpha, beta, False)
                
                if eval_score > max_eval:
                    max_eval = eval_score
                    best_move = move
                
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            
            return max_eval, best_move
        else:
            min_eval = float('inf')
            for move in moves:
                new_board = board.make_move(move)
                eval_score, _ = self.minimax(new_board, depth-1, alpha, beta, True)
                
                if eval_score < min_eval:
                    min_eval = eval_score
                    best_move = move
                
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            
            return min_eval, best_move
    
    def order_moves(self, board, moves):
        # Simple move ordering: captures first
        scored_moves = []
        for move in moves:
            score = 0
            # Check if capture
            captured = board.get_piece_at(move[2:4])
            if captured:
                score = PIECE_VALUES.get(captured[1], 0)
            
            # Check for checks
            new_board = board.make_move(move)
            # Simple check detection (would need full implementation)
            
            scored_moves.append((score, move))
        
        scored_moves.sort(reverse=True)
        return [move for _, move in scored_moves]
    
    def find_best_move(self, board, legal_moves):
        self.start_time = time.time()
        self.nodes_searched = 0
        
        # If few pieces, increase depth
        piece_count = sum(1 for row in board.board for piece in row if piece)
        max_depth = 3 if piece_count > 10 else 4
        
        best_move = None
        best_score = -float('inf')
        
        # Iterative deepening
        for depth in range(1, max_depth + 1):
            if time.time() - self.start_time > self.time_limit:
                break
            
            score, move = self.minimax(board, depth, -float('inf'), float('inf'), True)
            
            if move and (score > best_score or best_move is None):
                best_score = score
                best_move = move
        
        # Fallback: if no move found (shouldn't happen), use first legal move
        if not best_move and legal_moves:
            best_move = legal_moves[0]
        
        return best_move

def policy(pieces: dict[str, str], to_play: str, memory: dict) -> tuple[str, dict]:
    # Initialize AI if first call
    if 'ai' not in memory:
        memory['ai'] = ChessAI()
    
    ai = memory['ai']
    
    # Create board from current position
    board = ChessBoard(pieces, to_play)
    
    # Get legal moves from board (our own generation for search)
    legal_moves = board.generate_legal_moves()
    
    if not legal_moves:
        # Shouldn't happen in valid positions, but return a dummy move
        return '0000', memory
    
    # Find best move using minimax
    best_move = ai.find_best_move(board, legal_moves)
    
    # Ensure we return a legal move (fallback to first legal move)
    if best_move not in legal_moves:
        best_move = legal_moves[0]
    
    return best_move, memory
