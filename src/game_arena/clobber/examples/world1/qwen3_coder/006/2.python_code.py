
import numpy as np

def policy(you: list[int], opponent: list[int]) -> str:
    # Convert lists to numpy arrays for easier manipulation
    you_board = np.array(you).reshape(5, 6)
    opp_board = np.array(opponent).reshape(5, 6)

    # All possible directions
    directions = [(-1, 0, 'U'), (0, 1, 'R'), (1, 0, 'D'), (0, -1, 'L')]

    def get_legal_moves(board, opp):
        """Returns a list of all legal moves."""
        moves = []
        for r in range(5):
            for c in range(6):
                if board[r, c] == 1:
                    for dr, dc, dir_str in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 5 and 0 <= nc < 6 and opp[nr, nc] == 1:
                            moves.append((r, c, dir_str))
        return moves

    def make_move(board, opp, r, c, dir_str):
        """Applies a move and returns new board states."""
        new_board = board.copy()
        new_opp = opp.copy()
        dr, dc = {'U': (-1, 0), 'R': (0, 1), 'D': (1, 0), 'L': (0, -1)}[dir_str]
        nr, nc = r + dr, c + dc
        new_board[r, c] = 0
        new_board[nr, nc] = 1
        new_opp[nr, nc] = 0
        return new_board, new_opp

    def evaluate_position(board, opp):
        """A simple heuristic evaluation function."""
        score = 0
        
        # Mobility: count possible moves
        my_moves = len(get_legal_moves(board, opp))
        opp_moves = len(get_legal_moves(opp, board))
        score += (my_moves - opp_moves) * 10

        # Piece count
        my_pieces = np.sum(board)
        opp_pieces = np.sum(opp)
        score += (my_pieces - opp_pieces) * 5

        # Central control: reward pieces in center area
        center_area = [(1,1),(1,2),(1,3),(1,4),(2,1),(2,2),(2,3),(2,4),(3,1),(3,2),(3,3),(3,4)]
        my_center = sum(1 for (r,c) in center_area if board[r,c] == 1)
        opp_center = sum(1 for (r,c) in center_area if opp[r,c] == 1)
        score += (my_center - opp_center) * 3

        return score

    def minimax(board, opp, depth, is_maximizing, alpha, beta):
        """Minimax with alpha-beta pruning."""
        if depth == 0:
            return evaluate_position(board, opp)

        if is_maximizing:
            max_eval = -np.inf
            for r, c, dir_str in get_legal_moves(board, opp):
                new_board, new_opp = make_move(board, opp, r, c, dir_str)
                eval_score = minimax(new_opp, new_board, depth - 1, False, alpha, beta)
                max_eval = max(max_eval, eval_score)
                alpha = max(alpha, eval_score)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = np.inf
            for r, c, dir_str in get_legal_moves(opp, board):
                new_opp, new_board = make_move(opp, board, r, c, dir_str)
                eval_score = minimax(new_board, new_opp, depth - 1, True, alpha, beta)
                min_eval = min(min_eval, eval_score)
                beta = min(beta, eval_score)
                if beta <= alpha:
                    break
            return min_eval

    # Get all legal moves
    moves = get_legal_moves(you_board, opp_board)

    # Fallback: if no moves, return garbage (should not happen if called correctly)
    if not moves:
        return "0,0,U"

    # If only one move, take it
    if len(moves) == 1:
        r, c, d = moves[0]
        return f"{r},{c},{d}"

    # Use minimax to evaluate moves, look ahead 2 ply
    depth = 2
    best_move = None
    best_value = -np.inf
    alpha = -np.inf
    beta = np.inf

    # Sort moves heuristically for better alpha-beta pruning
    scored_moves = []
    for r, c, dir_str in moves:
        new_board, new_opp = make_move(you_board, opp_board, r, c, dir_str)
        score = evaluate_position(new_board, new_opp)
        scored_moves.append((score, r, c, dir_str))
    
    scored_moves.sort(reverse=True) # Sort descending by score
    
    # Evaluate top moves with minimax
    num_to_evaluate = min(8, len(scored_moves)) # Limit search for speed
    for _, r, c, dir_str in scored_moves[:num_to_evaluate]:
        new_board, new_opp = make_move(you_board, opp_board, r, c, dir_str)
        move_value = minimax(new_opp, new_board, depth - 1, False, alpha, beta)
        if move_value > best_value:
            best_value = move_value
            best_move = (r, c, dir_str)
        alpha = max(alpha, move_value)

    # Guaranteed to have a best move unless we pruned everything
    if best_move is None:
        r, c, d = moves[0]
        return f"{r},{c},{d}"
        
    r, c, d = best_move
    return f"{r},{c},{d}"
