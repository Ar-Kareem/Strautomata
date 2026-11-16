
import random

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A simple Go AI policy.
    """
    board_size = 19
    board = [[0 for _ in range(board_size + 1)] for _ in range(board_size + 1)]  # 1-indexed board
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

    def get_group(row, col):
        group = set()
        queue = [(row, col)]
        color = board[row][col]
        while queue:
            r, c = queue.pop(0)
            if (r, c) in group:
                continue
            group.add((r, c))
            for nr, nc in get_neighbors(r, c):
                if board[nr][nc] == color and (nr, nc) not in group:
                    queue.append((nr, nc))
        return group

    def get_liberties(group):
        liberties = set()
        for row, col in group:
            for nr, nc in get_neighbors(row, col):
                if board[nr][nc] == 0:
                    liberties.add((nr, nc))
        return liberties

    def would_be_suicide(row, col, player):
        board[row][col] = player
        group = get_group(row, col)
        liberties = get_liberties(group)
        board[row][col] = 0  # Reset the board

        if liberties:
            return False
        else:
            # Check for captures.  If we capture something, it's not suicide
            for nr, nc in get_neighbors(row, col):
                if board[nr][nc] == (3 - player):  # Opponent stone
                    opponent_group = get_group(nr, nc)
                    if not get_liberties(opponent_group):
                        return False  # Capture!

            return True # No liberties, no captures -> suicide.

    def find_captures(player):
        captures = []
        for row in range(1, board_size + 1):
            for col in range(1, board_size + 1):
                if board[row][col] == (3-player):
                    group = get_group(row, col)
                    if not get_liberties(group):
                        # Find the move that results in this capture
                        for r, c in get_neighbors(row, col):
                            if board[r][c] == 0:
                                board[r][c] = player # Temporarily place it
                                #Check for Suicide
                                suicide = would_be_suicide(r, c, player)
                                board[r][c] = 0 #Remove the placed stone
                                if not suicide:
                                    captures.append((r, c))
        return captures
    
    def avoid_self_atari(row, col, player):
        board[row][col] = player
        group = get_group(row, col)
        liberties = get_liberties(group)
        board[row][col] = 0

        if len(liberties) == 1:
            for nr, nc in get_neighbors(row, col):
              if board[nr][nc] == (3 - player):  # Opponent stone
                  opponent_group = get_group(nr, nc)
                  if not get_liberties(opponent_group):
                    return False # We are capturing, so atari is fine
            return True  # Putting ourselves in atari
        return False


    # 1. Check for captures
    captures = find_captures(1) # capturing as myself, since I am making the move.
    if captures:
        return random.choice(captures), memory

    # 2. Play near corners in early game
    if len(me) < 5 and len(opponent) < 5: # opening move heuristic
        corner_moves = [(2, 2), (2, board_size - 1), (board_size - 1, 2), (board_size - 1, board_size - 1)]
        for move in corner_moves:
            if is_valid_move(move[0], move[1]) and not would_be_suicide(move[0], move[1], 1):

                return move, memory

    # 3. Find a random valid move, but avoid suicide and self-atari
    valid_moves = []
    for row in range(1, board_size + 1):
        for col in range(1, board_size + 1):
            if is_valid_move(row, col):
                if not would_be_suicide(row, col, 1) and not avoid_self_atari(row, col, 1):
                    valid_moves.append((row, col))

    if valid_moves:
        return random.choice(valid_moves), memory
    else:
        # 4. If no valid moves, pass
        return (0, 0), memory
