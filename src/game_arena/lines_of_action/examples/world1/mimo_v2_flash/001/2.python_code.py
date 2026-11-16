
import numpy as np
import sys
from typing import List, Tuple, Optional

def policy(board) -> str:
    """
    Lines of Action AI Policy
    Uses evaluation with connectivity, captures, and minimax search
    """
    # Convert to numpy for easier manipulation
    board_array = np.array(board)
    
    # Create solver
    solver = LOASolver(board_array)
    
    # Get best move
    best_move = solver.get_best_move()
    
    return best_move

class LOASolver:
    def __init__(self, board: np.ndarray):
        self.board = board
        self.my_color = 1
        self.opp_color = -1
        self.size = 8
        
    def get_best_move(self) -> str:
        """Get the best move using search and evaluation"""
        moves = self.generate_all_moves()
        
        if not moves:
            # Should not happen in valid game
            raise ValueError("No legal moves found")
        
        # Check for immediate win
        for move in moves:
            new_board = self.simulate_move(self.board, move)
            if self.is_win(new_board, self.my_color):
                return self.move_to_string(move)
        
        # Check if opponent can win next turn
        opp_winning_moves = []
        for move in moves:
            new_board = self.simulate_move(self.board, move)
            opp_moves = self.generate_all_moves_for_board(new_board, self.opp_color)
            for opp_move in opp_moves:
                opp_new_board = self.simulate_move(new_board, opp_move)
                if self.is_win(opp_new_board, self.opp_color):
                    opp_winning_moves.append(move)
                    break
        
        # If opponent has winning move, try to block
        if opp_winning_moves:
            blocking_moves = []
            for move in opp_winning_moves:
                # Try this move and see if it blocks
                new_board = self.simulate_move(self.board, move)
                # Generate all possible responses and see if any block
                opp_moves_after = self.generate_all_moves_for_board(new_board, self.opp_color)
                can_block = False
                for opp_move in opp_moves_after:
                    final_board = self.simulate_move(new_board, opp_move)
                    if not self.is_win(final_board, self.opp_color):
                        can_block = True
                        break
                if can_block:
                    blocking_moves.append(move)
            
            if blocking_moves:
                # Use minimax to choose best blocking move
                best_move = self.minimax_search(blocking_moves, depth=2)
                return self.move_to_string(best_move)
        
        # Regular search - look ahead 2-3 moves
        if len(moves) <= 5:
            # Few moves, search deeper
            best_move = self.minimax_search(moves, depth=3)
        else:
            # Many moves, search shallower but evaluate all
            best_move = self.minimax_search(moves, depth=2)
        
        return self.move_to_string(best_move)
    
    def minimax_search(self, moves: List[Tuple[Tuple[int, int], Tuple[int, int]]], 
                      depth: int) -> Tuple[Tuple[int, int], Tuple[int, int]]:
        """Minimax with alpha-beta pruning"""
        best_move = moves[0]
        best_score = -float('inf')
        
        for move in moves:
            new_board = self.simulate_move(self.board, move)
            score = self.minimax(new_board, depth - 1, -float('inf'), float('inf'), False)
            if score > best_score:
                best_score = score
                best_move = move
        
        return best_move
    
    def minimax(self, board: np.ndarray, depth: int, alpha: float, beta: float, 
                is_maximizing: bool) -> float:
        """Recursive minimax"""
        if depth == 0:
            return self.evaluate(board)
        
        if is_maximizing:
            # My turn
            moves = self.generate_all_moves_for_board(board, self.my_color)
            if not moves:
                return -1000  # No moves = bad
            
            # Check win
            for move in moves:
                new_board = self.simulate_move(board, move)
                if self.is_win(new_board, self.my_color):
                    return 1000
            
            max_eval = -float('inf')
            for move in moves:
                new_board = self.simulate_move(board, move)
                eval_score = self.minimax(new_board, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            # Opponent turn
            moves = self.generate_all_moves_for_board(board, self.opp_color)
            if not moves:
                return 1000  # Opponent can't move = good for us
            
            # Check loss
            for move in moves:
                new_board = self.simulate_move(board, move)
                if self.is_win(new_board, self.opp_color):
                    return -1000
            
            min_eval = float('inf')
            for move in moves:
                new_board = self.simulate_move(board, move)
                eval_score = self.minimax(new_board, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval
    
    def evaluate(self, board: np.ndarray) -> float:
        """Evaluate board position"""
        my_pieces = self.get_piece_positions(board, self.my_color)
        opp_pieces = self.get_piece_positions(board, self.opp_color)
        
        if len(my_pieces) == 0:
            return -1000
        if len(opp_pieces) == 0:
            return 1000
        
        # Check for win
        if self.is_win(board, self.my_color):
            return 1000
        if self.is_win(board, self.opp_color):
            return -1000
        
        # Evaluate connectivity
        my_components = self.count_connected_components(board, self.my_color)
        opp_components = self.count_connected_components(board, self.opp_color)
        
        # Fewer components = better (more connected)
        connectivity_score = (opp_components - my_components) * 5
        
        # Piece count (fewer pieces = easier to connect, but don't sacrifice too many)
        piece_score = (len(opp_pieces) - len(my_pieces)) * 0.5
        
        # Centralization
        my_center = self.center_score(my_pieces)
        opp_center = self.center_score(opp_pieces)
        center_score = my_center - opp_center
        
        # Mobility
        my_mobility = len(self.generate_all_moves_for_board(board, self.my_color))
        opp_mobility = len(self.generate_all_moves_for_board(board, self.opp_color))
        mobility_score = (my_mobility - opp_mobility) * 0.1
        
        # Combine scores
        total_score = connectivity_score + piece_score + center_score + mobility_score
        
        return total_score
    
    def center_score(self, pieces: List[Tuple[int, int]]) -> float:
        """Score based on how centralized pieces are"""
        if not pieces:
            return 0
        score = 0
        for r, c in pieces:
            # Prefer center (dist from center of board)
            dist = abs(r - 3.5) + abs(c - 3.5)
            score += (7 - dist)  # Higher for closer to center
        return score / len(pieces)
    
    def generate_all_moves(self) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Generate all legal moves for current player"""
        return self.generate_all_moves_for_board(self.board, self.my_color)
    
    def generate_all_moves_for_board(self, board: np.ndarray, 
                                     color: int) -> List[Tuple[Tuple[int, int], Tuple[int, int]]]:
        """Generate all legal moves for given color"""
        moves = []
        pieces = self.get_piece_positions(board, color)
        
        for r, c in pieces:
            # Try all 8 directions
            for dr, dc in [(1,0), (-1,0), (0,1), (0,-1), (1,1), (-1,-1), (1,-1), (-1,1)]:
                step_count = self.count_line_pieces(board, r, c, dr, dc)
                if step_count == 0:
                    continue
                
                target_r = r + dr * step_count
                target_c = c + dc * step_count
                
                if 0 <= target_r < 8 and 0 <= target_c < 8:
                    # Check path validity
                    if self.is_path_clear(board, r, c, dr, dc, step_count, color):
                        moves.append(((r, c), (target_r, target_c)))
        
        return moves
    
    def count_line_pieces(self, board: np.ndarray, r: int, c: int, dr: int, dc: int) -> int:
        """Count pieces (both colors) in line before moving"""
        count = 0
        step = 1
        while True:
            nr = r + dr * step
            nc = c + dc * step
            if not (0 <= nr < 8 and 0 <= nc < 8):
                break
            if board[nr, nc] != 0:
                count += 1
            step += 1
        return count
    
    def is_path_clear(self, board: np.ndarray, r: int, c: int, dr: int, dc: int, 
                     steps: int, color: int) -> bool:
        """Check if path is clear (can jump over own pieces, but not enemy)"""
        for step in range(1, steps):
            nr = r + dr * step
            nc = c + dc * step
            if board[nr, nc] == -color:  # Enemy piece
                return False
        # Check target
        tr = r + dr * steps
        tc = c + dc * steps
        if board[tr, tc] == color:  # Can't land on own piece
            return False
        return True
    
    def simulate_move(self, board: np.ndarray, move: Tuple[Tuple[int, int], Tuple[int, int]]) -> np.ndarray:
        """Apply move to board and return new board"""
        new_board = board.copy()
        (from_r, from_c), (to_r, to_c) = move
        
        new_board[to_r, to_c] = new_board[from_r, from_c]
        new_board[from_r, from_c] = 0
        
        return new_board
    
    def get_piece_positions(self, board: np.ndarray, color: int) -> List[Tuple[int, int]]:
        """Get positions of pieces of given color"""
        positions = []
        for r in range(8):
            for c in range(8):
                if board[r, c] == color:
                    positions.append((r, c))
        return positions
    
    def is_win(self, board: np.ndarray, color: int) -> bool:
        """Check if color has all pieces connected"""
        pieces = self.get_piece_positions(board, color)
        if not pieces or len(pieces) == 1:
            return True
        
        # BFS to check connectivity
        visited = set()
        queue = [pieces[0]]
        
        while queue:
            r, c = queue.pop(0)
            if (r, c) in visited:
                continue
            visited.add((r, c))
            
            # Check all 8 neighbors
            for dr in [-1, 0, 1]:
                for dc in [-1, 0, 1]:
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 8 and 0 <= nc < 8:
                        if board[nr, nc] == color and (nr, nc) not in visited:
                            queue.append((nr, nc))
        
        return len(visited) == len(pieces)
    
    def count_connected_components(self, board: np.ndarray, color: int) -> int:
        """Count number of connected components for color"""
        pieces = self.get_piece_positions(board, color)
        if not pieces:
            return 0
        
        visited = set()
        components = 0
        
        for piece in pieces:
            if piece in visited:
                continue
            
            # New component
            components += 1
            queue = [piece]
            
            while queue:
                r, c = queue.pop(0)
                if (r, c) in visited:
                    continue
                visited.add((r, c))
                
                # Check all 8 neighbors
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            if board[nr, nc] == color and (nr, nc) not in visited:
                                queue.append((nr, nc))
        
        return components
    
    def move_to_string(self, move: Tuple[Tuple[int, int], Tuple[int, int]]) -> str:
        """Convert move to string format"""
        (from_r, from_c), (to_r, to_c) = move
        return f"{from_r},{from_c}:{to_r},{to_c}"

