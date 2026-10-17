
def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    occupied = set(me) | set(opponent)
    priority_moves = [
        (1, 1), (1, 19), (19, 1), (19, 19),  # Corners
        (4, 4), (4, 16), (16, 4), (16, 16),  # 4-4 points
        (4, 10), (10, 4), (10, 16), (16, 10), (10, 10),  # Star points
    ]
    
    for move in priority_moves:
        if move not in occupied:
            r, c = move
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 1 <= nr <= 19 and 1 <= nc <= 19:
                    if (nr, nc) not in occupied:
                        return move
    
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in occupied:
                for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nr, nc = r + dr, c + dc
                    if 1 <= nr <= 19 and 1 <= nc <= 19:
                        if (nr, nc) not in occupied:
                            return (r, c)
    
    return (0, 0)
