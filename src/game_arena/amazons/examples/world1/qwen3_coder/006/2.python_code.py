
import numpy as np

def policy(board) -> str:
    # Helper function to check if a position is on the board
    def on_board(r, c):
        return 0 <= r < 6 and 0 <= c < 6

    # Directions for queen moves (8 directions)
    directions = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

    # Function to get all legal destinations for an amazon move from a position
    def get_moves_from(board, r, c):
        moves = []
        for dr, dc in directions:
            for i in range(1, 6): # Max board size is 6
                nr, nc = r + dr * i, c + dc * i
                if not on_board(nr, nc) or board[nr, nc] != 0:
                    break
                moves.append((nr, nc))
        return moves

    # Function to generate all legal moves for a player (1 or 2)
    def get_all_moves(board, player):
        moves = []
        for r in range(6):
            for c in range(6):
                if board[r, c] == player:
                    destinations = get_moves_from(board, r, c)
                    for tr, tc in destinations:
                        moves.append(((r, c), (tr, tc)))
        return moves

    # Function to get all legal arrow shots from a position, considering the board state after a move
    def get_arrows_from(board_after_move, r, c):
        return get_moves_from(board_after_move, r, c)

    # Evaluation function for a given board state
    # Returns a score: higher is better for player 1
    def evaluate(board):
        # Count legal moves for player 1 (us)
        our_moves = get_all_moves(board, 1)
        our_mobility = 0
        for _, (tr, tc) in our_moves:
            temp_board = board.copy()
            # Find an arbitrary source for this move to count arrows
            for sr, sc in [(r, c) for r in range(6) for c in range(6) if board[r, c] == 1]:
                if (tr, tc) in get_moves_from(board, sr, sc):
                    temp_board[sr, sc] = 0
                    temp_board[tr, tc] = 1
                    our_mobility += len(get_arrows_from(temp_board, tr, tc))
                    temp_board[sr, sc] = 1
                    temp_board[tr, tc] = 0
                    break # One source is enough for a rough count

        # Count legal moves for player 2 (opponent)
        opp_moves = get_all_moves(board, 2)
        opp_mobility = 0
        for _, (tr, tc) in opp_moves:
            temp_board = board.copy()
            for sr, sc in [(r, c) for r in range(6) for c in range(6) if board[r, c] == 2]:
                if (tr, tc) in get_moves_from(board, sr, sc):
                    temp_board[sr, sc] = 0
                    temp_board[tr, tc] = 2
                    opp_mobility += len(get_arrows_from(temp_board, tr, tc))
                    temp_board[sr, sc] = 2
                    temp_board[tr, tc] = 0
                    break

        # We want to maximize our mobility and minimize opponent's
        W_OUR = 1
        W_OPP = 1
        return W_OUR * our_mobility - W_OPP * opp_mobility

    # --- Main Policy Logic ---
    best_move_str = ""
    best_score = float('-inf')

    # Iterate through all our amazons
    for from_r in range(6):
        for from_c in range(6):
            if board[from_r, from_c] == 1:
                # Get all legal destinations for this amazon
                destinations = get_moves_from(board, from_r, from_c)
                for to_r, to_c in destinations:
                    # Simulate the move
                    temp_board = board.copy()
                    temp_board[from_r, from_c] = 0
                    temp_board[to_r, to_c] = 1
                    
                    # Get all legal arrow shots from the new position
                    arrows = get_arrows_from(temp_board, to_r, to_c)
                    for arrow_r, arrow_c in arrows:
                        # Simulate shooting the arrow
                        temp_board2 = temp_board.copy()
                        temp_board2[arrow_r, arrow_c] = -1
                        
                        # Evaluate the resulting board state
                        score = evaluate(temp_board2)
                        
                        if score > best_score:
                            best_score = score
                            best_move_str = f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"

    # Fallback: if no move found (should not happen), pick any legal one
    if not best_move_str:
        for from_r in range(6):
            for from_c in range(6):
                if board[from_r, from_c] == 1:
                    destinations = get_moves_from(board, from_r, from_c)
                    if destinations:
                        to_r, to_c = destinations[0]
                        temp_board = board.copy()
                        temp_board[from_r, from_c] = 0
                        temp_board[to_r, to_c] = 1
                        arrows = get_arrows_from(temp_board, to_r, to_c)
                        if arrows:
                            arrow_r, arrow_c = arrows[0]
                            return f"{from_r},{from_c}:{to_r},{to_c}:{arrow_r},{arrow_c}"
    
    return best_move_str
