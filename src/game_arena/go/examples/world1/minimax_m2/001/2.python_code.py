
import collections

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    # Initialize the board with 0 for empty, 1 for my stones, -1 for opponent stones
    board = [[0 for _ in range(19)] for _ in range(19)]
    
    # Mark my stones on the board
    for r, c in me:
        board[r-1][c-1] = 1
    
    # Mark opponent stones on the board
    for r, c in opponent:
        board[r-1][c-1] = -1
    
    # Find all empty points
    empty_points = []
    for r in range(19):
        for c in range(19):
            if board[r][c] == 0:
                empty_points.append((r, c))
    
    # If there are no empty points, pass
    if not empty_points:
        return (0, 0)
    
    # Compute groups of stones and their liberties using flood-fill
    visited = [[False for _ in range(19)] for _ in range(19)]
    groups = []
    for r in range(19):
        for c in range(19):
            if board[r][c] != 0 and not visited[r][c]:
                color = board[r][c]
                stones = []
                liberties = set()
                queue = collections.deque()
                visited[r][c] = True
                queue.append((r, c))
                stones.append((r, c))
                
                while queue:
                    x, y = queue.popleft()
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < 19 and 0 <= ny < 19:
                            if board[nx][ny] == 0:
                                liberties.add((nx, ny))
                            elif board[nx][ny] == color and not visited[nx][ny]:
                                visited[nx][ny] = True
                                queue.append((nx, ny))
                                stones.append((nx, ny))
                
                groups.append({
                    'stones': stones,
                    'liberties': liberties,
                    'color': color
                })
    
    # Evaluate each empty point for capture score and legality
    best_value = -1
    best_move = (0, 0)
    for r, c in empty_points:
        # Calculate capture score for this point
        capture_score = 0
        for group in groups:
            if group['color'] == -1:  # opponent group
                if (r, c) in group['liberties']:
                    if len(group['liberties']) == 1:
                        capture_score += len(group['stones'])
        
        # Check legality of the move
        legal = False
        if capture_score > 0:
            legal = True
        else:
            # Check if any neighbor is empty or has my stone
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = r + dx, c + dy
                if 0 <= nx < 19 and 0 <= ny < 19:
                    if board[nx][ny] == 0 or board[nx][ny] == 1:
                        legal = True
                        break
        
        if legal:
            # Calculate position score based on distance to nearest edge
            distance = min(r, 18 - r, c, 18 - c)
            position_score = 100 - distance * 10
            value = capture_score * 1000 + position_score
            if value > best_value:
                best_value = value
                best_move = (r + 1, c + 1)  # Convert to 1-based index
    
    return best_move
