
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A Go policy that attempts to make smart moves.
    """

    board_size = 19
    all_stones = me + opponent

    def is_valid_move(row, col):
        """Checks if a move is within the board boundaries and not occupied."""
        return 1 <= row <= board_size and 1 <= col <= board_size and (row, col) not in all_stones

    def get_neighbors(row, col):
        """Returns a list of neighboring coordinates (row, col)."""
        neighbors = []
        for dr, dc in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            new_row, new_col = row + dr, col + dc
            if 1 <= new_row <= board_size and 1 <= new_col <= board_size:
                neighbors.append((new_row, new_col))
        return neighbors
    
    def get_group(row, col, stones):
        """
        Recursively finds a group of connected stones of the same color.
        """
        group = [(row, col)]
        visited = set()
        visited.add((row, col))
        
        queue = [(row, col)]
        while queue:
            curr_row, curr_col = queue.pop(0)
            for neighbor_row, neighbor_col in get_neighbors(curr_row, curr_col):
                if (neighbor_row, neighbor_col) in stones and (neighbor_row, neighbor_col) not in visited:
                    group.append((neighbor_row, neighbor_col))
                    visited.add((neighbor_row, neighbor_col))
                    queue.append((neighbor_row, neighbor_col))
        
        return group

    def get_liberties(group, all_stones):
        """
        Calculates the liberties (empty adjacent spaces) of a group of stones.
        """
        liberties = set()
        for row, col in group:
            for neighbor_row, neighbor_col in get_neighbors(row, col):
                if (neighbor_row, neighbor_col) not in all_stones:
                    liberties.add((neighbor_row, neighbor_col))
        return liberties

    def check_capture(row, col, player_stones, opponent_stones):
        """Checks if placing a stone at (row, col) captures any opponent groups."""
        captured_groups = []
        for neighbor_row, neighbor_col in get_neighbors(row, col):
            if (neighbor_row, neighbor_col) in opponent_stones:
                opponent_group = get_group(neighbor_row, neighbor_col, opponent_stones)
                liberties = get_liberties(opponent_group, me + opponent_stones + [(row, col)]) # Added new stone to board
                if not liberties:
                    captured_groups.append(opponent_group)
        return captured_groups
    
    def would_be_suicide(row, col, player_stones, opponent_stones):
         """Checks if placing a stone at (row, col) would be suicide."""

         temp_player_stones = player_stones + [(row, col)]
         
         group = get_group(row, col, temp_player_stones)

         liberties = get_liberties(group, temp_player_stones + opponent_stones)
         if liberties:
             return False

         # Check if it captures any opponent group, the move is not suicide.
         if check_capture(row, col, temp_player_stones, opponent_stones):
            return False

         return True
    

    # 1. Capture Detection
    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            if is_valid_move(row, col):
                captured_groups = check_capture(row, col, me + [(row, col)], opponent)
                if captured_groups:
                    return (row, col), memory

    # 2. Avoid Suicide
    possible_moves = []
    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            if is_valid_move(row, col) and not would_be_suicide(row, col, me, opponent):
                possible_moves.append((row, col))

    if possible_moves:
        return random.choice(possible_moves), memory
        
    # 3. Pass if no valid moves are found
    return (0, 0), memory
