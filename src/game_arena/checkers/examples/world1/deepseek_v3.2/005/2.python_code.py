
import itertools
import time
from typing import List, Tuple, Set, Optional, Dict
import math

def policy(my_men: List[Tuple[int, int]], my_kings: List[Tuple[int, int]], 
           opp_men: List[Tuple[int, int]], opp_kings: List[Tuple[int, int]], 
           color: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Return the best move for the current player."""
    
    # Create board representation
    board = CheckersBoard(my_men, my_kings, opp_men, opp_kings, color)
    
    # Get all possible moves
    all_moves = board.get_all_moves()
    if not all_moves:
        # Fallback - should never happen in valid game state
        return ((0, 0), (0, 0))
    
    # If only one move, return it immediately
    if len(all_moves) == 1:
        return all_moves[0]
    
    # Use iterative deepening with time limit
    time_limit = 0.95  # Leave some margin
    start_time = time.time()
    best_move = all_moves[0]
    
    # Try increasing depths until time runs out
    for depth in range(1, 7):  # Up to 6-ply search
        try:
            current_best = minimax_search(board, depth, start_time, time_limit)
            if current_best:
                best_move = current_best
        except TimeoutError:
            break
        
        if time.time() - start_time > time_limit * 0.5:
            break  # Don't start a new depth if we're already using half the time
    
    return best_move


class CheckersBoard:
    """Represents a checkers board state."""
    
    # Direction offsets for regular pieces
    WHITE_DIRS = [(-1, -1), (-1, 1)]  # White moves up (decreasing row)
    BLACK_DIRS = [(1, -1), (1, 1)]    # Black moves down (increasing row)
    KING_DIRS = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
    
    # Value weights for evaluation
    MAN_VALUE = 100
    KING_VALUE = 150
    CENTER_BONUS = 5
    BACK_ROW_BONUS = 10
    MOBILITY_FACTOR = 2
    
    def __init__(self, my_men, my_kings, opp_men, opp_kings, color):
        self.color = color  # 'w' or 'b'
        self.my_color = color
        self.opp_color = 'b' if color == 'w' else 'w'
        
        # Store positions in sets for faster lookup
        self.my_men = set(my_men)
        self.my_kings = set(my_kings)
        self.opp_men = set(opp_men)
        self.opp_kings = set(opp_kings)
        
        # All pieces for quick checking
        self.all_pieces = self.my_men | self.my_kings | self.opp_men | self.opp_kings
    
    def is_valid_square(self, row: int, col: int) -> bool:
        """Check if square is on board and dark."""
        return 0 <= row < 8 and 0 <= col < 8 and (row + col) % 2 == 1
    
    def is_empty(self, row: int, col: int) -> bool:
        """Check if square is empty."""
        return (row, col) not in self.all_pieces
    
    def is_opponent(self, row: int, col: int) -> bool:
        """Check if square contains opponent piece."""
        return (row, col) in self.opp_men or (row, col) in self.opp_kings
    
    def is_king(self, row: int, col: int) -> bool:
        """Check if piece at square is a king."""
        return (row, col) in self.my_kings or (row, col) in self.opp_kings
    
    def get_piece_color(self, row: int, col: int) -> Optional[str]:
        """Get color of piece at square, or None if empty."""
        if (row, col) in self.my_men or (row, col) in self.my_kings:
            return self.my_color
        elif (row, col) in self.opp_men or (row, col) in self.opp_kings:
            return self.opp_color
        return None
    
    def get_dirs(self, row: int, col: int) -> List[Tuple[int, int]]:
        """Get movement directions for piece at (row, col)."""
        if (row, col) in self.my_kings or (row, col) in self.opp_kings:
            return self.KING_DIRS
        elif self.get_piece_color(row, col) == 'w':
            return self.WHITE_DIRS
        else:  # 'b'
            return self.BLACK_DIRS
    
    def find_captures(self, row: int, col: int, visited=None) -> List[List[Tuple[int, int]]]:
        """Find all capture sequences starting from (row, col)."""
        if visited is None:
            visited = set()
        
        piece_color = self.get_piece_color(row, col)
        if piece_color is None:
            return []
        
        is_king = self.is_king(row, col)
        dirs = self.KING_DIRS if is_king else (self.WHITE_DIRS if piece_color == 'w' else self.BLACK_DIRS)
        
        captures = []
        
        for dr, dc in dirs:
            # Check for opponent piece to capture
            mid_r, mid_c = row + dr, col + dc
            land_r, land_c = row + 2*dr, col + 2*dc
            
            if not self.is_valid_square(mid_r, mid_c) or not self.is_valid_square(land_r, land_c):
                continue
            
            if self.is_opponent(mid_r, mid_c) and self.is_empty(land_r, land_c):
                # Make the capture
                captured = (mid_r, mid_c)
                if captured in visited:
                    continue
                
                # Create new board after capture
                new_board = self.copy()
                new_board.move_piece((row, col), (land_r, land_c), captured)
                
                # Check for further captures
                further_captures = new_board.find_captures(land_r, land_c, visited | {captured})
                
                if further_captures:
                    for seq in further_captures:
                        captures.append([(row, col), (land_r, land_c)] + seq[1:])
                else:
                    captures.append([(row, col), (land_r, land_c)])
        
        return captures
    
    def get_all_moves(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Get all legal moves for current player."""
        moves = []
        capture_moves = []
        
        # Check all pieces for captures
        for piece in self.my_men | self.my_kings:
            captures = self.find_captures(*piece)
            for capture_seq in captures:
                capture_moves.append((capture_seq[0], capture_seq[1]))
        
        # If captures exist, only return captures
        if capture_moves:
            return capture_moves
        
        # No captures, get regular moves
        for row, col in self.my_men | self.my_kings:
            dirs = self.get_dirs(row, col)
            for dr, dc in dirs:
                new_r, new_c = row + dr, col + dc
                if self.is_valid_square(new_r, new_c) and self.is_empty(new_r, new_c):
                    moves.append(((row, col), (new_r, new_c)))
        
        return moves
    
    def move_piece(self, from_pos: Tuple[int, int], to_pos: Tuple[int, int], 
                   captured: Optional[Tuple[int, int]] = None):
        """Move a piece and handle captures/promotions."""
        from_row, from_col = from_pos
        to_row, to_col = to_pos
        
        # Remove captured piece if any
        if captured:
            cap_row, cap_col = captured
            if (cap_row, cap_col) in self.opp_men:
                self.opp_men.remove((cap_row, cap_col))
            elif (cap_row, cap_col) in self.opp_kings:
                self.opp_kings.remove((cap_row, cap_col))
        
        # Move the piece
        if (from_row, from_col) in self.my_men:
            self.my_men.remove((from_row, from_col))
            # Check for promotion
            if (self.my_color == 'w' and to_row == 0) or (self.my_color == 'b' and to_row == 7):
                self.my_kings.add((to_row, to_col))
            else:
                self.my_men.add((to_row, to_col))
        elif (from_row, from_col) in self.my_kings:
            self.my_kings.remove((from_row, from_col))
            self.my_kings.add((to_row, to_col))
        
        # Update all pieces set
        self.all_pieces = self.my_men | self.my_kings | self.opp_men | self.opp_kings
    
    def copy(self) -> 'CheckersBoard':
        """Create a deep copy of the board."""
        return CheckersBoard(
            list(self.my_men), list(self.my_kings),
            list(self.opp_men), list(self.opp_kings),
            self.color
        )
    
    def evaluate(self) -> float:
        """Evaluate board position from current player's perspective."""
        score = 0
        
        # Material score
        score += len(self.my_men) * self.MAN_VALUE
        score += len(self.my_kings) * self.KING_VALUE
        score -= len(self.opp_men) * self.MAN_VALUE
        score -= len(self.opp_kings) * self.KING_VALUE
        
        # Positional bonuses
        for row, col in self.my_men:
            # Center control
            if 2 <= row <= 5 and 2 <= col <= 5:
                score += self.CENTER_BONUS
            
            # Advancement (closer to promotion is better)
            if self.my_color == 'w':
                score += (7 - row) * 2  # White wants to go to row 0
            else:
                score += row * 2  # Black wants to go to row 7
        
        for row, col in self.my_kings:
            # Kings in center
            if 2 <= row <= 5 and 2 <= col <= 5:
                score += self.CENTER_BONUS * 2
            
            # Kings on back row are safer
            if (self.my_color == 'w' and row == 7) or (self.my_color == 'b' and row == 0):
                score += self.BACK_ROW_BONUS
        
        # Mobility (approximate)
        my_moves = len(self.get_all_moves())
        
        # Switch perspective to estimate opponent mobility
        temp_board = self.copy()
        temp_board.color = self.opp_color
        temp_board.my_color, temp_board.opp_color = temp_board.opp_color, temp_board.my_color
        temp_board.my_men, temp_board.opp_men = temp_board.opp_men, temp_board.my_men
        temp_board.my_kings, temp_board.opp_kings = temp_board.opp_kings, temp_board.my_kings
        opp_moves = len(temp_board.get_all_moves())
        
        score += (my_moves - opp_moves) * self.MOBILITY_FACTOR
        
        # Endgame encouragement (trade pieces when ahead)
        piece_diff = (len(self.my_men) + len(self.my_kings)) - (len(self.opp_men) + len(self.opp_kings))
        if piece_diff > 0 and (len(self.my_men) + len(self.my_kings) + len(self.opp_men) + len(self.opp_kings)) < 10:
            score += piece_diff * 20
        
        return score
    
    def switch_turn(self):
        """Switch turn to opponent."""
        self.color = self.opp_color
        self.my_color, self.opp_color = self.opp_color, self.my_color
        self.my_men, self.opp_men = self.opp_men, self.my_men
        self.my_kings, self.opp_kings = self.opp_kings, self.my_kings


def minimax_search(board: CheckersBoard, depth: int, start_time: float, time_limit: float) -> Optional[Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Perform minimax search with alpha-beta pruning."""
    best_move = None
    best_value = -math.inf
    
    # Get moves and order them (captures first, then by heuristic)
    moves = board.get_all_moves()
    
    # Move ordering: captures first, then by destination square evaluation
    def move_score(move):
        _, (to_r, to_c) = move
        # Prefer moves that promote
        if (board.my_color == 'w' and to_r == 0) or (board.my_color == 'b' and to_r == 7):
            return 100
        # Prefer center squares
        center_dist = abs(to_r - 3.5) + abs(to_c - 3.5)
        return -center_dist
    
    moves.sort(key=move_score, reverse=True)
    
    alpha = -math.inf
    beta = math.inf
    
    for move in moves:
        # Check time
        if time.time() - start_time > time_limit:
            raise TimeoutError()
        
        new_board = board.copy()
        new_board.move_piece(*move)
        new_board.switch_turn()
        
        value = alphabeta(new_board, depth - 1, alpha, beta, False, start_time, time_limit)
        
        if value > best_value:
            best_value = value
            best_move = move
        
        alpha = max(alpha, best_value)
        if beta <= alpha:
            break
    
    return best_move


def alphabeta(board: CheckersBoard, depth: int, alpha: float, beta: float, 
              maximizing: bool, start_time: float, time_limit: float) -> float:
    """Alpha-beta pruning minimax."""
    # Check time
    if time.time() - start_time > time_limit:
        raise TimeoutError()
    
    # Terminal node or depth limit
    moves = board.get_all_moves()
    if depth == 0 or not moves:
        return board.evaluate()
    
    if maximizing:
        value = -math.inf
        for move in moves[:15]:  # Limit branching for speed
            new_board = board.copy()
            new_board.move_piece(*move)
            new_board.switch_turn()
            
            value = max(value, alphabeta(new_board, depth - 1, alpha, beta, False, start_time, time_limit))
            alpha = max(alpha, value)
            if beta <= alpha:
                break
        return value
    else:
        value = math.inf
        for move in moves[:15]:  # Limit branching for speed
            new_board = board.copy()
            new_board.move_piece(*move)
            new_board.switch_turn()
            
            value = min(value, alphabeta(new_board, depth - 1, alpha, beta, True, start_time, time_limit))
            beta = min(beta, value)
            if beta <= alpha:
                break
        return value
