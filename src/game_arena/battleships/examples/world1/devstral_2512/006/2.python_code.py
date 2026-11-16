
import numpy as np
from collections import deque

class BattleshipPolicy:
    def __init__(self):
        self.grid_size = 10
        self.ship_lengths = [5, 4, 3, 3, 2]
        self.probability_map = np.ones((self.grid_size, self.grid_size))
        self.hit_patterns = []
        self.target_queue = deque()
        self.last_hit = None
        self.search_direction = None
        self.initialize_probability_map()

    def initialize_probability_map(self):
        # Initialize with higher probability in central areas
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                # Distance from center (normalized)
                dist = ((i - 4.5)**2 + (j - 4.5)**2)**0.5
                self.probability_map[i][j] = max(0.1, 1 - dist/7)  # 7 is approx max distance

    def update_probability_map(self, row, col, result):
        """Update probability map based on shot result"""
        if result == -1:  # Miss
            # Reduce probability in surrounding area
            for i in range(max(0, row-1), min(self.grid_size, row+2)):
                for j in range(max(0, col-1), min(self.grid_size, col+2)):
                    self.probability_map[i][j] *= 0.5
        elif result == 1:  # Hit
            # Increase probability along potential ship directions
            for i in range(max(0, row-1), min(self.grid_size, row+2)):
                for j in range(max(0, col-1), min(self.grid_size, col+2)):
                    if (i, j) != (row, col):
                        self.probability_map[i][j] *= 1.2

            # Add to target queue for follow-up
            self.target_queue.append((row, col))
            self.last_hit = (row, col)

    def get_target_mode_move(self, board):
        """Handle moves when we have a hit to follow up on"""
        if not self.target_queue:
            return None

        # Check adjacent cells in all directions
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        row, col = self.last_hit

        # First check if we have a confirmed direction
        if self.search_direction:
            dr, dc = self.search_direction
            # Check in both directions along the axis
            for step in [1, -1]:
                r, c = row + dr*step, col + dc*step
                if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
                    if board[r][c] == 0:  # Not fired at yet
                        return (r, c)

        # If no confirmed direction, check all adjacent cells
        for dr, dc in directions:
            r, c = row + dr, col + dc
            if 0 <= r < self.grid_size and 0 <= c < self.grid_size:
                if board[r][c] == 0:
                    # Check if this could be part of the same ship
                    if self.is_valid_ship_extension(board, row, col, r, c):
                        self.search_direction = (dr, dc)
                        return (r, c)

        # If no immediate adjacent cells, use spiral search
        return self.spiral_search(board, row, col)

    def is_valid_ship_extension(self, board, r1, c1, r2, c2):
        """Check if (r2,c2) could be part of the same ship as (r1,c1)"""
        # Must be in same row or column
        if r1 != r2 and c1 != c2:
            return False

        # Check if there's a miss between them
        step_r = 1 if r2 > r1 else -1 if r2 < r1 else 0
        step_c = 1 if c2 > c1 else -1 if c2 < c1 else 0

        r, c = r1 + step_r, c1 + step_c
        while (r, c) != (r2, c2):
            if board[r][c] == -1:  # Miss in between
                return False
            r += step_r
            c += step_c

        return True

    def spiral_search(self, board, start_row, start_col, max_steps=20):
        """Perform spiral search around a hit location"""
        directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]
        step_size = 1
        current_dir = 0
        steps_taken = 0
        row, col = start_row, start_col

        visited = set()
        visited.add((row, col))

        while steps_taken < max_steps:
            for _ in range(2):  # Try each direction twice before increasing step
                dr, dc = directions[current_dir]
                for _ in range(step_size):
                    row += dr
                    col += dc
                    steps_taken += 1

                    if 0 <= row < self.grid_size and 0 <= col < self.grid_size:
                        if board[row][col] == 0 and (row, col) not in visited:
                            return (row, col)
                        visited.add((row, col))

                current_dir = (current_dir + 1) % 4

            step_size += 1

        return None

    def get_hunt_mode_move(self, board):
        """Get next move when no hits are being followed up"""
        # Find all available cells
        available = []
        for i in range(self.grid_size):
            for j in range(self.grid_size):
                if board[i][j] == 0:
                    available.append((i, j, self.probability_map[i][j]))

        if not available:
            return None  # Shouldn't happen as game would be over

        # Sort by probability (descending)
        available.sort(key=lambda x: -x[2])

        # Return the highest probability cell
        return (available[0][0], available[0][1])

# Global policy instance to maintain state between calls
policy_instance = BattleshipPolicy()

def policy(board):
    global policy_instance

    # Find all possible moves (cells with 0)
    possible_moves = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                possible_moves.append((i, j))

    if not possible_moves:
        # Shouldn't happen in normal gameplay, but return first available if any
        for i in range(10):
            for j in range(10):
                if board[i][j] != 1:  # Not a hit (could be miss or unknown)
                    return (i, j)
        return (0, 0)  # Fallback

    # Try target mode first if we have hits to follow up
    target_move = policy_instance.get_target_mode_move(board)
    if target_move:
        row, col = target_move
        # Update probability map for this move (we'll check result next call)
        policy_instance.update_probability_map(row, col, 0)  # Temporary, will update properly next call
        return target_move

    # Otherwise use hunt mode
    hunt_move = policy_instance.get_hunt_mode_move(board)
    if hunt_move:
        row, col = hunt_move
        policy_instance.update_probability_map(row, col, 0)  # Temporary
        return hunt_move

    # Fallback - return first possible move
    return possible_moves[0]
