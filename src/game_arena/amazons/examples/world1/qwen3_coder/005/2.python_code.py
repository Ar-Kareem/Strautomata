
import numpy as np

def get_legal_moves(board, player):
    """
    Return a list of all legal moves for the player.
    Each move is represented as ((from_r, from_c), (to_r, to_c), (arrow_r, arrow_c))
    """
    moves = []
    # Find all amazons of the player
    amazons = np.argwhere(board == player)
    for amazon in amazons:
        from_r, from_c = amazon
        # All 8 directions
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                # Try all distances
                for dist in range(1, 6):
                    to_r = from_r + dr * dist
                    to_c = from_c + dc * dist
                    # Check if destination is on board
                    if not (0 <= to_r < 6 and 0 <= to_c < 6):
                        break
                    # Check if destination is empty
                    if board[to_r, to_c] != 0:
                        break
                    # Now, shoot arrow from new position
                    # Temporarily move the amazon
                    temp_board = board.copy()
                    temp_board[from_r, from_c] = 0
                    temp_board[to_r, to_c] = player
                    # Arrow directions
                    for adr in [-1, 0, 1]:
                        for adc in [-1, 0, 1]:
                            if adr == 0 and adc == 0:
                                continue
                            # Try all arrow distances
                            for adist in range(1, 6):
                                arrow_r = to_r + adr * adist
                                arrow_c = to_c + adc * adist
                                # Check if arrow is on board
                                if not (0 <= arrow_r < 6 and 0 <= arrow_c < 6):
                                    break
                                # Check if arrow path is unobstructed and lands on empty square
                                arrow_blocked = False
                                for step in range(1, adist + 1):
                                    step_r = to_r + adr * step
                                    step_c = to_c + adc * step
                                    # Can pass through from square if it's vacated now
                                    if (step_r, step_c) == (from_r, from_c):
                                        continue  # It's vacated
                                    if temp_board[step_r, step_c] != 0:
                                        arrow_blocked = True
                                        break
                                if arrow_blocked:
                                    break
                                if temp_board[arrow_r, arrow_c] == 0:
                                    moves.append(((from_r, from_c), (to_r, to_c), (arrow_r, arrow_c)))
                                else:
                                    break  # Path blocked after this point
        return moves  # Early return for efficiency if needed, but better to get all moves


def evaluate_board(board, player):
    """
    Evaluate the board state.
    positive score favors player.
    """
    opponent = 2 if player == 1 else 1
    our_moves = get_legal_moves(board, player)
    opp_moves = get_legal_moves(board, opponent)
    num_our_moves = len(our_moves)
    num_opp_moves = len(opp_moves)
    if num_opp_moves == 0:
        return 10000  # We win
    if num_our_moves == 0:
        return -10000 # We lose
    # Mobility difference
    return (num_our_moves - num_opp_moves)

def policy(board) -> str:
    """
    Main policy function to decide the next move.
    """
    player = 1  # We are player 1
    opponent = 2
    legal_moves = get_legal_moves(board, player)
    if not legal_moves:
        # Should not happen, but return a dummy move for safety
        return "0,0:0,1:0,2"

    best_move = legal_moves[0]
    best_score = -np.inf

    for move in legal_moves:
        from_pos, to_pos, arrow_pos = move
        # Apply move
        new_board = board.copy()
        new_board[from_pos] = 0
        new_board[to_pos] = player
        new_board[arrow_pos] = -1 # Arrow placed

        # Evaluate the resulting board
        score = evaluate_board(new_board, player)
        if score > best_score:
            best_score = score
            best_move = move

    # Format the best move as string
    from_pos, to_pos, arrow_pos = best_move
    move_str = f"{from_pos[0]},{from_pos[1]}:{to_pos[0]},{to_pos[1]}:{arrow_pos[0]},{arrow_pos[1]}"
    return move_str
