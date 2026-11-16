
import numpy as np
import itertools
import copy
import random
from typing import List, Tuple, Optional

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    """
    Main policy function called by the arena.
    Returns a move string 'row,col,dir'.
    """
    # Instantiate the bot and get best move
    bot = DotsAndBoxesBot(horizontal, vertical, capture)
    move = bot.best_move()
    return f"{move[0]},{move[1]},{move[2]}"

class DotsAndBoxesBot:
    def __init__(self, horizontal, vertical, capture):
        self.h = horizontal
        self.v = vertical
        self.c = capture
        self.size = 4  # 4x4 boxes
        self.max_depth = 4  # search depth
        self.player = 1  # we are player 1
        
    def best_move(self) -> Tuple[int, int, str]:
        """Return (row, col, dir) for the best move."""
        moves = self.get_legal_moves()
        if not moves:
            raise RuntimeError("No legal moves")
        
        # If only one move, play it
        if len(moves) == 1:
            return moves[0]
        
        # Early game: use simple heuristic to speed up
        empty_boxes = np.sum(self.c == 0)
        if empty_boxes >= 14:  # very early
            return self.early_game_move(moves)
        
        # Mid/End game: use minimax
        best_score = -float('inf')
        best_moves = []
        alpha = -float('inf')
        beta = float('inf')
        
        for move in moves:
            # Quick check: never complete third side of a box unless forced
            if not self.is_forced_move(move) and self.completes_third_side(move):
                continue  # skip dangerous move unless necessary
            
            h2, v2, c2 = self.make_move(move)
            score = self.minimax(h2, v2, c2, depth=self.max_depth-1, alpha=alpha, beta=beta, maximizing=False)
            if score > best_score:
                best_score = score
                best_moves = [move]
            elif abs(score - best_score) < 0.1:
                best_moves.append(move)
        
        # If all moves were dangerous (third side), we must play one
        if not best_moves:
            best_moves = moves
        
        # Tie-breaker: prefer moves that don't give opponent long chains
        if len(best_moves) > 1:
            best_moves = self.tie_break(best_moves)
        
        return random.choice(best_moves) if best_moves else moves[0]
    
    def early_game_move(self, moves):
        """Simple heuristic for early game: avoid creating 3-sided boxes."""
        safe_moves = []
        for move in moves:
            if not self.completes_third_side(move):
                safe_moves.append(move)
        if safe_moves:
            # Prefer center moves
            center_pref = []
            for m in safe_moves:
                r, c, _ = m
                dist_from_center = abs(r - 2) + abs(c - 2)
                center_pref.append((dist_from_center, m))
            center_pref.sort()
            return center_pref[0][1]
        return moves[0]
    
    def tie_break(self, moves):
        """Choose among equally good moves: avoid giving opponent double-cross opportunities."""
        scored = []
        for move in moves:
            h2, v2, c2 = self.make_move(move)
            # Count how many 3-sided boxes we create for opponent
            danger = self.count_three_sided_boxes(h2, v2, c2)
            scored.append((danger, move))
        scored.sort()  # lower danger first
        best_danger = scored[0][0]
        return [m for d, m in scored if d == best_danger]
    
    def count_three_sided_boxes(self, h, v, capture):
        """Count boxes with exactly 3 sides drawn."""
        count = 0
        for r in range(self.size):
            for c in range(self.size):
                if capture[r, c] != 0:
                    continue
                sides = 0
                if h[r, c] != 0:
                    sides += 1
                if h[r+1, c] != 0:
                    sides += 1
                if v[r, c] != 0:
                    sides += 1
                if v[r, c+1] != 0:
                    sides += 1
                if sides == 3:
                    count += 1
        return count
    
    def completes_third_side(self, move):
        """Return True if playing this move creates a 3-sided box for opponent to capture."""
        r, c, dir = move
        # Check adjacent boxes
        if dir == 'H':
            # Box above (if exists)
            if r > 0:
                if self.count_box_sides(r-1, c) == 2 and not self.would_capture(r-1, c, move):
                    return True
            # Box below
            if r < self.size:
                if self.count_box_sides(r, c) == 2 and not self.would_capture(r, c, move):
                    return True
        else:  # 'V'
            # Box left
            if c > 0:
                if self.count_box_sides(r, c-1) == 2 and not self.would_capture(r, c-1, move):
                    return True
            # Box right
            if c < self.size:
                if self.count_box_sides(r, c) == 2 and not self.would_capture(r, c, move):
                    return True
        return False
    
    def would_capture(self, box_r, box_c, move):
        """Return True if playing move would capture this box."""
        r, c, dir = move
        # Check if this move completes the fourth side of the box
        sides_before = self.count_box_sides(box_r, box_c)
        # Simulate adding the edge
        if dir == 'H':
            if (box_r == r and box_c == c) or (box_r == r-1 and box_c == c):
                return sides_before == 3
        else:
            if (box_r == r and box_c == c) or (box_r == r and box_c == c-1):
                return sides_before == 3
        return False
    
    def count_box_sides(self, box_r, box_c):
        """Count drawn sides of a given box."""
        count = 0
        if self.h[box_r, box_c] != 0:
            count += 1
        if self.h[box_r+1, box_c] != 0:
            count += 1
        if self.v[box_r, box_c] != 0:
            count += 1
        if self.v[box_r, box_c+1] != 0:
            count += 1
        return count
    
    def is_forced_move(self, move):
        """Return True if this move captures at least one box (forced to play it)."""
        r, c, dir = move
        # Check adjacent boxes
        if dir == 'H':
            if r > 0 and self.count_box_sides(r-1, c) == 3:
                return True
            if r < self.size and self.count_box_sides(r, c) == 3:
                return True
        else:
            if c > 0 and self.count_box_sides(r, c-1) == 3:
                return True
            if c < self.size and self.count_box_sides(r, c) == 3:
                return True
        return False
    
    def minimax(self, h, v, capture, depth, alpha, beta, maximizing):
        """Minimax with alpha-beta pruning."""
        # Terminal or depth limit
        if depth == 0:
            return self.evaluate(h, v, capture)
        
        moves = self.get_legal_moves_state(h, v, capture)
        if not moves:
            # Game over
            our_boxes = np.sum(capture == 1)
            opp_boxes = np.sum(capture == -1)
            return our_boxes - opp_boxes
        
        if maximizing:
            max_eval = -float('inf')
            for move in moves:
                h2, v2, c2 = self.make_move_state(h, v, capture, move, player=1)
                # If we captured, we go again
                if self.move_captured_any(h, v, move):
                    eval = self.minimax(h2, v2, c2, depth-1, alpha, beta, True)
                else:
                    eval = self.minimax(h2, v2, c2, depth-1, alpha, beta, False)
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                h2, v2, c2 = self.make_move_state(h, v, capture, move, player=-1)
                if self.move_captured_any_state(h, v, move):
                    eval = self.minimax(h2, v2, c2, depth-1, alpha, beta, False)
                else:
                    eval = self.minimax(h2, v2, c2, depth-1, alpha, beta, True)
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            return min_eval
    
    def evaluate(self, h, v, capture):
        """Evaluation function: positive good for us."""
        our_boxes = np.sum(capture == 1)
        opp_boxes = np.sum(capture == -1)
        box_diff = our_boxes - opp_boxes
        
        # Count 3-sided boxes (dangerous)
        three_sided = 0
        two_sided = 0
        for r in range(self.size):
            for c in range(self.size):
                if capture[r, c] != 0:
                    continue
                sides = 0
                if h[r, c] != 0:
                    sides += 1
                if h[r+1, c] != 0:
                    sides += 1
                if v[r, c] != 0:
                    sides += 1
                if v[r, c+1] != 0:
                    sides += 1
                if sides == 3:
                    three_sided += 1
                elif sides == 2:
                    two_sided += 1
        
        # Prefer having fewer 3-sided boxes for opponent
        # and more 2-sided boxes (potential chains for us)
        score = box_diff * 10
        score -= three_sided * 3  # penalty for giving opponent opportunities
        score += two_sided * 1   # bonus for potential chains
        return score
    
    def move_captured_any(self, h, v, move):
        """Check if a move captures any box in the current state."""
        return self.move_captured_any_state(self.h, self.v, move)
    
    def move_captured_any_state(self, h, v, move):
        """Check if a move captures any box given state arrays."""
        r, c, dir = move
        if dir == 'H':
            # Check box above
            if r > 0:
                if self.count_box_sides_state(h, v, r-1, c) == 3:
                    return True
            # Check box below
            if r < self.size:
                if self.count_box_sides_state(h, v, r, c) == 3:
                    return True
        else:
            if c > 0:
                if self.count_box_sides_state(h, v, r, c-1) == 3:
                    return True
            if c < self.size:
                if self.count_box_sides_state(h, v, r, c) == 3:
                    return True
        return False
    
    def count_box_sides_state(self, h, v, box_r, box_c):
        """Count drawn sides of a box given state arrays."""
        count = 0
        if h[box_r, box_c] != 0:
            count += 1
        if h[box_r+1, box_c] != 0:
            count += 1
        if v[box_r, box_c] != 0:
            count += 1
        if v[box_r, box_c+1] != 0:
            count += 1
        return count
    
    def get_legal_moves(self):
        """Return list of (row, col, dir) for all legal moves."""
        moves = []
        # Horizontal edges
        for r in range(5):
            for c in range(4):
                if self.h[r, c] == 0:
                    moves.append((r, c, 'H'))
        # Vertical edges
        for r in range(4):
            for c in range(5):
                if self.v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves
    
    def get_legal_moves_state(self, h, v, capture):
        """Get legal moves from given state."""
        moves = []
        for r in range(5):
            for c in range(4):
                if h[r, c] == 0:
                    moves.append((r, c, 'H'))
        for r in range(4):
            for c in range(5):
                if v[r, c] == 0:
                    moves.append((r, c, 'V'))
        return moves
    
    def make_move(self, move):
        """Return new state arrays after making move in current state."""
        return self.make_move_state(self.h, self.v, self.c, move, player=1)
    
    def make_move_state(self, h, v, capture, move, player):
        """Simulate move on given state arrays."""
        r, c, dir = move
        h2 = h.copy()
        v2 = v.copy()
        c2 = capture.copy()
        
        if dir == 'H':
            h2[r, c] = player
        else:
            v2[r, c] = player
        
        # Check for captured boxes
        if dir == 'H':
            # Box above
            if r > 0:
                if self.count_box_sides_state(h2, v2, r-1, c) == 4 and c2[r-1, c] == 0:
                    c2[r-1, c] = player
            # Box below
            if r < self.size:
                if self.count_box_sides_state(h2, v2, r, c) == 4 and c2[r, c] == 0:
                    c2[r, c] = player
        else:
            # Box left
            if c > 0:
                if self.count_box_sides_state(h2, v2, r, c-1) == 4 and c2[r, c-1] == 0:
                    c2[r, c-1] = player
            # Box right
            if c < self.size:
                if self.count_box_sides_state(h2, v2, r, c) == 4 and c2[r, c] == 0:
                    c2[r, c] = player
        
        return h2, v2, c2
