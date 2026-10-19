
import random
import itertools

def policy(board: list[list[int]]) -> tuple[int, int]:
    """
    A policy for Phantom Tic Tac Toe that attempts to win, block opponent wins,
    and prioritize center, corners, and edges.
    """

    def check_win(board):
        """Checks if the current board has a winning row/col/diagonal for the player (1)."""
        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] == 1:
                return True
            if board[0][i] == board[1][i] == board[2][i] == 1:
                return True
        if board[0][0] == board[1][1] == board[2][2] == 1:
            return True
        if board[0][2] == board[1][1] == board[2][0] == 1:
            return True
        return False

    def find_winning_move(board):
        """Finds a move that leads to an immediate win."""
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    temp_board = [row[:] for row in board]  # Create a copy
                    temp_board[r][c] = 1
                    if check_win(temp_board):
                        return (r, c)
        return None

    def find_blocking_move(board):
        """
        Finds a move to block the opponent from winning, considering all possible board states where the opponent's marks could be.
        """
        empty_cells = []
        for r in range(3):
            for c in range(3):
                if board[r][c] == 0:
                    empty_cells.append((r, c))

        for move_r in range(3):
            for move_c in range(3):
                if board[move_r][move_c] == 0:
                    # Create a large number of hypothetical boards to check if this move blocks opponent's win.
                   
                    opponent_win_possible = False
                    for i in range(min(100, 2**len(empty_cells))):  #Limit the number of random simulation
                        
                        hypothetical_board = [row[:] for row in board]
                        hypothetical_board[move_r][move_c] = 1 # Temporarily place the move
                        
                        # Simulate adversary placements
                        temp_empty_cells = [cell for cell in empty_cells if cell != (move_r, move_c)]
                        
                        for k, (r, c) in enumerate(temp_empty_cells):

                            if (i >> (k)) & 1 : #Use the bits of 'i' as flag to indicate opponent marks
                                hypothetical_board[r][c] = 2 # Assume 2 is adversary marking
                            else:
                                hypothetical_board[r][c] = 0  # Leaving these spaces as unknown

                        # Find if the opponent could have a win in this board
                        temp_board = [row[:] for row in hypothetical_board]
                        
                        def hypothetical_check_opponent_win(temp_board):
                            """Checks if opponent would have a win row/col/diagonal"""
                            for row in range(3):
                                if temp_board[row][0] == temp_board[row][1] == temp_board[row][2] == 2:
                                    return True
                                if temp_board[0][row] == temp_board[1][row] == temp_board[2][row] == 2:
                                    return True

                            if temp_board[0][0] == temp_board[1][1] == temp_board[2][2] == 2:
                                return True
                            if temp_board[0][2] == temp_board[1][1] == temp_board[2][0] == 2:
                                return True
                            return False
                            
                        if hypothetical_check_opponent_win(temp_board):
                            opponent_win_possible = True
                            break                   
                    if not opponent_win_possible:
                        return (move_r, move_c) # this move prevents the opponent from winning

        return None

    # 1. Check for a winning move
    winning_move = find_winning_move(board)
    if winning_move:
        return winning_move

    # 2. Check for a blocking move
    blocking_move = find_blocking_move(board)
    if blocking_move:
        return blocking_move

    # 3. Prioritize the center
    if board[1][1] == 0:
        return (1, 1)

    # 4. Prioritize corners
    corners = [(0, 0), (0, 2), (2, 0), (2, 2)]
    for r, c in corners:
        if board[r][c] == 0:
            return (r, c)

    # 5. Prioritize edges
    edges = [(0, 1), (1, 0), (1, 2), (2, 1)]
    for r, c in edges:
        if board[r][c] == 0:
            return (r, c)

    # 6. Choose a random legal move if all else fails.
    legal_moves = []
    for r in range(3):
        for c in range(3):
            if board[r][c] == 0:
                legal_moves.append((r, c))
    
    if legal_moves:
        return random.choice(legal_moves)
    else:
        # Should never reach here if the game is played correctly
        return (0, 0) # Default if there are no legal moves, but should never happen in correct play.

