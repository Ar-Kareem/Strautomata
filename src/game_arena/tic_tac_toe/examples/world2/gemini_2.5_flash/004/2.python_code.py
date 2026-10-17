
import random

def policy(board: list[list[int]]) -> tuple[int, int]:
    # Define player IDs
    PLAYER = 1 # Your player ID
    OPPONENT = -1 # Opponent's player ID

    # --- Helper function to check if a specific player has won ---
    def check_win(current_board: list[list[int]], player_id: int) -> bool:
        # Check rows
        for r in range(4):
            if all(current_board[r][c] == player_id for c in range(4)):
                return True
        # Check columns
        for c in range(4):
            if all(current_board[r][c] == player_id for r in range(4)):
                return True
        # Check main diagonal (top-left to bottom-right)
        if all(current_board[i][i] == player_id for i in range(4)):
            return True
        # Check anti-diagonal (top-right to bottom-left)
        if all(current_board[i][3 - i] == player_id for i in range(4)):
            return True
        return False

    # --- Strategy Steps ---

    # 1. Check for immediate winning move for self
    # Iterate through all empty cells
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = PLAYER  # Tentatively make the move
                if check_win(board, PLAYER):
                    board[r][c] = 0  # Undo the move before returning
                    return (r, c)
                board[r][c] = 0  # Undo the tentative move to restore board state

    # 2. Check for immediate winning move for opponent and block it
    # Iterate through all empty cells
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                board[r][c] = OPPONENT # Tentatively make opponent's move
                if check_win(board, OPPONENT):
                    board[r][c] = 0 # Undo the move before returning
                    return (r, c)
                board[r][c] = 0 # Undo the tentative move to restore board state

    # 3. Prioritize strategic squares if no immediate win/block
    
    # Center squares (most strategic for 4x4, the 2x2 inner square)
    center_squares = [(1, 1), (1, 2), (2, 1), (2, 2)]
    # Randomize order to add some non-determinism if multiple centers are open
    random.shuffle(center_squares) 
    for r, c in center_squares:
        if board[r][c] == 0:
            return (r, c)

    # Corner squares (also strategic)
    corner_squares = [(0, 0), (0, 3), (3, 0), (3, 3)]
    random.shuffle(corner_squares)
    for r, c in corner_squares:
        if board[r][c] == 0:
            return (r, c)

    # 4. Take any available empty square (fallback)
    # Collect all empty cells
    empty_cells = []
    for r in range(4):
        for c in range(4):
            if board[r][c] == 0:
                empty_cells.append((r, c))
    
    if empty_cells:
        # Pick a random empty cell to add some variety if many are available
        return random.choice(empty_cells) 

    # This part should ideally not be reached in a valid game scenario
    # where a move is expected (i.e., if board is full and no moves possible).
    # Returning (0,0) as a default to satisfy type signature, though it implies
    # an error in game state assumptions if called on a full board.
    return (0, 0)
