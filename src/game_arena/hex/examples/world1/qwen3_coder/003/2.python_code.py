
import numpy as np
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board_size = 11
    me_set = set(me)
    opp_set = set(opp)
    all_occupied = me_set.union(opp_set)
    
    # Helper function to get neighbors of a cell
    def get_neighbors(r, c):
        neighbors = []
        for dr, dc in [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]:
            nr, nc = r + dr, c + dc
            if 0 <= nr < board_size and 0 <= nc < board_size:
                neighbors.append((nr, nc))
        return neighbors

    # BFS to find shortest path for a player to win
    def bfs_shortest_path(player_stones, player_color):
        visited = set(player_stones)
        queue = deque()
        
        if player_color == 'b':  # Black connects top to bottom
            for c in range(board_size):
                if (0, c) in player_stones:
                    queue.append((0, c, 0))  # (row, col, distance)
                    visited.add((0, c))
        else:  # White connects left to right
            for r in range(board_size):
                if (r, 0) in player_stones:
                    queue.append((r, 0, 0))  # (row, col, distance)
                    visited.add((r, 0))
        
        while queue:
            r, c, dist = queue.popleft()
            
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in visited:
                    continue
                if (nr, nc) not in player_stones:
                    continue
                    
                if (player_color == 'b' and nr == board_size - 1) or \
                   (player_color == 'w' and nc == board_size - 1):
                    return dist + 1  # Win in this many steps
                
                visited.add((nr, nc))
                queue.append((nr, nc, dist + 1))
        return float('inf')  # No path found

    # Check for winning move
    for r in range(board_size):
        for c in range(board_size):
            if (r, c) in all_occupied:
                continue
            me_set.add((r, c))
            if bfs_shortest_path(list(me_set), color) == 1:
                me_set.remove((r, c))
                return (r, c)
            me_set.remove((r, c))

    # Check for opponent's winning move to block
    opp_color = 'b' if color == 'w' else 'w'
    for r in range(board_size):
        for c in range(board_size):
            if (r, c) in all_occupied:
                continue
            opp_set.add((r, c))
            if bfs_shortest_path(list(opp_set), opp_color) == 1:
                opp_set.remove((r, c))
                return (r, c)
            opp_set.remove((r, c))

    # Evaluate each empty cell
    best_move = None
    best_score = float('-inf')
    
    for r in range(board_size):
        for c in range(board_size):
            if (r, c) in all_occupied:
                continue
                
            score = 0
            neighbors = get_neighbors(r, c)
            
            # Bonus for neighbors that are our stones
            for nr, nc in neighbors:
                if (nr, nc) in me_set:
                    score += 3
                elif (nr, nc) in opp_set:
                    score -= 1  # Slight penalty for crowding opponent (strategic)
            
            # Positional bonuses
            if color == 'b':  # Black wants to move vertically
                # Encourage moves towards center rows
                score += 2 * (board_size // 2 - abs(r - board_size // 2))
                # Bonus for being in key connecting positions
                score += 1 * min(r, board_size - 1 - r) 
            else:  # White wants to move horizontally
                # Encourage moves towards center columns
                score += 2 * (board_size // 2 - abs(c - board_size // 2))
                # Bonus for being in key connecting positions
                score += 1 * min(c, board_size - 1 - c)
            
            # Evaluate connectivity improvement
            temp_me = me + [(r, c)]
            try:
                current_dist = bfs_shortest_path(me, color)
                new_dist = bfs_shortest_path(temp_me, color)
                if new_dist < current_dist:
                    score += 5
            except:
                pass
            
            if score > best_score:
                best_score = score
                best_move = (r, c)
    
    return best_move if best_move else (board_size//2, board_size//2)
