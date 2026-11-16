
import numpy as np
from typing import List, Tuple, Optional, Dict

# Board size constants
BOARD_SIZE = 15

# Precompute board geometry for faster neighbor lookups
def get_neighbors(row: int, col: int) -> List[Tuple[int, int]]:
    """Get all valid neighbors for a given position on the hexagonal grid."""
    neighbors = []
    
    # Same column
    if row > 0: neighbors.append((row - 1, col))
    if row < BOARD_SIZE - 1: neighbors.append((row + 1, col))
    
    # Left column
    if col > 0:
        if row > 0: neighbors.append((row - 1, col - 1))
        neighbors.append((row, col - 1))
    
    # Right column  
    if col < BOARD_SIZE - 1:
        if row > 0: neighbors.append((row - 1, col + 1))
        neighbors.append((row, col + 1))
    
    return neighbors

def get_edge_type(row: int, col: int) -> Optional[str]:
    """Determine which edge a position is on, if any."""
    if row == 0: return "top"
    if row == BOARD_SIZE - 1: return "bottom"
    if col == 0: return "left"
    if col == BOARD_SIZE - 1: return "right"
    if row + col == 0: return "corner_top_left"
    if row + col == BOARD_SIZE - 1: return "corner_bottom_right"
    return None

def is_corner(row: int, col: int) -> bool:
    """Check if a position is a corner."""
    return (row == 0 and col == 0) or \
           (row == 0 and col == BOARD_SIZE - 1) or \
           (row == BOARD_SIZE - 1 and col == 0) or \
           (row == BOARD_SIZE - 1 and col == BOARD_SIZE - 1) or \
           (row + col == 0) or \
           (row + col == BOARD_SIZE - 1)

