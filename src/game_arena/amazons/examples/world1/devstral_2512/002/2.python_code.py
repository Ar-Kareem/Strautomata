
import numpy as np

def policy(board) -> str:
    # Directions for queen-like movement (8 directions)
    directions = [(-1, -1), (-1, 0), (-1, 1),
                  (0, -1),           (0, 1),
                  (1, -1),  (1, 0),  (1, 1)]

    def is_valid_move(from_pos, to_pos):
        """Check if the amazon move from from_pos to to_pos is valid."""
        fr, fc = from_pos
        tr, tc = to_pos
        if board[fr, fc] != 1 or board[tr, tc] != 0:
            return False
        dr, dc = tr - fr, tc - fc
        if dr == 0 and dc == 0:
            return False
        # Check if the move is queen-like (straight or diagonal)
        if dr != 0 and dc != 0 and abs(dr) != abs(dc):
            return False
        # Check path is unobstructed
        step_r = 1 if dr > 0 else -1 if dr < 0 else 0
        step_c = 1 if dc > 0 else -1 if dc < 0 else 0
        r, c = fr + step_r, fc + step_c
        while (r, c) != (tr, tc):
            if board[r, c] != 0:
                return False
            r += step_r
            c += step_c
        return True

    def is_valid_arrow(from_pos, to_pos, arrow_pos):
        """Check if the arrow shot from to_pos to arrow_pos is valid."""
        tr, tc = to_pos
        ar, ac = arrow_pos
        if board[ar, ac] != 0:
            return False
        dr, dc = ar - tr, ac - tc
        if dr == 0 and dc == 0:
            return False
        # Check if the arrow is queen-like
        if dr != 0 and dc != 0 and abs(dr) != abs(dc):
            return False
        # Check path is unobstructed (treat from_pos as empty)
        step_r = 1 if dr > 0 else -1 if dr < 0 else 0
        step_c = 1 if dc > 0 else -1 if dc < 0 else 0
        r, c = tr + step_r, tc + step_c
        while (r, c) != (ar, ac):
            if board[r, c] != 0:
                return False
            r += step_r
            c += step_c
        return True

    def generate_moves():
        """Generate all legal moves for the current board state."""
        moves = []
        # Find all positions of the player's amazons
        amazon_positions = np.argwhere(board == 1)
        for from_pos in amazon_positions:
            fr, fc = from_pos
            # Generate all possible moves for this amazon
            for dr, dc in directions:
                tr, tc = fr + dr, fc + dc
                while 0 <= tr < 6 and 0 <= tc < 6:
                    if is_valid_move((fr, fc), (tr, tc)):
                        # Generate all possible arrow shots from (tr, tc)
                        for adr, adc in directions:
                            ar, ac = tr + adr, tc + adc
                            while 0 <= ar < 6 and 0 <= ac < 6:
                                if is_valid_arrow((fr, fc), (tr, tc), (ar, ac)):
                                    moves.append(f"{fr},{fc}:{tr},{tc}:{ar},{ac}")
                                ar += adr
                                ac += adc
                    tr += dr
                    tc += dc
        return moves

    def evaluate_move(move):
        """Evaluate a move based on mobility and centrality."""
        # Parse the move
        parts = move.split(':')
        from_pos = tuple(map(int, parts[0].split(',')))
        to_pos = tuple(map(int, parts[1].split(',')))
        arrow_pos = tuple(map(int, parts[2].split(',')))

        # Create a temporary board to simulate the move
        temp_board = board.copy()
        fr, fc = from_pos
        tr, tc = to_pos
        ar, ac = arrow_pos
        temp_board[fr, fc] = 0
        temp_board[tr, tc] = 1
        temp_board[ar, ac] = -1

        # Count opponent's mobility after the move
        opponent_amazons = np.argwhere(temp_board == 2)
        opponent_moves = 0
        for amazon in opponent_amazons:
            ar, ac = amazon
            for dr, dc in directions:
                tr, tc = ar + dr, ac + dc
                while 0 <= tr < 6 and 0 <= tc < 6:
                    if temp_board[tr, tc] == 0:
                        opponent_moves += 1
                    tr += dr
                    tc += dc

        # Count player's mobility after the move
        player_amazons = np.argwhere(temp_board == 1)
        player_moves = 0
        for amazon in player_amazons:
            ar, ac = amazon
            for dr, dc in directions:
                tr, tc = ar + dr, ac + dc
                while 0 <= tr < 6 and 0 <= tc < 6:
                    if temp_board[tr, tc] == 0:
                        player_moves += 1
                    tr += dr
                    tc += dc

        # Centrality score (closer to center is better)
        center = (2.5, 2.5)
        tr, tc = to_pos
        centrality = -((tr - center[0])**2 + (tc - center[1])**2)

        # Total score: prioritize mobility and centrality
        score = player_moves - opponent_moves + centrality
        return score

    # Generate all legal moves
    legal_moves = generate_moves()
    if not legal_moves:
        # This should not happen as per the problem statement
        return "0,0:0,0:0,0"  # Fallback (invalid but required)

    # Evaluate and select the best move
    best_move = max(legal_moves, key=evaluate_move)
    return best_move
