
import numpy as np
import collections

def count_components(board, player):
    visited = np.zeros((8, 8), dtype=bool)
    components = 0
    directions = [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]
    
    def bfs(sr, sc):
        queue = collections.deque([(sr, sc)])
        visited[sr, sc] = True
        while queue:
            r, c = queue.popleft()
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8 and board[nr, nc] == player and not visited[nr, nc]:
                    visited[nr, nc] = True
                    queue.append((nr, nc))
    
    for r in range(8):
        for c in range(8):
            if board[r, c] == player and not visited[r, c]:
                components += 1
                bfs(r, c)
    return components

def get_legal_moves(board):
    moves = []
    directions = [
        (0, 1), (0, -1), (1, 0), (-1, 0),
        (1, 1), (1, -1), (-1, 1), (-1, -1)
    ]
    
    def compute_k(r, c, dr, dc):
        if dr == 0:  # horizontal
            return sum(abs(board[r, j]) for j in range(8))
        elif dc == 0:  # vertical
            return sum(abs(board[i, c]) for i in range(8))
        else:  # diagonal
            if dr == dc:  # i - j = const or i + j = const? For (1,1)/(-1,-1): i - j = const
                const = r - c
                return sum(abs(board[i, j]) for i in range(8) for j in range(8) if i - j == const)
            else:  # (1,-1)/(-1,1): i + j = const
                const = r + c
                return sum(abs(board[i, j]) for i in range(8) for j in range(8) if i + j == const)
    
    for r in range(8):
        for c in range(8):
            if board[r, c] == 1:
                for dr, dc in directions:
                    k = compute_k(r, c, dr, dc)
                    r2, c2 = r + k * dr, c + k * dc
                    if 0 <= r2 < 8 and 0 <= c2 < 8:
                        # Check path
                        legal = True
                        for step in range(1, k):
                            nr, nc = r + step * dr, c + step * dc
                            if board[nr, nc] == -1:
                                legal = False
                                break
                        if legal:
                            moves.append((r, c, r2, c2))
    return moves

def policy(board):
    board = np.array(board)  # Ensure it's a numpy array
    moves = get_legal_moves(board)
    best_score = float('inf')
    best_move = None
    
    for r, c, r2, c2 in moves:
        new_board = board.copy()
        new_board[r, c] = 0
        new_board[r2, c2] = 1
        my_comp = count_components(new_board, 1)
        opp_comp = count_components(new_board, -1)
        score = my_comp - opp_comp  # Minimize this: low my, high opp
        if score < best_score:
            best_score = score
            best_move = f"{r},{c}:{r2},{c2}"
    
    return best_move  # Assumes at least one move exists
