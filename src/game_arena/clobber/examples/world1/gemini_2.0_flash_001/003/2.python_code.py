
import numpy as np
import random
from collections import deque

def count_connected_components(board):
    rows, cols = board.shape
    visited = np.zeros((rows, cols), dtype=bool)
    count = 0

    def bfs(r, c):
        if r < 0 or r >= rows or c < 0 or c >= cols or visited[r, c] or board[r, c] == 0:
            return
        
        q = deque([(r, c)])
        visited[r, c] = True

        while q:
            row, col = q.popleft()

            neighbors = [(row + 1, col), (row - 1, col), (row, col + 1), (row, col - 1)]
            for nr, nc in neighbors:
                if 0 <= nr < rows and 0 <= nc < cols and board[nr, nc] == 1 and not visited[nr, nc]:
                    q.append((nr, nc))
                    visited[nr, nc] = True

    for r in range(rows):
        for c in range(cols):
            if board[r, c] == 1 and not visited[r, c]:
                bfs(r, c)
                count += 1

    return count

def policy(you: list[int], opponent: list[int]) -> str:
    you = np.array(you).reshape((5, 6))
    opponent = np.array(opponent).reshape((5, 6))
    rows, cols = you.shape
    
    legal_moves = []
    for r in range(rows):
        for c in range(cols):
            if you[r, c] == 1:
                # Check up
                if r > 0 and opponent[r-1, c] == 1:
                    legal_moves.append((r, c, 'U'))
                # Check down
                if r < rows - 1 and opponent[r+1, c] == 1:
                    legal_moves.append((r, c, 'D'))
                # Check left
                if c > 0 and opponent[r, c-1] == 1:
                    legal_moves.append((r, c, 'L'))
                # Check right
                if c < cols - 1 and opponent[r, c+1] == 1:
                    legal_moves.append((r, c, 'R'))

    if not legal_moves:
        return "0,0,U"

    best_move = None
    min_components_sum = float('inf')

    for move in legal_moves:
        r, c, direction = move
        
        # Simulate the move
        new_you = you.copy()
        new_opponent = opponent.copy()
        
        new_you[r, c] = 0
        
        if direction == 'U':
            new_you[r-1, c] = 1
            new_opponent[r-1, c] = 0
        elif direction == 'D':
            new_you[r+1, c] = 1
            new_opponent[r+1, c] = 0
        elif direction == 'L':
            new_you[r, c-1] = 1
            new_opponent[r, c-1] = 0
        elif direction == 'R':
            new_you[r, c+1] = 1
            new_opponent[r, c+1] = 0
            
        # Count connected components
        you_components = count_connected_components(new_you)
        opponent_components = count_connected_components(new_opponent)
        
        components_sum = you_components + opponent_components
        
        if components_sum < min_components_sum:
            min_components_sum = components_sum
            best_move = move

    if best_move:
        r, c, direction = best_move
        return f"{r},{c},{direction}"
    else:
        r, c, direction = random.choice(legal_moves)
        return f"{r},{c},{direction}"
