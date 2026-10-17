
import collections

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    # Precompute neighbors_cache for 11x11 board
    neighbors_cache = [[None]*11 for _ in range(11)]
    for i in range(11):
        for j in range(11):
            neighbors = []
            # The 6 neighbors: top-left, top-right, left, right, bottom-left, bottom-right
            for di, dj in [(-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0)]:
                ni, nj = i+di, j+dj
                if 0<=ni<=10 and 0<=nj<=10:
                    neighbors.append((ni, nj))
            neighbors_cache[i][j] = neighbors

    # Map color to our_val and opp_val
    if color == 'b':
        our_val = 1
        opp_val = 2
    else:
        our_val = 2
        opp_val = 1

    # Build board: 11x11, initialize to 0
    board = [[0]*11 for _ in range(11)]
    for (i, j) in me:
        board[i][j] = our_val
    for (i, j) in opp:
        board[i][j] = opp_val

    # Generate empty_moves
    empty_moves = []
    for i in range(11):
        for j in range(11):
            if board[i][j] == 0:
                empty_moves.append((i, j))

    # Helper function: check_win
    def check_win(board, color, neighbors_cache):
        if color == 'b':
            target_val = 1
            # Start from row0
            queue = collections.deque()
            visited = set()
            for j in range(11):
                if board[0][j] == target_val:
                    queue.append((0, j))
                    visited.add((0, j))
            while queue:
                i, j = queue.popleft()
                if i == 10:
                    return True
                for neighbor in neighbors_cache[i][j]:
                    ni, nj = neighbor
                    if board[ni][nj] == target_val and (ni, nj) not in visited:
                        visited.add((ni, nj))
                        queue.append((ni, nj))
            return False
        else:
            target_val = 2
            queue = collections.deque()
            visited = set()
            for i in range(11):
                if board[i][0] == target_val:
                    queue.append((i, 0))
                    visited.add((i, 0))
            while queue:
                i, j = queue.popleft()
                if j == 10:
                    return True
                for neighbor in neighbors_cache[i][j]:
                    ni, nj = neighbor
                    if board[ni][nj] == target_val and (ni, nj) not in visited:
                        visited.add((ni, nj))
                        queue.append((ni, nj))
            return False

    # Helper function: score_move
    def score_move(i, j, board, our_val, neighbors_cache):
        score = 0
        for neighbor in neighbors_cache[i][j]:
            ni, nj = neighbor
            if board[ni][nj] == our_val:
                score += 10
            elif board[ni][nj] == (3 - our_val):
                score += 5
        return score

    # Step 1: Check for immediate win and record blocking moves.
    blocking_moves = []
    for move in empty_moves:
        i, j = move
        # Check our win
        board[i][j] = our_val
        if check_win(board, color, neighbors_cache):
            return move   # immediate win
        board[i][j] = 0   # reset

        # Check opponent win (if we don't block)
        board[i][j] = opp_val
        opponent_color = 'b' if color=='w' else 'w'
        if check_win(board, opponent_color, neighbors_cache):
            blocking_moves.append(move)
        board[i][j] = 0   # reset

    # Step 2: If we have blocking moves, choose the best one from blocking_moves by `score_move`.
    if blocking_moves:
        best_move = None
        best_score = -1
        for move in blocking_moves:
            i, j = move
            s = score_move(i, j, board, our_val, neighbors_cache)
            if s > best_score:
                best_score = s
                best_move = move
        return best_move

    # Step 3: Otherwise, choose the best move from all empty_moves by `score_move`.
    best_move = None
    best_score = -1
    for move in empty_moves:
        i, j = move
        s = score_move(i, j, board, our_val, neighbors_cache)
        if s > best_score:
            best_score = s
            best_move = move
    return best_move
