
import sys
from typing import List, Tuple, Dict

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: dict) -> Tuple[Tuple[int, int], dict]:
    # Convert input to sets for efficient operations
    me_set = set(me)
    opponent_set = set(opponent)
    
    # Update memory: shift the board state history
    if not memory:
        memory['board_prev_prev'] = None
        memory['board_prev'] = (me_set, opponent_set)
    else:
        memory['board_prev_prev'] = memory['board_prev']
        memory['board_prev'] = (me_set, opponent_set)
    
    # Helper function to build the board matrix
    def build_matrix(me_set_local, opponent_set_local):
        board = [[0] * 19 for _ in range(19)]
        for (r, c) in me_set_local:
            board[r-1][c-1] = 1
        for (r, c) in opponent_set_local:
            board[r-1][c-1] = 2
        return board
    
    # Helper function to get adjacent points
    def adjacent_points(r, c):
        points = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = r + dr, c + dc
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                points.append((nr, nc))
        return points
    
    # Helper function to find captured stones
    def get_captures(board, r, c, opponent_color=2):
        # Set the new stone at (r, c) to 1 (our color)
        board[r-1][c-1] = 1
        visited = [[False] * 19 for _ in range(19)]
        captured = set()
        for i in range(19):
            for j in range(19):
                if board[i][j] == opponent_color and not visited[i][j]:
                    stack = [(i, j)]
                    group = set()
                    liberties = set()
                    while stack:
                        x, y = stack.pop()
                        if visited[x][y]:
                            continue
                        visited[x][y] = True
                        group.add((x+1, y+1))
                        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            nx, ny = x + dx, y + dy
                            if 0 <= nx < 19 and 0 <= ny < 19:
                                if board[nx][ny] == 0:
                                    liberties.add((nx+1, ny+1))
                                elif board[nx][ny] == opponent_color and not visited[nx][ny]:
                                    stack.append((nx, ny))
                    if not liberties:
                        captured.update(group)
        return captured
    
    # Generate candidate moves: points adjacent to existing stones
    candidate_moves = set()
    for (r, c) in me_set:
        for nr, nc in adjacent_points(r, c):
            if (nr, nc) not in me_set and (nr, nc) not in opponent_set:
                candidate_moves.add((nr, nc))
    for (r, c) in opponent_set:
        for nr, nc in adjacent_points(r, c):
            if (nr, nc) not in me_set and (nr, nc) not in opponent_set:
                candidate_moves.add((nr, nc))
    
    # If no candidate moves, pass
    if not candidate_moves:
        return ((0, 0), memory)
    
    # 1. Check for capture moves
    capture_moves = []
    for move in candidate_moves:
        new_me_set = me_set | {move}
        board = build_matrix(new_me_set, opponent_set)
        captured = get_captures(board, move[0], move[1])
        if captured:
            new_opponent_set = opponent_set - captured
            # Check for ko: if the board state after this move is the same as two moves ago
            if memory['board_prev_prev'] is not None and (new_me_set, new_opponent_set) == memory['board_prev_prev']:
                continue
            capture_moves.append((move, captured))
    
    if capture_moves:
        # Choose the move that captures the most stones
        best_move, best_captured = max(capture_moves, key=lambda x: len(x[1]))
        return (best_move, memory)
    
    # 2. Check for self-defense moves
    # Build board matrix without the new stone
    board0 = build_matrix(me_set, opponent_set)
    visited = [[False] * 19 for _ in range(19)]
    atari_liberties = set()
    for i in range(19):
        for j in range(19):
            if board0[i][j] == 1 and not visited[i][j]:
                stack = [(i, j)]
                group = set()
                liberties = set()
                while stack:
                    x, y = stack.pop()
                    if visited[x][y]:
                        continue
                    visited[x][y] = True
                    group.add((x+1, y+1))
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 19 and 0 <= ny < 19:
                            if board0[nx][ny] == 0:
                                liberties.add((nx+1, ny+1))
                            elif board0[nx][ny] == 1 and not visited[nx][ny]:
                                stack.append((nx, ny))
                if len(liberties) == 1:
                    atari_liberties.add(list(liberties)[0])
    
    defense_moves = atari_liberties.intersection(candidate_moves)
    if defense_moves:
        best_move = None
        best_liberty_count = -1
        for move in defense_moves:
            new_me_set = me_set | {move}
            board = build_matrix(new_me_set, opponent_set)
            # Check liberties of the group containing the new stone
            stack = [move]
            group = set()
            liberties = set()
            visited_local = set()
            while stack:
                r0, c0 = stack.pop()
                if (r0, c0) in visited_local:
                    continue
                visited_local.add((r0, c0))
                group.add((r0, c0))
                for nr, nc in adjacent_points(r0, c0):
                    if (nr, nc) not in me_set and (nr, nc) not in opponent_set:
                        liberties.add((nr, nc))
                    elif (nr, nc) in new_me_set and (nr, nc) not in visited_local:
                        stack.append((nr, nc))
            liberty_count = len(liberties)
            if liberty_count > best_liberty_count:
                best_liberty_count = liberty_count
                best_move = move
        return (best_move, memory)
    
    # 3. Development moves
    best_move = None
    best_score = -1
    for move in candidate_moves:
        r, c = move
        new_me_set = me_set | {move}
        board = build_matrix(new_me_set, opponent_set)
        captured = get_captures(board, r, c)
        new_opponent_set = opponent_set - captured
        
        # Check for ko
        if memory['board_prev_prev'] is not None and (new_me_set, new_opponent_set) == memory['board_prev_prev']:
            continue
        
        # Check for suicide if no capture
        if not captured:
            # Find liberties of the new stone's group
            stack = [move]
            group = set()
            liberties = set()
            visited_local = set()
            while stack:
                r0, c0 = stack.pop()
                if (r0, c0) in visited_local:
                    continue
                visited_local.add((r0, c0))
                group.add((r0, c0))
                for nr, nc in adjacent_points(r0, c0):
                    if (nr, nc) not in me_set and (nr, nc) not in opponent_set:
                        liberties.add((nr, nc))
                    elif (nr, nc) in new_me_set and (nr, nc) not in visited_local:
                        stack.append((nr, nc))
            if not liberties:
                continue  # Suicide move, skip
        
        # Calculate score for the move
        score = 0
        # Proximity to corners
        corners = [(1,1), (1,19), (19,1), (19,19)]
        min_dist = min(max(abs(r - cr), abs(c - cc)) for cr, cc in corners)
        if min_dist <= 5:
            score += 10
        # Side bonus
        if r <= 5 or r >= 15 or c <= 5 or c >= 15:
            score += 5
        # Adjacent to own stones
        adj_own = sum(1 for (nr, nc) in adjacent_points(r, c) if (nr, nc) in me_set)
        score += adj_own
        # Adjacent to opponent stones
        adj_opp = sum(1 for (nr, nc) in adjacent_points(r, c) if (nr, nc) in opponent_set)
        score += 2 * adj_opp
        
        if score > best_score:
            best_score = score
            best_move = move
    
    if best_move is not None:
        return (best_move, memory)
    else:
        return ((0, 0), memory)
