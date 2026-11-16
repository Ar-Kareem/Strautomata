
import numpy as np
from typing import List, Tuple
import copy
import time

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """
    Returns the best move for the current player using minimax with alpha-beta pruning.
    """
    # Initialize board state
    board = CheckersBoard(my_men, my_kings, opp_men, opp_kings, color)
    
    # Time management
    start_time = time.time()
    time_limit = 0.95  # Use 95% of available time
    
    # Get all legal moves
    all_moves = board.get_all_moves()
    
    # If only one move, return it immediately
    if len(all_moves) == 1:
        return all_moves[0]
    
    # Order moves for better pruning
    ordered_moves = order_moves(board, all_moves)
    
    # Use iterative deepening with time limit
    best_move = ordered_moves[0]
    depth = 1
    max_depth = 6  # Maximum depth to prevent excessive branching
    
    while time.time() - start_time < time_limit and depth <= max_depth:
        current_best = None
        alpha = float('-inf')
        beta = float('inf')
        
        for move in ordered_moves:
            new_board = board.make_move(move)
            if new_board is None:
                continue
                
            # If immediate capture of king or multiple pieces, prioritize
            if board.is_capture(move):
                captured_count = board.get_captured_count(move)
                if captured_count >= 2:
                    # High value capture - consider it immediately
                    score = 100 + captured_count * 10
                    if score > alpha:
                        alpha = score
                        current_best = move
                    continue
            
            # Evaluate with minimax
            score = minimax(new_board, depth - 1, alpha, beta, False, start_time, time_limit)
            
            if score > alpha:
                alpha = score
                current_best = move
        
        if current_best is not None:
            best_move = current_best
        
        # Increase depth for next iteration
        depth += 1
        
        # Break if we've used too much time
        if time.time() - start_time > time_limit * 0.7:
            break
    
    return best_move


def order_moves(board, moves):
    """Order moves for better alpha-beta pruning."""
    capture_moves = []
    non_capture_moves = []
    
    for move in moves:
        if board.is_capture(move):
            # Prioritize captures that capture more pieces or kings
            score = board.get_capture_score(move)
            capture_moves.append((score, move))
        else:
            # Prioritize moves that advance toward promotion
            score = board.get_advancement_score(move)
            non_capture_moves.append((score, move))
    
    # Sort capture moves by score (highest first)
    capture_moves.sort(key=lambda x: x[0], reverse=True)
    
    # Sort non-capture moves by score (highest first)
    non_capture_moves.sort(key=lambda x: x[0], reverse=True)
    
    # Return all moves with captures first
    return [move for _, move in capture_moves] + [move for _, move in non_capture_moves]


def minimax(board, depth, alpha, beta, maximizing, start_time, time_limit):
    """Minimax algorithm with alpha-beta pruning."""
    # Check time limit
    if time.time() - start_time > time_limit:
        return board.evaluate()
    
    # Terminal node or depth limit reached
    if depth == 0 or board.is_terminal():
        return board.evaluate()
    
    if maximizing:
        max_eval = float('-inf')
        moves = board.get_all_moves()
        
        for move in moves:
            new_board = board.make_move(move)
            if new_board is None:
                continue
                
            eval_score = minimax(new_board, depth - 1, alpha, beta, False, start_time, time_limit)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            
            if beta <= alpha:
                break  # Beta cutoff
        
        return max_eval
    else:
        min_eval = float('inf')
        moves = board.get_all_moves()
        
        for move in moves:
            new_board = board.make_move(move)
            if new_board is None:
                continue
                
            eval_score = minimax(new_board, depth - 1, alpha, beta, True, start_time, time_limit)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            
            if beta <= alpha:
                break  # Alpha cutoff
        
        return min_eval


