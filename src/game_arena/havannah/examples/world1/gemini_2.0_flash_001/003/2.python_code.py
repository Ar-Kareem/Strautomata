
import numpy as np
import random

def get_neighbors(row, col, board_size):
    neighbors = []
    if row > 0:
        neighbors.append((row - 1, col))
        if col < board_size - 1:
            neighbors.append((row - 1, col + 1))
    if row < board_size - 1:
        neighbors.append((row + 1, col))
        if col > 0:
            neighbors.append((row + 1, col - 1))
    if col > 0:
        neighbors.append((row, col - 1))
    if col < board_size - 1:
        neighbors.append((row, col + 1))
    return neighbors

def check_bridge(me, board_size):
    corners = [(0, 0), (0, board_size - 1), (board_size - 1, 0), (board_size - 1, board_size - 1), (board_size // 2, 0), (board_size // 2, board_size -1)]

    def bfs(start, end, player_stones, board_size):
        visited = set()
        queue = [start]
        visited.add(start)

        while queue:
            node = queue.pop(0)
            if node == end:
                return True

            neighbors = get_neighbors(node[0], node[1], board_size)
            for neighbor in neighbors:
                if neighbor in player_stones and neighbor not in visited:
                    queue.append(neighbor)
                    visited.add(neighbor)
        return False

    for i in range(len(corners)):
      for j in range(i + 1, len(corners)):
        if bfs(corners[i], corners[j], set(me), board_size):
          return True
    return False

def check_fork(me, board_size):
    edges = []
    for i in range(1, board_size - 1):
        edges.append((0, i))
        edges.append((board_size - 1, i))
        edges.append((i, 0))
        edges.append((i, board_size - 1))

    def bfs(start, others, player_stones, board_size):
        visited = set()
        queue = [start]
        visited.add(start)
        paths = 0

        while queue:
            node = queue.pop(0)
            if node in others:
                paths += 1
                if paths == 2:
                  return True
                continue

            neighbors = get_neighbors(node[0], node[1], board_size)
            for neighbor in neighbors:
                if neighbor in player_stones and neighbor not in visited:
                    queue.append(neighbor)
                    visited.add(neighbor)
        return False
    
    for i in range(len(edges)):
        remaining_edges = edges[:i] + edges[i+1:]
        
        for j in range(len(remaining_edges)):
            
            
            third_edges = remaining_edges[:j] + remaining_edges[j+1:]
            
            for k in range(len(third_edges)):
                if bfs(edges[i], set(remaining_edges[j:j+1] + third_edges[k:k+1]), set(me), board_size):
                  return True
    return False


def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    board_size = valid_mask.shape[0]

    # 1. Check for immediate winning moves (bridge or fork)
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp:
                temp_me = me + [(r, c)]
                if check_bridge(temp_me, board_size) or check_fork(temp_me, board_size):

                    return (r, c)

    # 2. Prioritize Corner Moves early
    corners = [(0, 0), (0, board_size - 1), (board_size - 1, 0), (board_size - 1, board_size - 1), (board_size // 2, 0), (board_size // 2, board_size -1) ]
    for corner in corners:
        if valid_mask[corner[0]][corner[1]] and corner not in me and corner not in opp:
            return corner
    
    # 3. Strategic move selection
    best_move = None
    best_score = -1


    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp:
                
                score = 0
                
                # Connectivity bonus:
                neighbors = get_neighbors(r, c, board_size)
                for neighbor in neighbors:
                    if neighbor in me:
                        score += 1
                
                # Blocking Opponent's bridge
                temp_opp = opp + [(r,c)]

                if check_bridge(temp_opp, board_size):
                  score += 2
                
                #Give higher score to middle cells
                score += ((board_size//2 - r)**2 + (board_size//2 - c)**2)**0.5 * (-0.01)

                if score > best_score:
                    best_score = score
                    best_move = (r, c)

    
    if best_move:
      return best_move

    # 4. If no strategic move is found, choose a random valid move.
    possible_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp:
                possible_moves.append((r, c))

    if possible_moves:
        return random.choice(possible_moves)
    else:
        # Should not happen given the problem constraints, but handle it gracefully.
        return (0, 0)

