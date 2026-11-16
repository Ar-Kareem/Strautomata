
import numpy as np
from collections import defaultdict, deque
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    # Initialize memory if empty
    if not memory:
        memory = {
            'board_history': [],
            'territory_map': None,
            'influence_map': None,
            'move_number': 0,
            'last_move': None,
            'important_points': set()
        }

    # Update move number and last move
    memory['move_number'] += 1
    memory['last_move'] = (me + opponent)[-1] if (me + opponent) else None

    # Create board representation
    board = np.zeros((19, 19), dtype=int)
    for r, c in me:
        board[r-1, c-1] = 1
    for r, c in opponent:
        board[r-1, c-1] = -1

    # Check for ko situation
    current_hash = hash(board.tobytes())
    if current_hash in memory['board_history']:
        # Ko rule - cannot repeat previous board position
        # Find all legal moves except the ko point
        ko_point = memory['board_history'][-1]
        legal_moves = get_legal_moves(board, exclude=ko_point)
    else:
        legal_moves = get_legal_moves(board)

    if not legal_moves:
        return (0, 0), memory

    # Update board history
    memory['board_history'].append(current_hash)
    if len(memory['board_history']) > 5:
        memory['board_history'].pop(0)

    # Calculate liberties for all groups
    my_groups = find_groups(board, 1)
    opp_groups = find_groups(board, -1)

    # 1. Check for immediate atari situations (stones with 1 liberty)
    atari_moves = []
    for group in opp_groups:
        if len(group['liberties']) == 1:
            atari_moves.append(group['liberties'][0])
    for group in my_groups:
        if len(group['liberties']) == 1:
            # Try to save our own atari stones
            for liberty in group['liberties']:
                if (liberty[0]+1, liberty[1]+1) in legal_moves:
                    atari_moves.insert(0, liberty)  # Prioritize saving our own stones

    if atari_moves:
        # Choose the most urgent atari move
        best_move = atari_moves[0]
        return ((best_move[0]+1, best_move[1]+1), memory)

    # 2. Early game - focus on corners and sides
    if memory['move_number'] < 20:
        corner_moves = [(0,0), (0,18), (18,0), (18,18)]
        side_moves = [(0,3), (0,9), (0,15), (3,0), (9,0), (15,0),
                     (18,3), (18,9), (18,15), (3,18), (9,18), (15,18)]
        all_strategic = corner_moves + side_moves

        for move in all_strategic:
            if (move[0]+1, move[1]+1) in legal_moves:
                return ((move[0]+1, move[1]+1), memory)

    # 3. Calculate influence map if not exists or outdated
    if memory['influence_map'] is None or memory['move_number'] % 5 == 0:
        memory['influence_map'] = calculate_influence(board)

    # 4. Find moves that maximize influence
    influence_moves = []
    for r in range(19):
        for c in range(19):
            if board[r,c] == 0 and (r+1, c+1) in legal_moves:
                influence_moves.append((memory['influence_map'][r,c], r, c))

    if influence_moves:
        influence_moves.sort(reverse=True, key=lambda x: x[0])
        best_influence = influence_moves[0][1:]
        return ((best_influence[0]+1, best_influence[1]+1), memory)

    # 5. Territory-based moves
    if memory['territory_map'] is None or memory['move_number'] % 10 == 0:
        memory['territory_map'] = calculate_territory(board)

    territory_moves = []
    for r in range(19):
        for c in range(19):
            if board[r,c] == 0 and (r+1, c+1) in legal_moves:
                territory_moves.append((memory['territory_map'][r,c], r, c))

    if territory_moves:
        territory_moves.sort(reverse=True, key=lambda x: x[0])
        best_territory = territory_moves[0][1:]
        return ((best_territory[0]+1, best_territory[1]+1), memory)

    # 6. Random legal move if nothing better found
    return (random.choice(legal_moves), memory)

def get_legal_moves(board, exclude=None):
    legal_moves = []
    for r in range(19):
        for c in range(19):
            if board[r,c] == 0:
                move = (r+1, c+1)
                if move != exclude:
                    # Check if move is legal (not suicide)
                    temp_board = board.copy()
                    temp_board[r,c] = 1
                    if not is_suicide(temp_board, r, c):
                        legal_moves.append(move)
    return legal_moves

def find_groups(board, player):
    visited = np.zeros((19, 19), dtype=bool)
    groups = []

    for r in range(19):
        for c in range(19):
            if not visited[r,c] and board[r,c] == player:
                group, liberties = find_group(board, r, c, visited)
                groups.append({
                    'stones': group,
                    'liberties': liberties,
                    'size': len(group)
                })

    return groups

def find_group(board, r, c, visited):
    queue = deque([(r, c)])
    visited[r,c] = True
    group = []
    liberties = set()

    while queue:
        x, y = queue.popleft()
        group.append((x, y))

        for dx, dy in [(0,1), (1,0), (0,-1), (-1,0)]:
            nx, ny = x+dx, y+dy
            if 0 <= nx < 19 and 0 <= ny < 19:
                if not visited[nx,ny]:
                    if board[nx,ny] == board[x,y]:
                        visited[nx,ny] = True
                        queue.append((nx, ny))
                    elif board[nx,ny] == 0:
                        liberties.add((nx, ny))

    return group, list(liberties)

def is_suicide(board, r, c):
    # Check if the move would result in a group with no liberties
    visited = np.zeros((19, 19), dtype=bool)
    group, liberties = find_group(board, r, c, visited)
    return len(liberties) == 0

def calculate_influence(board):
    influence = np.zeros((19, 19))

    # Simple influence calculation based on distance to stones
    for r in range(19):
        for c in range(19):
            if board[r,c] != 0:
                player = board[r,c]
                for dr in range(-3, 4):
                    for dc in range(-3, 4):
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 19 and 0 <= nc < 19:
                            distance = max(abs(dr), abs(dc))
                            if distance == 0:
                                influence[nr,nc] = player * 100
                            else:
                                influence[nr,nc] += player / distance

    return influence

def calculate_territory(board):
    territory = np.zeros((19, 19))

    # Simple territory estimation
    for r in range(19):
        for c in range(19):
            if board[r,c] == 0:
                # Count nearby stones
                black = 0
                white = 0
                for dr in range(-2, 3):
                    for dc in range(-2, 3):
                        nr, nc = r+dr, c+dc
                        if 0 <= nr < 19 and 0 <= nc < 19:
                            if board[nr,nc] == 1:
                                black += 1
                            elif board[nr,nc] == -1:
                                white += 1

                if black > white:
                    territory[r,c] = 1
                elif white > black:
                    territory[r,c] = -1

    return territory
