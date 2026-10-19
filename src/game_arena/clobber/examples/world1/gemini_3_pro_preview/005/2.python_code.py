
import time

def policy(you: list[int], opponent: list[int]) -> str:
    """
    Determines the next move for the Clobber game on a 5x6 grid.
    
    Args:
        you: 5x6 list describing your pieces (1 if present, else 0).
        opponent: 5x6 list describing opponent pieces.
        
    Returns:
        A string representing the move in the format 'row,col,dir'.
    """
    return bot.find_best_move(you, opponent)

class ClobberAI:
    def __init__(self):
        self.ROWS = 5
        self.COLS = 6
        # A 5x6 grid has 30 cells.
        # Masks for column boundaries to prevent wrap-around moves during bitwise shifts.
        # Col 0 indices: 0, 6, 12, 18, 24
        self.MASK_COL_0 = sum(1 << (r * 6) for r in range(5))
        # Col 5 indices: 5, 11, 17, 23, 29
        self.MASK_COL_5 = sum(1 << (r * 6 + 5) for r in range(5))
        
        # Inverted masks
        self.MASK_NOT_COL_0 = ((1 << 30) - 1) ^ self.MASK_COL_0
        self.MASK_NOT_COL_5 = ((1 << 30) - 1) ^ self.MASK_COL_5
        
        self.start_time = 0
        self.time_limit = 0.95  # 1.0s limit, stop slightly early
        self.nodes_visited = 0

    def get_mobility_score(self, P, O):
        """
        Calculates the mobility difference: (Moves for P) - (Moves for O).
        Uses bitwise operations to count moves in all 4 directions simultaneously.
        """
        def count_moves(A, B):
            cnt = 0
            # Up: A moves to B (index - 6). Condition: A has piece at i, B at i-6.
            # Mask logic: (A >> 6) & B. The set bits are the DESTINATIONS in B.
            cnt += bin((A >> 6) & B).count('1')
            
            # Down: A moves to B (index + 6).
            cnt += bin((A << 6) & B).count('1')
            
            # Left: A moves to B (index - 1). B must NOT be in Col 5 (wrap-around from prev row).
            # Source A is at index, Dest B is at index-1. 
            # Check: (A >> 1) & B. Ensure dest is not Col 5.
            cnt += bin((A >> 1) & B & self.MASK_NOT_COL_5).count('1')
            
            # Right: A moves to B (index + 1). B must NOT be in Col 0.
            # Source A is at index, Dest B is at index+1.
            # Check: (A << 1) & B. Ensure dest is not Col 0.
            cnt += bin((A << 1) & B & self.MASK_NOT_COL_0).count('1')
            return cnt

        return count_moves(P, O) - count_moves(O, P)

    def get_moves_internal(self, P, O):
        """
        Generator for moves suitable for internal search nodes.
        Yields (src_index, dst_index).
        """
        # UP: src = dst + 6. Dest is (P >> 6) & O
        tgt = (P >> 6) & O
        while tgt:
            # Extract lowest set bit index
            dst = (tgt & -tgt).bit_length() - 1
            tgt &= tgt - 1
            yield (dst + 6, dst)

        # DOWN: src = dst - 6. Dest is (P << 6) & O
        tgt = (P << 6) & O
        while tgt:
            dst = (tgt & -tgt).bit_length() - 1
            tgt &= tgt - 1
            yield (dst - 6, dst)

        # LEFT: src = dst + 1. Dest is (P >> 1) & O. Dest cannot be Col 5.
        tgt = (P >> 1) & O & self.MASK_NOT_COL_5
        while tgt:
            dst = (tgt & -tgt).bit_length() - 1
            tgt &= tgt - 1
            yield (dst + 1, dst)

        # RIGHT: src = dst - 1. Dest is (P << 1) & O. Dest cannot be Col 0.
        tgt = (P << 1) & O & self.MASK_NOT_COL_0
        while tgt:
            dst = (tgt & -tgt).bit_length() - 1
            tgt &= tgt - 1
            yield (dst - 1, dst)

    def get_moves_root(self, P, O):
        """
        Generate moves for the root node, including the required string format.
        Returns list of ((src, dst), move_string).
        """
        moves = []
        
        # UP
        tgt = (P >> 6) & O
        while tgt:
            dst = (tgt & -tgt).bit_length() - 1
            tgt &= tgt - 1
            src = dst + 6
            r, c = divmod(src, 6)
            moves.append(((src, dst), f"{r},{c},U"))

        # DOWN
        tgt = (P << 6) & O
        while tgt:
            dst = (tgt & -tgt).bit_length() - 1
            tgt &= tgt - 1
            src = dst - 6
            r, c = divmod(src, 6)
            moves.append(((src, dst), f"{r},{c},D"))

        # LEFT
        tgt = (P >> 1) & O & self.MASK_NOT_COL_5
        while tgt:
            dst = (tgt & -tgt).bit_length() - 1
            tgt &= tgt - 1
            src = dst + 1
            r, c = divmod(src, 6)
            moves.append(((src, dst), f"{r},{c},L"))

        # RIGHT
        tgt = (P << 1) & O & self.MASK_NOT_COL_0
        while tgt:
            dst = (tgt & -tgt).bit_length() - 1
            tgt &= tgt - 1
            src = dst - 1
            r, c = divmod(src, 6)
            moves.append(((src, dst), f"{r},{c},R"))
            
        return moves

    def alphabeta(self, P, O, depth, alpha, beta, maximizing):
        # Time check every 1024 nodes
        if (self.nodes_visited & 1023) == 0:
            if time.time() - self.start_time > self.time_limit:
                 raise TimeoutError()
        self.nodes_visited += 1

        if depth == 0:
            return self.get_mobility_score(P, O)

        # Generate all pseudo-legal moves
        has_move = False
        best_val = -1000000  # Start with a losing score
        
        for src, dst in self.get_moves_internal(P, O):
            has_move = True
            
            # Apply move: 
            # Remove piece from src in P.
            # Add piece to dst in P.
            # Remove piece from dst in O (capture).
            new_P = (P ^ (1 << src)) | (1 << dst)
            new_O = O ^ (1 << dst)
            
            # Recursion with Negamax: flip P and O, negate value, flip alpha/beta
            val = -self.alphabeta(new_O, new_P, depth - 1, -beta, -alpha, not maximizing)
            
            if val > best_val:
                best_val = val
            alpha = max(alpha, val)
            if alpha >= beta:
                break
        
        if not has_move:
            # No moves available = Loss.
            # Score is very low. We add depth to prefer "losing later" if inevitable.
            return -1000000 + depth 
            
        return best_val

    def find_best_move(self, you, opponent):
        self.start_time = time.time()
        self.nodes_visited = 0
        
        # Convert 2D arrays to Bitboards
        P = 0
        O = 0
        for r in range(5):
            for c in range(6):
                idx = r * 6 + c
                if you[r][c]:
                    P |= (1 << idx)
                elif opponent[r][c]:
                    O |= (1 << idx)
                    
        root_moves = self.get_moves_root(P, O)
        
        # If no moves, game rules imply loss. Return a dummy format to satisfy API.
        if not root_moves:
            return "0,0,U"
            
        # If only one move, take it immediately
        if len(root_moves) == 1:
            return root_moves[0][1]

        best_move_str = root_moves[0][1]
        
        # Iterative Deepening
        try:
            # Depth range: 1 to max possible (unlikely to exceed 20 in 1s for mid-game)
            for depth in range(1, 50):
                alpha = -float('inf')
                beta = float('inf')
                current_depth_best_val = -float('inf')
                current_depth_best_move = None
                
                for (src, dst), mv_str in root_moves:
                    new_P = (P ^ (1 << src)) | (1 << dst)
                    new_O = O ^ (1 << dst)
                    
                    # Call alpha-beta
                    val = -self.alphabeta(new_O, new_P, depth - 1, -beta, -alpha, False)
                    
                    if val > current_depth_best_val:
                        current_depth_best_val = val
                        current_depth_best_move = mv_str
                    
                    alpha = max(alpha, val)
                
                # Update global best only after completing full depth search for all moves
                if current_depth_best_move:
                    best_move_str = current_depth_best_move
                    
                # Small optimization: If we found a winning mate score, we can stop early
                if current_depth_best_val > 900000:
                    break
                    
        except TimeoutError:
            # Return the best move from the last fully completed depth
            pass
            
        return best_move_str

# Global bot instance to reuse precomputed masks (though lightweight)
bot = ClobberAI()
