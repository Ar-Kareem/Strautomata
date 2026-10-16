
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    dirs = [ (0, 1), (1, 0), (0, -1), (-1, 0) ]  # east, south, west, north
    rows = len(board)
    cols = len(board[0]) if rows > 0 else 0

    # Collect all unknown cells adjacent to hits
    hit_adjacent_targets = []
    for i in range(rows):
        for j in range(cols):
            if board[i][j] == 1:
                for dx, dy in dirs:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < rows and 0 <= nj < cols and board[ni][nj] == 0:
                        hit_adjacent_targets.append( (ni, nj) )

    # Targeting phase: prioritize cells in line with existing hits
    if hit_adjacent_targets:
        best_score = -1
        best_target = None
        candidates = []
        for (i, j) in hit_adjacent_targets:
            score = 0
            for (dx, dy) in dirs:
                length = 0
                ci, cj = i, j
                while True:
                    ci -= dx
                    cj -= dy
                    if 0 <= ci < rows and 0 <= cj < cols and board[ci][cj] == 1:
                        length += 1
                    else:
                        break
                score += length
            if score > best_score:
                best_score = score
                best_target = (i, j)
                candidates = [(i, j)]
            elif score == best_score:
                candidates.append( (i, j) )
        if len(candidates) > 0:
            return random.choice(candidates)  # randomize among best candidates

    # Hunting phase: select cell with most adjacent unknowns (central tendency)
    max_adj_unknown = -1
    best_hunt = []
    checkerboard_priority = 0  # prefers even i+j when tied
    for i in range(rows):
        for j in range(cols):
            if board[i][j] == 0:
                adj_unknown = 0
                for dx, dy in dirs:
                    ni, nj = i + dx, j + dy
                    if 0 <= ni < rows and 0 <= nj < cols and board[ni][nj] == 0:
                        adj_unknown += 1
                if adj_unknown > max_adj_unknown:
                    max_adj_unknown = adj_unknown
                    best_hunt = [ (i, j) ]
                elif adj_unknown == max_adj_unknown:
                    best_hunt.append( (i, j) )

    # Among best hunting candidates, prefer checkerboard pattern to spread shots
    if best_hunt:
        filtered = [ (i,j) for (i,j) in best_hunt if (i + j) % 2 == checkerboard_priority ]
        if not filtered:
            filtered = best_hunt
        return random.choice(filtered)  # randomize among remaining candidates

    # Fallback: return first available cell (shouldn't reach here)
    for i in range(rows):
        for j in range(cols):
            if board[i][j] == 0:
                return (i, j)
    return (0, 0)  # should never happen if called properly
