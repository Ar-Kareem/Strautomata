
import random

def compute_prob(n=10, ships=[5, 4, 3, 3, 2]):
    prob = [[0.0] * n for _ in range(n)]
    for length in ships:
        # Horizontal
        for r in range(n):
            for sc in range(n - length + 1):
                for i in range(length):
                    prob[r][sc + i] += 1.0
        # Vertical
        for c in range(n):
            for sr in range(n - length + 1):
                for i in range(length):
                    prob[sr + i][c] += 1.0
    return prob

def policy(board: list[list[int]]) -> tuple[int, int]:
    n = len(board)
    dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def valid(r: int, c: int) -> bool:
        return 0 <= r < n and 0 <= c < n

    # Find hot cells: empty cells adjacent to hits, scored by number of adjacent hits
    hot = []
    for r in range(n):
        for c in range(n):
            if board[r][c] != 0:
                continue
            score = 0
            for dr, dc in dirs:
                nr, nc = r + dr, c + dc
                if valid(nr, nc) and board[nr][nc] == 1:
                    score += 1
            if score > 0:
                hot.append(((r, c), score))

    if hot:
        hot.sort(key=lambda x: x[1], reverse=True)
        max_score = hot[0][1]
        candidates = [pos for pos, sc in hot if sc == max_score]
        return random.choice(candidates)

    # Hunt phase: probability-based selection
    probs = compute_prob(n)
    empties = []
    for r in range(n):
        for c in range(n):
            if board[r][c] == 0:
                empties.append((r, c, probs[r][c]))
    empties.sort(key=lambda x: x[2], reverse=True)
    max_prob = empties[0][2]
    candidates = [(r, c) for r, c, p in empties if p == max_prob]
    return random.choice(candidates)
