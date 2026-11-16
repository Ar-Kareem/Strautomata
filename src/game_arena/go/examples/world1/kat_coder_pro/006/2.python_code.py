
import random
import numpy as np
from typing import List, Tuple, Set, Dict
from collections import defaultdict

# Board size constants
BOARD_SIZE = 19
ROWS = COLUMNS = BOARD_SIZE

# Direction offsets for neighbors (up, down, left, right)
DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

class GoPolicy:
    def __init__(self):
        self.board = np.zeros((ROWS, COLUMNS), dtype=int)
        self.my_stones = set()
        self.opponent_stones = set()
        self.empty_points = set((r, c) for r in range(ROWS) for c in range(COLUMNS))
        
    def update_board(self, me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]):
        """Update internal board state"""
        self.board = np.zeros((ROWS, COLUMNS), dtype=int)
        self.my_stones = set()
        self.opponent_stones = set()
        
        for r, c in me:
            self.board[r-1, c-1] = 1  # 1 for my stones
            self.my_stones.add((r-1, c-1))
            
        for r, c in opponent:
            self.board[r-1, c-1] = 2  # 2 for opponent stones
            self.opponent_stones.add((r-1, c-1))
            
        self.empty_points = set()
        for r in range(ROWS):
            for c in range(COLUMNS):
                if self.board[r, c] == 0:
                    self.empty_points.add((r, c))
    
    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        """Get valid neighboring coordinates"""
        neighbors = []
        for dr, dc in DIRECTIONS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLUMNS:
                neighbors.append((nr, nc))
        return neighbors
    
    def get_group_liberties(self, r: int, c: int, color: int) -> int:
        """Count liberties for a group of stones"""
        visited = set()
        queue = [(r, c)]
        visited.add((r, c))
        liberties = 0
        
        while queue:
            curr_r, curr_c = queue.pop(0)
            for nr, nc in self.get_neighbors(curr_r, curr_c):
                if (nr, nc) not in visited:
                    if self.board[nr, nc] == 0:
                        liberties += 1
                    elif self.board[nr, nc] == color:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                        
        return liberties
    
    def evaluate_move(self, r: int, c: int) -> float:
        """Evaluate the quality of a move"""
        score = 0.0
        
        # Basic safety check - avoid suicidal moves
        if self.is_suicidal(r, c):
            return -1000.0
            
        # Distance from existing stones
        min_dist = float('inf')
        for my_r, my_c in self.my_stones:
            dist = abs(r - my_r) + abs(c - my_c)
            min_dist = min(min_dist, dist)
            
        # Prefer moves that are not too close or too far from existing stones
        if min_dist < 2:
            score -= 1.0  # Too close
        elif min_dist > 6:
            score -= 0.5  # Too far
            
        # Influence score - prefer central positions
        center_r, center_c = ROWS // 2, COLUMNS // 2
        dist_from_center = abs(r - center_r) + abs(c - center_c)
        score += max(0, 5.0 - dist_from_center * 0.2)
        
        # Territory potential
        neighbors = self.get_neighbors(r, c)
        empty_neighbors = sum(1 for nr, nc in neighbors if self.board[nr, nc] == 0)
        my_neighbors = sum(1 for nr, nc in neighbors if self.board[nr, nc] == 1)
        opponent_neighbors = sum(1 for nr, nc in neighbors if self.board[nr, nc] == 2)
        
        # Prefer moves with empty neighbors (territory expansion)
        score += empty_neighbors * 0.3
        # Prefer moves connected to our stones
        score += my_neighbors * 0.5
        # Be cautious of opponent pressure
        score -= opponent_neighbors * 0.2
        
        # Capture potential
        captures = self.count_captures(r, c)
        score += captures * 5.0
        
        # Threat assessment - avoid moves that give opponent easy captures
        opponent_threats = self.count_opponent_threats(r, c)
        score -= opponent_threats * 2.0
        
        return score
    
    def is_suicidal(self, r: int, c: int) -> bool:
        """Check if placing a stone here would be suicidal"""
        # Temporarily place the stone
        self.board[r, c] = 1
        
        # Check if the new stone has any liberties
        liberties = self.get_group_liberties(r, c, 1)
        
        # Remove the temporary stone
        self.board[r, c] = 0
        
        return liberties == 0
    
    def count_captures(self, r: int, c: int) -> int:
        """Count how many opponent stones would be captured"""
        captures = 0
        self.board[r, c] = 1  # Temporarily place our stone
        
        for nr, nc in self.get_neighbors(r, c):
            if self.board[nr, nc] == 2:  # Opponent stone
                liberties = self.get_group_liberties(nr, nc, 2)
                if liberties == 0:
                    captures += 1
                    
        self.board[r, c] = 0  # Remove temporary stone
        return captures
    
    def count_opponent_threats(self, r: int, c: int) -> int:
        """Count potential threats from opponent if we play here"""
        threats = 0
        self.board[r, c] = 1  # Temporarily place our stone
        
        for nr, nc in self.get_neighbors(r, c):
            if self.board[nr, nc] == 2:  # Opponent stone
                # Check if opponent could capture us by playing adjacent
                for nnr, nnc in self.get_neighbors(nr, nc):
                    if self.board[nnr, nnc] == 0:  # Empty point
                        # Temporarily place opponent stone
                        self.board[nnr, nnc] = 2
                        # Check if our group would be captured
                        liberties = self.get_group_liberties(r, c, 1)
                        if liberties == 0:
                            threats += 1
                        self.board[nnr, nnc] = 0  # Remove temporary opponent stone
                        
        self.board[r, c] = 0  # Remove temporary stone
        return threats
    
    def get_best_move(self) -> Tuple[int, int]:
        """Find the best move using our evaluation"""
        if not self.empty_points:
            return (0, 0)  # Pass if board is full
            
        # If first move, play in center
        if not self.my_stones and not self.opponent_stones:
            return (10, 10)
            
        # If opponent played first, respond appropriately
        if len(self.opponent_stones) == 1 and not self.my_stones:
            # Play near opponent's first move but not too close
            opp_r, opp_c = next(iter(self.opponent_stones))
            # Try to find a good response point
            candidates = []
            for dr in [-3, -2, -1, 0, 1, 2, 3]:
                for dc in [-3, -2, -1, 0, 1, 2, 3]:
                    if abs(dr) + abs(dc) == 3:  # L-shaped distance
                        nr, nc = opp_r + dr, opp_c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLUMNS:
                            candidates.append((nr, nc))
            
            if candidates:
                return random.choice(candidates)
                
        # Evaluate all possible moves
        best_score = float('-inf')
        best_moves = []
        
        # Limit search space for performance
        search_points = list(self.empty_points)
        if len(search_points) > 100:  # If board has many empty points
            # Focus on area around existing stones
            relevant_points = set()
            for r, c in self.my_stones | self.opponent_stones:
                for dr in range(-3, 4):
                    for dc in range(-3, 4):
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < ROWS and 0 <= nc < COLUMNS:
                            relevant_points.add((nr, nc))
            search_points = list(relevant_points & self.empty_points)
            
        for r, c in search_points:
            score = self.evaluate_move(r, c)
            if score > best_score:
                best_score = score
                best_moves = [(r, c)]
            elif score == best_score:
                best_moves.append((r, c))
                
        if not best_moves:
            return (0, 0)  # Pass
            
        # Choose randomly among best moves to add variety
        best_r, best_c = random.choice(best_moves)
        return (best_r + 1, best_c + 1)  # Convert to 1-based indexing

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    """
    Main policy function that returns the next move.
    
    Args:
        me: List of (row, col) tuples for my stones (1-based)
        opponent: List of (row, col) tuples for opponent stones (1-based)
        
    Returns:
        (row, col) tuple for next move (1-based), or (0, 0) to pass
    """
    go_policy = GoPolicy()
    go_policy.update_board(me, opponent)
    return go_policy.get_best_move()
