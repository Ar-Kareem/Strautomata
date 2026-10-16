
def policy(board: list[list[int]]) -> tuple[int, int]:
    # Function to get all hunting candidates based on active hits
    def get_hunt_candidates():
        candidates = []
        seen = set()  # To avoid duplicates
        for i in range(10):
            for j in range(10):
                if board[i][j] == 1:
                    # Vertical up
                    ni = i - 1
                    while ni >= 0:
                        if board[ni][j] == 0:
                            if (ni, j) not in seen:
                                candidates.append((ni, j))
                                seen.add((ni, j))
                            break
                        elif board[ni][j] == -1:
                            break
                        else:
                            ni -= 1
                    # Vertical down
                    ni = i + 1
                    while ni < 10:
                        if board[ni][j] == 0:
                            if (ni, j) not in seen:
                                candidates.append((ni, j))
                                seen.add((ni, j))
                            break
                        elif board[ni][j] == -1:
                            break
                        else:
                            ni += 1
                    # Horizontal left
                    nj = j - 1
                    while nj >= 0:
                        if board[i][nj] == 0:
                            if (i, nj) not in seen:
                                candidates.append((i, nj))
                                seen.add((i, nj))
                            break
                        elif board[i][nj] == -1:
                            break
                        else:
                            nj -= 1
                    # Horizontal right
                    nj = j + 1
                    while nj < 10:
                        if board[i][nj] == 0:
                            if (i, nj) not in seen:
                                candidates.append((i, nj))
                                seen.add((i, nj))
                            break
                        elif board[i][nj] == -1:
                            break
                        else:
                            nj += 1
        return candidates

    # Hunting mode: Use candidates from hits
    candidates = get_hunt_candidates()
    if candidates:
        # Return the first candidate (deterministic for testing, but effective)
        return candidates[0]
    
    # Search mode: Checkerboard pattern
    for i in range(10):
        for j in range(10):
            if (i + j) % 2 == 0 and board[i][j] == 0:
                return (i, j)
    
    # Fallback: Any unexplored cell (should not happen, but ensures legality)
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
    
    # Redundant fallback (impossible in a valid board with ships unsolved)
    return (0, 0)
