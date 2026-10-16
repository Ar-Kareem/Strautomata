
import copy

# Precomputed board geometry
ROWS = "abcdefghi"
COLS = "123456789"
VERT_NAMES = ["a5","a6","a7","a8","a9","b9","c9","d9","e9"]
UNUSABLE = {(1,7), (3,5), (4,1), (4,3), (5,4), (7,4)}  # (r_idx, c_idx) 0-indexed

# Build valid cells and line mappings
VALID_CELLS = set()
CELL_LINES = {}  # (r,c) -> [("letter",r), ("number",c), ("vertical", v_idx)]
LINE_CELLS = {}  # (type, id) -> set of (r,c)
LINE_LENGTH = {}  # (type, id) -> int

for r in range(9):
    for c in range(9):
        # Check bounds using 1-indexed logic then convert
        r1 = r + 1
        c1 = c + 1
        min_c1 = max(1, 6 - r1)
        max_c1 = min(9, 14 - r1)
        if c1 < min_c1 or c1 > max_c1:
            continue
        if (r, c) in UNUSABLE:
            continue
        VALID_CELLS.add((r, c))
        v_idx = r + c - 4  # sum ranges 4-12, map to 0-8
        lines = [("letter", r), ("number", c), ("vertical", v_idx)]
        CELL_LINES[(r, c)] = lines
        for line in lines:
            if line not in LINE_CELLS:
                LINE_CELLS[line] = set()
            LINE_CELLS[line].add((r, c))

for line, cells in LINE_CELLS.items():
    LINE_LENGTH[line] = len(cells)

def policy(state: list[list[object]], role: str) -> str:
    opponent = "blue" if role == "red" else "red"
    
    # Parse occupied cells
    occupied = {}  # (r,c) -> color
    for fact in state:
        if fact[0] == "cell":
            row_char, col_char, color = fact[1], fact[2], fact[3]
            r = ROWS.index(row_char)
            c = COLS.index(col_char)
            occupied[(r, c)] = color
    
    # Initialize line counts and won lines from occupied
    line_counts = {}  # (line, color) -> count
    lines_won = {role: {"letter": 0, "number": 0, "vertical": 0},
                 opponent: {"letter": 0, "number": 0, "vertical": 0}}
    
    for (r, c), color in occupied.items():
        for line in CELL_LINES[(r, c)]:
            key = (line, color)
            line_counts[key] = line_counts.get(key, 0) + 1
    
    # Determine won lines
    for line, cells in LINE_CELLS.items():
        l_type = line[0]
        length = LINE_LENGTH[line]
        maj = length // 2 + 1
        for color in [role, opponent]:
            cnt = line_counts.get((line, color), 0)
            if cnt >= maj:
                lines_won[color][l_type] += 1
    
    # Get legal moves
    legal = list(VALID_CELLS - set(occupied.keys()))
    if not legal:
        return "place(a,5)"  # Should not happen
    
    # Quick check for immediate win
    for move in legal:
        val = simulate_move_value(occupied, line_counts, lines_won, move, role, opponent, check_only_win=True)
        if val > 90000:  # Winning move
            r, c = move
            return f"place({ROWS[r]},{c+1})"
    
    # Determine search depth
    n_legal = len(legal)
    if n_legal <= 10:
        depth = 4
    elif n_legal <= 20:
        depth = 3
    else:
        depth = 3  # Safe for 1 second
    
    # Alpha-beta search
    best_val, best_move = alphabeta(set(occupied.keys()), dict(line_counts), 
                                    {c: dict(d) for c, d in lines_won.items()},
                                    depth, True, role, opponent, -float('inf'), float('inf'))
    
    if best_move is None:
        best_move = legal[0]
    
    r, c = best_move
    return f"place({ROWS[r]},{c+1})"

