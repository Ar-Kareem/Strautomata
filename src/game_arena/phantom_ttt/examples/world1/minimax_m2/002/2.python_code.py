
import itertools

# Precompute the lines for three in a row
lines = [
    [0, 1, 2],  # Row 0
    [3, 4, 5],  # Row 1
    [6, 7, 8],  # Row 2
    [0, 3, 6],  # Col 0
    [1, 4, 7],  # Col 1
    [2, 5, 8],  # Col 2
    [0, 4, 8],  # Diag 0
    [2, 4, 6]   # Diag 1
]

# All cells bitmask (9 bits set)
ALL_CELLS = (1 << 9) - 1  # 511

# Function to check if a set has three in a row
def has_win(bitmask):
    for line in lines:
        if all(bitmask & (1 << cell) for cell in line):
            return True
    return False

# Function to check if there are no empty cells
def is_full(bitmask):
    return bitmask == ALL_CELLS

# Memoization dictionary for the value function
memo = {}

def value_function(s_mask, t_mask, turn):
    """
    Compute the probability of winning for the current player (me) given state (s_mask, t_mask) and turn.
    s_mask: bitmask of my marks
    t_mask: bitmask of opponent's marks
    turn: "me" or "opponent"
    """
    key = (s_mask, t_mask, turn)
    if key in memo:
        return memo[key]

    # Check if turn is consistent with the number of marks
    s_count = bin(s_mask).count('1')
    t_count = bin(t_mask).count('1')
    if turn == "me":
        if s_count != t_count:
            memo[key] = 0.0
            return 0.0
    else:  # turn == "opponent"
        if s_count != t_count + 1:
            memo[key] = 0.0
            return 0.0

    # Check for wins
    if has_win(s_mask):
        memo[key] = 1.0
        return 1.0
    if has_win(t_mask):
        memo[key] = 0.0
        return 0.0

    # Check for draw
    if is_full(s_mask | t_mask):
        memo[key] = 0.0
        return 0.0

    if turn == "me":
        # My turn: I choose a move
        u_mask = ALL_CELLS ^ s_mask  # cells not in my marks
        max_value = -1.0
        for m in range(9):
            if u_mask & (1 << m):
                if t_mask & (1 << m):  # I fail
                    val = value_function(s_mask, t_mask, "opponent")
                else:  # I succeed
                    val = value_function(s_mask | (1 << m), t_mask, "opponent")
                if val > max_value:
                    max_value = val
        memo[key] = max_value
        return max_value
    else:  # turn == "opponent"
        # Opponent's turn: opponent chooses a move
        v_mask = ALL_CELLS ^ t_mask  # cells not in opponent's marks
        max_value = -1.0
        for n in range(9):
            if v_mask & (1 << n):
                if s_mask & (1 << n):  # opponent fails
                    val = value_function(s_mask, t_mask, "me")
                else:  # opponent succeeds
                    val = value_function(s_mask, t_mask | (1 << n), "me")
                if val > max_value:
                    max_value = val
        memo[key] = max_value
        return max_value

# Precompute all value functions for all states
# This is done by calling value_function for all relevant states to populate the memo
# We will iterate over all possible s_mask and t_mask with s_mask & t_mask == 0
for s_mask in range(ALL_CELLS + 1):
    for t_mask in range(ALL_CELLS + 1):
        if s_mask & t_mask == 0:
            # Check if the state is valid for some turn
            s_count = bin(s_mask).count('1')
            t_count = bin(t_mask).count('1')
            if s_count == t_count:
                value_function(s_mask, t_mask, "me")
            if s_count == t_count + 1:
                value_function(s_mask, t_mask, "opponent")

def policy(board, legal_moves):
    """
    Compute the next move for Phantom Tic Tac Toe.
    :param board: 3x3 list of lists, 1 for my mark, 0 for unknown
    :param legal_moves: list of integers (0-8) allowed by the engine
    :return: tuple (row, col) for the move
    """
    # Convert board to bitmask for my marks
    s_mask = 0
    for r in range(3):
        for c in range(3):
            if board[r][c] == 1:
                s_mask |= (1 << (r * 3 + c))
    
    k = bin(s_mask).count('1')
    u_mask = ALL_CELLS ^ s_mask  # unknown cells
    # Generate all possible opponent mark configurations for averaging
    # T must be a subset of u_mask with size k
    u_cells = [i for i in range(9) if u_mask & (1 << i)]
    t_combinations = list(itertools.combinations(u_cells, k)) if k <= len(u_cells) else []
    
    best_move = None
    best_value = -1.0
    for m in legal_moves:
        if not (u_mask & (1 << m)):
            continue  # m should be in u_mask, but legal_moves might not cover all, so check
        
        expected_value = 0.0
        for t_comb in t_combinations:
            t_mask = 0
            for cell in t_comb:
                t_mask |= (1 << cell)
            
            # Check if m in T
            if t_mask & (1 << m):
                val = value_function(s_mask, t_mask, "opponent")
            else:
                val = value_function(s_mask | (1 << m), t_mask, "opponent")
            expected_value += val
        
        if t_combinations:
            expected_value /= len(t_combinations)
        
        if expected_value > best_value:
            best_value = expected_value
            best_move = m
    
    if best_move is None:
        # Should not happen, but fall back to first legal move
        best_move = legal_moves[0]
    
    row = best_move // 3
    col = best_move % 3
    return (row, col)
