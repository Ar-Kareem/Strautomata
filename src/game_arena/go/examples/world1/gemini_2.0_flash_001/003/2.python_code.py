
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    A Go policy that prioritizes captures, liberty deprivation, and avoids self-capture.
    """

    board_size = 19

    def is_valid_move(row: int, col: int, my_stones: list[tuple[int, int]], opponent_stones: list[tuple[int, int]]) -> bool:
        """Checks if a move is within the board and not occupied."""
        if not (1 <= row <= board_size and 1 <= col <= board_size):
            return False
        if (row, col) in my_stones or (row, col) in opponent_stones:
            return False
        return True

    def get_neighbors(row: int, col: int) -> list[tuple[int, int]]:
        """Returns the neighbors of a given position."""
        neighbors = []
        if row > 1:
            neighbors.append((row - 1, col))
        if row < board_size:
            neighbors.append((row + 1, col))
        if col > 1:
            neighbors.append((row, col - 1))
        if col < board_size:
            neighbors.append((row, col + 1))
        return neighbors

    def get_liberties(row: int, col: int, stones: list[tuple[int, int]], opponent_stones: list[tuple[int, int]]) -> int:
        """Counts the liberties of a stone group."""
        group = find_group(row, col, stones)
        liberties = set()
        for r, c in group:
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) not in stones and (nr, nc) not in opponent_stones:
                    liberties.add((nr, nc))
        return len(liberties)

    def find_group(row: int, col: int, stones: list[tuple[int, int]]) -> set[tuple[int, int]]:
        """Finds the group of connected stones that a stone belongs to."""
        group = set()
        queue = [(row, col)]
        group.add((row, col))
        while queue:
            r, c = queue.pop(0)
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in group:
                    group.add((nr, nc))
                    queue.append((nr, nc))
        return group

    def check_capture(row: int, col: int, my_stones: list[tuple[int, int]], opponent_stones: list[tuple[int, int]]) -> list[tuple[int, int]]:
        """Checks if placing a stone at (row, col) captures any opponent stones."""
        captured_stones = []
        for nr, nc in get_neighbors(row, col):
            if (nr, nc) in opponent_stones:
                group = find_group(nr, nc, opponent_stones)
                temp_board = list(opponent_stones)
                for r, c in group:
                    temp_board.remove((r,c))

                if get_liberties(nr, nc, opponent_stones=temp_board+[(row, col)], stones=my_stones) == 0:
                    captured_stones.extend(group)
        return captured_stones

    # Capture Detection
    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            if is_valid_move(row, col, me, opponent):
                captured = check_capture(row, col, me + [(row, col)], opponent)
                if captured:
                    return (row, col)

    # Liberty Deprivation
    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            if is_valid_move(row, col, me, opponent):
                for nr, nc in get_neighbors(row, col):
                    if (nr, nc) in opponent:
                        liberties_before = get_liberties(nr, nc, opponent, me)
                        temp_opponent_stones = list(opponent)
                        liberties_after = get_liberties(nr, nc, opponent_stones=temp_opponent_stones + [(row,col)], stones=me)
                        if liberties_before > liberties_after:
                          return (row, col)

    # Avoid Self-Capture and maintain own liberties
    valid_moves = []
    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            if is_valid_move(row, col, me, opponent):
                if get_liberties(row, col, me + [(row, col)], opponent) >0:
                  valid_moves.append((row, col))

    # Random Valid Move with center preference.
    if valid_moves:
        center_row = board_size // 2 + 1
        center_col = board_size // 2 + 1
        
        center_moves = []
        other_moves = []
        for move in valid_moves:
            dist_to_center = abs(move[0] - center_row) + abs(move[1] - center_col)
            if dist_to_center <= 5:
                center_moves.append(move)
            else:
                other_moves.append(move)
            
        if center_moves:
            return random.choice(center_moves)
        else:
            return random.choice(other_moves)

    # Pass if no valid moves are found.
    return (0, 0)
