
import numpy as np

def get_liberties(stones, board_size=19):
    liberties = set()
    for r, c in stones:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if(abs(dr) + abs(dc) == 1):  # Only check neighbors
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= board_size and 1 <= nc <= board_size:
                        liberties.add((nr, nc))
    return liberties

def is_point_occupied(point, my_stones, opponent_stones):
    return point in my_stones or point in opponent_stones

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    board_size = 19
    my_stones = set(me)
    opponent_stones = set(opponent)

    # Get potential liberties
    my_liberties = get_liberties(my_stones, board_size)
    opponent_liberties = get_liberties(opponent_stones, board_size)

    # Find safe moves (not occupied by our or opponent's stones)
    safe_moves = [pos for pos in my_liberties if not is_point_occupied(pos, my_stones, opponent_stones)]
    
    if not safe_moves:
        return (0, 0)  # Pass if no moves available

    # Evaluate the best move (naive heuristic by selecting the first safe move)
    # More advanced evaluation can be done here by considering the influence and terrain of the move.
    return safe_moves[0]
