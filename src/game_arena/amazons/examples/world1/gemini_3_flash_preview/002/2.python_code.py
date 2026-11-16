
import numpy as np

def policy(board) -> str:
    def get_queen_moves(start_pos, current_board):
        moves = []
        directions = [
            (0, 1), (0, -1), (1, 0), (-1, 0),
            (1, 1), (1, -1), (-1, 1), (-1, -1)
        ]
        r_start, c_start = start_pos
        for dr, dc in directions:
            for dist in range(1, 6):
                nr, nc = r_start + dr * dist, c_start + dc * dist
                if 0 <= nr < 6 and 0 <= nc < 6:
                    if current_board[nr, nc] == 0:
                        moves.append((nr, nc))
                    else:
                        break
                else:
                    break
        return moves

    my_positions = np.argwhere(board == 1)
    best_move = None
    best_score = -999999

    # Generate all legal moves
    for r_from, c_from in my_positions:
        possible_to = get_queen_moves((r_from, c_from), board)
        for r_to, c_to in possible_to:
            # Temporarily update board to find valid arrow shots
            # The 'from' square becomes empty, the 'to' square becomes occupied
            temp_board = board.copy()
            temp_board[r_from, c_from] = 0
            temp_board[r_to, c_to] = 1
            
            possible_arrows = get_queen_moves((r_to, c_to), temp_board)
            
            for r_arrow, c_arrow in possible_arrows:
                # Simple mobility heuristic: 
                # Count squares reachable by the amazon just moved
                score = len(get_queen_moves((r_to, c_to), temp_board))
                
                # Check if this is the best move found so far
                if score > best_score:
                    best_score = score
                    best_move = f"{r_from},{c_from}:{r_to},{c_to}:{r_arrow},{c_arrow}"
                
                # Optimization: If we find a decent move, we can return early if time is a concern
                # but for 6x6, the search space is small enough for 1-ply.

    # Fallback to ensure a move is always returned
    if not best_move:
        # This shouldn't happen given the problem constraints
        for r_from, c_from in my_positions:
            to_moves = get_queen_moves((r_from, c_from), board)
            if to_moves:
                r_to, c_to = to_moves[0]
                temp_board = board.copy()
                temp_board[r_from, c_from] = 0
                temp_board[r_to, c_to] = 1
                arrow_moves = get_queen_moves((r_to, c_to), temp_board)
                if arrow_moves:
                    r_a, c_a = arrow_moves[0]
                    return f"{r_from},{c_from}:{r_to},{c_to}:{r_a},{c_a}"

    return best_move
