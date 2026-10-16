
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]]) -> tuple[int, int]:
    """
    A Go policy that attempts to play a reasonable game within time constraints.
    """
    board_size = 19
    board = [[0 for _ in range(board_size + 1)] for _ in range(board_size + 1)]

    # Initialize the board with existing stones.
    for r, c in me:
        board[r][c] = 1  # 1 represents AI's stones.
    for r, c in opponent:
        board[r][c] = 2  # 2 represents opponent's stones.

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

    def get_group(row, col):
        """
        Finds all stones belonging to the same connected group.
        """
        group = [(row, col)]
        group_set = set(group)
        player = board[row][col]
        queue = [(row, col)]

        while queue:
            r, c = queue.pop(0)
            for nr, nc in get_neighbors(r, c):
                if board[nr][nc] == player and (nr, nc) not in group_set:
                    group.append((nr, nc))
                    group_set.add((nr, nc))
                    queue.append((nr, nc))
        return group

    def get_liberties(group):
        """
        Finds all empty intersections adjacent to the group.
        """
        liberties = set()
        for row, col in group:
            for nr, nc in get_neighbors(row, col):
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
        return list(liberties)

    def will_be_captured(row, col, player):
        """
        Checks if placing a stone at (row, col) will result in its capture.
        """
        board[row][col] = player  # Temporarily place the stone
        group = get_group(row, col)
        liberties = get_liberties(group)
        board[row][col] = 0 # Remove test stone
        if not liberties:
            return True
        else:
            return False
    
    def is_suicidal(row, col):
        board[row][col] = 1
        group = get_group(row, col)
        liberties = get_liberties(group)
        board[row][col] = 0
        
        if liberties:
            return False
        
        # Check if placement will save neighbours
        for nr, nc in get_neighbors(row, col):
            if board[nr][nc] == 1:
                group_neighbour = get_group(nr, nc)
                liberties_neighbour = get_liberties(group_neighbour)
        
                if len(liberties_neighbour) == 1: # Only one liberty before the new stone
                    board[row][col] = 1
                    group_neighbour = get_group(nr, nc)
                    liberties_neighbour = get_liberties(group_neighbour)
                    board[row][col] = 0

                    if len(liberties_neighbour) > 1:
                        # Placing the stone can save neighbour, so placement is not suicidal
                         return False
        
        return True

    def is_legal_move(row, col):
        if row < 1 or row > board_size or col < 1 or col > board_size:
            return False
        if board[row][col] != 0:
            return False
        if is_suicidal(row, col):
            return False
        return True
    
    # Capture Opponent Stones
    for r in range(1, board_size + 1):
        for c in range(1, board_size + 1):
            if board[r][c] == 0:
                board[r][c] = 1
                opponent_stones_to_remove = []
                for nr, nc in get_neighbors(r, c):
                    if board[nr][nc] == 2: # Opponent stones
                        group = get_group(nr, nc)
                        liberties = get_liberties(group)
                        if not liberties:
                            opponent_stones_to_remove.extend(group)
                
                board[r][c] = 0
                
                if opponent_stones_to_remove:
                    if is_legal_move(r, c):
                        return (r, c)

    # 1. Prioritize moves that prevent immediate capture of my stones.
    for r, c in me:
      for nr, nc in get_neighbors(r, c):
        if board[nr][nc] == 0 and is_legal_move(nr, nc):
            # temporarily place stone and check if existing grouping is safe.
            board[nr][nc] = 1
            my_group = get_group(r,c)
            my_liberties = get_liberties(my_group)
            board[nr][nc] = 0
            if len(my_liberties) > 1:
              return(nr, nc)


    # 2. Look for opportunities to capture opponent stones.
    for r in range(1, board_size + 1):
        for c in range(1, board_size + 1):
          if board[r][c] == 0 and is_legal_move(r, c):
            board[r][c] = 1
            
            captured_opponent_stones = []
            for nr, nc in get_neighbors(r, c):
                if board[nr][nc] == 2: # Opponent group next to proposed move
                    opp_group = get_group(nr, nc)
                    opp_liberties = get_liberties(opp_group)
                    if not opp_liberties:
                        captured_opponent_stones.extend(opp_group)
            board[r][c] = 0
            if captured_opponent_stones:
              return (r, c)


    # 3. Attempt to claim territory
    for r in range(1, board_size + 1):
        for c in range(1, board_size + 1):
            if board[r][c] == 0 and is_legal_move(r, c):
                return (r, c)


    # 4. If all else fails, try random valid moves
    possible_moves = []
    for r in range(1, board_size + 1):
        for c in range(1, board_size + 1):
            if board[r][c] == 0 and is_legal_move(r, c):
                possible_moves.append((r, c))

    if possible_moves:
        return random.choice(possible_moves)

    # 5. Pass if no valid moves are found.
    return (0, 0)
