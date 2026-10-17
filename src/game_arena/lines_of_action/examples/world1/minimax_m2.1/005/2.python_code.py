
import collections

def policy(board):
    current_player = 1
    opponent = -1
    directions = [(-1,0), (1,0), (0,-1), (0,1), (-1,-1), (-1,1), (1,-1), (1,1)]

    def count_pieces_in_line(board, r, c, dr, dc):
        if dr == 0 and dc != 0: # horizontal
            return sum(1 for j in range(8) if board[r][j] != 0)
        elif dc == 0 and dr != 0: # vertical
            return sum(1 for i in range(8) if board[i][c] != 0)
        elif abs(dr) == abs(dc) and dr != 0: # diagonal
            if dr == dc: # main diagonal
                count = 0
                for i in range(8):
                    j = i - (r - c)
                    if 0<=j<8:
                        if board[i][j] != 0:
                            count += 1
                return count
            else: # anti-diagonal
                count = 0
                for i in range(8):
                    j = (r + c) - i
                    if 0<=j<8:
                        if board[i][j] != 0:
                            count += 1
                return count
        else:
            return 0

    def evaluate_board(board, current_player):
        opponent = -current_player
        visited = [[False]*8 for _ in range(8)]
        player_components = 0
        player_largest = 0
        player_total = 0
        opponent_components = 0
        opponent_largest = 0
        opponent_total = 0

        for i in range(8):
            for j in range(8):
                if board[i][j] == current_player:
                    player_total += 1
                elif board[i][j] == opponent:
                    opponent_total += 1

        for i in range(8):
            for j in range(8):
                if board[i][j] == current_player and not visited[i][j]:
                    player_components += 1
                    queue = collections.deque()
                    queue.append((i,j))
                    visited[i][j] = True
                    size = 0
                    while queue:
                        x, y = queue.popleft()
                        size += 1
                        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                            nx, ny = x+dx, y+dy
                            if 0<=nx<8 and 0<=ny<8 and not visited[nx][ny] and board[nx][ny]==current_player:
                                visited[nx][ny] = True
                                queue.append((nx,ny))
                    if size > player_largest:
                        player_largest = size

        visited2 = [[False]*8 for _ in range(8)]
        for i in range(8):
            for j in range(8):
                if board[i][j] == opponent and not visited2[i][j]:
                    opponent_components += 1
                    queue = collections.deque()
                    queue.append((i,j))
                    visited2[i][j] = True
                    size = 0
                    while queue:
                        x, y = queue.popleft()
                        size += 1
                        for dx,dy in [(-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)]:
                            nx, ny = x+dx, y+dy
                            if 0<=nx<8 and 0<=ny<8 and not visited2[nx][ny] and board[nx][ny]==opponent:
                                visited2[nx][ny] = True
                                queue.append((nx,ny))
                    if size > opponent_largest:
                        opponent_largest = size

        base_score = 10 * (player_largest) \
                    - 20 * (player_components) \
                    - 10 * (opponent_largest) \
                    + 20 * (opponent_components) \
                    + (player_total - opponent_total)

        if player_components == 1:
            base_score += 1000
        if opponent_components == 1:
            base_score -= 1000

        return base_score

    moves = []
    for r in range(8):
        for c in range(8):
            if board[r][c] == current_player:
                for dr, dc in directions:
                    count = count_pieces_in_line(board, r, c, dr, dc)
                    if count == 0:
                        continue
                    target_r = r + dr * count
                    target_c = c + dc * count
                    if not (0<=target_r<8 and 0<=target_c<8):
                        continue
                    legal = True
                    for step in range(1, count):
                        nr = r + dr * step
                        nc = c + dc * step
                        if board[nr][nc] == opponent:
                            legal = False
                            break
                    if not legal:
                        continue
                    if board[target_r][target_c] == current_player:
                        continue
                    moves.append((r, c, target_r, target_c))

    if not moves:
        found = False
        for r in range(8):
            for c in range(8):
                if board[r][c] == current_player:
                    for dr, dc in directions:
                        count = count_pieces_in_line(board, r, c, dr, dc)
                        if count == 0:
                            continue
                        target_r = r + dr * count
                        target_c = c + dc * count
                        if 0<=target_r<8 and 0<=target_c<8:
                            legal = True
                            for step in range(1, count):
                                nr = r + dr * step
                                nc = c + dc * step
                                if board[nr][nc] == opponent:
                                    legal = False
                                    break
                            if not legal:
                                continue
                            if board[target_r][target_c] == current_player:
                                continue
                            moves.append((r, c, target_r, target_c))
                            found = True
                            break
                    if found:
                        break
                if found:
                    break
            if found:
                break

    if not moves:
        return "0,0:0,0"

    best_move = None
    best_score = -10**9

    for move in moves:
        r, c, target_r, target_c = move
        new_board = [row[:] for row in board]
        new_board[r][c] = 0
        new_board[target_r][target_c] = current_player
        score = evaluate_board(new_board, current_player)
        if score > best_score:
            best_score = score
            best_move = move

    return f"{best_move[0]},{best_move[1]}:{best_move[2]},{best_move[3]}"
