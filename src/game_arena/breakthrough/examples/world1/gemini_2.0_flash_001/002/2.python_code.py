
import numpy as np

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    A policy for playing Breakthrough.

    Args:
        me: A list of (row, col) tuples containing your pieces.
        opp: A list of (row, col) tuples containing the opponent's pieces.
        color: 'b' for player 0 and 'w' for player 1.

    Returns:
        A move as a tuple: ((from_row, from_col), (to_row, to_col)).
    """

    board = np.zeros((8, 8), dtype=int)  # 0: empty, 1: me, -1: opp
    for r, c in me:
        board[r, c] = 1
    for r, c in opp:
        board[r, c] = -1

    def get_legal_moves(r, c):
        moves = []
        direction = 1 if color == 'w' else -1
        
        # Move forward
        new_r = r + direction
        if 0 <= new_r < 8 and board[new_r, c] == 0:
            moves.append((new_r, c))
        
        # Capture diagonally left
        new_r = r + direction
        new_c = c - 1
        if 0 <= new_r < 8 and 0 <= new_c < 8 and board[new_r, new_c] == -1:
            moves.append((new_r, new_c))
        
        # Capture diagonally right
        new_r = r + direction
        new_c = c + 1
        if 0 <= new_r < 8 and 0 <= new_c < 8 and board[new_r, new_c] == -1:
            moves.append((new_r, new_c))

        # Move diagonally forward if empty
        new_r = r + direction
        new_c = c - 1
        if 0 <= new_r < 8 and 0 <= new_c < 8 and board[new_r, new_c] == 0:
            moves.append((new_r, new_c))
        
        new_r = r + direction
        new_c = c + 1
        if 0 <= new_r < 8 and 0 <= new_c < 8 and board[new_r, new_c] == 0:
            moves.append((new_r, new_c))

        return moves

    def evaluate_move(from_pos, to_pos, board, color):
        r, c = from_pos
        new_r, new_c = to_pos
        
        evaluation = 0

        # Win condition: reaching opponent's home row
        if (color == 'w' and new_r == 7) or (color == 'b' and new_r == 0):
            evaluation += 1000

        # Capture: prefer capturing pieces
        if board[new_r, new_c] == -1:
            evaluation += 500

        # Move closer to the opponent's home row
        if color == 'w':
            evaluation += (new_r - r) * 10 # Encourage forward movement
        else:
            evaluation += (r - new_r) * 10
        
        # Consider the number of available moves after the move
        temp_board = np.copy(board)
        temp_board[r,c] = 0
        temp_board[new_r, new_c] = 1
        
        num_available_moves = 0
        for piece_r, piece_c in me:
            if (piece_r, piece_c) == (r,c):
                continue
            moves = get_legal_moves(piece_r, piece_c)
            num_available_moves += len(moves)
                
        
        evaluation += num_available_moves


        return evaluation

    best_move = None
    best_eval = -float('inf')
    
    for r, c in me:
        legal_moves = get_legal_moves(r, c)
        for new_r, new_c in legal_moves:
            
            # Creating dummy board
            temp_board = np.copy(board)
            temp_board[r, c] = 0
            temp_board[new_r, new_c] = 1
            
            eval_score = evaluate_move((r,c), (new_r, new_c), temp_board, color)
                
            if eval_score > best_eval:
                best_eval = eval_score
                best_move = ((r, c), (new_r, new_c))

    if best_move is None:
        # If no move is found just pick the first legal move available
        for r, c in me:
            legal_moves = get_legal_moves(r, c)
            if legal_moves:
                best_move = ((r, c), legal_moves[0])
                break

    return best_move
