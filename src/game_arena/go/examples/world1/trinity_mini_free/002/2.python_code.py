
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Check for opponent atari (one liberty)
    for stone in opponent:
        liberties = []
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            r, c = stone[0] + dr, stone[1] + dc
            if 1 <= r <= 19 and 1 <= c <= 19:
                if (r, c) not in me and (r, c) not in opponent:
                    liberties.append((r, c))
        if len(liberties) == 1:
            return liberties[0]  # Capture opponent stone
    
    # Check for my own atari
    for stone in me:
        liberties = []
        for dr, dc in [(1,0), (-1,0), (0,1), (0,-1)]:
            r, c = stone[0] + dr, stone[1] + dc
            if 1 <= r <= 19 and 1 <= c <= 19:
                if (r, c) not in me and (r, c) not in opponent:
                    liberties.append((r, c))
        if len(liberties) == 1:
            return liberties[0]  # Save my stone
    
    # Expand territory on 3rd/4th lines
    priority_positions = [
        (3, 3), (3, 4), (4, 3), (4, 4),
        (3, 16), (3, 15), (4, 15), (4, 16),
        (16, 3), (16, 4), (15, 3), (15, 4),
        (16, 16), (16, 15), (15, 16), (15, 15)
    ]
    for pos in priority_positions:
        if pos not in me and pos not in opponent:
            return pos
    
    # Pass if no opportunities
    return (0, 0)
