
from functools import lru_cache
from typing import List, Tuple

def policy(board: List[List[int]]) -> Tuple[int, int]:
    # Convert board to tuple for caching
    b = tuple(tuple(row) for row in board)

    def check_winner(bd):
        # rows, cols, diagonals
        for i in range(3):
            s = sum(bd[i])
            if s == 3: return 1
            if s == -3: return -1
            s = bd[0][i] + bd[1][i] + bd[2][i]
            if s == 3: return 1
            if s == -3: return -1
        d1 = bd[0][0] + bd[1][1] + bd[2][2]
        d2 = bd[0][2] + bd[1][1] + bd[2][0]
        if d1 == 3 or d2 == 3: return 1
        if d1 == -3 or d2 == -3: return -1
        return 0

    def moves(bd):
        return [(r, c) for r in range(3) for c in range(3) if bd[r][c] == 0]

    @lru_cache(None)
    def minimax(bd, player):
        # bd is tuple of tuples, player is 1 or -1
        winner = check_winner(bd)
        if winner != 0:
            return winner, None
        if all(bd[r][c] != 0 for r in range(3) for c in range(3)):
            return 0, None

        best_score = -2 if player == 1 else 2
        best_move = None
        for (r, c) in moves(bd):
            new_bd = [list(row) for row in bd]
            new_bd[r][c] = player
            new_bd_t = tuple(tuple(row) for row in new_bd)
            score, _ = minimax(new_bd_t, -player)
            if player == 1:
                if score > best_score:
                    best_score = score
                    best_move = (r, c)
            else:
                if score < best_score:
                    best_score = score
                    best_move = (r, c)
        return best_score, best_move

    # Tie-break preference: center, corners, edges
    preferred = [(1,1), (0,0), (0,2), (2,0), (2,2), (0,1), (1,0), (1,2), (2,1)]

    score, move = minimax(b, 1)
    if move is None:
        # fallback: first available preferred
        for (r,c) in preferred:
            if board[r][c] == 0:
                return (r,c)
    return move
