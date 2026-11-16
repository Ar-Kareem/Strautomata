
import itertools

class GameMemory:
    """
    Singleton class to persist game state information across multiple policy calls.
    Tracks probabilities of cells being empty and history of attempts.
    """
    _instance = None
    
    def __init__(self):
        # Probability that each cell (0-8) is empty. Initialize with 1.0 (likely empty).
        self.empty_probs = [1.0] * 9
        # History of results for each cell index: list of booleans (True=Success, False=Fail).
        self.attempt_history = {} 
        # Store the flattened board state from the previous turn to detect changes.
        self.last_board_flat = None
        # Store the index of the move made in the previous turn.
        self.last_move_made = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = GameMemory()
        return cls._instance

def policy(board: list[list[int]], legal_moves: list[int]) -> tuple[int, int]:
    memory = GameMemory.get_instance()
    
    # 1. Flatten the board for easier access (0-8 indices)
    # board[row][col] -> flat[row * 3 + col]
    flat_board = [cell for row in board for cell in row]
    
    # 2. Detect Game Reset
    # If the number of '1's decreased (or we have no history), reset memory.
    # This handles cases where the engine resets the game.
    if memory.last_board_flat is None:
        # First call, just init
        pass
    else:
        current_ones = sum(flat_board)
        prev_ones = sum(memory.last_board_flat)
        if current_ones < prev_ones:
            # Game reset detected
            memory.empty_probs = [1.0] * 9
            memory.attempt_history = {}
            memory.last_move_made = None

    # 3. Update Probabilities based on the outcome of the previous move
    if memory.last_move_made is not None:
        move = memory.last_move_made
        if 0 <= move < 9:
            # Determine outcome: Did the cell become 1 (Success) or stay 0 (Fail)?
            # Note: In Phantom Tic Tac Toe, you don't see opponent marks.
            # If we placed successfully, it becomes 1. If we placed on occupied, it stays 0.
            if flat_board[move] == 1:
                # Success: The cell was empty. It is now confirmed ours (empty).
                if move not in memory.attempt_history:
                    memory.attempt_history[move] = []
                memory.attempt_history[move].append(True)
                memory.empty_probs[move] = 0.0  # Confirmed empty/owned
            else:
                # Failure: The cell was occupied (by opponent or previously missed).
                if move not in memory.attempt_history:
                    memory.attempt_history[move] = []
                memory.attempt_history[move].append(False)
                
                # Decrease probability based on failure count
                # If we failed once, 50% chance it's empty (uncertain).
                # If failed twice, 25% chance, etc.
                fails = memory.attempt_history[move].count(False)
                new_prob = 1.0
                for _ in range(fails):
                    new_prob *= 0.5
                # Keep the lower probability (don't increase if we previously thought it was low)
                memory.empty_probs[move] = min(memory.empty_probs[move], new_prob)

    # 4. Fix probabilities for cells that are currently '1' (confirmed ours)
    # These are definitely empty (occupied by us).
    for idx, cell in enumerate(flat_board):
        if cell == 1:
            memory.empty_probs[idx] = 0.0

    # 5. Move Selection Logic
    
    # Helper: Get indices of our confirmed '1's
    my_indices = [i for i, x in enumerate(flat_board) if x == 1]
    
    # Heuristic values for cells: Center (4) is best, Corners (0,2,6,8) next, Edges (1,3,5,7) last
    cell_heuristics = {
        0: 0.8, 1: 0.0, 2: 0.8,
        3: 0.0, 4: 1.0, 5: 0.0,
        6: 0.8, 7: 0.0, 8: 0.8
    }

    # Determine potential winning/setup lines
    lines = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Rows
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Cols
        [0, 4, 8], [2, 4, 6]             # Diagonals
    ]

    # 5a. Immediate Win Check
    # Look for lines with 2 of my '1's and 1 '0'
    winning_moves = []
    for line in lines:
        line_cells = [flat_board[i] for i in line]
        if line_cells.count(1) == 2 and line_cells.count(0) == 1:
            # Find the '0'
            target_idx = line[line_cells.index(0)]
            winning_moves.append(target_idx)
    
    # 5b. Setup/Threat Check
    # Look for lines with 1 of my '1's and 2 '0's. Prioritize these moves.
    setup_moves = []
    for line in lines:
        line_cells = [flat_board[i] for i in line]
        if line_cells.count(1) == 1 and line_cells.count(0) == 2:
            for idx in line:
                if flat_board[idx] == 0:
                    setup_moves.append(idx)

    # 5c. Filter Legal Moves
    # Remove moves that are already confirmed '1' (shouldn't be in legal_moves, but safe to check)
    # Also remove moves that have very low probability of being empty (unless no other options)
    candidates = []
    for move in legal_moves:
        if flat_board[move] == 1:
            continue # Already confirmed mine
        candidates.append(move)

    # 5d. Scoring and Selection
    # Prefer: 1. Immediate Win -> 2. Setup Moves -> 3. High Probability + Heuristic
    best_score = -1.0
    best_move = None
    
    # Prioritize immediate win
    for move in candidates:
        if move in winning_moves:
            return (move // 3, move % 3)

    # Score remaining candidates
    # We want to explore (high probability of empty) and exploit (good heuristic value)
    for move in candidates:
        prob_empty = memory.empty_probs[move]
        
        # Base score is probability it is empty
        score = prob_empty
        
        # Add heuristic boost (normalized)
        score += cell_heuristics[move] * 0.1
        
        # Boost if it is a setup move (creates potential for future win)
        if move in setup_moves:
            score += 0.2
        
        # If we have failed this move before, it should have lower probability already,
        # but we add a small penalty to break ties against untried moves if needed.
        if move in memory.attempt_history:
            if False in memory.attempt_history[move]:
                score -= 0.05

        if score > best_score:
            best_score = score
            best_move = move

    # Fallback: If no move selected (e.g. candidates empty or scores very low), pick random legal
    if best_move is None and candidates:
        best_move = candidates[0] # Pick first available or random

    # 6. Store State for Next Turn
    memory.last_board_flat = flat_board
    memory.last_move_made = best_move

    # 7. Return Result
    # Return (row, col) as requested
    return (best_move // 3, best_move % 3)
