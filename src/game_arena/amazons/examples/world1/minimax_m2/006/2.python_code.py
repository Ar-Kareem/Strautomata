
import numpy as np

def generate_moves(board, player):
    """
    Generate all legal move-commands for the given player on the board.
    A move-command is a tuple (from_r, from_c, to_r, to_c, arrow_r, arrow_c).
    """
    moves = []
    # Get all positions of the player's amazons
    for r in range(6):
        for c in range(6):
            if board[r, c] == player:
                from_pos = (r, c)
                # Explore all 8 directions for the queen move
                for dr in [-1, 0, 1]:
                    for dc in [-1, 0, 1]:
                        if dr == 0 and dc == 0:
                            continue
                        new_r = r + dr
                        new_c = c + dc
                        # Step in the direction until obstacle or board edge
                        while 0 <= new_r < 6 and 0 <= new_c < 6 and board[new_r, new_c] == 0:
                            to_pos = (new_r, new_c)
                            # Generate arrow shots from the to-square
                            for dr2 in [-1, 0, 1]:
                                for dc2 in [-1, 0, 1]:
                                    if dr2 == 0 and dc2 == 0:
                                        continue
                                    arrow_r = new_r + dr2
                                    arrow_c = new_mc + dc2
                                    while 0 <= arrow_r < 6 and 0 <= arrow_c < 6:
                                        # Allow the arrow to be shot to the from-square
                                        if arrow_r == from_pos[0] and arrow_c == from_pos[1]:
                                            moves.append((from_pos[0], from_pos[1], to_pos[0], to_pos[1], arrow_r, arrow_c))
                                            arrow_r += dr2
                                            arrow_c += dc2
                                        elif board[arrow_r, arrow_c] == 0:
                                            moves.append((from_pos[0], from_pos[1], to_pos[0], to_pos[1], arrow_r, arrow_c))
                                            arrow_r += dr2
                                            arrow_c += dc2
                                        else:
                                            break
                            new_r += dr
                            new_c += dc
    return moves

def apply_move(board, move):
    """
    Apply a move-command to the board and return the new board state.
    The move is a tuple (from_r, from_c, to_r, to_c, arrow_r, arrow_c).
    """
    new_board = board.copy()
    from_r, from_c, to_r, to_c, arrow_r, arrow_c = move
    new_board[from_r, from_c] = 0
    new_board[to_r, to_c] = 1
    new_board[arrow_r, arrow_c] = -1
    return new_board

def policy(board):
    """
    The policy function that selects the best move based on mobility advantage.
    """
    # Generate all legal move-commands for player 1 (self)
    my_moves = generate_moves(board, player=1)
    if not my_moves:
        # Fallback in case no moves are found (should not happen per problem statement)
        return "0,0:0,0:0,0"
    
    best_move = None
    best_score = -float('inf')
    
    for move in my_moves:
        new_board = apply_move(board, move)
        mobility_me = len(generate_moves(new_board, player=1))
        mobility_opponent = len(generate_moves(new_board, player=2))
        score = mobility_me - mobility_opponent
        
        if score > best_score:
            best_score = score
            best_move = move
    
    # Format the best move as a string
    from_r, from_c, to_r, to_c, arrow_r, arrow_c = best_move
    return f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
