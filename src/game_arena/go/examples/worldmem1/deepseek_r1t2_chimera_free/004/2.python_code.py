
import random
import math
from collections import deque

def policy(me, opponent, memory):
    BOARD_SIZE = 19

    # Initialize board
    board = [[0] * BOARD_SIZE for _ in range(BOARD_SIZE)]
    for (r, c) in me:
        board[r-1][c-1] = 1
    for (r, c) in opponent:
        board[r-1][c-1] = -1

    # Check for opening moves
    if len(me) == 0 and len(opponent) == 0:
        # Play in corner for first move
        return ((4, 4), memory)
    if len(me) == 1 and len(opponent) == 1:
        # Mirror opponent's first move in opposite quadrant
        opp_r, opp_c = opponent[0]
        return ((BOARD_SIZE + 1 - opp_r, BOARD_SIZE + 1 - opp_c), memory)

    # Get currently empty points
    empty_points = [(r+1, c+1) for r in range(BOARD_SIZE) for c in range(BOARD_SIZE) if board[r][c] == 0]

    # Check for immediate captures
    def get_adjacent(r, c):
        dirs = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        return [(r+dr, c+dc) for dr, dc in dirs if 0 <= r+dr < BOARD_SIZE and 0 <= c+dc < BOARD_SIZE]

    capture_moves = []
    for (r, c) in empty_points:
        r0, c0 = r-1, c-1
        for nr, nc in get_adjacent(r0, c0):
            if board[nr][nc] == -1:
                # Check if opponent group has exactly one liberty
                visited = set()
                queue = deque([(nr, nc)])
                group = set()
                liberties = set()
                while queue:
                    cr, cc = queue.popleft()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    group.add((cr, cc))
                    for ar, ac in get_adjacent(cr, cc):
                        if board[ar][ac] == 0:
                            liberties.add((ar, ac))
                        elif board[ar][ac] == -1 and (ar, ac) not in visited:
                            queue.append((ar, ac))
                if len(liberties) == 1 and (r0, c0) in liberties:
                    capture_moves.append((r, c, len(group)))

    if capture_moves:
        # Select capture with maximum stones
        max_capture = max(capture_moves, key=lambda x: x[2])
        return (max_capture[:2], memory)

    # Check for defense moves
    defense_moves = []
    for (r, c) in empty_points:
        r0, c0 = r-1, c-1
        for nr, nc in get_adjacent(r0, c0):
            if board[nr][nc] == 1:
                # Check if our group has exactly one liberty
                visited = set()
                queue = deque([(nr, nc)])
                group = set()
                liberties = set()
                while queue:
                    cr, cc = queue.popleft()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    group.add((cr, cc))
                    for ar, ac in get_adjacent(cr, cc):
                        if board[ar][ac] == 0:
                            liberties.add((ar, ac))
                        elif board[ar][ac] == 1 and (ar, ac) not in visited:
                            queue.append((ar, ac))
                if len(liberties) == 1 and (r0, c0) in liberties:
                    defense_moves.append((r, c))

    if defense_moves:
        # Select defense move with best positional value
        defense_moves = sorted(defense_moves, key=lambda x: position_value(x[0], x[1]))
        return (defense_moves[-1], memory)

    # Positional weights based on phase
    total_moves = len(me) + len(opponent)
    opening_phase = total_moves < BOARD_SIZE * 2
    midgame_phase = BOARD_SIZE * 2 <= total_moves < BOARD_SIZE * 10

    def position_value(r, c):
        corner_dist = min(r-1, BOARD_SIZE-r) + min(c-1, BOARD_SIZE-c)
        if opening_phase:
            return -corner_dist  # Prefer corners
        elif midgame_phase:
            center_dist = abs(r - BOARD_SIZE//2) + abs(c - BOARD_SIZE//2)
            return -center_dist / 2 - corner_dist / 4
        else:
            # Endgame favors center influence
            return -abs(r - BOARD_SIZE//2) - abs(c - BOARD_SIZE//2)

    # Score empty points by positional value and stone proximity
    scored_points = []
    for (r, c) in empty_points:
        score = position_value(r, c)
        
        # Add proximity bonus
        proximity_bonus = 0
        for stone_r, stone_c in me + opponent:
            dist = math.sqrt((r - stone_r)**2 + (c - stone_c)**2)
            if dist < 5:
                proximity_bonus += 1 / (dist + 1)
        score += proximity_bonus
        
        scored_points.append((score, r, c))

    # Select best scored legal move
    scored_points.sort(reverse=True)
    for (score, r, c) in scored_points:
        r0, c0 = r-1, c-1
        legal = is_legal_move(board, r0, c0)
        if legal:
            return ((r, c), memory)
    
    # Fallback to random move if no legal found
    random.shuffle(empty_points)
    for move in empty_points:
        r0, c0 = move[0]-1, move[1]-1
        legal = is_legal_move(board, r0, c0)
        if legal:
            return (move, memory)
    
    # If all else fails, pass
    return ((0, 0), memory)

def is_legal_move(board, r, c):
    # Check if the move is in board bounds and position is empty
    if r < 0 or r >= len(board) or c < 0 or c >= len(board[0]):
        return False
    if board[r][c] != 0:
        return False
    
    # Temporarily place the stone
    board[r][c] = 1
    directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
    liberties = set()
    has_liberties = False
    stones_to_remove = []
    
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        if 0 <= nr < len(board) and 0 <= nc < len(board[0]):
            if board[nr][nc] == 0:
                has_liberties = True
                break
            elif board[nr][nc] == -1:
                # Check opponent group liberties
                visited = set()
                stack = [(nr, nc)]
                group = []
                group_liberties = set()
                while stack:
                    cr, cc = stack.pop()
                    if (cr, cc) in visited:
                        continue
                    visited.add((cr, cc))
                    group.append((cr, cc))
                    for ddr, ddc in directions:
                        ncr, ncc = cr + ddr, cc + ddc
                        if 0 <= ncr < len(board) and 0 <= ncc < len(board[0]):
                            if board[ncr][ncc] == 0:
                                group_liberties.add((ncr, ncc))
                            elif board[ncr][ncc] == -1 and (ncr, ncc) not in visited:
                                stack.append((ncr, ncc))
                if not group_liberties:
                    stones_to_remove.extend(group)
    
    # Remove any captured stones
    for stone in stones_to_remove:
        sr, sc = stone
        board[sr][sc] = 0
    
    # Check if our move has liberties
    if has_liberties or stones_to_remove:
        board[r][c] = 0
        for stone in stones_to_remove:
            sr, sc = stone
            board[sr][sc] = -1
        return True
    
    # Our group must have liberties
    visited = set()
    stack = [(r, c)]
    while stack:
        cr, cc = stack.pop()
        if (cr, cc) in visited:
            continue
        visited.add((cr, cc))
        for dr, dc in directions:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < len(board) and 0 <= nc < len(board[0]):
                if board[nr][nc] == 0:
                    has_liberties = True
                    break
                elif board[nr][nc] == 1 and (nr, nc) not in visited:
                    stack.append((nr, nc))
        if has_liberties:
            break
    
    # Restore board
    board[r][c] = 0
    for stone in stones_to_remove:
        sr, sc = stone
        board[sr][sc] = -1
    
    return has_liberties
