
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Targeting mode: look for hits and their adjacent cells
    for r in range(10):
        for c in range(10):
            if board[r][c] == 1:
                # Check right for consecutive hits
                dc = 1
                while c + dc < 10 and board[r][c + dc] == 1:
                    dc += 1
                if c + dc < 10 and board[r][c + dc] == 0:
                    return (r, c + dc)
                # Check down for consecutive hits
                dr = 1
                while r + dr < 10 and board[r + dr][c] == 1:
                    dr += 1
                if r + dr < 10 and board[r + dr][c] == 0:
                    return (r + dr, c)
                # Check left for consecutive hits
                dc = 1
                while c - dc >= 0 and board[r][c - dc] == 1:
                    dc += 1
                if c - dc >= 0 and board[r][c - dc] == 0:
                    return (r, c - dc)
                # Check up for consecutive hits
                dr = 1
                while r - dr >= 0 and board[r - dr][c] == 1:
                    dr += 1
                if r - dr >= 0 and board[r - dr][c] == 0:
                    return (r - dr, c)
                # Check immediate neighboring cells if no consecutive hits
                for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                        return (nr, nc)
    # Hunting mode: checkerboard pattern (even then odd)
    for parity in [0, 1]:
        for r in range(10):
            for c in range(10):
                if board[r][c] == 0 and (r + c) % 2 == parity:
                    return (r, c)
    # Fallback if all covered (shouldn't be necessary)
    for r in range(10):
        for c in range(10):
            if board[r][c] == 0:
                return (r, c)
    return (0, 0)  # default case
