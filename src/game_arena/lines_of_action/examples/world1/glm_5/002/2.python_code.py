
import time

def policy(board):
    # Constants
    PLAYER = 1
    OPPONENT = -1
    DIRS = [(0, 1), (1, 0), (1, 1), (1, -1), (0, -1), (-1, 0), (-1, -1), (-1, 1)]
    
    start_time = time.time()
    TIME_LIMIT = 0.95
    
    # Helper: Count connected components using BFS
    def count_components(b, player):
        pieces = []
        for r in range(8):
            for c in range(8):
                if b[r][c] == player:
                    pieces.append((r, c))
        
        if not pieces:
            return 0
        
        visited = set()
        components = 0
        
        for start_node in pieces:
            if start_node not in visited:
                components += 1
                queue = [start_node]
                visited.add(start_node)
                while queue:
                    r, c = queue.pop(0)
                    for dr, dc in DIRS:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 8 and 0 <= nc < 8:
                            if b[nr][nc] == player and (nr, nc) not in visited:
                                visited.add((nr, nc))
                                queue.append((nr, nc))
        return components

    # Helper: Pre-calculate piece counts for all lines
    def get_line_counts(b):
        rows = [0] * 8
        cols = [0] * 8
        diag1 = [0] * 15 # r - c + 7
        diag2 = [0] * 15 # r + c
        
        for r in range(8):
            for c in range(8):
                if b[r][c] != 0:
                    rows[r] += 1
                    cols[c] += 1
                    diag1[r - c + 7] += 1
                    diag2[r + c] += 1
        return rows, cols, diag1, diag2

    # Helper: Generate valid moves
    def get_moves(b, player, line_counts):
        rows, cols, diag1, diag2 = line_counts
        moves = []
        
        for r in range(8):
            for c in range(8):
                if b[r][c] == player:
                    for dr, dc in DIRS:
                        # Determine distance based on line type
                        if dr == 0: distance = rows[r]
                        elif dc == 0: distance = cols[c]
                        elif dr == dc: distance = diag1[r - c + 7]
                        else: distance = diag2[r + c]
                        
                        tr, tc = r + dr * distance, c + dc * distance
                        
                        # Check bounds
                        if not (0 <= tr < 8 and 0 <= tc < 8):
                            continue
                        
                        # Cannot land on own piece
                        if b[tr][tc] == player:
                            continue
                            
                        # Check path blocking (cannot jump opponent)
                        blocked = False
                        for step in range(1, distance):
                            ir, ic = r + dr * step, c + dc * step
                            if b[ir][ic] == -player:
                                blocked = True
                                break
                        if blocked:
                            continue
                            
                        moves.append(((r, c), (tr, tc)))
        return moves

    # Helper: Apply move to board (returns new board state)
    def apply_move(b, move):
        (r1, c1), (r2, c2) = move
        new_b = [row[:] for row in b]
        piece = new_b[r1][c1]
        new_b[r1][c1] = 0
        new_b[r2][c2] = piece
        return new_b

    # Evaluation Function
    def evaluate(b):
        my_comp = count_components(b, PLAYER)
        opp_comp = count_components(b, OPPONENT)
        
        # Terminal conditions
        if my_comp == 1: return 100000
        if opp_comp == 1: return -100000
        
        # Primary Heuristic: Connectivity
        score = (opp_comp - my_comp) * 1000
        
        # Secondary Heuristic: Centralization (distance from center)
        my_dist = 0
        opp_dist = 0
        for r in range(8):
            for c in range(8):
                if b[r][c] == PLAYER:
                    my_dist += max(abs(r - 3.5), abs(c - 3.5))
                elif b[r][c] == OPPONENT:
                    opp_dist += max(abs(r - 3.5), abs(c - 3.5))
        
        score += (opp_dist - my_dist) * 2
        return score

    # Minimax with Alpha-Beta Pruning
    class Timeout(Exception):
        pass

    def minimax(b, depth, alpha, beta, maximizing):
        if time.time() - start_time > TIME_LIMIT:
            raise Timeout()
            
        my_comp = count_components(b, PLAYER)
        opp_comp = count_components(b, OPPONENT)
        
        if my_comp == 1: return 100000
        if opp_comp == 1: return -100000
        
        if depth == 0:
            return evaluate(b)
        
        line_counts = get_line_counts(b)
        current_player = PLAYER if maximizing else OPPONENT
        moves = get_moves(b, current_player, line_counts)
        
        # Simple move ordering: captures first
        def move_priority(m):
            (_, _), (tr, tc) = m
            return 1 if b[tr][tc] == -current_player else 0
            
        moves.sort(key=move_priority, reverse=True)
        
        if not moves:
            return -100000 if maximizing else 100000

        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                new_b = apply_move(b, move)
                val = minimax(new_b, depth - 1, alpha, beta, False)
                max_eval = max(max_eval, val)
                alpha = max(alpha, val)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                new_b = apply_move(b, move)
                val = minimax(new_b, depth - 1, alpha, beta, True)
                min_eval = min(min_eval, val)
                beta = min(beta, val)
                if beta <= alpha:
                    break
            return min_eval

    # Main Execution
    # Initial move list to ensure we have a fallback
    init_counts = get_line_counts(board)
    legal_moves = get_moves(board, PLAYER, init_counts)
    
    if not legal_moves:
        return "0,0:0,0" # Should not happen in a valid game
    
    best_move = legal_moves[0]
    
    try:
        # Iterative Deepening
        for depth in range(1, 6):
            # Order root moves based on previous iteration or simple heuristic
            legal_moves.sort(key=lambda m: 1 if board[m[1][0]][m[1][1]] == OPPONENT else 0, reverse=True)
            
            current_best_val = -float('inf')
            current_best_move = legal_moves[0]
            
            for move in legal_moves:
                new_b = apply_move(board, move)
                
                # Check immediate win
                if count_components(new_b, PLAYER) == 1:
                    return f"{move[0][0]},{move[0][1]}:{move[1][0]},{move[1][1]}"
                
                val = minimax(new_b, depth - 1, -float('inf'), float('inf'), False)
                
                if val > current_best_val:
                    current_best_val = val
                    current_best_move = move
            
            best_move = current_best_move
            
    except Timeout:
        pass
    except Exception:
        pass

    return f"{best_move[0][0]},{best_move[0][1]}:{best_move[1][0]},{best_move[1][1]}"
