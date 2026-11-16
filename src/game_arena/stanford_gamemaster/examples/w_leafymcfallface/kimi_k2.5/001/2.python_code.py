
from collections import deque

def policy(state: list[list[object]], role: str) -> str:
    # Parse state
    leaves = set()  # Set of (r, c) tuples with leaves
    positions = {}  # role -> (r, c)
    
    for atom in state:
        if atom[0] == "leaf":
            r, c = int(atom[1]), int(atom[2])
            leaves.add((r, c))
        elif atom[0] == "isplayer":
            r, c = int(atom[1]), int(atom[2])
            player_role = str(atom[3])
            positions[player_role] = (r, c)
    
    my_role = role
    opp_role = "blue" if role == "red" else "red"
    my_pos = positions[my_role]
    opp_pos = positions[opp_role]
    
    # Helper: get legal moves from position
    def get_moves(pos, leaf_set):
        r, c = pos
        moves = []
        for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nr, nc = r + dr, c + dc
            if (nr, nc) in leaf_set:
                moves.append((nr, nc))
        return moves
    
    # Helper: BFS flood fill counting reachable cells
    def count_reachable(start, blocked_pos, leaf_set):
        # blocked_pos is a position that blocks (the other player)
        # Can't pass through blocked_pos or non-leaf cells
        q = deque([start])
        visited = {start}
        count = 0
        while q:
            p = q.popleft()
            if p != start:
                count += 1
            pr, pc = p
            for dr, dc in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                np = (pr + dr, pc + dc)
                if np in leaf_set and np not in visited and np != blocked_pos:
                    visited.add(np)
                    q.append(np)
        return count
    
    # Evaluation function
    def evaluate(me, opp, lf):
        my_moves = get_moves(me, lf)
        opp_moves = get_moves(opp, lf)
        
        # Terminal conditions
        if not my_moves and opp_moves:
            return -1000  # I lose
        if my_moves and not opp_moves:
            return 1000   # I win
        if not my_moves and not opp_moves:
            return 0
        
        # Voronoi (space advantage)
        my_area = count_reachable(me, opp, lf)
        opp_area = count_reachable(opp, me, lf)
        return my_area - opp_area
    
    # Minimax search
    def minimax(me, opp, lf, depth, is_my_turn):
        if depth == 0:
            return evaluate(me, opp, lf)
        
        if is_my_turn:
            moves = get_moves(me, lf)
            if not moves:
                return -1000
            best = -float('inf')
            for m in moves:
                # When I move to m: leaf m is consumed
                new_lf = lf - {m}
                val = minimax(m, opp, new_lf, depth - 1, False)
                best = max(best, val)
                if best >= 1000:  # Pruning: found win
                    break
            return best
        else:
            moves = get_moves(opp, lf)
            if not moves:
                return 1000
            best = float('inf')
            for m in moves:
                new_lf = lf - {m}
                val = minimax(me, m, new_lf, depth - 1, True)
                best = min(best, val)
                if best <= -1000:  # Pruning: found loss
                    break
            return best
    
    # Determine search depth based on game stage (deeper in endgame)
    num_leaves = len(leaves)
    if num_leaves < 8:
        search_depth = 4
    elif num_leaves < 15:
        search_depth = 3
    else:
        search_depth = 2
    
    # Find best move
    my_moves = get_moves(my_pos, leaves)
    if not my_moves:
        # Should not happen in valid game, but return arbitrary legal format
        return "move(1,1)"
    
    best_move = my_moves[0]
    best_score = -float('inf')
    
    for m in my_moves:
        new_lf = leaves - {m}
        score = minimax(m, opp_pos, new_lf, search_depth - 1, False)
        if score > best_score:
            best_score = score
            best_move = m
        # Immediate winning move?
        if best_score >= 1000:
            break
    
    r, c = best_move
    return f"move({r},{c})"
