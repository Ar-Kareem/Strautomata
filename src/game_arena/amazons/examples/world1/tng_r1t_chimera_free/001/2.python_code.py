
import numpy as np

def policy(board) -> str:
    legal_moves = []
    my_amazon_positions = list(zip(*np.where(board == 1)))

    def get_reachable_squares(b, sr, sc):
        reachable = []
        directions = [(-1, 0), (1, 0), (0, -1), (0, 1),
                      (-1, -1), (-1, 1), (1, -1), (1, 1)]
        for dr, dc in directions:
            r, c = sr + dr, sc + dc
            while 0 <= r < 6 and 0 <= c < 6:
                if b[r, c] != 0:
                    break
                reachable.append((r, c))
                r += dr
                c += dc
        return reachable

    for from_row, from_col in my_amazon_positions:
        move_dests = get_reachable_squares(board, from_row, from_col)
        for to_row, to_col in move_dests:
            temp_board = board.copy()
            temp_board[from_row, from_col] = 0
            temp_board[to_row, to_col] = 1
            arrow_dests = get_reachable_squares(temp_board, to_row, to_col)
            for arrow_row, arrow_col in arrow_dests:
                move_str = f"{from_row},{from_col}:{to_row},{to_col}:{arrow_row},{arrow_col}"
                legal_moves.append(move_str)
    
    return legal_moves[0] if legal_moves else "0,0:0,0:0,0"
