
import numpy as np

def policy(you: list, opponent: list) -> str:
    # Convert to numpy arrays for easier manipulation
    you_board = np.array(you, dtype=bool)
    opp_board = np.array(opponent, dtype=bool)
    rows, cols = 5, 6

    # Directions: Up, Right, Down, Left
    dir_names = ['U', 'R', 'D', 'L']
    dr = [-1, 0, 1, 0]
    dc = [0, 1, 0, -1]

    def count_mobility(my_board, opp_board):
        """Count how many legal moves the player has."""
        count = 0
        for r in range(rows):
            for c in range(cols):
                if my_board[r, c]:
                    for di in range(4):
                        nr, nc = r + dr[di], c + dc[di]
                        if 0 <= nr < rows and 0 <= nc < cols:
                            if opp_board[nr, nc]:
                                count += 1
        return count

    def simulate_move(r, c, di):
        """Simulate moving piece at (r,c) in direction di. Return new (my, opp) boards."""
        my_new = you_board.copy()
        opp_new = opp_board.copy()
        nr, nc = r + dr[di], c + dc[di]
        # Move our piece
        my_new[r, c] = False
        my_new[nr, nc] = True
        # Capture opponent's piece
        opp_new[nr, nc] = False
        return my_new, opp_new

    # Collect all legal moves
    legal_moves = []
    for r in range(rows):
        for c in range(cols):
            if you_board[r, c]:
                for di in range(4):
                    nr, nc = r + dr[di], c + dc[di]
                    if 0 <= nr < rows and 0 <= nc < cols:
                        if opp_board[nr, nc]:
                            legal_moves.append((r, c, di))

    # If only one move, return it
    if len(legal_moves) == 1:
        r, c, di = legal_moves[0]
        return f"{r},{c},{dir_names[di]}"

    # Evaluate each move based on resulting mobility (number of own moves after)
    best_move = legal_moves[0]
    best_mobility = -1
    for (r, c, di) in legal_moves:
        my_new, opp_new = simulate_move(r, c, di)
        mobility = count_mobility(my_new, opp_new)
        if mobility > best_mobility:
            best_mobility = mobility
            best_move = (r, c, di)

    r, c, di = best_move
    return f"{r},{c},{dir_names[di]}"
