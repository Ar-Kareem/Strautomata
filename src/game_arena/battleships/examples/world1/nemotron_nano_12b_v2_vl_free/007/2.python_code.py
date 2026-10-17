
def policy(board):
    def generate_row_wise_order():
        order = []
        for r in range(10):
            if r % 2 == 0:
                for c in range(10):
                    order.append((r, c))
            else:
                for c in range(9, -1, -1):
                    order.append((r, c))
        return order

    # Check for hits and expand
    hits = [(r, c) for r in range(10) for c in range(10) if board[r][c] == 1]
    if hits:
        candidates = []
        for (r, c) in hits:
            for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    candidates.append((nr, nc, r, c))
        
        sorted_candidates = []
        for (nr, nc, orig_r, orig_c) in candidates:
            dx = nc - orig_c
            dy = nr - orig_r
            if dx == 1 and dy == 0:
                priority = 0  # right
            elif dx == -1 and dy == 0:
                priority = 1  # left
            elif dy == 1 and dx == 0:
                priority = 2  # down
            elif dy == -1 and dx == 0:
                priority = 3  # up
            else:
                priority = 4  # not adjacent
            sorted_candidates.append((priority, (nr, nc)))
        
        if sorted_candidates:
            sorted_candidates.sort(key=lambda x: x[0])
            for candidate in sorted_candidates:
                if board[candidate[0]][candidate[1]] == 0:
                    return candidate[0], candidate[1]
    
    # If no hits, use row-wise search
    order = generate_row_wise_order()
    for (r, c) in order:
        if board[r][c] == 0:
            return r, c
    
    return (0, 0)
