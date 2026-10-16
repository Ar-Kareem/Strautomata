
import numpy as np
import time

# Global timing state
START_TIME = 0
TIME_LIMIT = 0.95  # seconds, leave some margin
MAX_DEPTH = 20

class TranspositionTable:
    def __init__(self):
        self.table = {}
    
    def key(self, board, color):
        # board is an 8x8 array: 1=my piece, -1=opp piece, 0=empty
        # color encoded in key
        return (board.tobytes(), color)
    
    def get(self, board, color):
        k = self.key(board.copy(), color)
        return self.table.get(k)
    
    def store(self, board, color, depth, value, move, flag):
        k = self.key(board.copy(), color)
        # Store only if deeper or exact
        if k not in self.table or self.table[k][0] <= depth:
            self.table[k] = (depth, value, move, flag)

TT = TranspositionTable()

def to_board(me, opp, color):
    """Convert piece lists to 8x8 board array from my perspective.
    Returns board where +1 is my piece, -1 is opponent piece."""
    board = np.zeros((8, 8), dtype=np.int8)
    for r, c in me:
        board[r, c] = 1
    for r, c in opp:
        board[r, c] = -1
    return board

def get_moves(board, color):
    """Generate all legal moves for the given color on the board.
    color: 'w' moves up (+row), 'b' moves down (-row)
    board: +1 are friendlies, -1 are enemies.
    Returns list of ((r,c), (r,c)) moves."""
    moves = []
    direction = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0
    
    my_pieces = np.argwhere(board == 1)
    for r, c in my_pieces:
        # Straight forward
        fr = r + direction
        if 0 <= fr <= 7 and board[fr, c] == 0:
            moves.append(((r, c), (fr, c)))
        # Diagonal captures and diagonal empty moves
        for dc in [-1, 1]:
            fc = c + dc
            if 0 <= fr <= 7 and 0 <= fc <= 7:
                if board[fr, fc] == -1:  # capture
                    moves.append(((r, c), (fr, fc)))
                elif board[fr, fc] == 0:  # diagonal empty
                    moves.append(((r, c), (fr, fc)))
    return moves

def apply_move(board, move, color):
    """Apply move and return new board from my perspective.
    Also returns the new color (opponent's perspective) because board is always from current player's view."""
    (r1, c1), (r2, c2) = move
    new_board = board.copy()
    # Remove my piece from origin
    new_board[r1, c1] = 0
    # Place my piece at destination (capturing overwrites opponent)
    new_board[r2, c2] = 1
    # Flip perspective: new board is from opponent's view
    return -new_board

def is_terminal(board, color):
    """Check if the game is over for the player whose turn it is (given by board perspective).
    board: current player's pieces are +1, opponent -1.
    Returns (is_over, score) where score is from current player's perspective."""
    direction = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0
    
    # Check if any of my pieces reached opponent's home row
    my_pieces = np.argwhere(board == 1)
    for r, c in my_pieces:
        if r == home_row:
            return True, 10000  # current player wins
        
    # Check if opponent has no pieces
    if np.sum(board == -1) == 0:
        return True, 10000  # current player wins
    
    # Check if current player has no pieces (shouldn't happen if we're to move but just in case)
    if np.sum(board == 1) == 0:
        return True, -10000
    
    # Opponent immediate win condition? If opponent could win on their next move? Not needed here.
    return False, 0

def evaluate(board):
    """Heuristic evaluation from current player's perspective (+1 is my pieces)."""
    # Piece count
    my_count = np.sum(board == 1)
    opp_count = np.sum(board == -1)
    piece_score = 100 * (my_count - opp_count)
    
    # Advancement: distance to opponent's home row
    # My pieces (color 'w' goes to row 7, 'b' to row 0)
    # Since board is from player perspective, we need to know which color we are.
    # But board alone doesn't store color. We'll pass a color-agnostic advancement measure:
    # For pieces on positive side (+1), advancement is towards row 7.
    # For pieces on negative side (-1), advancement is towards row 0.
    
    my_positions = np.argwhere(board == 1)
    opp_positions = np.argwhere(board == -1)
    
    my_advance = 0
    for r, c in my_positions:
        my_advance += r  # row index from bottom (0) to top (7); higher is more advanced toward row 7
    my_advance = my_advance / max(1, my_count)
    
    opp_advance = 0
    for r, c in opp_positions:
        opp_advance += (7 - r)  # from opponent's perspective, advancement would be downward toward 0
    opp_advance = opp_advance / max(1, opp_count)
    
    advance_score = 20 * (my_advance - opp_advance)
    
    # Mobility (number of legal moves)
    my_moves = len(get_moves(board, 'w' if True else 'b'))  # color doesn't matter for move count, just direction
    # Actually direction matters. Since board is from current player's perspective, assume we are 'w' for advance direction.
    # But we don't know true color. Let's pass color info through a separate mechanism.
    # For consistent evaluation regardless of color, we can compute mobility for both and difference.
    # This is a simplified eval. We'll do a color-aware eval via wrapper.
    
    return piece_score + advance_score

