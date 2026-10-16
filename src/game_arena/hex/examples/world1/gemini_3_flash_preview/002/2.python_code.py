
import heapq

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board_size = 11
    me_set = set(me)
    opp_set = set(opp)
    all_occupied = me_set.union(opp_set)

    def get_neighbors(r, c):
        # Hex neighbors for (r, c)
        neighbors = [(r-1, c), (r-1, c+1), (r, c-1), (r, c+1), (r+1, c-1), (r+1, c)]
        return [(nr, nc) for nr, nc in neighbors if 0 <= nr < board_size and 0 <= nc < board_size]

    def shortest_path_dist(player_stones, opponent_stones, player_color):
        # Dijkstra to find min stones to connect sides
        pq = [] # (dist, r, c)
        dist_map = {}

        # Initialize sides
        if player_color == 'b': # Top to Bottom
            for c in range(board_size):
                if (0, c) not in opponent_stones:
                    d = 0 if (0, c) in player_stones else 1
                    dist_map[(0, c)] = d
                    heapq.heappush(pq, (d, 0, c))
        else: # White: Left to Right
            for r in range(board_size):
                if (r, 0) not in opponent_stones:
                    d = 0 if (r, 0) in player_stones else 1
                    dist_map[(r, 0)] = d
                    heapq.heappush(pq, (d, r, 0))

        while pq:
            d, r, c = heapq.heappop(pq)
            if d > dist_map.get((r, c), float('inf')):
                continue
            
            # Check win condition
            if player_color == 'b' and r == board_size - 1: return d
            if player_color == 'w' and c == board_size - 1: return d

            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in opponent_stones:
                    continue
                cost = 0 if (nr, nc) in player_stones else 1
                new_dist = d + cost
                if new_dist < dist_map.get((nr, nc), float('inf')):
                    dist_map[(nr, nc)] = new_dist
                    heapq.heappush(pq, (new_dist, nr, nc))
        return float('inf')

    # Basic Opening: Middle is strong
    center = (board_size // 2, board_size // 2)
    if center not in all_occupied:
        return center

    best_move = None
    max_score = -float('inf')
    
    # Evaluate every legal move
    legal_moves = [(r, c) for r in range(board_size) for c in range(board_size) if (r, c) not in all_occupied]
    
    # Heuristic: only look at moves near existing stones to save time, or all if few moves
    if len(all_occupied) > 0:
        base_me = shortest_path_dist(me_set, opp_set, color)
        opp_color = 'w' if color == 'b' else 'b'
        base_opp = shortest_path_dist(opp_set, me_set, opp_color)

        for move in legal_moves:
            # Score = (How much it helps me) + (How much it hurts opponent)
            # Evaluation: Simulate the move
            me_set.add(move)
            new_me = shortest_path_dist(me_set, opp_set, color)
            me_set.remove(move)
            
            opp_set.add(move)
            new_opp = shortest_path_dist(opp_set, me_set, opp_color)
            opp_set.remove(move)
            
            # Use differences. Smaller distance is better.
            # We add a small tie-breaker for central positions.
            dist_to_center = abs(move[0]-5) + abs(move[1]-5)
            score = (base_me - new_me) * 1.1 + (new_opp - base_opp) * 1.0 - (dist_to_center * 0.01)
            
            if score > max_score:
                max_score = score
                best_move = move

    return best_move if best_move else legal_moves[0]
