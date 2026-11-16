
import numpy as np

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Convert board to numpy array for easier manipulation
    board_np = np.array(board)
    
    # Helper function to check if a player can win by placing at (r, c)
    def can_win(player, r, c):
        if board_np[r, c] != 0:
            return False
        # Place temporarily
        board_np[r, c] = player
        # Check rows
        if np.all(board_np[r, :] == player):
            board_np[r, c] = 0  # Undo
            return True
        # Check columns
        if np.all(board_np[:, c] == player):
            board_np[r, c] = 0  # Undo
            return True
        # Check main diagonal
        if r == c and np.all(np.diag(board_np) == player):
            board_np[r, c] = 0  # Undo
            return True
        # Check anti-diagonal
        if r + c == 2 and np.all(np.diag(np.fliplr(board_np)) == player):
            board_np[r, c] = 0  # Undo
            return True
        board_np[r, c] = 0  # Undo
        return False
    
    # 1. Check if I can win in one move
    for r in range(3):
        for c in range(3):
            if board_np[r, c] == 0 and can_win(1, r, c):
                return (r, c)
    
    # 2. Check if opponent can win and block
    for r in range(3):
        for c in range(3):
            if board_np[r, c] == 0 and can_win(-1, r, c):
                return (r, c)
    
    # 3. Take center if available
    if board_np[1, 1] == 0:
        return (1, 1)
    
    # 4. Take a corner if available (in order: (0,0), (0,2), (2,0), (2,2))
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if board_np[r, c] == 0:
            return (r, c)
    
    # 5. Take any available edge
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in edges:
        if board_np[r, c] == 0:
            return (r, c)
    
    # Fallback (should not happen in a valid game)
    for r in range(3):
        for c in range(3):
            if board_np[r, c] == 0:
                return (r, c)
    
    # If board is full (shouldn't occur during normal play), return arbitrary move
    return (0, 0)
