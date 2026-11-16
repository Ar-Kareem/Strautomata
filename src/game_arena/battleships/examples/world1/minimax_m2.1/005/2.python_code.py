
import random
import time

def generate_random_placement(board, ships):
    """
    Generate a random valid ship placement consistent with the board.
    Returns a list of ship placements (each placement is a list of cell tuples) if successful, else None.
    """
    # Identify hit and miss cells
    hits = set()
    miss = set()
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.add((i, j))
            elif board[i][j] == -1:
                miss.add((i, j))
    
    # Available cells are all cells minus miss cells
    available = set((i, j) for i in range(10) for j in range(10)) - miss
    covered_hits = set()
    ships_shuffled = ships[:]  # Copy the list of ships
    random.shuffle(ships_shuffled)
    placements = []  # List to store placements for each ship
    
    def backtrack(ships_list, available, covered_hits, placements):
        if not ships_list:
            # All ships placed; check if all hits are covered
            if covered_hits == hits:
                return True
            else:
                return False
        
        ship = ships_list[0]
        # Generate all possible placements for this ship
        possible_placements = []
        for i in range(10):
            for j in range(10):
                # Horizontal placement
                if j + ship <= 10:
                    cells = [(i, j + k) for k in range(ship)]
                    if all(cell in available for cell in cells):
                        possible_placements.append(cells)
                # Vertical placement
                if i + ship <= 10:
                    cells = [(i + k, j) for k in range(ship)]
                    if all(cell in available for cell in cells):
                        possible_placements.append(cells)
        
        random.shuffle(possible_placements)  # Randomize the order of placements
        
        for placement in possible_placements:
            new_covered_hits = covered_hits | (set(placement) & hits)
            new_available = available - set(placement)
            placements.append(placement)
            if backtrack(ships_list[1:], new_available, new_covered_hits, placements):
                return True
            placements.pop()  # Backtrack
        
        return False  # No valid placement found for this ship
    
    if backtrack(ships_shuffled, available, covered_hits, placements):
        return placements
    else:
        return None

def policy(board):
    """
    Determines the next move based on Monte Carlo sampling of valid ship placements.
    Returns a tuple (row, col) representing the next cell to fire at.
    """
    ships = [5, 4, 3, 3, 2]
    num_samples = 100  # Number of random placements to sample
    probability_grid = [[0.0 for _ in range(10)] for _ in range(10)]
    sample_count = 0
    start_time = time.time()
    timeout = 0.5  # Time limit in seconds for generating samples
    
    # Generate random placements and update probability grid
    while sample_count < num_samples and time.time() - start_time < timeout:
        placement = generate_random_placement(board, ships)
        if placement is not None:
            sample_count += 1
            for ship_placement in placement:
                for cell in ship_placement:
                    i, j = cell
                    probability_grid[i][j] += 1.0
    
    # Normalize the probability grid
    for i in range(10):
        for j in range(10):
            if sample_count > 0:
                probability_grid[i][j] /= sample_count
            else:
                probability_grid[i][j] = 0.0
    
    # Select the cell with the highest probability that has not been fired at
    best_cell = None
    best_prob = -1.0
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:  # Cell has not been fired at
                if probability_grid[i][j] > best_prob:
                    best_prob = probability_grid[i][j]
                    best_cell = (i, j)
    
    # Fallback to random unknown cell if no samples were generated
    if best_cell is None:
        unknown_cells = [(i, j) for i in range(10) for j in range(10) if board[i][j] == 0]
        if unknown_cells:
            best_cell = random.choice(unknown_cells)
        else:
            # If all cells are known, return a dummy value (should not happen in practice)
            best_cell = (0, 0)
    
    return best_cell
