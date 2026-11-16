
def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    board_size = 11
    my_stones = set(me)
    opponent_stones = set(opp)

    def is_winning_move(stone_set):
        # A simple approach to check for winning condition (you may want to refine this)
        # We'll check connections for my color
        def check_connection(start, visited):
            stack = [start]
            while stack:
                x, y = stack.pop()
                if color == 'b' and x == board_size - 1:  # Bottom row for black
                    return True
                if color == 'w' and y == board_size - 1:  # Right column for white
                    return True
                neighbors = [
                    (x, y - 1), (x, y + 1),
                    (x - 1, y), (x + 1, y), 
                    (x - 1, y + 1), (x + 1, y - 1)
                ]
                for nx, ny in neighbors:
                    if (0 <= nx < board_size and 0 <= ny < board_size and
                            (nx, ny) in stone_set and (nx, ny) not in visited):
                        visited.add((nx, ny))
                        stack.append((nx, ny))
            return False

        for stone in stone_set:
            if check_connection(stone, {stone}):
                return True
        return False

    def get_empty_neighbors(x, y):
        neighbors = [
            (x, y - 1), (x, y + 1), 
            (x - 1, y), (x + 1, y), 
            (x - 1, y + 1), (x + 1, y - 1)
        ]
        return [(nx, ny) for nx, ny in neighbors if 0 <= nx < board_size and 0 <= ny < board_size and (nx, ny) not in my_stones and (nx, ny) not in opponent_stones]

    # Check for immediate winning move 
    for x in range(board_size):
        for y in range(board_size):
            if (x, y) not in my_stones and (x, y) not in opponent_stones:
                my_stones.add((x, y))
                if is_winning_move(my_stones):
                    return (x, y)
                my_stones.remove((x, y))

    # Block opponent's winning moves
    for x in range(board_size):
        for y in range(board_size):
            if (x, y) not in my_stones and (x, y) not in opponent_stones:
                opponent_stones.add((x, y))
                if is_winning_move(opponent_stones):
                    opponent_stones.remove((x, y))
                    return (x, y)
                opponent_stones.remove((x, y))

    # Create a scoring system to evaluate potential moves
    best_move = None
    best_score = -1

    for x in range(board_size):
        for y in range(board_size):
            if (x, y) not in my_stones and (x, y) not in opponent_stones:
                # Pretend to place my stone
                my_stones.add((x, y))
                score = 0
                
                # Increase score based on connectivity
                for nx, ny in get_empty_neighbors(x, y):
                    if (nx, ny) in my_stones:
                        score += 1
                
                # Decrease score if it connects the opponent
                for nx, ny in get_empty_neighbors(x, y):
                    if (nx, ny) in opponent_stones:
                        score -= 1

                if score > best_score:
                    best_score = score
                    best_move = (x, y)

                my_stones.remove((x, y))

    # Fallback if no move could be evaluated
    return best_move if best_move else (0, 0)

