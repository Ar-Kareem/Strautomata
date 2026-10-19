
import numpy as np
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Selects the next move for Havannah on a 15x15 board.
    """
    board_size = valid_mask.shape[0]
    me_set = set(me)
    opp_set = set(opp)

    def distance_to_nearest_corner(row, col):
        corners = [(0, 0), (0, board_size - 1), (board_size - 1, 0), (board_size - 1, board_size - 1), (board_size // 2, 0), (board_size // 2, board_size - 1)]
        return min((abs(row - r) + abs(col - c)) for r, c in corners)

    def distance_to_nearest_edge(row, col):
        return min(row, col, board_size - 1 - row, board_size - 1 - col)
    
    def get_neighbors(row, col):
        neighbors = []
        if row > 0:
            neighbors.append((row - 1, col))
        if row < board_size - 1:
            neighbors.append((row + 1, col))
        if col > 0:
            neighbors.append((row, col - 1))
            if row < board_size -1:
                neighbors.append((row + 1, col - 1))
        if col < board_size - 1:
            neighbors.append((row, col + 1))
            if row > 0:
                neighbors.append((row - 1, col + 1))
        return neighbors

    def check_ring_threat(row, col):
        # Check for near-rings by opponent
        for r, c in opp:
            neighbors = get_neighbors(r, c)
            empty_neighbors = []
            opp_neighbors = 0
            for nr, nc in neighbors:
              if 0 <= nr < board_size and 0 <= nc < board_size and valid_mask[nr][nc]:
                if (nr, nc) not in me_set and (nr, nc) not in opp_set:
                  empty_neighbors.append((nr, nc))
                if (nr, nc) in opp_set:
                  opp_neighbors+=1
            if opp_neighbors >= 4 and len(empty_neighbors) > 0:
              for nr, nc in empty_neighbors:
                if nr == row and nc == col:
                  return True
        return False

    def score_move(row, col):
        score = 0

        # Corner/Edge Prioritization
        score += 15 - distance_to_nearest_corner(row, col)
        score += 10 - distance_to_nearest_edge(row, col)

        # Connectivity
        for r, c in get_neighbors(row, col):
            if (r, c) in me_set:
                score += 5

        # Ring Threat
        if check_ring_threat(row, col):
            score += 40  # High priority to block rings

        #Bridge/Fork Formation Bonus
        connected_to_corner = False
        connected_to_edge = False
        for r,c in get_neighbors(row, col):
          if (r,c) in me_set:
            if distance_to_nearest_corner(r,c) == 0:
              connected_to_corner = True
            if distance_to_nearest_edge(r,c) == 0:
              connected_to_edge = True
        
        if connected_to_corner and connected_to_edge:
          score += 30
        elif connected_to_corner and len([n for n in get_neighbors(row,col) if n in me_set and distance_to_nearest_corner(n[0], n[1]) == 0]) > 0:
          score+=20
        
        # Exploration
        score += random.random() * 2

        return score

    best_move = None
    best_score = -1

    valid_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if valid_mask[r][c] and (r, c) not in me_set and (r, c) not in opp_set:
                valid_moves.append((r, c))
    if not valid_moves:
        #Should never occur if valid_mask is constructed correctly. Added for safety.
        return (0,0)

    for row, col in valid_moves:
        score = score_move(row, col)
        if score > best_score:
            best_score = score
            best_move = (row, col)
        elif score == best_score and random.random() < 0.5:
            best_move = (row, col)

    return best_move
