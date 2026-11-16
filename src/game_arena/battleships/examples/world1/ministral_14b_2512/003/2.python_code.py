
import heapq

def policy(board):
    # Collect all hits
    hits = []
    for i in range(10):
        for j in range(10):
            if board[i][j] == 1:
                hits.append((i, j))

    # If no hits, use a systematic search (e.g., diagonal)
    if not hits:
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    return (i, j)
        return (0, 0)

    # Priority queue for candidates: (-score, row, col)
    candidates = []

    # Directions: horizontal and vertical
    directions = [(0, 1), (1, 0)]  # right and down

    # For each hit, explore possible ship extensions
    for (r, c) in hits:
        # Check horizontal line
        # Left
        for k in range(1, 6):
            nr, nc = r, c - k
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                # Score based on consecutive hits to the right
                consecutive = 0
                for l in range(1, k + 1):
                    nr2, nc2 = r, c + l
                    if 0 <= nr2 < 10 and 0 <= nc2 < 10 and board[nr2][nc2] == 1:
                        consecutive += 1
                    else:
                        break
                score = consecutive * 10
                heapq.heappush(candidates, (-score, nr, nc))

        # Right
        for k in range(1, 6):
            nr, nc = r, c + k
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                consecutive = 0
                for l in range(1, k + 1):
                    nr2, nc2 = r, c - l
                    if 0 <= nr2 < 10 and 0 <= nc2 < 10 and board[nr2][nc2] == 1:
                        consecutive += 1
                    else:
                        break
                score = consecutive * 10
                heapq.heappush(candidates, (-score, nr, nc))

        # Check vertical line
        # Up
        for k in range(1, 6):
            nr, nc = r - k, c
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                consecutive = 0
                for l in range(1, k + 1):
                    nr2, nc2 = r + l, c
                    if 0 <= nr2 < 10 and 0 <= nc2 < 10 and board[nr2][nc2] == 1:
                        consecutive += 1
                    else:
                        break
                score = consecutive * 10
                heapq.heappush(candidates, (-score, nr, nc))

        # Down
        for k in range(1, 6):
            nr, nc = r + k, c
            if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                consecutive = 0
                for l in range(1, k + 1):
                    nr2, nc2 = r - l, c
                    if 0 <= nr2 < 10 and 0 <= nc2 < 10 and board[nr2][nc2] == 1:
                        consecutive += 1
                    else:
                        break
                score = consecutive * 10
                heapq.heappush(candidates, (-score, nr, nc))

    # Also consider cells adjacent to hits (not just in lines)
    for (r, c) in hits:
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr][nc] == 0:
                    # Score based on proximity to hits
                    score = 0
                    for dr2 in [-1, 0, 1]:
                        for dc2 in [-1, 0, 1]:
                            if dr2 == 0 and dc2 == 0:
                                continue
                            nr2, nc2 = nr + dr2, nc + dc2
                            if 0 <= nr2 < 10 and 0 <= nc2 < 10 and board[nr2][nc2] == 1:
                                score += 1
                    heapq.heappush(candidates, (-score, nr, nc))

    # If no candidates (shouldn't happen if there are hits), fall back to spiral
    if not candidates:
        for i in range(10):
            for j in range(10):
                if board[i][j] == 0:
                    return (i, j)
        return (0, 0)

    # Get the highest scoring candidate
    while candidates:
        neg_score, r, c = heapq.heappop(candidates)
        if board[r][c] == 0:
            return (r, c)

    # Fallback: return any unfired cell
    for i in range(10):
        for j in range(10):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)
