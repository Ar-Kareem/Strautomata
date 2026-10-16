
import numpy as np
import random

def get_neighbors(row, col, board_size):
    neighbors = []
    if row > 0:
        neighbors.append((row - 1, col))
    if row < board_size - 1:
        neighbors.append((row + 1, col))
    if col > 0:
        neighbors.append((row, col - 1))
        if row < board_size - 1:
            neighbors.append((row + 1, col - 1))
    if col < board_size - 1:
        neighbors.append((row, col + 1))
        if row > 0:
            neighbors.append((row - 1, col + 1))
    return neighbors

def check_bridge(me, board_size):
    corners = [(0,0), (0, board_size - 1), (board_size -1, 0), (board_size - 1,board_size - 1), (board_size // 2, 0), (board_size // 2, board_size - 1)]
    for c1 in corners:
        for c2 in corners:
            if c1 != c2:
                visited = set()
                queue = [c1]
                visited.add(c1)
                while queue:
                    curr = queue.pop(0)
                    if curr == c2:
                        return True
                    row, col = curr
                    neighbors = get_neighbors(row, col, board_size)
                    for neighbor_row, neighbor_col in neighbors:
                        if (neighbor_row, neighbor_col) in me and (neighbor_row, neighbor_col) not in visited:
                            queue.append((neighbor_row, neighbor_col))
                            visited.add((neighbor_row, neighbor_col))
    return False

def check_fork(me, board_size):
    edges = []
    for i in range(1, board_size -1):
        edges.append((0, i))
        edges.append((board_size - 1, i))
        edges.append((i, 0))
        edges.append((i, board_size - 1))
        if i != board_size//2:
            edges.append((i, board_size // 2))

    count = 0
    visited_edges = [False] * len(edges)

    for i in range(len(edges)):
          edge = edges[i]
          visited = set()
          queue = [edge]
          visited.add(edge)
          while queue:
              curr = queue.pop(0)
              row, col = curr
              if len(visited) > 1:
                  count +=1 
                  visited_edges[i] = True
                  break
              neighbors = get_neighbors(row, col, board_size)
              for neighbor_row, neighbor_col in neighbors:
                  if (neighbor_row, neighbor_col) in me and (neighbor_row, neighbor_col) not in visited:
                      queue.append((neighbor_row, neighbor_col))
                      visited.add((neighbor_row, neighbor_col))
    
    count_true = 0
    for val in visited_edges:
        if val:
            count_true+=1
    
    return count_true >= 3



def check_ring(me, board_size, opp):
    for row in range(board_size):
        for col in range(board_size):
            if (row, col) not in me and (row, col) not in opp:
                is_inside = True
                visited = set()
                queue = [(row, col)]
                visited.add((row, col))
                
                while queue:
                    curr_row, curr_col = queue.pop(0)
                    neighbors = get_neighbors(curr_row, curr_col, board_size)
                    
                    all_neighbors_mine = True
                    for n_row, n_col in neighbors:
                        if (n_row, n_col) not in me and (n_row, n_col) != (row, col):
                            all_neighbors_mine = False
                            break
                    
                    if not all_neighbors_mine:
                        is_inside = False
                        break
                    
                if is_inside:
                    return True
    return False

def check_win(me, board_size, opp):
    if check_bridge(me, board_size): return True
    if check_fork(me, board_size): return True
    if check_ring(me, board_size, opp): return True
    return False

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    board_size = valid_mask.shape[0]
    valid_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me and (r, c) not in opp:
                valid_moves.append((r, c))

    # 1. Check for winning moves
    for move in valid_moves:
        temp_me = me + [move]
        if check_win(temp_me, board_size, opp):
            return move

    # 2. Check for blocking moves
    for move in valid_moves:
        temp_opp = opp + [move]
        if check_win(temp_opp, board_size, me):
            return move

    # 3. Play a random valid move
    if valid_moves:
        return random.choice(valid_moves)
    else:
        # Should not happen, but return something legal in case of a bug
        for r in range(board_size):
            for c in range(board_size):
                if valid_mask[r][c]:
                    return (r, c)
        return (0, 0)  # If somehow all cells are invalid, return (0, 0). It shouldn't happen.
