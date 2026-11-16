
import random

# Global constants for board dimensions and player representation
ROWS = 6
COLS = 7
PLAYER = 1         # Represents our disc on the board
OPPONENT = -1      # Represents the opponent's disc on the board

# Prioritized list of columns (center preference).
# Columns are ordered from most preferred (center) to least preferred (edges).
CENTER_PRIORITY = [3, 2, 4, 1, 5, 0, 6]

def policy(board: list[list[int]]) -> int:
    """
    Implements a targeting policy for a Connect 4 game.
    The policy prioritizes winning, blocking, creating forks, and controlling the center.

    Args:
        board: A 6x7 grid representing the Connect 4 board.
               0 = empty, 1 = player's disc, -1 = opponent's disc.

    Returns:
        An integer representing the column index (0-6) to drop a disc.
        The selected column must not be full.
    """

    def is_valid_move(board_state: list[list[int]], col: int) -> bool:
        """Checks if a column is within bounds and not full."""
        return 0 <= col < COLS and board_state[0][col] == 0

    def get_valid_moves(board_state: list[list[int]]) -> list[int]:
        """Returns a list of all valid column indices for dropping a disc."""
        return [c for c in range(COLS) if is_valid_move(board_state, c)]

    def drop_disc_internal(board_state: list[list[int]], col: int, player: int) -> list[list[int]]:
        """
        Returns a new board state after dropping a disc in the specified column for the given player.
        Assumes the move is valid (i.e., the column is not full).

        Args:
            board_state: The current state of the board.
            col: The column where the disc is to be dropped.
            player: The player whose disc is being dropped (1 or -1).

        Returns:
            A new list of lists representing the board after the move.
        """
        temp_board = [row[:] for row in board_state]  # Create a deep copy
        for r in range(ROWS - 1, -1, -1):  # Iterate from bottom to top
            if temp_board[r][col] == 0:
                temp_board[r][col] = player
                return temp_board
        return temp_board # Should not be reached if move is valid, but good for type safety

    def check_win_internal(board_state: list[list[int]], player: int) -> bool:
        """
        Checks if the given player has formed a line of four on the current board.

        Args:
            board_state: The current state of the board.
            player: The player to check for a win (1 or -1).

        Returns:
            True if the player has won, False otherwise.
        """
        # Check horizontal
        for r in range(ROWS):
            for c in range(COLS - 3):
                if all(board_state[r][c + i] == player for i in range(4)):
                    return True
        # Check vertical
        for r in range(ROWS - 3):
            for c in range(COLS):
                if all(board_state[r + i][c] == player for i in range(4)):
                    return True
        # Check positive diagonal (bottom-left to top-right)
        for r in range(ROWS - 3):
            for c in range(COLS - 3):
                if all(board_state[r + i][c + i] == player for i in range(4)):
                    return True
        # Check negative diagonal (top-right to bottom-left)
        for r in range(ROWS - 3):
            for c in range(3, COLS):
                if all(board_state[r + i][c - i] == player for i in range(4)):
                    return True
        return False
    
    def count_potential_wins(board_state: list[list[int]], player: int) -> int:
        """
        Counts how many distinct *next* moves would result in a win for the given player
        on the provided board state. This is used to detect "forks" or strong threats.

        Args:
            board_state: The current state of the board.
            player: The player to check for potential wins (1 or -1).

        Returns:
            The number of distinct moves that would result in a win for the player.
        """
        potential_wins = 0
        current_valid_moves = get_valid_moves(board_state)
        for c_next in current_valid_moves:
            # Simulate placing disc for 'player' on c_next
            temp_board_win_check = drop_disc_internal(board_state, c_next, player)
            if check_win_internal(temp_board_win_check, player):
                potential_wins += 1
        return potential_wins

    valid_moves = get_valid_moves(board)

    # 1. Strategy: Check for immediate win (Player 1)
    # If we can win in the current turn, take that move.
    for col in valid_moves:
        next_board_my_move = drop_disc_internal(board, col, PLAYER)
        if check_win_internal(next_board_my_move, PLAYER):
            return col

    # 2. Strategy: Check for immediate opponent win and block (Player -1)
    # If the opponent can win on their next turn, block that move.
    for col in valid_moves:
        next_board_opponent_sim = drop_disc_internal(board, col, OPPONENT)
        if check_win_internal(next_board_opponent_sim, OPPONENT):
            return col  # Block the opponent's winning move

    # 3. Strategy: Evaluate strategic moves (no immediate win or block found)
    best_score = -float('inf')  # Initialize with a very low score
    # Fallback to a random valid move initially, in case no strategic move gives a positive score
    best_choice = random.choice(valid_moves) 

    for col in valid_moves:
        current_score = 0
        
        # Simulate placing our disc in 'col'
        sim_board_my_move = drop_disc_internal(board, col, PLAYER)

        # Calculate our offensive potential: How many "forks" or strong threats we create.
        # A fork means creating multiple distinct winning opportunities for ourselves on the next turn.
        my_forks = count_potential_wins(sim_board_my_move, PLAYER)
        current_score += my_forks * 100  # High value for creating multiple winning opportunities

        # Calculate opponent's defensive requirements: Check if our move creates any
        # immediate winning traps for the opponent on their *next* turn.
        opponent_immediate_wins_after_my_move = count_potential_wins(sim_board_my_move, OPPONENT)
        
        # If our move creates an immediate winning opportunity for the opponent (a trap),
        # penalize this move heavily. The square factor ensures multiple opponent threats
        # are penalized more severely.
        if opponent_immediate_wins_after_my_move > 0:
            current_score -= (opponent_immediate_wins_after_my_move ** 2) * 200

        # Heuristic: Center preference.
        # Columns closer to the center are generally more strategic as they offer
        # more potential lines to connect 4. We use the CENTER_PRIORITY list.
        col_index_in_priority = CENTER_PRIORITY.index(col)
        # Assign a higher score for higher priority (smaller index in CENTER_PRIORITY means higher priority)
        current_score += (COLS - col_index_in_priority) 

        # Update the best move if the current move has a higher score.
        if current_score > best_score:
            best_score = current_score
            best_choice = col
        # If scores are equal, prefer columns closer to the center (using CENTER_PRIORITY order).
        elif current_score == best_score:
            best_choice_priority_index = CENTER_PRIORITY.index(best_choice)
            current_choice_priority_index = CENTER_PRIORITY.index(col)
            if current_choice_priority_index < best_choice_priority_index:
                best_choice = col
    
    return best_choice
