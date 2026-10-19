
import numpy as np

def connected_components(board, player):
    visited = np.zeros(board.shape, dtype=bool)
    component_sizes = []

    def dfs(start):
        stack = [start]
        size = 0
        while stack:
            x, y = stack.pop()
            if visited[x, y]:
                continue
            visited[x, y] = True
            size += 1
            for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8 and not visited[nx, ny] and board[nx, ny] == player:
                    stack.append((nx, ny))
        return size

    for i in range(8):
        for j in range(8):
            if board[i, j] == player and not visited[i, j]:
                component_size = dfs((i, j))
                if component_size > 0:
                    component_sizes.append(component_size)

    return sum(component_sizes)

def evaluate_move(board, from_pos, to_pos):
    nx, ny = to_pos
    piece_count = np.sum(np.abs(board))  # Total number of pieces
    line_length = (board[from_pos] == 1).sum() + (board[from_pos] == -1).sum()
    
    # Verify move length
    if abs(nx - from_pos[0]) + abs(ny - from_pos[1]) != line_length:
        return -1  # Invalid move based on length rules
    
    # Check for blocking by opponent's pieces
    direction = np.sign((nx - from_pos[0], ny - from_pos[1]))
    x, y = from_pos[0] + direction[0], from_pos[1] + direction[1]
    while (x, y) != (nx, ny):
        if board[x, y] == -1:
            return -1  # Blocked by opponent flag
        x += direction[0]
        y += direction[1]
    
    # Simulate the move
    board_copy = board.copy()
    board_copy[to_pos] = 1
    board_copy[from_pos] = 0
    
    # Calculate new connected components
    my_component_size = connected_components(board_copy, 1)
    opponent_component_size = connected_components(board_copy, -1)
    
    return my_component_size - opponent_component_size


def policy(board):
    board = np.array(board)
    legal_moves = []

    for i in range(8):
        for j in range(8):
            if board[i, j] == 1:  # My piece
                for dx in range(-7, 8):  # Line movement in x-direction
                    for dy in range(-7, 8):  # Line movement in y-direction
                        if dx == 0 and dy == 0:
                            continue

                        # Calculate potential new position
                        to_x = i + dx
                        to_y = j + dy
                        if 0 <= to_x < 8 and 0 <= to_y < 8:  # Ensure it's within the board
                            move = (i, j), (to_x, to_y)
                            score = evaluate_move(board, (i, j), (to_x, to_y))
                            
                            if score >= 0:
                                legal_moves.append((move, score))

    if not legal_moves:
        return ""  # Ideally should not happen based on constraints

    # Sort moves based on score
    legal_moves.sort(key=lambda x: x[1], reverse=True)
    best_move = legal_moves[0][0]

    return f"{best_move[0][0]},{best_move[0][1]}:{best_move[1][0]},{best_move[1][1]}"
