
def policy(me, opponent, memory):
    """
    Policy function for Go game that selects the next move based on proximity to opponent stones and board center.
    
    Parameters:
    - me (list[tuple[int, int]]): List of (row, column) tuples representing the current player's stones.
    - opponent (list[tuple[int, int]]): List of (row, column) tuples representing the opponent's stones.
    - memory (dict): Optional dictionary to retain state between moves (not currently used).
    
    Returns:
    - tuple: A tuple (action, memory) where action is the next move (tuple[int, int]) and memory is to be updated.
    """
    candidates = []

    # Check all cells on the board
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) in me or (r, c) in opponent:
                continue  # Skip occupied cells

            # Check for at least one liberty
            has_liberty = False
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    if (nr, nc) not in me and (nr, nc) not in opponent:
                        has_liberty = True
                        break

            if has_liberty:
                candidates.append((r, c))

    if not candidates:
        return ((0, 0), memory)  # No legal move, pass

    # Heuristic to choose best move
    def eval_move(pos):
        r, c = pos
        op_count = 0
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if (nr, nc) in opponent:
                    op_count += 1
        
        distance_to_center = abs(r - 10) + abs(c - 10)
        return (-op_count, distance_to_center, r, c)

    # Sort candidates based on the heuristic
    candidates.sort(key=lambda p: (eval_move(p), p[0], p[1]))
    
    return ((candidates[0][0], candidates[0][1]), {})
