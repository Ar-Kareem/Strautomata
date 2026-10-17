
import heapq

def policy(state: list[list[object]], role: str) -> str:
    # Board dimensions
    SIZE = 7
    
    # Coordinate mappings
    cols = {'a':0, 'b':1, 'c':2, 'd':3, 'e':4, 'f':5, 'g':6}
    rows = {'1':0, '2':1, '3':2, '4':3, '5':4, '6':5, '7':6}
    inv_cols = {v:k for k,v in cols.items()}
    inv_rows = {v:k for k,v in rows.items()}
    
    opponent = "black" if role == "red" else "red"
    
    # Parse board: (c,r) -> color
    board = {}
    for fact in state:
        if fact[0] == "cell" and len(fact) == 4:
            col, row, color = fact[1], fact[2], fact[3]
            if col in cols and row in rows:
                board[(cols[col], rows[row])] = color
    
    # Generate empty cells (legal moves)
    empty = [(c, r) for c in range(SIZE) for r in range(SIZE) if (c, r) not in board]
    
    if not empty:
        return "place(a,1)"  # Fallback, should not happen in valid game
    
    # Hex grid neighbors (axial coordinates)
    def neighbors(c, r):
        deltas = [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, 1), (1, -1)]
        for dc, dr in deltas:
            nc, nr = c + dc, r + dr
            if 0 <= nc < SIZE and 0 <= nr < SIZE:
                yield (nc, nr)
    
    def shortest_path_distance(color, sim_board):
        """Calculate minimum stones needed to connect goal sides."""
        if color == "red":
            # Connect left (col 0) to right (col 6)
            sources = [(0, r) for r in range(SIZE)]
            targets = set([(SIZE-1, r) for r in range(SIZE)])
        else:
            # Connect top (row 0) to bottom (row 6)
            sources = [(c, 0) for c in range(SIZE)]
            targets = set([(c, SIZE-1) for c in range(SIZE)])
        
        # Dijkstra's algorithm (0-1 BFS variant with heap)
        dist = {}
        pq = []
        
        for s in sources:
            if s in sim_board:
                if sim_board[s] == color:
                    d = 0  # Already occupied by me
                else:
                    continue  # Blocked by opponent
            else:
                d = 1  # Need to place here
            
            dist[s] = d
            heapq.heappush(pq, (d, s))
        
        while pq:
            d, u = heapq.heappop(pq)
            if d != dist[u]:
                continue
            if u in targets:
                return d
            
            for v in neighbors(*u):
                if v in sim_board:
                    if sim_board[v] == color:
                        nd = d  # No cost to traverse my stone
                    else:
                        continue  # Cannot traverse opponent stone
                else:
                    nd = d + 1  # Cost 1 to place here
                
                if v not in dist or nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(pq, (nd, v))
        
        return float('inf')
    
    # Check for immediate winning moves
    for cell in empty:
        new_board = board.copy()
        new_board[cell] = role
        if shortest_path_distance(role, new_board) == 0:
            c, r = cell
            return f"place({inv_cols[c]},{inv_rows[r]})"
    
    # Check for opponent winning threats (must block)
    threats = []
    for cell in empty:
        new_board = board.copy()
        new_board[cell] = opponent
        if shortest_path_distance(opponent, new_board) == 0:
            threats.append(cell)
    
    if threats:
        # Block the first threat found (if multiple, we're likely lost anyway)
        c, r = threats[0]
        return f"place({inv_cols[c]},{inv_rows[r]})"
    
    # Evaluate all moves with heuristic
    best_move = empty[0]
    best_score = -float('inf')
    
    for cell in empty:
        new_board = board.copy()
        new_board[cell] = role
        
        my_dist = shortest_path_distance(role, new_board)
        if my_dist == float('inf'):
            continue
            
        opp_dist = shortest_path_distance(opponent, new_board)
        
        # Heuristic: prefer reducing my distance and increasing opponent's distance
        # Weight my distance more heavily (10:1 ratio)
        score = -10 * my_dist + opp_dist
        
        # Slight preference for central cells (better connectivity)
        c, r = cell
        center_dist = abs(c - 3) + abs(r - 3)
        score -= center_dist * 0.1
        
        if score > best_score:
            best_score = score
            best_move = cell
    
    c, r = best_move
    return f"place({inv_cols[c]},{inv_rows[r]})"
