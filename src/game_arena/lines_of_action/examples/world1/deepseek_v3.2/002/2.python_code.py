
import numpy as np
import time
from typing import List, Tuple, Optional

# Directions: (dr, dc) for 8 directions
DIRECTIONS = [
    (0, 1),   # right
    (1, 0),   # down
    (0, -1),  # left
    (-1, 0),  # up
    (1, 1),   # down-right
    (1, -1),  # down-left
    (-1, 1),  # up-right
    (-1, -1)  # up-left
]

class LOAState:
    """Represents a Lines of Action game state."""
    
    def __init__(self, board: np.ndarray, player: int = 1):
        self.board = board.copy()
        self.player = player  # 1 for current player to move, -1 for opponent
        
    def copy(self) -> 'LOAState':
        return LOAState(self.board, self.player)
    
    def get_pieces(self, player: int) -> List[Tuple[int, int]]:
        """Return list of coordinates for given player's pieces."""
        pieces = []
        for r in range(8):
            for c in range(8):
                if self.board[r, c] == player:
                    pieces.append((r, c))
        return pieces
    
    def count_pieces_in_line(self, r: int, c: int, dr: int, dc: int) -> int:
        """Count pieces (both players) in the line starting from (r,c) in direction (dr,dc)."""
        count = 0
        rr, cc = r, c
        while 0 <= rr < 8 and 0 <= cc < 8:
            if self.board[rr, cc] != 0:
                count += 1
            rr += dr
            cc += dc
        # Also check opposite direction
        rr, cc = r - dr, c - dc
        while 0 <= rr < 8 and 0 <= cc < 8:
            if self.board[rr, cc] != 0:
                count += 1
            rr -= dr
            cc -= dc
        return count
    
    def get_legal_moves(self) -> List[str]:
        """Generate all legal moves for current player."""
        moves = []
        pieces = self.get_pieces(self.player)
        
        for r, c in pieces:
            for dr, dc in DIRECTIONS:
                # Number of squares to move = pieces in this line
                steps = self.count_pieces_in_line(r, c, dr, dc)
                if steps == 0:
                    continue
                    
                # Check if move is valid
                new_r = r + dr * steps
                new_c = c + dc * steps
                
                if 0 <= new_r < 8 and 0 <= new_c < 8:
                    # Check path for enemy pieces (cannot jump over)
                    valid = True
                    rr, cc = r, c
                    for step in range(1, steps):
                        rr += dr
                        cc += dc
                        if self.board[rr, cc] == -self.player:
                            valid = False
                            break
                    
                    if valid:
                        # Check landing square (can be empty or enemy, not friendly)
                        if self.board[new_r, new_c] != self.player:
                            moves.append(f"{r},{c}:{new_r},{new_c}")
        
        return moves
    
    def make_move(self, move_str: str) -> 'LOAState':
        """Apply move and return new state."""
        # Parse move
        parts = move_str.split(":")
        from_part = parts[0].split(",")
        to_part = parts[1].split(",")
        
        fr, fc = int(from_part[0]), int(from_part[1])
        tr, tc = int(to_part[0]), int(to_part[1])
        
        # Create new state
        new_state = self.copy()
        
        # Move piece
        piece = new_state.board[fr, fc]
        new_state.board[fr, fc] = 0
        
        # Capture if enemy piece at destination
        if new_state.board[tr, tc] == -piece:
            new_state.board[tr, tc] = 0
            
        # Place piece
        new_state.board[tr, tc] = piece
        
        # Switch player
        new_state.player = -self.player
        
        return new_state
    
    def is_terminal(self) -> bool:
        """Check if game is over."""
        # Check if current player has all pieces connected
        player_pieces = self.get_pieces(self.player)
        opponent_pieces = self.get_pieces(-self.player)
        
        # If a player has no pieces, game over
        if not player_pieces or not opponent_pieces:
            return True
        
        # Check connectivity for current player
        if self._are_all_connected(player_pieces):
            return True
        
        # Also check opponent (they might have won on previous move)
        if self._are_all_connected(opponent_pieces):
            return True
            
        return False
    
    def _are_all_connected(self, pieces: List[Tuple[int, int]]) -> bool:
        """Check if all pieces are connected via 8-direction adjacency."""
        if not pieces:
            return False
            
        visited = set()
        stack = [pieces[0]]
        
        while stack:
            r, c = stack.pop()
            if (r, c) in visited:
                continue
            visited.add((r, c))
            
            # Check all 8 directions
            for dr, dc in DIRECTIONS:
                nr, nc = r + dr, c + dc
                if (nr, nc) in pieces and (nr, nc) not in visited:
                    stack.append((nr, nc))
        
        return len(visited) == len(pieces)
    
    def evaluate(self) -> float:
        """Evaluate position from perspective of player 1 (original player)."""
        # Terminal state evaluation
        player_pieces = self.get_pieces(1)
        opponent_pieces = self.get_pieces(-1)
        
        # If game over
        if self._are_all_connected(player_pieces):
            return 1000  # Max win score
        if self._are_all_connected(opponent_pieces):
            return -1000  # Max loss score
        
        # If no pieces
        if not player_pieces:
            return -1000
        if not opponent_pieces:
            return 1000
        
        # Heuristic evaluation
        score = 0
        
        # 1. Material difference (weight: 10)
        material = len(player_pieces) - len(opponent_pieces)
        score += 10 * material
        
        # 2. Connectivity (main objective, weight: 100)
        # Use BFS to find connected components
        player_components = self._find_connected_components(player_pieces)
        opponent_components = self._find_connected_components(opponent_pieces)
        
        # Fewer components is better (negative for opponent)
        score += 100 * (len(opponent_components) - len(player_components))
        
        # 3. Compactness - average distance between pieces in same component
        # Lower distances are better
        player_compactness = self._calculate_compactness(player_pieces, player_components)
        opponent_compactness = self._calculate_compactness(opponent_pieces, opponent_components)
        score += 20 * (opponent_compactness - player_compactness)
        
        # 4. Center control - pieces in center 4x4 area
        center_score = 0
        for r in range(2, 6):
            for c in range(2, 6):
                if self.board[r, c] == 1:
                    center_score += 1
                elif self.board[r, c] == -1:
                    center_score -= 1
        score += 3 * center_score
        
        # 5. Mobility (number of legal moves)
        mobility = len(self.get_legal_moves())
        # Generate opponent's moves temporarily
        temp_state = self.copy()
        temp_state.player = -self.player
        opponent_mobility = len(temp_state.get_legal_moves())
        score += 0.5 * (mobility - opponent_mobility)
        
        return score
    
    def _find_connected_components(self, pieces: List[Tuple[int, int]]) -> List[List[Tuple[int, int]]]:
        """Find connected components using BFS."""
        if not pieces:
            return []
        
        visited = set()
        components = []
        
        for piece in pieces:
            if piece in visited:
                continue
                
            # Start new component
            component = []
            stack = [piece]
            
            while stack:
                r, c = stack.pop()
                if (r, c) in visited:
                    continue
                visited.add((r, c))
                component.append((r, c))
                
                # Check all 8 directions
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if (nr, nc) in pieces and (nr, nc) not in visited:
                        stack.append((nr, nc))
            
            components.append(component)
        
        return components
    
    def _calculate_compactness(self, pieces: List[Tuple[int, int]], 
                               components: List[List[Tuple[int, int]]]) -> float:
        """Calculate average distance between pieces in same component."""
        if not pieces:
            return 0
        
        total_distance = 0
        for component in components:
            if len(component) <= 1:
                continue
            # Calculate average Manhattan distance between pieces in component
            for i in range(len(component)):
                for j in range(i+1, len(component)):
                    r1, c1 = component[i]
                    r2, c2 = component[j]
                    # Use Chebyshev distance (max of row diff and col diff)
                    # since connectivity is 8-directional
                    dist = max(abs(r1 - r2), abs(c1 - c2))
                    total_distance += dist
        
        # Normalize by number of piece pairs
        num_pairs = sum(len(c)*(len(c)-1)//2 for c in components)
        if num_pairs == 0:
            return 0
        return total_distance / num_pairs


def minimax(state: LOAState, depth: int, alpha: float, beta: float, 
            maximizing_player: bool, start_time: float, time_limit: float) -> Tuple[float, Optional[str]]:
    """Minimax search with alpha-beta pruning."""
    # Time check
    if time.time() - start_time > time_limit:
        return state.evaluate(), None
    
    # Terminal node or depth limit
    if depth == 0 or state.is_terminal():
        return state.evaluate(), None
    
    moves = state.get_legal_moves()
    if not moves:
        return state.evaluate(), None
    
    if maximizing_player:
        max_eval = -float('inf')
        best_move = None
        
        for move in moves:
            new_state = state.make_move(move)
            eval_val, _ = minimax(new_state, depth-1, alpha, beta, False, start_time, time_limit)
            
            if eval_val > max_eval:
                max_eval = eval_val
                best_move = move
            
            alpha = max(alpha, eval_val)
            if beta <= alpha:
                break  # Beta cutoff
        
        return max_eval, best_move
    else:
        min_eval = float('inf')
        best_move = None
        
        for move in moves:
            new_state = state.make_move(move)
            eval_val, _ = minimax(new_state, depth-1, alpha, beta, True, start_time, time_limit)
            
            if eval_val < min_eval:
                min_eval = eval_val
                best_move = move
            
            beta = min(beta, eval_val)
            if beta <= alpha:
                break  # Alpha cutoff
        
        return min_eval, best_move


def iterative_deepening(state: LOAState, time_limit: float) -> str:
    """Perform iterative deepening search with time limit."""
    start_time = time.time()
    best_move = None
    depth = 1
    
    # Get initial moves as fallback
    moves = state.get_legal_moves()
    if not moves:
        return ""
    
    # Use first move as default
    best_move = moves[0]
    
    while time.time() - start_time < time_limit * 0.8:  # Use 80% of time limit
        current_depth = depth
        eval_val, move = minimax(state, current_depth, -float('inf'), float('inf'), 
                                True, start_time, time_limit)
        
        if move is not None:
            best_move = move
        
        depth += 1
        
        # If we found a winning move, return immediately
        if eval_val > 900:
            break
    
    return best_move


def policy(board) -> str:
    """Main policy function."""
    # Convert board to numpy array
    board_np = np.array(board, dtype=int)
    
    # Create game state
    state = LOAState(board_np, player=1)
    
    # Get legal moves
    moves = state.get_legal_moves()
    if not moves:
        return ""  # No moves (shouldn't happen)
    
    # If few moves or terminal, just pick first move
    if len(moves) == 1 or state.is_terminal():
        return moves[0]
    
    # Use iterative deepening with time limit of 0.9 seconds
    time_limit = 0.9
    best_move = iterative_deepening(state, time_limit)
    
    return best_move
