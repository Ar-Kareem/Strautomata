
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A Go policy that prioritizes captures, avoids suicide, and prefers corners.
    """

    board_size = 19
    occupied = set(me + opponent)

    def get_neighbors(row, col):
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

    def get_liberties(stones):
        liberties = set()
        for row, col in stones:
            for r, c in get_neighbors(row, col):
                if (r, c) not in occupied:
                    liberties.add((r, c))
        return liberties

    def get_group(row, col, stones):
        group = {(row, col)}
        queue = [(row, col)]
        while queue:
            r, c = queue.pop(0)
            for nr, nc in get_neighbors(r, c):
                if (nr, nc) in stones and (nr, nc) not in group:
                    group.add((nr, nc))
                    queue.append((nr, nc))
        return group

    def find_captures(player_stones, opponent_stones):
        captures = []
        for row, col in opponent_stones:
            opponent_group = get_group(row, col, set(opponent_stones))
            liberties = get_liberties(opponent_group)
            if len(liberties) == 1:
                capture_point = list(liberties)[0]
                if capture_point not in player_stones and capture_point not in opponent_stones and capture_point[0] > 0 and capture_point[1] > 0:
                   captures.append(capture_point)
        return captures

    def is_suicide(row, col, my_stones, opponent_stones):
        new_stones = my_stones + [(row, col)]
        my_group = get_group(row, col, set(new_stones))
        liberties = get_liberties(my_group)
        if len(liberties) == 0: #No liberties at all
            # Check if opponent stones captured by this move
            temp_board = set(new_stones)
            captured_opponent_stones = []
            for r, c in opponent_stones:
                opponent_group = get_group(r, c, set(opponent_stones))
                opponent_liberties = get_liberties(opponent_group)
                if len(opponent_liberties.intersection(temp_board)) == 0:
                    captured_opponent_stones.extend(opponent_group)

            if not captured_opponent_stones:
                return True

        return False

    # 1. Capture Detection
    captures = find_captures(me, opponent)
    if captures:
        return random.choice(captures), memory

    # 2. Avoid Suicide & Check for valid moves, prioritize corner moves
    valid_moves = []
    corner_moves = []
    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            if (row, col) not in occupied:
                if not is_suicide(row, col, me, opponent):
                    valid_moves.append((row, col))
                    # Prioritize corners
                    if (row <= 3 or row >= board_size - 2) and (col <= 3 or col >= board_size - 2):
                        corner_moves.append((row,col))
    
    if corner_moves:
        return random.choice(corner_moves), memory

    #3. Play a random valid move
    if valid_moves:
        return random.choice(valid_moves), memory
    # 4. Pass
    return (0, 0), memory
