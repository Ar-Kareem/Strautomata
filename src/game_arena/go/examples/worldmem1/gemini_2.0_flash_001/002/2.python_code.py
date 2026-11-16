
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A Go policy that combines heuristics to choose the next move.
    """

    board_size = 19
    board = [[0 for _ in range(board_size + 1)] for _ in range(board_size + 1)]
    for r, c in me:
        board[r][c] = 1
    for r, c in opponent:
        board[r][c] = 2

    def is_valid_move(row, col):
        return 1 <= row <= board_size and 1 <= col <= board_size and board[row][col] == 0

    def get_neighbors(row, col):
        neighbors = []
        if row > 1:
            neighbors.append((row - 1, col))
        if row < board_size:
            neighbors.append((row + 1, col))
        if col > 1:
            neighbors.append((row, col - 1))
        if col < board_size:
            neighbors.append((row, col + 1))
        return neighbors

    def get_liberties(row, col, player, visited=None):
        if visited is None:
            visited = set()
        
        if (row, col) in visited:
            return 0, visited
            
        visited.add((row, col))
        
        liberties = 0
        neighbors = get_neighbors(row, col)
        
        for nr, nc in neighbors:
            if board[nr][nc] == 0:
                liberties += 1
            elif board[nr][nc] == player:
                l, visited = get_liberties(nr, nc, player, visited)
                liberties += l
        return liberties, visited

    def find_group(row, col, player, visited=None):
        if visited is None:
            visited = set()

        if (row, col) in visited:
            return visited

        visited.add((row, col))
        neighbors = get_neighbors(row, col)
        for nr, nc in neighbors:
            if board[nr][nc] == player:
                visited = find_group(nr, nc, player, visited)
        return visited

    def check_capture(row, col, player):
        neighbors = get_neighbors(row, col)
        captured = []
        for nr, nc in neighbors:
            if board[nr][nc] == 3 - player:
                group = find_group(nr, nc, 3 - player)
                
                group_liberties = 0
                group_stones = list(group)
                for gr, gc in group_stones:
                     liberties, _ = get_liberties(gr, gc, 3 - player)
                     if liberties > group_liberties:
                        group_liberties = liberties

                if group_liberties == 0:
                    captured.extend(group)
        return captured

    def would_be_suicide(row, col, player):
        board[row][col] = player
        group = find_group(row, col, player)
        
        group_liberties = 0
        group_stones = list(group)
        for gr, gc in group_stones:
             liberties, _ = get_liberties(gr, gc, player)
             if liberties > group_liberties:
                group_liberties = liberties

        board[row][col] = 0  # Reset the board
        return group_liberties == 0

    # 1. Prevent Immediate Capture
    for r, c in me:
        neighbors = get_neighbors(r, c)
        for nr, nc in neighbors:
            if is_valid_move(nr, nc):
                 board[nr][nc] = 1
                 captured = check_capture(nr, nc, 1) 
                 board[nr][nc] = 0
                 if captured:
                     return (nr, nc), memory
    
    # 2. Capture Opponent Stones
    for r, c in opponent:
        neighbors = get_neighbors(r, c)
        for nr, nc in neighbors:
            if is_valid_move(nr, nc):
                board[nr][nc] = 1
                captured = check_capture(nr, nc,1)
                board[nr][nc] = 0
                if captured:
                    return (nr, nc), memory
    
    # 3. Play at Liberties
    candidates = []
    for r, c in me + opponent:
        neighbors = get_neighbors(r, c)
        for nr, nc in neighbors:
            if is_valid_move(nr, nc):
                candidates.append((nr, nc))

    #Remove duplicates
    candidates = list(set(candidates))

    # Sort candidates by the number of liberties
    candidates.sort(key=lambda move: len(get_neighbors(move[0], move[1])), reverse=True)

    for row, col in candidates:
        if not would_be_suicide(row, col, 1):
            return (row, col), memory

    # 4. Opening Moves (around center/star points if the board is mostly empty)
    if len(me) + len(opponent) < 10:
        opening_moves = [(4,4), (4,16), (16,4), (16,16), (10,10)]
        for row, col in opening_moves:
            if is_valid_move(row, col):
                if not would_be_suicide(row, col, 1):
                    return (row, col), memory

    # 5. Random Move (Fallback)
    possible_moves = [(r, c) for r in range(1, board_size + 1) for c in range(1, board_size + 1) if is_valid_move(r, c)]
    possible_moves = [move for move in possible_moves if not would_be_suicide(move[0], move[1], 1)]

    if possible_moves:
        return random.choice(possible_moves), memory
    else:
        return (0, 0), memory  # Pass if no legal moves