class GameEvaluator:
    def __init__(self, me: List[Tuple[int, int]], opp: List[Tuple[int, int]]):
        self.me = set(me)
        self.opp = set(opp)
        self.occupied = self.me | self.opp
        self.board = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=int)
        for r, c in me:
            self.board[r, c] = 1
        for r, c in opp:
            self.board[r, c] = 2

    def is_winning_move(self, row: int, col: int, is_me: bool) -> bool:
        """Check if placing a stone at (row, col) creates a winning structure."""
        if is_me:
            stones = self.me | {(row, col)}
            opponent_stones = self.opp
        else:
            stones = self.opp | {(row, col)}
            opponent_stones = self.me

        return (self._check_ring(stones, opponent_stones) or
                self._check_bridge(stones) or
                self._check_fork(stones))

    def _check_ring(self, stones: set, opponent_stones: set) -> bool:
        """Check if the stones form a ring."""
        # Find all empty cells that could be surrounded
        empty_cells = set()
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if (r, c) not in stones and (r, c) not in opponent_stones:
                    empty_cells.add((r, c))
        
        # For each empty cell, try to flood fill to see if it's enclosed
        def flood_fill(start_r: int, start_c: int, visited: set) -> bool:
            if (start_r, start_c) in visited:
                return True
            if (start_r, start_c) in stones:
                return True
            if (start_r, start_c) in opponent_stones:
                return False
            
            visited.add((start_r, start_c))
            result = True
            for nr, nc in get_neighbors(start_r, start_c):
                result = result and flood_fill(nr, nc, visited)
            return result

        for empty in empty_cells:
            if flood_fill(empty[0], empty[1], set()):
                return True
        return False

    def _check_bridge(self, stones: set) -> bool:
        """Check if the stones form a bridge connecting any two corners."""
        corners = [(0, 0), (0, BOARD_SIZE - 1), (BOARD_SIZE - 1, 0), 
                  (BOARD_SIZE - 1, BOARD_SIZE - 1)]
        
        # Find connected components
        visited = set()
        components = []
        
        for stone in stones:
            if stone not in visited:
                component = self._get_connected_component(stone, stones, visited)
                components.append(component)
        
        # Check if any component connects two corners
        for component in components:
            corner_count = 0
            for corner in corners:
                if corner in component:
                    corner_count += 1
            if corner_count >= 2:
                return True
        return False

    def _check_fork(self, stones: set) -> bool:
        """Check if the stones form a fork connecting any three edges."""
        edges = {"top": set(), "bottom": set(), "left": set(), "right": set()}
        
        # Categorize stones by edges
        for stone in stones:
            edge_type = get_edge_type(stone[0], stone[1])
            if edge_type and edge_type in edges:
                edges[edge_type].add(stone)
        
        # Find connected components
        visited = set()
        components = []
        
        for stone in stones:
            if stone not in visited:
                component = self._get_connected_component(stone, stones, visited)
                components.append(component)
        
        # Check if any component touches three different edges
        for component in components:
            edge_count = 0
            for edge_name, edge_stones in edges.items():
                if component & edge_stones:
                    edge_count += 1
            if edge_count >= 3:
                return True
        return False

    def _get_connected_component(self, start: Tuple[int, int], stones: set, visited: set) -> set:
        """Get the connected component containing start."""
        component = set()
        stack = [start]
        
        while stack:
            stone = stack.pop()
            if stone in visited or stone not in stones:
                continue
            visited.add(stone)
            component.add(stone)
            
            for neighbor in get_neighbors(stone[0], stone[1]):
                if neighbor in stones and neighbor not in visited:
                    stack.append(neighbor)
        
        return component

    def evaluate_position(self, row: int, col: int) -> int:
        """Evaluate the strategic value of placing a stone at (row, col)."""
        score = 0
        
        # Immediate winning move
        if self.is_winning_move(row, col, True):
            return 10000
        
        # Block opponent's winning move
        if self.is_winning_move(row, col, False):
            return 9000
        
        # Central control
        center_dist = abs(row - BOARD_SIZE // 2) + abs(col - BOARD_SIZE // 2)
        score += max(0, 15 - center_dist)
        
        # Connectivity to existing stones
        neighbor_count = 0
        for nr, nc in get_neighbors(row, col):
            if (nr, nc) in self.me:
                neighbor_count += 1
                # Bonus for connecting multiple stones
                score += 5
        
        # Edge/corner bonuses
        if is_corner(row, col):
            score += 20
        elif get_edge_type(row, col):
            score += 10
        
        # Threat creation
        if neighbor_count > 0:
            score += 15
        
        return score

def policy(me: List[Tuple[int, int]], opp: List[Tuple[int, int]], valid_mask) -> Tuple[int, int]:
    """Main policy function."""
    evaluator = GameEvaluator(me, opp)
    best_score = -float('inf')
    best_move = None
    
    valid_moves = []
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            if valid_mask[r][c] and (r, c) not in evaluator.occupied:
                valid_moves.append((r, c))
    
    if not valid_moves:
        # Fallback - should not happen in normal play
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                if valid_mask[r][c]:
                    return (r, c)
    
    # Sort moves by evaluation score to prioritize better moves
    moves_with_scores = [(move, evaluator.evaluate_position(move[0], move[1])) 
                        for move in valid_moves]
    moves_with_scores.sort(key=lambda x: x[1], reverse=True)
    
    # Consider top N moves for deeper evaluation
    top_moves = moves_with_scores[:min(10, len(moves_with_scores))]
    
    for move, base_score in top_moves:
        # Alpha-beta search with limited depth
        score = alpha_beta_search(evaluator, move, depth=2, alpha=-float('inf'), beta=float('inf'), maximizing=False)
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is None:
        best_move = valid_moves[0]  # Fallback
    
    return best_move

def alpha_beta_search(evaluator: GameEvaluator, move: Tuple[int, int], depth: int, alpha: float, beta: float, maximizing: bool) -> float:
    """Alpha-beta pruning search for better move evaluation."""
    if depth == 0:
        return evaluator.evaluate_position(move[0], move[1])
    
    # Create new evaluator state for this move
    new_me = evaluator.me | {move} if maximizing else evaluator.me
    new_opp = evaluator.opp | {move} if not maximizing else evaluator.opp
    
    new_evaluator = GameEvaluator(list(new_me), list(new_opp))
    valid_moves = [(r, c) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) 
                  if (r, c) not in new_evaluator.occupied]
    
    if maximizing:
        max_eval = -float('inf')
        for next_move in valid_moves:
            eval_score = alpha_beta_search(new_evaluator, next_move, depth - 1, alpha, beta, False)
            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, eval_score)
            if beta <= alpha:
                break
        return max_eval
    else:
        min_eval = float('inf')
        for next_move in valid_moves:
            eval_score = alpha_beta_search(new_evaluator, next_move, depth - 1, alpha, beta, True)
            min_eval = min(min_eval, eval_score)
            beta = min(beta, eval_score)
            if beta <= alpha:
                break
        return min_eval
