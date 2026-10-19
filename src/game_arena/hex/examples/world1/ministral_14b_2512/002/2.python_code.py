
import random
from collections import deque

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Convert to sets for faster lookups
    my_stones = set(me)
    opp_stones = set(opp)

    # Check for immediate win
    move = find_immediate_win(my_stones, opp_stones, color)
    if move is not None:
        return move

    # Check for opponent's immediate win and block
    move = find_immediate_win(opp_stones, my_stones, 'w' if color == 'b' else 'b')
    if move is not None:
        return move

    # Strong opening strategy
    if len(my_stones) < 3:
        return strong_opening(color, my_stones, opp_stones)

    # For later moves, use a more sophisticated strategy
    return best_move(my_stones, opp_stones, color)

def strong_opening(color: str, my_stones: set, opp_stones: set) -> tuple[int, int]:
    # Predefined strong opening moves for Hex
    openings = {
        'b': [(5, 5), (5, 6), (4, 5), (6, 5)],
        'w': [(5, 5), (5, 4), (6, 5), (4, 5)]
    }
    for move in openings[color]:
        if move not in my_stones and move not in opp_stones:
            return move
    return (5, 5)  # fallback

def find_immediate_win(my_stones: set, opp_stones: set, color: str) -> tuple[int, int]:
    # Check if placing a stone at (row, col) completes a path
    for row in range(11):
        for col in range(11):
            if (row, col) not in my_stones and (row, col) not in opp_stones:
                # Check if adding this stone completes a path
                temp_stones = my_stones.copy()
                temp_stones.add((row, col))
                if is_winner(temp_stones, color):
                    return (row, col)
    return None

def is_winner(stones: set, color: str) -> bool:
    # Check if the stones form a connected path from one side to the other
    if color == 'b':
        # Black connects top to bottom
        for col in range(11):
            # Check vertical path
            path = []
            for row in range(11):
                if (row, col) in stones:
                    path.append((row, col))
                    if len(path) >= 2 and path[0][0] == 0 and path[-1][0] == 10:
                        return True
            # Check diagonal paths (top-left to bottom-right)
            for row in range(11):
                for col in range(11):
                    if (row, col) in stones:
                        # Check if this stone is part of a diagonal path
                        # This is a simplified check; a full implementation would be more complex
                        pass
    else:
        # White connects left to right
        for row in range(11):
            # Check horizontal path
            path = []
            for col in range(11):
                if (row, col) in stones:
                    path.append((row, col))
                    if len(path) >= 2 and path[0][1] == 0 and path[-1][1] == 10:
                        return True
    # More sophisticated checks for non-axial paths
    # This is a placeholder; a full implementation would use BFS/DFS to check connectivity
    return False

def best_move(my_stones: set, opp_stones: set, color: str) -> tuple[int, int]:
    # Evaluate all possible moves and choose the best one
    best_score = -float('inf')
    best_move = None

    for row in range(11):
        for col in range(11):
            if (row, col) not in my_stones and (row, col) not in opp_stones:
                # Simulate placing the stone
                temp_my_stones = my_stones.copy()
                temp_my_stones.add((row, col))
                score = evaluate_move(temp_my_stones, opp_stones, color)
                if score > best_score:
                    best_score = score
                    best_move = (row, col)
                elif score == best_score:
                    # Randomly choose between equally good moves
                    if random.random() < 0.5:
                        best_move = (row, col)

    return best_move

def evaluate_move(my_stones: set, opp_stones: set, color: str) -> float:
    # Evaluate the strategic value of a move
    score = 0

    # Check if the move creates a potential winning path
    if is_potential_win(my_stones, opp_stones, color):
        score += 1000

    # Check connectivity
    score += len(get_connected_components(my_stones)) * 10

    # Check control of the center
    if 4 <= row <= 6 and 4 <= col <= 6:
        score += 5

    # Check proximity to opponent's stones
    for (r, c) in opp_stones:
        if abs(r - row) <= 1 and abs(c - col) <= 1:
            score += 2

    # Check if the move is near the edges (for black/white)
    if color == 'b':
        if row == 0 or row == 10:
            score += 10
    else:
        if col == 0 or col == 10:
            score += 10

    return score

def is_potential_win(my_stones: set, opp_stones: set, color: str) -> bool:
    # Simplified check for potential winning moves
    # This is a placeholder; a full implementation would be more complex
    return False

def get_connected_components(stones: set) -> int:
    # Count the number of connected components
    visited = set()
    components = 0

    for stone in stones:
        if stone not in visited:
            components += 1
            queue = deque([stone])
            visited.add(stone)
            while queue:
                current = queue.popleft()
                for neighbor in get_neighbors(current):
                    if neighbor in stones and neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
    return components

def get_neighbors(cell: tuple[int, int]) -> list[tuple[int, int]]:
    # Get all 6 neighbors of a hexagonal cell
    row, col = cell
    neighbors = [
        (row - 1, col), (row - 1, col + 1),
        (row, col + 1), (row + 1, col),
        (row + 1, col - 1), (row, col - 1)
    ]
    # Filter out invalid neighbors (out of bounds)
    return [n for n in neighbors if 0 <= n[0] <= 10 and 0 <= n[1] <= 10]
