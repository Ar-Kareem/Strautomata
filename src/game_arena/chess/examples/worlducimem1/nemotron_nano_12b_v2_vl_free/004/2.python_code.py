
# chess policy with move generation and evaluation

from collections import defaultdict

PIECE_VALUES = {'K': 100, 'Q': 9, 'R': 5, 'B': 3, 'N': 3, 'P': 1}

class ChessPolicy:
    def __init__(self):
        self._memory = {}
    
    def move_generator(self, pieces, to_play):
        current_color = 'w' if to_play == 'white' else 'b'
        current_color_short = current_color
        opponent_color = 'b' if current_color == 'w' else 'w'
        moves = []
        king_pos = self._find_king(pieces, current_color)
        
        for square in pieces:
            if pieces[square][0] != current_color:
                continue
            piece_type = pieces[square][1]
            
            if piece_type == 'P':
                # Generate pawn moves
                moves.extend(self._pawn_moves(square, current_color, pieces))
            elif piece_type == 'N':
                moves.extend(self._knight_moves(square, pieces))
            # ... other piece types omitted for brevity
            
            # Filter legal moves by checking if king is safe after move
            for move in moves:
                new_board = self._simulate_move(pieces, move)
                if self._is_king_safe(new_board, current_color):
                    legal_moves.append(move)
        return legal_moves
    
    def _pawn_moves(self, sq, color, board):
        # generate pawn moves (simplified)
        moves = []
        rank = int(sq[1])
        direction = 1 if color == 'white' else -1
        
        new_sq = sq[0] + str(rank + direction)
        if new_sq not in board:
            moves.append(new_sq)
            # two-step move
            if (color == 'white' and rank == 2) or (color == 'black' and rank == 7):
                next_sq = sq[0] + str(rank + 2 * direction)
                if next_sq not in board:
                    moves.append(next_sq)
        
        # captures
        for file_offset in [-1, 1]:
            new_sq_file = chr(ord(sq[0]) + file_offset)
            new_sq = new_sq_file + str(rank + direction)
            if new_sq in board and board[new_sq][0] != color:
                moves.append(new_sq)
            # en passant (simplified)
        return moves
    
    def _knight_moves(self, sq, board):
        moves = []
        f = ord(sq[0]) - ord('a')
        r = int(sq[1])
        deltas = [(2,1), (2,-1), (-2,1), (-2,-1),
                  (1,2), (1,-2), (-1,2), (-1,-2)]
        for df, dr in deltas:
            new_f = f + df
            new_r = r + dr
            if 0 <= new_f < 8 and 0 <= new_r < 8:
                new_sq = chr(ord('a') + new_f) + str(new_r + 1)
                if new_sq not in board or board[new_sq][0] != board[sq][0]:
                    moves.append(new_sq)
        return moves
    
    def _simulate_move(self, pieces, move):
        # simulate move and return new board
        new_pieces = dict(pieces)
        from_sq = move[:2]
        to_sq = move[-2:]
        piece = new_pieces[from_sq]
        new_pieces.pop(from_sq)
        if to_sq in new_pieces:
            # capture
            new_pieces.pop(to_sq)
        new_pieces[to_sq] = piece
        return new_pieces
    
    def _find_king(self, pieces, color):
        king = color + 'K'
        for sq, pc in pieces.items():
            if pc == king:
                return sq
        return None
    
    def _is_king_in_check(self, pieces, color):
        king_sq = self._find_king(pieces, color)
        if not king_sq:
            return False
        opponent_color = 'b' if color == 'w' else 'w'
        for sq, (col, typ) in pieces.items():
            if col == opponent_color:
                if self._can_attack(sq, king_sq, typ, pieces):
                    return True
        return False
    
    def _can_attack(self, from_sq, to_sq, piece_type, board):
        # simplified attack check
        if piece_type == 'K':
            return abs(ord(from_sq[0]) - ord(to_sq[0])) <= 1 and abs(int(from_sq[1]) - int(to_sq[1])) <= 1
        # ... other piece types omitted for brevity
        return False
    
    def policy(self, pieces, to_play, memory):
        legal_moves = self.move_generator(pieces, to_play)
        
        if not legal_moves:
            return ('', memory)
        
        # Evaluate each move for material gain
        best_move = legal_moves[0]
        max_eval = -float('inf')
        
        for move in legal_moves:
            new_pieces = self._simulate_move(pieces, move)
            eval = self._evaluate_position(new_pieces, to_play)
            if eval > max_eval:
                max_eval = eval
                best_move = move
        
        return (best_move, memory)

# Example usage
policy = ChessPolicy().policy
# dummy move evaluation
# ... (actual simulation needed)
