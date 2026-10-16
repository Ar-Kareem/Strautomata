
import random
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Convert to sets for faster lookups
    my_stones = set(me)
    opp_stones = set(opp)

    # Determine the goal sides for the current player
    if color == 'b':
        goal_rows = {0, 10}  # Black connects top (0) and bottom (10)
    else:
        goal_cols = {0, 10}  # White connects left (0) and right (10)

    # Generate all empty cells
    empty_cells = []
    for i in range(11):
        for j in range(11):
            if (i, j) not in my_stones and (i, j) not in opp_stones:
                empty_cells.append((i, j))

    # Check if opponent is about to win (block immediately)
    opp_move = find_opponent_win(opp_stones, my_stones, color)
    if opp_move is not None:
        return opp_move

    # Check if we can win immediately (prioritize)
    my_move = find_my_win(my_stones, opp_stones, color)
    if my_move is not None:
        return my_move

    # If no immediate win/block, evaluate all possible moves
    best_move = None
    best_score = -float('inf')

    for move in empty_cells:
        # Simulate placing the stone
        temp_my_stones = my_stones.copy()
        temp_my_stones.add(move)

        # Evaluate the move using a heuristic
        score = evaluate_move(temp_my_stones, opp_stones, color)

        if score > best_score:
            best_score = score
            best_move = move

    # If no clear best move, pick a random one (fallback)
    if best_move is None:
        best_move = random.choice(empty_cells)

    return best_move

def find_opponent_win(opp_stones, my_stones, color):
    """Check if the opponent can win on their next move. If so, return the blocking move."""
    for move in opp_stones:
        # Simulate opponent placing a stone at 'move'
        temp_opp_stones = opp_stones.copy()
        temp_opp_stones.add(move)

        # Check if opponent has a winning path
        if has_winning_path(temp_opp_stones, my_stones, color, is_opponent=True):
            # Find the move that blocks this path
            for neighbor in get_neighbors(move):
                if neighbor not in my_stones and neighbor not in opp_stones:
                    return neighbor
    return None

def find_my_win(my_stones, opp_stones, color):
    """Check if we can win on our next move. If so, return the winning move."""
    for move in my_stones:
        # Simulate placing a stone at 'move'
        temp_my_stones = my_stones.copy()
        temp_my_stones.add(move)

        # Check if we have a winning path
        if has_winning_path(temp_my_stones, opp_stones, color, is_opponent=False):
            return move
    return None

def has_winning_path(stones, opponent_stones, color, is_opponent=False):
    """Check if 'stones' has a winning path (connects the goal sides)."""
    if color == 'b':
        # Black connects top (0) and bottom (10)
        goal_rows = {0, 10}
        for row in goal_rows:
            for col in range(11):
                if (row, col) in stones:
                    # BFS from this goal cell
                    visited = set()
                    queue = deque([(row, col)])
                    visited.add((row, col))

                    while queue:
                        i, j = queue.popleft()
                        for neighbor in get_neighbors((i, j)):
                            if neighbor in stones and neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)
                                if (neighbor[0] in goal_rows and neighbor != (row, col)):
                                    return True
    else:
        # White connects left (0) and right (10)
        goal_cols = {0, 10}
        for col in goal_cols:
            for row in range(11):
                if (row, col) in stones:
                    # BFS from this goal cell
                    visited = set()
                    queue = deque([(row, col)])
                    visited.add((row, col))

                    while queue:
                        i, j = queue.popleft()
                        for neighbor in get_neighbors((i, j)):
                            if neighbor in stones and neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)
                                if (neighbor[1] in goal_cols and neighbor != (row, col)):
                                    return True
    return False

def evaluate_move(my_stones, opp_stones, color):
    """Evaluate the strength of a move using heuristics."""
    score = 0

    # Heuristic 1: Number of potential winning paths for us
    score += len(get_potential_winning_paths(my_stones, opp_stones, color))

    # Heuristic 2: Number of opponent's potential winning paths (avoid)
    score -= len(get_potential_winning_paths(opp_stones, my_stones, 'w' if color == 'b' else 'b'))

    # Heuristic 3: Center control (prefer moves near the center)
    center_bias = 1 - (abs(5 - 5) + abs(5 - 5)) / 10  # Simplified center bias
    score += center_bias * 10

    # Heuristic 4: Longest chain length
    longest_chain = max(get_chain_lengths(my_stones, opp_stones, color))
    score += longest_chain * 2

    return score

def get_potential_winning_paths(stones, opponent_stones, color):
    """Get the number of potential winning paths for 'stones'."""
    paths = set()

    if color == 'b':
        # Black connects top (0) and bottom (10)
        for row in {0, 10}:
            for col in range(11):
                if (row, col) in stones:
                    # BFS from this goal cell
                    visited = set()
                    queue = deque([(row, col)])
                    visited.add((row, col))

                    while queue:
                        i, j = queue.popleft()
                        for neighbor in get_neighbors((i, j)):
                            if neighbor in stones and neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)
                                if (neighbor[0] in {0, 10} and neighbor != (row, col)):
                                    paths.add(tuple(sorted(visited)))
    else:
        # White connects left (0) and right (10)
        for col in {0, 10}:
            for row in range(11):
                if (row, col) in stones:
                    # BFS from this goal cell
                    visited = set()
                    queue = deque([(row, col)])
                    visited.add((row, col))

                    while queue:
                        i, j = queue.popleft()
                        for neighbor in get_neighbors((i, j)):
                            if neighbor in stones and neighbor not in visited:
                                visited.add(neighbor)
                                queue.append(neighbor)
                                if (neighbor[1] in {0, 10} and neighbor != (row, col)):
                                    paths.add(tuple(sorted(visited)))
    return paths

def get_chain_lengths(my_stones, opp_stones, color):
    """Get the lengths of all chains for 'my_stones'."""
    visited = set()
    chains = []

    for stone in my_stones:
        if stone not in visited:
            # BFS to find the chain
            queue = deque([stone])
            visited.add(stone)
            chain = set([stone])

            while queue:
                i, j = queue.popleft()
                for neighbor in get_neighbors((i, j)):
                    if neighbor in my_stones and neighbor not in visited:
                        visited.add(neighbor)
                        chain.add(neighbor)
                        queue.append(neighbor)
            chains.append(len(chain))
    return chains

def get_neighbors(cell):
    """Get all 6 neighbors of a hexagonal cell (i, j)."""
    i, j = cell
    neighbors = [
        (i-1, j), (i-1, j+1),  # Top-left and top-right
        (i, j-1), (i, j+1),    # Left and right
        (i+1, j-1), (i+1, j)   # Bottom-left and bottom-right
    ]
    # Filter out invalid neighbors (out of bounds)
    valid_neighbors = []
    for ni, nj in neighbors:
        if 0 <= ni < 11 and 0 <= nj < 11:
            valid_neighbors.append((ni, nj))
    return valid_neighbors