def alphabeta(occ_set, l_counts, l_won, depth, is_maximizing, me, opp, alpha, beta):
    # Check terminal
    my_dirs = sum(1 for d in ["letter","number","vertical"] if l_won[me][d] >= 5)
    opp_dirs = sum(1 for d in ["letter","number","vertical"] if l_won[opp][d] >= 5)
    
    if my_dirs >= 2:
        return 100000, None
    if opp_dirs >= 2:
        return -100000, None
    if depth == 0:
        return evaluate(l_counts, l_won, me, opp), None
    
    legal = list(VALID_CELLS - occ_set)
    if not legal:
        return 0, None
    
    player = me if is_maximizing else opp
    best_move = None
    
    # Sort moves: check winning moves first for better pruning
    if is_maximizing:
        best_val = -float('inf')
        for move in legal:
            newly_won, added = apply_move(occ_set, l_counts, l_won, move, player)
            # Check immediate win
            if l_won[player]["letter"] >= 5 or l_won[player]["number"] >= 5 or l_won[player]["vertical"] >= 5:
                val = 100000 if player == me else -100000
            else:
                val, _ = alphabeta(occ_set, l_counts, l_won, depth-1, not is_maximizing, me, opp, alpha, beta)
            undo_move(occ_set, l_counts, l_won, move, player, newly_won, added)
            
            if val > best_val:
                best_val = val
                best_move = move
            alpha = max(alpha, val)
            if beta <= alpha:
                break
        return best_val, best_move
    else:
        best_val = float('inf')
        for move in legal:
            newly_won, added = apply_move(occ_set, l_counts, l_won, move, player)
            # Check immediate win for opponent (bad for us)
            if l_won[player]["letter"] >= 5 or l_won[player]["number"] >= 5 or l_won[player]["vertical"] >= 5:
                val = -100000 if player == opp else 100000
            else:
                val, _ = alphabeta(occ_set, l_counts, l_won, depth-1, not is_maximizing, me, opp, alpha, beta)
            undo_move(occ_set, l_counts, l_won, move, player, newly_won, added)
            
            if val < best_val:
                best_val = val
                best_move = move
            beta = min(beta, val)
            if beta <= alpha:
                break
        return best_val, best_move

def apply_move(occ_set, l_counts, l_won, move, player):
    occ_set.add(move)
    newly_won_types = []
    added_counts = []
    for line in CELL_LINES[move]:
        key = (line, player)
        old = l_counts.get(key, 0)
        new = old + 1
        l_counts[key] = new
        added_counts.append((line, player, old))
        
        length = LINE_LENGTH[line]
        maj = length // 2 + 1
        if new >= maj and old < maj:
            line_type = line[0]
            l_won[player][line_type] += 1
            newly_won_types.append(line_type)
    return newly_won_types, added_counts

def undo_move(occ_set, l_counts, l_won, move, player, newly_won_types, added_counts):
    occ_set.remove(move)
    for line_type in newly_won_types:
        l_won[player][line_type] -= 1
    for line, color, old_val in added_counts:
        if old_val == 0:
            del l_counts[(line, color)]
        else:
            l_counts[(line, color)] = old_val

def evaluate(l_counts, l_won, me, opp):
    # Direction score
    my_score = 0
    opp_score = 0
    for d in ["letter", "number", "vertical"]:
        my_w = l_won[me][d]
        opp_w = l_won[opp][d]
        my_score += my_w * 100
        opp_score += opp_w * 100
    
    # Line potential score
    pot_score = 0
    for line in LINE_CELLS.keys():
        my_c = l_counts.get((line, me), 0)
        opp_c = l_counts.get((line, opp), 0)
        length = LINE_LENGTH[line]
        maj = length // 2 + 1
        
        if my_c >= maj or opp_c >= maj:
            continue
        
        # Value based on how close to majority
        if my_c + opp_c < length:  # Not full
            pot_score += (my_c - opp_c) * 10
    
    return my_score - opp_score + pot_score

def simulate_move_value(occupied, l_counts, l_won, move, me, opp, check_only_win=False):
    # Fast simulation to check if move wins game
    occ_copy = set(occupied.keys())
    occ_copy.add(move)
    
    # Update line counts for this move only
    temp_l_won = {me: dict(l_won[me]), opp: dict(l_won[opp])}
    
    for line in CELL_LINES[move]:
        my_c = l_counts.get((line, me), 0) + 1
        length = LINE_LENGTH[line]
        maj = length // 2 + 1
        if my_c >= maj and l_counts.get((line, me), 0) < maj:
            temp_l_won[me][line[0]] += 1
            if temp_l_won[me][line[0]] >= 5:
                dirs = sum(1 for d in ["letter","number","vertical"] if temp_l_won[me][d] >= 5)
                if dirs >= 2:
                    return 100000
    
    return 0 if check_only_win else evaluate(l_counts, temp_l_won, me, opp)
