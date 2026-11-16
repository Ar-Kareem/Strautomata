
import time
import numpy as np

class ClobberSolver:
    def __init__(self, you, opponent, time_limit=0.95):
        # Board dimensions
        self.rows = 5
        self.cols = 6
        self.full_mask = (1 << 30) - 1
        self.start_time = time.time()
        self.time_limit = time_limit
        self.nodes = 0
        
        # Transposition Table: map (me, opp) -> (depth, value, flag)
        # flag: 0=exact, 1=lower, 2=upper
        self.tt = {}

        # Parse inputs to bitboards
        self.me = self.to_bitboard(you)
        self.opp = self.to_bitboard(opponent)

        # Precompute column masks for efficient move generation
        self.mask_not_col_0 = 0
        self.mask_not_col_5 = 0
        for r in range(self.rows):
            for c in range(self.cols):
                idx = r * 6 + c
                if c > 0: self.mask_not_col_0 |= (1 << idx)
                if c < 5: self.mask_not_col_5 |= (1 << idx)

    def to_bitboard(self, arr):
        # Converts list/array to single integer bitmask
        flat = np.array(arr).flatten()
        bits = 0
        for i, val in enumerate(flat):
            if val == 1:
                bits |= (1 << i)
        return bits

    def count_moves(self, me, opp):
        # Counts legal moves efficiently using bitwise operations
        cnt = 0
        # Up (me at i, opp at i-6) -> (me >> 6) & opp
        cnt += bin((me >> 6) & opp).count('1')
        # Down (me at i, opp at i+6) -> (me << 6) & opp
        cnt += bin((me << 6) & opp & self.full_mask).count('1')
        # Left (me at i, opp at i-1) -> (me >> 1) & opp (masked to avoid wrap)
        cnt += bin((me & self.mask_not_col_0) >> 1 & opp).count('1')
        # Right (me at i, opp at i+1) -> (me << 1) & opp (masked to avoid wrap)
        cnt += bin((me & self.mask_not_col_5) << 1 & opp & self.full_mask).count('1')
        return cnt

    def get_moves(self, me, opp):
        # Generator for all legal moves
        moves = []
        
        # Helper to extract moves from a validity mask
        def extract(valid_mask, direction, offset):
            while valid_mask:
                # Get lowest set bit (destination index)
                lsb = valid_mask & -valid_mask
                dest_idx = lsb.bit_length() - 1
                valid_mask ^= lsb # Clear bit
                
                src_idx = dest_idx + offset
                
                # Calculate new board states
                # Move 'me' from src to dest, remove 'opp' from dest
                new_me = (me & ~(1 << src_idx)) | (1 << dest_idx)
                new_opp = opp & ~(1 << dest_idx)
                
                moves.append(((src_idx, dest_idx, direction), new_me, new_opp))

        # Generate moves for each direction
        # UP: offset +6 (src = dest + 6)
        extract((me >> 6) & opp, 'U', 6)
        # DOWN: offset -6
        extract((me << 6) & opp & self.full_mask, 'D', -6)
        # LEFT: offset +1
        extract((me & self.mask_not_col_0) >> 1 & opp, 'L', 1)
        # RIGHT: offset -1
        extract((me & self.mask_not_col_5) << 1 & opp & self.full_mask, 'R', -1)
        
        return moves

    def negamax(self, me, opp, depth, alpha, beta):
        # Check time limit periodically
        if (self.nodes & 1023) == 0:
            if time.time() - self.start_time > self.time_limit:
                raise TimeoutError()
        self.nodes += 1

        # Check Transposition Table
        state_key = (me, opp)
        if state_key in self.tt:
            tt_depth, tt_val, tt_flag = self.tt[state_key]
            if tt_depth >= depth:
                if tt_flag == 0: return tt_val # Exact
                if tt_flag == 1: alpha = max(alpha, tt_val) # Lower bound
                if tt_flag == 2: beta = min(beta, tt_val) # Upper bound
                if alpha >= beta: return tt_val

        # Leaf evaluation
        if depth == 0:
            # Heuristic: Mobility difference
            return self.count_moves(me, opp) - self.count_moves(opp, me)

        moves = self.get_moves(me, opp)
        
        # Terminal state check
        if not moves:
            # Loss: return very low score, adjusted by depth to prolong game if losing
            return -100000 + depth 

        # Move Ordering: Sort by opponent's mobility ascending (try to restrict opp)
        if depth > 1:
            moves.sort(key=lambda x: self.count_moves(x[2], x[1]))

        best_val = -float('inf')
        orig_alpha = alpha
        
        for _, n_me, n_opp in moves:
            try:
                # Recursive step: negate and swap players
                val = -self.negamax(n_opp, n_me, depth - 1, -beta, -alpha)
            except TimeoutError:
                raise

            if val > best_val:
                best_val = val
            
            alpha = max(alpha, val)
            if alpha >= beta:
                break # Beta cutoff
        
        # Update Transposition Table
        flag = 0
        if best_val <= orig_alpha: flag = 2 # Fail low (Upper bound)
        elif best_val >= beta: flag = 1 # Fail high (Lower bound)
        
        self.tt[state_key] = (depth, best_val, flag)
        return best_val

    def find_best_move(self):
        moves = self.get_moves(self.me, self.opp)
        if not moves:
            return None # No legal moves available
            
        best_move_info = moves[0][0]
        
        try:
            # Iterative Deepening
            for d in range(1, 40):
                alpha = -float('inf')
                beta = float('inf')
                best_d_val = -float('inf')
                best_d_move = None
                
                # Order moves based on heuristic for root level
                moves.sort(key=lambda x: self.count_moves(x[2], x[1]))
                
                for m_info, n_me, n_opp in moves:
                    val = -self.negamax(n_opp, n_me, d - 1, -beta, -alpha)
                    
                    if val > best_d_val:
                        best_d_val = val
                        best_d_move = m_info
                    
                    alpha = max(alpha, val)
                
                if best_d_move:
                    best_move_info = best_d_move
                
                # Check for proven win
                if best_d_val > 50000:
                    break
                    
        except TimeoutError:
            pass # Return best move found so far

        # Format output string
        src = best_move_info[0]
        r, c = divmod(src, 6)
        d_char = best_move_info[2]
        return f"{r},{c},{d_char}"

def policy(you: list[int], opponent: list[int]) -> str:
    # Instantiate solver and search
    solver = ClobberSolver(you, opponent)
    move = solver.find_best_move()
    
    # Fallback if no moves (though game handles this as loss)
    if move is None:
        return "0,0,U"
        
    return move
