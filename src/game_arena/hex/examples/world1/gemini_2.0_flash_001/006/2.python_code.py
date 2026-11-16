
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    A Hex policy that combines bridge completion, opponent disruption, and near-goal placement.
    """
    board_size = 11
    empty_cells = [(r, c) for r in range(board_size) for c in range(board_size) if (r, c) not in me and (r, c) not in opp]

    if not me:  # First move: choose the center
        return (board_size // 2, board_size // 2)

    def get_neighbors(row, col):
        neighbors = []
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == -1 and dc == -1:
                    continue
                if dr == 1 and dc == 1:
                    continue
                if dr == 0 and dc == 0:
                    continue
                new_row = row + dr
                new_col = col + dc
                if 0 <= new_row < board_size and 0 <= new_col < board_size:
                    neighbors.append((new_row, new_col))
        return neighbors

    def find_bridges(stones):
        bridges = []
        for r, c in stones:
            for rr, cc in get_neighbors(r, c):
                if (rr, cc) in stones:
                    continue
                neighbors_of_neighbor = get_neighbors(rr, cc)
                for rrr, ccc in neighbors_of_neighbor:
                    if (rrr, ccc) in stones and (rrr, ccc) != (r,c):
                        bridges.append(((r,c), (rrr,ccc), (rr, cc)))
        
        unique_bridges = []
        seen = set()
        for bridge in bridges:
          sorted_cells = tuple(sorted((bridge[0], bridge[1])))
          if sorted_cells not in seen:
            unique_bridges.append(bridge)
            seen.add(sorted_cells)
        return unique_bridges


    my_bridges = find_bridges(me)
    potential_bridge_fills = [bridge[2] for bridge in my_bridges if bridge[2] in empty_cells]
    if potential_bridge_fills:
      return potential_bridge_fills[0]


    opponent_bridges = find_bridges(opp)
    opponent_bridge_fills = [bridge[2] for bridge in opponent_bridges if bridge[2] in empty_cells]
    if opponent_bridge_fills:
      return opponent_bridge_fills[0]

    # Near-goal placement
    if color == 'b':  # Black: connect top and bottom
        # Prioritize cells in the top and bottom rows
        top_row_cells = [(0, c) for c in range(board_size) if (0, c) in empty_cells]
        bottom_row_cells = [(board_size - 1, c) for c in range(board_size) if (board_size - 1, c) in empty_cells]

        if top_row_cells:
            return top_row_cells[0]
        if bottom_row_cells:
            return bottom_row_cells[0]
            

    elif color == 'w':  # White: connect left and right
        # Prioritize cells in the left and right columns
        left_col_cells = [(r, 0) for r in range(board_size) if (r, 0) in empty_cells]
        right_col_cells = [(r, board_size - 1) for r in range(board_size) if (r, board_size - 1) in empty_cells]

        if left_col_cells:
            return left_col_cells[0]
        if right_col_cells:
            return right_col_cells[0]
    
    # Random move if no strategic move is found.
    return random.choice(empty_cells)
