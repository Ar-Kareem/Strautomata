
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board, dtype=int)

    def get_hunt():
        hunt = np.zeros((10, 10), dtype=float)
        lengths = [5, 4, 3, 3, 2]
        for length in lengths:
            # horizontal
            for r in range(10):
                for startc in range(11 - length):
                    for k in range(length):
                        hunt[r, startc + k] += 1
            # vertical
            for c in range(10):
                for startr in range(11 - length):
                    for k in range(length):
                        hunt[startr + k, c] += 1
        return hunt

    hunt = get_hunt()

    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    # Collect unique target candidates: unknown cells adjacent to hits
    target_candidates = set()
    for r in range(10):
        for c in range(10):
            if board[r, c] == 1:
                for dr, dc in directions:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < 10 and 0 <= nc < 10 and board[nr, nc] == 0:
                        target_candidates.add((nr, nc))

    if target_candidates:
        # Prioritize candidate adjacent to most hits
        best_pos = None
        best_score = -np.inf
        for cand_r, cand_c in target_candidates:
            score = 0
            for dr, dc in directions:
                nr, nc = cand_r + dr, cand_c + dc
                if 0 <= nr < 10 and 0 <= nc < 10 and board[nr, nc] == 1:
                    score += 1
            pos = (cand_r, cand_c)
            if best_pos is None or score > best_score or (score == best_score and pos < best_pos):
                best_score = score
                best_pos = pos
        return best_pos
    else:
        # Hunt mode: unknown cell with highest hunt score, lex smallest tiebreaker
        best_pos = None
        best_score = -np.inf
        for r in range(10):
            for c in range(10):
                if board[r, c] == 0:
                    score = hunt[r, c]
                    pos = (r, c)
                    if best_pos is None or score > best_score or (score == best_score and pos < best_pos):
                        best_score = score
                        best_pos = pos
        return best_pos
