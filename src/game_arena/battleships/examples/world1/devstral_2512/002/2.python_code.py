
import random

class BattleshipPolicy:
    def __init__(self):
        self.targets = []
        self.fired_cells = set()
        self.initialize_targets()

    def initialize_targets(self):
        # Initialize targets in a checkerboard pattern
        for row in range(10):
            for col in range(10):
                if (row + col) % 2 == 0:
                    self.targets.append((row, col))
        # Shuffle to add some randomness
        random.shuffle(self.targets)

    def policy(self, board):
        # Check for hits and prioritize adjacent cells
        hits = []
        for row in range(10):
            for col in range(10):
                if board[row][col] == 1:
                    hits.append((row, col))

        if hits:
            # If there are hits, prioritize adjacent cells
            for hit in hits:
                row, col = hit
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    new_row, new_col = row + dr, col + dc
                    if 0 <= new_row < 10 and 0 <= new_col < 10:
                        if board[new_row][new_col] == 0 and (new_row, new_col) not in self.fired_cells:
                            # Insert at the beginning to prioritize
                            if (new_row, new_col) not in self.targets:
                                self.targets.insert(0, (new_row, new_col))

        # Find the next target that hasn't been fired at
        for target in self.targets:
            row, col = target
            if board[row][col] == 0 and (row, col) not in self.fired_cells:
                self.fired_cells.add((row, col))
                return (row, col)

        # If all targets are exhausted, reinitialize (shouldn't happen in practice)
        self.fired_cells.clear()
        self.initialize_targets()
        return self.policy(board)

# Initialize the policy instance
policy_instance = BattleshipPolicy()

def policy(board):
    return policy_instance.policy(board)
