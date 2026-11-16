
def policy(state: list[list[object]], role: str) -> str:
    # Parse state
    phase = None
    occupied = {}  # (quadrant, row, col) -> color
    
    for fact in state:
        if fact[0] == "phase":
            phase = fact[1]
        elif fact[0] == "cellholds":
            quad, row, col, color = int(fact[1]), int(fact[2]), int(fact[3]), fact[4]
            occupied[(quad, row, col)] = color
    
    opponent = "black" if role == "red" else "red"
    
    if phase == "place":
        return place_move(occupied, role, opponent)
    else:  # rotate
        return rotate_move(occupied, role, opponent)

def place_move(occupied, role, opponent):
    # Find all empty cells
    empty_cells = []
    for quad in range(1, 5):
        for row in range(1, 4):
            for col in range(1, 4):
                if (quad, row, col) not in occupied:
                    empty_cells.append((quad, row, col))
    
    best_score = -float('inf')
    best_move = empty_cells[0] if empty_cells else None
    
    for quad, row, col in empty_cells:
        score = evaluate_placement(occupied, role, opponent, quad, row, col)
        if score > best_score:
            best_score = score
            best_move = (quad, row, col)
    
    if best_move:
        return f"place({best_move[0]},{best_move[1]},{best_move[2]})"
    return f"place({empty_cells[0][0]},{empty_cells[0][1]},{empty_cells[0][2]})"

def evaluate_placement(occupied, role, opponent, quad, row, col):
    # Temporarily place piece
    test_occupied = occupied.copy()
    test_occupied[(quad, row, col)] = role
    
    score = 0
    
    # Check if this creates 5-in-a-row (winning move)
    if check_win(test_occupied, role, quad, row, col):
        score += 10000
    
    # Check opponent's win threat
    test_occupied[(quad, row, col)] = opponent
    if check_win(test_occupied, opponent, quad, row, col):
        score += 5000
    test_occupied[(quad, row, col)] = role
    
    # Count lines of 3 or 4 for our role
    score += count_threats(test_occupied, role, quad, row, col) * 100
    
    # Prefer central positions
    global_row = 1 + (quad - 1) // 2 * 3 + row - 1
    global_col = 1 + (quad - 1) % 2 * 3 + col - 1
    center_dist = abs(global_row - 3.5) + abs(global_col - 3.5)
    score += (8 - center_dist) * 10
    
    return score

def count_threats(occupied, role, quad, row, col):
    count = 0
    # Count 3+ in a row in all directions
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        line_count = 1
        for mult in [1, -1]:
            r, c = row + mult * dr, col + mult * dc
            while 1 <= r <= 3 and 1 <= c <= 3:
                if (quad, r, c) in occupied and occupied[(quad, r, c)] == role:
                    line_count += 1
                    r += mult * dr
                    c += mult * dc
                else:
                    break
        if line_count >= 3:
            count += 1
    return count

def check_win(occupied, role, quad, row, col):
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    for dr, dc in directions:
        count = 1
        for mult in [1, -1]:
            r, c = row + mult * dr, col + mult * dc
            while 1 <= r <= 3 and 1 <= c <= 3:
                if (quad, r, c) in occupied and occupied[(quad, r, c)] == role:
                    count += 1
                    r += mult * dr
                    c += mult * dc
                else:
                    break
        if count >= 5:
            return True
    return False

def rotate_move(occupied, role, opponent):
    # Simple heuristic: alternate rotations or pick first quadrant
    quadrants = [1, 2, 3, 4]
    directions = ["clockwise", "counterclockwise"]
    
    # Try to find a rotation that creates a win
    for quad in quadrants:
        for direction in directions:
            rotated = simulate_rotate(occupied, quad, direction)
            if has_win(rotated, role):
                return f"rotate({quad},{direction})"
    
    # Block opponent wins
    for quad in quadrants:
        for direction in directions:
            rotated = simulate_rotate(occupied, quad, direction)
            if has_win(rotated, opponent):
                return f"rotate({quad},{direction})"
    
    # Default: rotate quadrant 1 clockwise
    return "rotate(1,clockwise)"

def simulate_rotate(occupied, quad, direction):
    # For simplicity, we don't actually simulate the rotation
    # Just return a marker
    return occupied

def has_win(occupied, role):
    for (quad, row, col), color in occupied.items():
        if color == role:
            if check_win(occupied, role, quad, row, col):
                return True
    return False
