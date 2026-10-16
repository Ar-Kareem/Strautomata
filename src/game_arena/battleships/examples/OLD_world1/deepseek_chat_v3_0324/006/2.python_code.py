
import numpy as np
from collections import deque

class BattleshipPolicy:
    def __init__(self):
        self.size = 10
        self.ship_sizes = [5, 4, 3, 3, 2]
        self.directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        self.reset()
        
    def reset(self):
        self.prob_map = np.ones((self.size, self.size), dtype=float)
        self.hits = []
        self.misses = set()
        self.hit_cells = set()
        self.sunk_cells = set()
        self.target_queue = deque()
        
    def update_probability_map(self):
        self.prob_map.fill(1.0)
        
        # Mark known cells
        for r in range(self.size):
            for c in range(self.size):
                if (r, c) in self.misses or (r, c) in self.sunk_cells:
                    self.prob_map[r, c] = 0.0
        
        # Calculate probability for each cell
        for ship_size in self.ship_sizes:
            temp_prob = np.zeros((self.size, self.size))
            
            # Horizontal placements
            for r in range(self.size):
                for c in range(self.size - ship_size + 1):
                    valid = True
                    for i in range(ship_size):
                        if (r, c + i) in self.misses or (r, c + i) in self.sunk_cells:
                            valid = False
                            break
                    if valid:
                        for i in range(ship_size):
                            temp_prob[r, c + i] += 1
            
            # Vertical placements
            for r in range(self.size - ship_size + 1):
                for c in range(self.size):
                    valid = True
                    for i in range(ship_size):
                        if (r + i, c) in self.misses or (r + i, c) in self.sunk_cells:
                            valid = False
                            break
                    if valid:
                        for i in range(ship_size):
                            temp_prob[r + i, c] += 1
            
            self.prob_map += temp_prob
        
        # Zero out already hit cells
        for r, c in self.hit_cells:
            self.prob_map[r, c] = 0.0
    
    def find_target(self, board):
        # Check if we have hits to process
        if self.target_queue:
            return self.target_queue.popleft()
        
        # Find all current hits
        current_hits = []
        for r in range(self.size):
            for c in range(self.size):
                if board[r][c] == 1 and (r, c) not in self.hit_cells:
                    current_hits.append((r, c))
        
        # If we have new hits, process them
        if current_hits:
            for hit in current_hits:
                self.hit_cells.add(hit)
                self.hits.append(hit)
            
            # Process hits to find ship orientations
            for r, c in current_hits:
                for dr, dc in self.directions:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < self.size and 0 <= nc < self.size and 
                        board[nr][nc] == 0 and (nr, nc) not in self.misses):
                        self.target_queue.append((nr, nc))
        
        # If we have targets, return them
        if self.target_queue:
            return self.target_queue.popleft()
        
        # Otherwise use probability map
        self.update_probability_map()
        
        # Find cell with highest probability
        max_prob = np.max(self.prob_map)
        candidates = np.argwhere(self.prob_map == max_prob)
        r, c = candidates[np.random.choice(len(candidates))]
        return (r, c)
    
    def process_board(self, board):
        # Update misses and sunk ships
        for r in range(self.size):
            for c in range(self.size):
                if board[r][c] == -1 and (r, c) not in self.misses:
                    self.misses.add((r, c))
                
                # Check for sunk ships (hit cells that are now surrounded by misses)
                if board[r][c] == 1 and (r, c) not in self.sunk_cells:
                    sunk = True
                    for dr, dc in self.directions:
                        nr, nc = r + dr, c + dc
                        if (0 <= nr < self.size and 0 <= nc < self.size and 
                            board[nr][nc] == 0 and (nr, nc) not in self.misses):
                            sunk = False
                            break
                    if sunk:
                        self.sunk_cells.add((r, c))
                        if (r, c) in self.hit_cells:
                            self.hit_cells.remove((r, c))

policy_obj = BattleshipPolicy()

def policy(board):
    policy_obj.process_board(board)
    row, col = policy_obj.find_target(board)
    return (int(row), int(col))