class CheckersBoard:
    """Represents the checkers board state."""
    
    def __init__(self, my_men, my_kings, opp_men, opp_kings, color):
        self.my_color = color
        self.opp_color = 'w' if color == 'b' else 'b'
        
        # Initialize board matrix (0 = empty, 1 = my man, 2 = my king, -1 = opp man, -2 = opp king)
        self.board = np.zeros((8, 8), dtype=int)
        
        # Place pieces
        for r, c in my_men:
            self.board[r, c] = 1
        for r, c in my_kings:
            self.board[r, c] = 2
        for r, c in opp_men:
            self.board[r, c] = -1
        for r, c in opp_kings:
            self.board[r, c] = -2
    
    def get_all_moves(self):
        """Get all legal moves for current player."""
        moves = []
        capture_moves = []
        
        # Check all squares for pieces of current player
        for r in range(8):
            for c in range(8):
                piece = self.board[r, c]
                if (piece > 0 and self.my_color == 'b') or (piece < 0 and self.my_color == 'w'):
                    # This is our piece
                    piece_moves = self.get_moves_for_piece(r, c)
                    for move in piece_moves:
                        if self.is_capture(move):
                            capture_moves.append(move)
                        else:
                            moves.append(move)
        
        # If captures are available, only return captures
        if capture_moves:
            return capture_moves
        return moves
    
    def get_moves_for_piece(self, r, c):
        """Get all legal moves for a piece at (r, c)."""
        moves = []
        piece = self.board[r, c]
        is_king = abs(piece) == 2
        is_mine = (piece > 0 and self.my_color == 'b') or (piece < 0 and self.my_color == 'w')
        
        if not is_mine:
            return moves
        
        # Determine movement directions
        if is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif self.my_color == 'b':  # Black moves down
            directions = [(-1, -1), (-1, 1)]
        else:  # White moves up
            directions = [(1, -1), (1, 1)]
        
        # Check regular moves
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8 and self.board[nr, nc] == 0:
                moves.append(((r, c), (nr, nc)))
        
        # Check capture moves (jumps)
        for dr, dc in directions:
            nr, nc = r + 2*dr, c + 2*dc
            mr, mc = r + dr, c + dc
            
            if (0 <= nr < 8 and 0 <= nc < 8 and 
                self.board[nr, nc] == 0 and
                0 <= mr < 8 and 0 <= mc < 8):
                
                middle_piece = self.board[mr, mc]
                if middle_piece != 0:
                    # Check if middle piece is opponent's
                    is_opponent = ((middle_piece > 0 and self.my_color == 'w') or 
                                  (middle_piece < 0 and self.my_color == 'b'))
                    
                    if is_opponent:
                        moves.append(((r, c), (nr, nc)))
        
        return moves
    
    def is_capture(self, move):
        """Check if a move is a capture (jump)."""
        (fr, fc), (tr, tc) = move
        return abs(tr - fr) == 2
    
    def get_captured_count(self, move):
        """Get number of pieces captured by this move."""
        if not self.is_capture(move):
            return 0
        
        (fr, fc), (tr, tc) = move
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        
        if self.board[mr, mc] != 0:
            return 1
        return 0
    
    def get_capture_score(self, move):
        """Score capture moves for ordering."""
        if not self.is_capture(move):
            return 0
        
        score = 0
        (fr, fc), (tr, tc) = move
        mr, mc = (fr + tr) // 2, (fc + tc) // 2
        
        captured_piece = abs(self.board[mr, mc])
        if captured_piece == 2:  # King
            score += 30
        else:  # Regular piece
            score += 10
        
        # Check if this leads to promotion
        if self.would_promote(move):
            score += 20
        
        return score
    
    def get_advancement_score(self, move):
        """Score non-capture moves for ordering."""
        (fr, fc), (tr, tc) = move
        score = 0
        
        # Advancement toward promotion
        if self.my_color == 'b':  # Black moves toward row 0
            advancement = fr - tr  # Positive is forward
        else:  # White moves toward row 7
            advancement = tr - fr  # Positive is forward
        
        score += advancement * 3
        
        # Center control
        if tr in [3, 4] and tc in [2, 3, 4, 5]:
            score += 2
        
        # Avoid edges
        if tr in [0, 7] or tc in [0, 7]:
            score -= 1
        
        return score
    
    def would_promote(self, move):
        """Check if move would promote piece to king."""
        (fr, fc), (tr, tc) = move
        piece = self.board[fr, fc]
        
        if abs(piece) == 2:  # Already a king
            return False
        
        if self.my_color == 'b' and tr == 0:  # Black reaches first row
            return True
        elif self.my_color == 'w' and tr == 7:  # White reaches last row
            return True
        
        return False
    
    def make_move(self, move):
        """Create a new board with the move applied."""
        (fr, fc), (tr, tc) = move
        
        # Create copy of board
        new_board = copy.deepcopy(self.board)
        piece = new_board[fr, fc]
        
        # Move piece
        new_board[tr, tc] = piece
        new_board[fr, fc] = 0
        
        # Handle capture
        if self.is_capture(move):
            mr, mc = (fr + tr) // 2, (fc + tc) // 2
            new_board[mr, mc] = 0
        
        # Handle promotion
        if self.would_promote(move):
            if piece > 0:  # My piece
                new_board[tr, tc] = 2
            else:  # Opponent piece (shouldn't happen in our simulation)
                new_board[tr, tc] = -2
        
        # Create new board object
        my_men_new = []
        my_kings_new = []
        opp_men_new = []
        opp_kings_new = []
        
        for r in range(8):
            for c in range(8):
                val = new_board[r, c]
                if val == 1:
                    my_men_new.append((r, c))
                elif val == 2:
                    my_kings_new.append((r, c))
                elif val == -1:
                    opp_men_new.append((r, c))
                elif val == -2:
                    opp_kings_new.append((r, c))
        
        # Swap perspective for next player
        return CheckersBoard(opp_men_new, opp_kings_new, my_men_new, my_kings_new, self.opp_color)
    
    def evaluate(self):
        """Evaluate board state from current player's perspective."""
        score = 0
        
        # Material evaluation
        my_pieces = np.sum(self.board > 0)
        opp_pieces = np.sum(self.board < 0)
        score += (my_pieces - opp_pieces) * 10
        
        # King bonus
        my_kings = np.sum(self.board == 2)
        opp_kings = np.sum(self.board == -2)
        score += (my_kings - opp_kings) * 30
        
        # Positional evaluation
        for r in range(8):
            for c in range(8):
                if self.board[r, c] > 0:  # My piece
                    # Center control
                    if r in [3, 4] and c in [2, 3, 4, 5]:
                        score += 2
                    
                    # Advancement
                    if self.my_color == 'b':  # Black
                        score += (7 - r) * 1  # Closer to bottom is better
                    else:  # White
                        score += r * 1  # Closer to top is better
                    
                    # Safety - avoid edges
                    if c in [0, 7]:
                        score -= 1
                
                elif self.board[r, c] < 0:  # Opponent piece
                    # Center control (negative for opponent)
                    if r in [3, 4] and c in [2, 3, 4, 5]:
                        score -= 2
                    
                    # Advancement (negative for opponent)
                    if self.my_color == 'b':  # Opponent is white
                        score -= r * 1  # White wants to go up
                    else:  # Opponent is black
                        score -= (7 - r) * 1  # Black wants to go down
        
        # Mobility bonus
        my_moves = len(self.get_all_moves())
        
        # Switch perspective to count opponent moves
        temp_board = CheckersBoard(
            [(r, c) for r in range(8) for c in range(8) if self.board[r, c] == 1],
            [(r, c) for r in range(8) for c in range(8) if self.board[r, c] == 2],
            [(r, c) for r in range(8) for c in range(8) if self.board[r, c] == -1],
            [(r, c) for r in range(8) for c in range(8) if self.board[r, c] == -2],
            self.opp_color
        )
        opp_moves = len(temp_board.get_all_moves())
        
        score += (my_moves - opp_moves) * 0.5
        
        return score
    
    def is_terminal(self):
        """Check if game is over."""
        # No pieces left for current player
        my_pieces = np.sum(self.board > 0 if self.my_color == 'b' else self.board < 0)
        if my_pieces == 0:
            return True
        
        # No legal moves
        if len(self.get_all_moves()) == 0:
            return True
        
        return False
