
def policy(state, role):
    # Parse the state
    board = {}  # (q, r, c) -> player
    phase = None
    for fact in state:
        if not fact:
            continue
        pred = fact[0]
        if pred == "cellholds":
            q = int(fact[1])
            r = int(fact[2])
            c = int(fact[3])
            player = fact[4]
            board[(q, r, c)] = player
        elif pred == "phase":
            phase = fact[1]
    
    opponent = "black" if role == "red" else "red"
    
    def to_grid(bd):
        """Convert board dict to 6x6 grid"""
        grid = [[None for _ in range(6)] for _ in range(6)]
        for (q, r, c), p in bd.items():
            gr = ((q - 1) // 2) * 3 + (r - 1)
            gc = ((q - 1) % 2) * 3 + (c - 1)
            grid[gr][gc] = p
        return grid
    
    def has_five(bd, player):
        """Check if player has 5 in a row"""
        g = to_grid(bd)
        # Horizontal
        for r in range(6):
            for c in range(2):
                if all(g[r][c + i] == player for i in range(5)):
                    return True
        # Vertical
        for c in range(6):
            for r in range(2):
                if all(g[r + i][c] == player for i in range(5)):
                    return True
        # Diagonal \
        for r in range(2):
            for c in range(2):
                if all(g[r + i][c + i] == player for i in range(5)):
                    return True
        # Diagonal /
        for r in range(2):
            for c in range(4, 6):
                if all(g[r + i][c - i] == player for i in range(5)):
                    return True
        return False
    
    def evaluate(bd):
        """Static evaluation: positive for good for role, negative for bad"""
        g = to_grid(bd)
        score = 0
        lines = []
        # Horizontal
        for r in range(6):
            for c in range(2):
                lines.append([g[r][c + i] for i in range(5)])
        # Vertical
        for c in range(6):
            for r in range(2):
                lines.append([g[r + i][c] for i in range(5)])
        # Diagonal \
        for r in range(2):
            for c in range(2):
                lines.append([g[r + i][c + i] for i in range(5)])
        # Diagonal /
        for r in range(2):
            for c in range(4, 6):
                lines.append([g[r + i][c - i] for i in range(5)])
        
        for line in lines:
            my = line.count(role)
            op = line.count(opponent)
            empty = 5 - my - op
            if my == 5:
                return 100000
            if op == 5:
                return -100000
            if op == 0:
                if my == 4:
                    score += 1000
                elif my == 3:
                    score += 100
                elif my == 2:
                    score += 10
            if my == 0:
                if op == 4:
                    score -= 1000
                elif op == 3:
                    score -= 100
                elif op == 2:
                    score -= 10
        return score
    
    def apply_rot(bd, q, direction):
        """Apply rotation to a copy of the board"""
        new_bd = {k: v for k, v in bd.items() if k[0] != q}
        # Extract cells in quadrant q
        cells = {}
        for (bq, br, bc), p in bd.items():
            if bq == q:
                cells[(br, bc)] = p
        # Rotate coordinates
        for (r, c), p in cells.items():
            if direction == "clockwise":
                nr, nc = c, 4 - r
            else:  # counterclockwise
                nr, nc = 4 - c, r
            new_bd[(q, nr, nc)] = p
        return new_bd
    
    def best_rotation_val(bd):
        """Best evaluation achievable by rotating"""
        best = -float('inf')
        for q in range(1, 5):
            for d in ["clockwise", "counterclockwise"]:
                nb = apply_rot(bd, q, d)
                val = evaluate(nb)
                if has_five(nb, role):
                    val = 100000
                if val > best:
                    best = val
        return best
    
    if phase == "place":
        # Generate empty cells
        empties = []
        for q in range(1, 5):
            for r in range(1, 4):
                for c in range(1, 4):
                    if (q, r, c) not in board:
                        empties.append((q, r, c))
        if not empties:
            return "place(1,1,1)"
        
        best_move = empties[0]
        best_score = -float('inf')
        
        for cell in empties:
            # Simulate placement
            new_bd = board.copy()
            new_bd[cell] = role
            # Check immediate win
            if has_five(new_bd, role):
                return f"place({cell[0]},{cell[1]},{cell[2]})"
            # Evaluate considering optimal rotation
            val = best_rotation_val(new_bd)
            if val > best_score:
                best_score = val
                best_move = cell
        return f"place({best_move[0]},{best_move[1]},{best_move[2]})"
    
    else:  # rotate phase
        best_move = (1, "clockwise")
        best_score = -float('inf')
        for q in range(1, 5):
            for d in ["clockwise", "counterclockwise"]:
                nb = apply_rot(board, q, d)
                if has_five(nb, role):
                    return f"rotate({q},{d})"
                val = evaluate(nb)
                if val > best_score:
                    best_score = val
                    best_move = (q, d)
        return f"rotate({best_move[0]},{best_move[1]})"
