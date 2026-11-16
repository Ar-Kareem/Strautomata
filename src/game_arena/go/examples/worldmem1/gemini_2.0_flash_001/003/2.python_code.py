
import numpy as np

def policy(me: list[tuple[int, int]], opponent: list[tuple[int, int]], memory: dict) -> tuple[tuple[int, int], dict]:
    """
    A Go playing policy that prioritizes corners, edges, capturing, and territory control.
    """

    board_size = 19
    board = np.zeros((board_size, board_size), dtype=int)  # 0: empty, 1: me, -1: opponent

    for r, c in me:
        board[r - 1, c - 1] = 1
    for r, c in opponent:
        board[r - 1, c - 1] = -1

    last_captured = memory.get('last_captured', None)

    def get_neighbors(row, col):
        neighbors = []
        if row > 0:
            neighbors.append((row - 1, col))
        if row < board_size - 1:
            neighbors.append((row + 1, col))
        if col > 0:
            neighbors.append((row, col - 1))
        if col < board_size - 1:
            neighbors.append((row, col + 1))
        return neighbors

    def get_liberties(row, col, player):
        liberties = set()
        group = set()
        visited = set()

        def explore_group(r, c):
            if (r, c) in visited:
                return

            visited.add((r, c))
            if board[r, c] == player:
                group.add((r, c))
                for nr, nc in get_neighbors(r, c):
                    explore_group(nr, nc)
            elif board[r, c] == 0:
                liberties.add((r, c))

        explore_group(row, col)
        return liberties, group

    def check_suicide(row, col, player):
        board[row, col] = player
        liberties, group = get_liberties(row, col, player)
        board[row, col] = 0  # Reset the board
        return len(liberties) == 0

    def find_captures(player):
        captures = []
        opponent_player = -1 if player == 1 else 1
        for r in range(board_size):
            for c in range(board_size):
                if board[r, c] == opponent_player:
                    liberties, group = get_liberties(r, c, opponent_player)
                    if len(liberties) == 0:
                        captures.extend(group)
        return captures

    # 1. Capture opponent's stones
    for r in range(board_size):
        for c in range(board_size):
            if board[r, c] == 0:
                board[r, c] = 1
                captures = find_captures(1)
                board[r, c] = 0
                if captures:
                    row, col = r + 1, c + 1
                    memory['last_captured'] = None
                    return (row, col), memory

    # 2. Block opponent's captures
    for r in range(board_size):
        for c in range(board_size):
            if board[r, c] == 0:
                board[r, c] = -1
                captures = find_captures(-1)
                board[r, c] = 0
                if captures:
                    row, col = r + 1, c + 1
                    if (row, col) != last_captured:
                       memory['last_captured'] = None
                       return (row, col), memory


    # 3. Play corners and edges.
    corners = [(1, 1), (1, board_size), (board_size, 1), (board_size, board_size)]
    for r, c in corners:
        if board[r-1, c-1] == 0:
            if not check_suicide(r-1, c-1, 1):
              memory['last_captured'] = None
              return (r, c), memory

    # 4. Play edges.

    edge_spots = []

    for i in range(2, board_size):
        edge_spots.append((1, i))
        edge_spots.append((board_size, i))
        edge_spots.append((i, 1))
        edge_spots.append((i, board_size))

    for r,c in edge_spots:
        if board[r-1, c-1] == 0:
            if not check_suicide(r-1, c-1, 1):
                memory['last_captured'] = None
                return (r, c), memory

    # 5. Play Random legal moves

    possible_moves = []
    for r in range(board_size):
        for c in range(board_size):
            if board[r, c] == 0:
                if not check_suicide(r, c, 1):
                    possible_moves.append((r+1, c+1))

    if possible_moves:
        action = possible_moves[0]
        memory['last_captured'] = None
        return action, memory

    # 6. Pass if no other move is available
    memory['last_captured'] = None
    return (0, 0), memory
