
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    A Go AI policy that considers Atari saving/capturing and strategic placement.
    """
    board_size = 19
    board = [[0 for _ in range(board_size + 1)] for _ in range(board_size + 1)]  # 1-indexed

    for r, c in me:
        board[r][c] = 1  # My stones
    for r, c in opponent:
        board[r][c] = 2  # Opponent stones

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

    def get_liberties(row, col, stones, visited):
        liberties = 0
        group = []

        def explore(r, c):
            nonlocal liberties
            if (r, c) in visited:
                return
            visited.add((r, c))
            group.append((r, c))

            for nr, nc in get_neighbors(r, c):
                if board[nr][nc] == 0:
                    liberties += 1
                elif board[nr][nc] == board[row][col]:
                    explore(nr, nc)

        explore(row, col)
        return liberties, group
    
    def is_atari(row, col):
            visited = set()
            liberties, _ = get_liberties(row, col, me if board[row][col] == 1 else opponent, visited)
            return liberties == 1

    # 1. Save stones in Atari
    my_stones = list(me)
    for row, col in my_stones:
        if is_atari(row, col):
            for nr, nc in get_neighbors(row, col):
                if board[nr][nc] == 0:
                    #Checking not to suicide
                    temp_board = [row[:] for row in board]
                    temp_board[nr][nc] = 1
                    new_board = [[0 for _ in range(board_size + 1)] for _ in range(board_size + 1)]
                    for r, c in me:
                         new_board[r][c] = 1
                    for r, c in opponent:
                         new_board[r][c] = 2
                    new_board[nr][nc] = 1
                    is_suicide = True
                    visited = set()
                    liberties, _ = get_liberties(nr, nc, new_board, visited)
                    if liberties > 0:
                        return (nr, nc)


    # 2. Capture opponent stones in Atari
    opponent_stones = list(opponent)
    for row, col in opponent_stones:
        if is_atari(row,col):
            for nr, nc in get_neighbors(row, col):
                if board[nr][nc] == 0:
                    temp_board = [row[:] for row in board]
                    temp_board[nr][nc] = 1
                    is_suicide = True
                    visited = set()
                    liberties, _ = get_liberties(nr, nc, me,visited)
                    if liberties > 0:
                         return (nr, nc)

                    

    # 3. Strategic Placement (Heuristic)
    def evaluate_move(row, col):
        liberties = 0
        friendly_neighbors = 0
        enemy_neighbors = 0
        
        for nr, nc in get_neighbors(row, col):

            if board[nr][nc] == 0:
                liberties+=1
            elif board[nr][nc] == 1:
                friendly_neighbors +=1
            elif board[nr][nc] == 2:
                enemy_neighbors +=1
        
        score = liberties * 2 + friendly_neighbors - enemy_neighbors
        #Bonus for edges and corners early in the game
        if (row <=3 or row >= board_size-2) and (col <=3 or col >= board_size-2):
            score +=1

        return score
    
    best_move = None
    best_score = float('-inf')
    
    empty_points = []
    for r in range(1, board_size + 1):
        for c in range(1, board_size + 1):
            if board[r][c] == 0:
                empty_points.append((r, c))
    
    random.shuffle(empty_points) #randomize order for equal exploration

    for row, col in empty_points:
        # Check for suicide
        temp_board = [row[:] for row in board]
        temp_board[row][col] = 1
        is_suicide = True
        visited = set()
        liberties, _ = get_liberties(row, col, me,visited)
        
        if liberties > 0:
            score = evaluate_move(row, col)

            if score > best_score:
                best_score = score
                best_move = (row, col)

    if best_move:
        return best_move

    # 4. Fallback: Random legal move
    possible_moves = []
    for r in range(1, board_size + 1):
        for c in range(1, board_size + 1):
            if board[r][c] == 0:
                #Check for suicide before appending as valid
                temp_board = [row[:] for row in board]
                temp_board[r][c] = 1
                
                is_suicide = True
                visited = set()
                liberties, _ = get_liberties(r, c, me,visited)
                if liberties > 0:
                    possible_moves.append((r, c))

    if possible_moves:
        return random.choice(possible_moves)

    # 5. Pass if no legal moves
    return (0, 0)
