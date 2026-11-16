
import random
from collections import deque

def get_neighbors(i, j):
    neighbors = []
    if i > 0:
        neighbors.append((i-1, j))
    if i < 18:
        neighbors.append((i+1, j))
    if j > 0:
        neighbors.append((i, j-1))
    if j < 18:
        neighbors.append((i, j+1))
    return neighbors

def get_group(board, i, j, color):
    visited = set()
    group = set()
    queue = deque([(i,j)])
    while queue:
        point = queue.popleft()
        if point in visited:
            continue
        visited.add(point)
        if board[point[0]][point[1]] == color:
            group.add(point)
            for neighbor in get_neighbors(point[0], point[1]):
                if neighbor not in visited:
                    queue.append(neighbor)
    liberties = set()
    for point in group:
        for neighbor in get_neighbors(point[0], point[1]):
            if board[neighbor[0]][neighbor[1]] == 0:
                liberties.add(neighbor)
    return group, liberties

def simulate_move(board, i, j, color):
    new_board = [row[:] for row in board]
    new_board[i][j] = color
    opponent_color = 3 - color
    captured_stones = []
    visited = set()
    for neighbor in get_neighbors(i,j):
        if neighbor in visited:
            continue
        if new_board[neighbor[0]][neighbor[1]] == opponent_color:
            group, liberties = get_group(new_board, neighbor[0], neighbor[1], opponent_color)
            if not liberties:
                for point in group:
                    new_board[point[0]][point[1]] = 0
                    captured_stones.append(point)
                visited.update(group)
    my_group, my_liberties = get_group(new_board, i, j, color)
    if my_liberties:
        is_legal = True
    else:
        is_legal = len(captured_stones) > 0
    return new_board, captured_stones, is_legal

def get_position_value(i,j):
    if (i,j) in [(0,0), (0,18), (18,0), (18,18)]:
        return 20
    elif i==0 or i==18 or j==0 or j==18:
        return 10
    else:
        return 0

def policy(me, opponent, memory):
    if not memory:
        memory = {}
    memory['move_number'] = memory.get('move_number', 0) + 1

    board = [[0]*19 for _ in range(19)]
    for row, col in me:
        board[row-1][col-1] = 1
    for row, col in opponent:
        board[row-1][col-1] = 2

    empty_points = []
    for i in range(19):
        for j in range(19):
            if board[i][j] == 0:
                empty_points.append((i,j))

    if not empty_points:
        return (0,0), memory

    best_move = None
    best_score = -float('inf')
    for i,j in empty_points:
        new_board, captured_stones, is_legal = simulate_move(board, i, j, 1)
        if is_legal:
            capture_count = len(captured_stones)
            position_val = get_position_value(i,j)
            influence_val = 0
            for ni,nj in get_neighbors(i,j):
                if new_board[ni][nj] != 0:
                    influence_val += 1
            score = capture_count * 100 + position_val + influence_val * 5
            if score > best_score:
                best_score = score
                best_move = (i,j)
            elif score == best_score and best_move is not None:
                if random.random() < 0.5:
                    best_move = (i,j)

    if best_move is None:
        return (0,0), memory
    else:
        return (best_move[0]+1, best_move[1]+1), memory