def evaluate_color(board, color):
    """Color-aware evaluation."""
    direction = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0
    
    my_count = np.sum(board == 1)
    opp_count = np.sum(board == -1)
    piece_score = 200 * (my_count - opp_count)
    
    my_positions = np.argwhere(board == 1)
    opp_positions = np.argwhere(board == -1)
    
    # Advancement toward opponent's home row
    my_advance = 0
    for r, c in my_positions:
        if color == 'w':
            my_advance += r  # distance from row 0
        else:
            my_advance += (7 - r)  # distance from row 7
    
    opp_advance = 0
    for r, c in opp_positions:
        if color == 'w':
            opp_advance += (7 - r)  # opponent is 'b', wants row 0
        else:
            opp_advance += r  # opponent is 'w', wants row 7
    
    adv_score = 30 * (my_advance / max(1, my_count) - opp_advance / max(1, opp_count))
    
    # Mobility
    my_moves = len(get_moves(board, color))
    # Opponent mobility: flip board and check moves for opponent
    opp_board = -board
    opp_color = 'b' if color == 'w' else 'w'
    opp_moves = len(get_moves(opp_board, opp_color))
    mob_score = 10 * (my_moves - opp_moves)
    
    # Home row threat: how many of my pieces are 1 step from winning
    threat_row = home_row - direction
    if 0 <= threat_row <= 7:
        threat_count = np.sum(board[threat_row, :] == 1)
    else:
        threat_count = 0
    threat_score = 500 * threat_count
    
    # Opponent threat
    opp_home_row = 0 if color == 'w' else 7
    opp_threat_row = opp_home_row + (1 if color == 'w' else -1)
    if 0 <= opp_threat_row <= 7:
        opp_threat_count = np.sum(board[opp_threat_row, :] == -1)
    else:
        opp_threat_count = 0
    threat_score -= 500 * opp_threat_count
    
    return piece_score + adv_score + mob_score + threat_score

def order_moves(moves, board, color):
    """Order moves for better pruning: captures first, then advanced moves."""
    direction = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0
    
    def move_score(move):
        (r1, c1), (r2, c2) = move
        score = 0
        # Captures are good
        if board[r2, c2] == -1:
            score += 1000
        # Moving toward home row
        if color == 'w':
            score += r2 * 10
        else:
            score += (7 - r2) * 10
        # Moving from advanced position
        if color == 'w':
            score += r1 * 5
        else:
            score += (7 - r1) * 5
        return score
    
    return sorted(moves, key=move_score, reverse=True)

def alpha_beta(board, color, depth, alpha, beta, maximizing):
    """Alpha-beta search with transposition table."""
    global START_TIME, TIME_LIMIT
    
    if time.time() - START_TIME > TIME_LIMIT:
        raise TimeoutError()
    
    # Check terminal
    done, val = is_terminal(board, color)
    if done:
        return val, None
    
    if depth == 0:
        return evaluate_color(board, color), None
    
    # Transposition table lookup
    tt_entry = TT.get(board, color)
    if tt_entry is not None:
        tt_depth, tt_value, tt_move, tt_flag = tt_entry
        if tt_depth >= depth:
            if tt_flag == 'exact':
                return tt_value, tt_move
            elif tt_flag == 'lower' and tt_value >= beta:
                return tt_value, tt_move
            elif tt_flag == 'upper' and tt_value <= alpha:
                return tt_value, tt_move
    
    moves = get_moves(board, color)
    if not moves:
        # No moves means we lose (shouldn't happen if terminal check is correct)
        return -10000, None
    
    moves = order_moves(moves, board, color)
    
    best_move = moves[0]
    best_val = -np.inf if maximizing else np.inf
    
    for move in moves:
        new_board, new_color = apply_move(board, move, color), ('b' if color == 'w' else 'w')
        # Note: apply_move returns board and new_color
        child_board = apply_move(board, move, color)
        child_val, _ = alpha_beta(child_board, ('b' if color == 'w' else 'w'), depth - 1, alpha, beta, not maximizing)
        
        if maximizing:
            if child_val > best_val:
                best_val = child_val
                best_move = move
            alpha = max(alpha, best_val)
        else:
            if child_val < best_val:
                best_val = child_val
                best_move = move
            beta = min(beta, best_val)
        
        if alpha >= beta:
            break
    
    # Store in TT
    flag = 'exact'
    if best_val <= alpha:
        flag = 'upper'
    elif best_val >= beta:
        flag = 'lower'
    TT.store(board, color, depth, best_val, best_move, flag)
    
    return best_val, best_move

class TimeoutError(Exception):
    pass

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[tuple[int, int], tuple[int, int]]:
    global START_TIME, TIME_LIMIT, TT
    START_TIME = time.time()
    TT = TranspositionTable()  # fresh table for each move
    
    board = to_board(me, opp, color)
    
    # Check if any immediate winning move exists
    moves = get_moves(board, color)
    direction = 1 if color == 'w' else -1
    home_row = 7 if color == 'w' else 0
    
    for move in moves:
        (r1, c1), (r2, c2) = move
        if r2 == home_row:
            return move  # winning move
    
    # Check if we can capture to prevent opponent immediate win next turn
    # (Opponent winning next turn means they have a piece 1 step from home)
    opp_home_row = 0 if color == 'w' else 7
    opp_threat_row = opp_home_row - direction  # row opponent needs to step to
    if 0 <= opp_threat_row <= 7:
        for r, c in np.argwhere(board == -1):
            if r == opp_threat_row:
                # Try to capture it
                for move in moves:
                    (r1, c1), (r2, c2) = move
                    if (r2, c2) == (r, c) and board[r, c] == -1:
                        return move  # capture the threatening piece
    
    # Iterative deepening
    best_move = moves[0]  # fallback
    depth = 1
    try:
        while depth <= MAX_DEPTH:
            val, move = alpha_beta(board, color, depth, -np.inf, np.inf, True)
            if move is not None:
                best_move = move
            depth += 1
            if time.time() - START_TIME > TIME_LIMIT * 0.3:
                # If we already spent good time, skip deeper if not much time left
                if depth > 6 and time.time() - START_TIME > TIME_LIMIT * 0.5:
                    break
    except TimeoutError:
        pass
    
    return best_move
