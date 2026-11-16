
def policy(board: list[list[list[int]]]) -> tuple[int, int, int]:
    """
    AI policy for 3x3x3 Tic Tac Toe.
    Uses Minimax with Alpha-Beta pruning and Iterative Deepening.
    """
    
    # Constants for players
    AI = 1
    OPPONENT = -1
    
    # Check if a board is full
    def is_full(b):
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if b[x][y][z] == 0:
                        return False
        return True

    # Check for a winner
    def get_winner(b):
        lines = []
        # Planes (z layers)
        for z in range(3):
            lines.extend([[b[x][y][z] for x in range(3)] for y in range(3)]) # Rows
            lines.extend([[b[x][y][z] for y in range(3)] for x in range(3)]) # Cols
            lines.append([b[i][i][z] for i in range(3)]) # Diag
            lines.append([b[i][2-i][z] for i in range(3)]) # Anti-diag
        
        # Lines perpendicular to planes (z-axis lines)
        for x in range(3):
            for y in range(3):
                lines.append([b[x][y][z] for z in range(3)])
        
        # 3D Diagonals
        lines.append([b[i][i][i] for i in range(3)])
        lines.append([b[i][i][2-i] for i in range(3)])
        lines.append([b[i][2-i][i] for i in range(3)])
        lines.append([b[i][2-i][2-i] for i in range(3)])

        for line in lines:
            if sum(line) == 3: return 1
            if sum(line) == -3: return -1
        return 0

    # Generate valid moves with basic ordering (Center -> Corners -> Edges)
    def get_moves(b):
        moves = []
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if b[x][y][z] == 0:
                        # Prioritize center and axes for pruning
                        priority = 0
                        if x == 1 and y == 1 and z == 1: priority = 3 # Center
                        elif (x == 1 and y == 1) or (x == 1 and z == 1) or (y == 1 and z == 1): priority = 2 # Axis centers
                        elif x == 1 or y == 1 or z == 1: priority = 1 # Faces center
                        else: priority = 0 # Corner (actually corner is best for win, but center is best for blocking/speed)
                        # Let's refine: Center is best for win. Corners are next best.
                        # Actually for 3D, center of cube (1,1,1) is part of 27 lines.
                        # Let's just simple sort: Center first.
                        moves.append((priority, (x, y, z)))
        moves.sort(key=lambda m: m[0], reverse=True)
        return [m[1] for m in moves]

    # Evaluation heuristic
    def evaluate(b, player):
        # 1. Check win
        w = get_winner(b)
        if w == player: return 100000
        if w == -player: return -100000
        
        # 2. Positional advantage (only if no win found)
        # Count lines with 2 of player and 1 empty (threats) and 1 of player and 2 empty (opportunities)
        score = 0
        
        # We can cache this or just run it. It's fast enough.
        lines = []
        for z in range(3):
            lines.extend([[b[x][y][z] for x in range(3)] for y in range(3)])
            lines.extend([[b[x][y][z] for y in range(3)] for x in range(3)])
            lines.append([b[i][i][z] for i in range(3)])
            lines.append([b[i][2-i][z] for i in range(3)])
        for x in range(3):
            for y in range(3):
                lines.append([b[x][y][z] for z in range(3)])
        lines.extend([
            [b[i][i][i] for i in range(3)],
            [b[i][i][2-i] for i in range(3)],
            [b[i][2-i][i] for i in range(3)],
            [b[i][2-i][2-i] for i in range(3)]
        ])

        for line in lines:
            count_p = line.count(player)
            count_o = line.count(-player)
            count_0 = line.count(0)
            if count_p == 2 and count_0 == 1: score += 10
            elif count_p == 1 and count_0 == 2: score += 1
            if count_o == 2 and count_0 == 1: score -= 10
            elif count_o == 1 and count_0 == 2: score -= 1

        # Center piece bonus
        if b[1][1][1] == player: score += 2
        elif b[1][1][1] == -player: score -= 2
            
        return score

    # Transposition table
    tt = {}

    def minimax(b, depth, alpha, beta, is_maximizing, player, start_time):
        # Time check
        if (time.time_ns() - start_time) > 800_000_000: # Leave 0.2s buffer
            raise TimeoutError

        state_key = str(b) + str(depth) + str(player) # Simple key
        if state_key in tt:
            return tt[state_key]

        # Leaf conditions
        w = get_winner(b)
        if w == player: return 1000000 - (10 - depth) # Prefer faster wins
        if w == -player: return -1000000 + (10 - depth)
        if depth == 0 or is_full(b):
            # If depth 0, return heuristic
            val = evaluate(b, player)
            tt[state_key] = val
            return val

        moves = get_moves(b)
        
        if is_maximizing:
            max_eval = -float('inf')
            for move in moves:
                x, y, z = move
                b[x][y][z] = player
                eval = minimax(b, depth - 1, alpha, beta, False, player, start_time)
                b[x][y][z] = 0
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            tt[state_key] = max_eval
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                x, y, z = move
                b[x][y][z] = -player
                eval = minimax(b, depth - 1, alpha, beta, True, player, start_time)
                b[x][y][z] = 0
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            tt[state_key] = min_eval
            return min_eval

    # Main Logic
    import time
    
    # 1. Identify Player (Self-correction)
    # If board is empty, I am Player 1 (1).
    # If I find an opponent move, I know who I am.
    my_symbol = 1
    opponent_symbol = -1
    found_my_move = False
    found_opp_move = False
    cell_count = 0
    for x in range(3):
        for y in range(3):
            for z in range(3):
                if board[x][y][z] != 0:
                    cell_count += 1
                    if board[x][y][z] == 1:
                        found_my_move = True
                    if board[x][y][z] == -1:
                        found_opp_move = True
    
    # If I found an opponent move and no my move, I am -1
    if found_opp_move and not found_my_move:
        my_symbol = -1
        opponent_symbol = 1

    # 2. Search Logic
    best_move = None
    start_time = time.time_ns()
    
    # Depth limit for iterative deepening
    # Max possible depth is 27. 
    try:
        # Try full search first (it's 3x3x3, usually very fast)
        # We will just run iterative deepening to be safe
        for depth in range(1, 28): 
            current_best_move = None
            best_val = -float('inf')
            
            # Move ordering: Center first
            moves = get_moves(board)
            
            for move in moves:
                x, y, z = move
                board[x][y][z] = my_symbol
                
                # If this move wins immediately, take it
                if get_winner(board) == my_symbol:
                    board[x][y][z] = 0
                    return move
                
                val = minimax(board, depth - 1, -float('inf'), float('inf'), False, my_symbol, start_time)
                board[x][y][z] = 0
                
                if val > best_val:
                    best_val = val
                    current_best_move = move
                
                # Time check in loop
                if (time.time_ns() - start_time) > 800_000_000:
                    raise TimeoutError
            
            if current_best_move:
                best_move = current_best_move
                
    except TimeoutError:
        pass # Return the best found so far

    # Fallback if something weird happens (should not happen)
    if best_move is None:
        # Pick first empty
        for x in range(3):
            for y in range(3):
                for z in range(3):
                    if board[x][y][z] == 0:
                        return (x, y, z)

    return best_move
