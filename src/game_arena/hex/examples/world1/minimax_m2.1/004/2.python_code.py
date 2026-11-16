
import collections

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Convert lists to sets for efficient lookup
    me_set = set(me)
    opp_set = set(opp)
    
    # Precompute start and end sets for both colors
    start_set_b = {(0, j) for j in range(11)}
    end_set_b = {(10, j) for j in range(11)}
    start_set_w = {(i, 0) for i in range(11)}
    end_set_w = {(i, 10) for i in range(11)}
    
    def get_start_set(color):
        if color == 'b':
            return start_set_b
        else:
            return start_set_w
    
    def get_end_set(color):
        if color == 'b':
            return end_set_b
        else:
            return end_set_w
    
    def get_opp_color(color):
        return 'w' if color == 'b' else 'b'
    
    def get_neighbors(i, j):
        directions = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        neighbors = []
        for di, dj in directions:
            ni, nj = i + di, j + dj
            if 0 <= ni < 11 and 0 <= nj < 11:
                neighbors.append((ni, nj))
        return neighbors
    
    def shortest_path(stones, start_set, end_set):
        # BFS to find shortest path from start_set to end_set through stones
        if not stones:
            return float('inf')
        visited = set()
        queue = collections.deque()
        for s in start_set:
            if s in stones:
                queue.append((s, 0))
                visited.add(s)
        while queue:
            cell, dist = queue.popleft()
            if cell in end_set:
                return dist
            for neighbor in get_neighbors(*cell):
                if neighbor in stones and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, dist + 1))
        return float('inf')
    
    def check_win(stones, color):
        return shortest_path(stones, get_start_set(color), get_end_set(color)) != float('inf')
    
    def possible_moves(me_set, opp_set):
        moves = []
        for i in range(11):
            for j in range(11):
                if (i, j) not in me_set and (i, j) not in opp_set:
                    moves.append((i, j))
        return moves
    
    def evaluate(me_stones, opp_stones, my_color):
        my_dist = shortest_path(me_stones, get_start_set(my_color), get_end_set(my_color))
        opp_color = get_opp_color(my_color)
        opp_dist = shortest_path(opp_stones, get_start_set(opp_color), get_end_set(opp_color))
        return opp_dist - my_dist
    
    def minimax(me_stones, opp_stones, turn, depth, alpha, beta, my_color):
        if depth == 0:
            return evaluate(me_stones, opp_stones, my_color)
        
        if turn == 'me':
            best_value = -float('inf')
            best_move = None
            for move in possible_moves(me_stones, opp_stones):
                new_me = me_stones | {move}
                if check_win(new_me, my_color):
                    return (move, float('inf'))  # Win immediately
                value = minimax(new_me, opp_stones, 'opp', depth-1, alpha, beta, my_color)
                if value > best_value:
                    best_value = value
                    best_move = move
                alpha = max(alpha, best_value)
                if best_value >= beta:
                    break
            return (best_move, best_value)
        else:
            best_value = float('inf')
            for move in possible_moves(me_stones, opp_stones):
                new_opp = opp_stones | {move}
                opp_color = get_opp_color(my_color)
                if check_win(new_opp, opp_color):
                    return (None, -float('inf'))  # Loss
                value = minimax(me_stones, new_opp, 'me', depth-1, alpha, beta, my_color)
                if value < best_value:
                    best_value = value
                beta = min(beta, best_value)
                if best_value <= alpha:
                    break
            return (None, best_value)
    
    # Perform minimax search with depth 2
    best_move, best_value = minimax(me_set, opp_set, 'me', 2, -float('inf'), float('inf'), color)
    return best_move
