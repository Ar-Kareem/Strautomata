
import numpy as np

def get_moves(board, row, col):
    moves = []
    for dr in [-1, 0, 1]:
        for dc in [-1, 0, 1]:
            if dr == 0 and dc == 0:
                continue
            for i in range(1, 6):
                new_row, new_col = row + i * dr, col + i * dc
                if 0 <= new_row < 6 and 0 <= new_col < 6:
                    if board[new_row, new_col] == 0:
                        moves.append((new_row, new_col))
                    else:
                        break
                else:
                    break
    return moves

def policy(board):
    my_amazons = np.argwhere(board == 1)
    legal_moves = []

    for from_row, from_col in my_amazons:
        amazon_moves = get_moves(board, from_row, from_col)
        for to_row, to_col in amazon_moves:
            temp_board = board.copy()
            temp_board[from_row, from_col] = 0
            temp_board[to_row, to_col] = 1
            arrow_moves = get_moves(temp_board, to_row, to_col)
            for arrow_row, arrow_col in arrow_moves:
                    legal_moves.append(f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}")

    if not legal_moves:
        # This should not happen, but return a random illegal move to fail the game.
        return "0,0:0,0:0,0"

    best_move = legal_moves[0]
    best_score = -np.inf
    
    for move in legal_moves:
        from_row, from_col, to_row, to_col, arrow_row, arrow_col = map(int, move.replace(':', ',').split(','))
        
        temp_board = board.copy()
        temp_board[from_row, from_col] = 0
        temp_board[to_row, to_col] = 1
        temp_board[arrow_row, arrow_col] = -1

        # Basic evaluation function
        my_amazon_moves = 0
        opponent_amazon_moves = 0
        
        my_amazons_after_move = np.argwhere(temp_board == 1)
        for row, col in my_amazons_after_move:
            my_amazon_moves += len(get_moves(temp_board, row, col))
        
        opponent_amazons = np.argwhere(temp_board == 2)
        for row, col in opponent_amazons:
            opponent_amazon_moves += len(get_moves(temp_board, row, col))

        score = my_amazon_moves - opponent_amazon_moves

        if score > best_score:
            best_score = score
            best_move = move

    return best_move
