
import random
import math
import time
from collections import deque

class HexGame:
    """Efficient Hex game state representation"""
    
    def __init__(self, size=11):
        self.size = size
        self.black = 0
        self.white = 0
        self.turn = 'b'
        self.move_count = 0
        self.neighbor_cache = {}
        self._init_neighbor_cache()
    
    def _init_neighbor_cache(self):
        """Precompute neighbors for all cells"""
        dirs = [(-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0)]
        for r in range(self.size):
            for c in range(self.size):
                neighbors = []
                for dr, dc in dirs:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < self.size and 0 <= nc < self.size:
                        neighbors.append((nr, nc))
                self.neighbor_cache[(r, c)] = neighbors
    
    def from_lists(self, black_list, white_list):
        """Initialize from stone lists"""
        self.black = 0
        self.white = 0
        for r, c in black_list:
            self.black |= 1 << (r * self.size + c)
        for r, c in white_list:
            self.white |= 1 << (r * self.size + c)
        self.move_count = len(black_list) + len(white_list)
        return self
    
    def get_neighbors(self, r, c):
        return self.neighbor_cache[(r, c)]
    
    def get_empty_neighbors(self, r, c):
        """Get empty neighboring cells"""
        pos = r * self.size + c
        mask = self.black | self.white
        return [(nr, nc) for nr, nc in self.neighbor_cache[(r, c)] 
                if not (mask & (1 << (nr * self.size + nc)))]
    
    def is_empty(self, r, c):
        pos = r * self.size + c
        return not ((self.black | self.white) & (1 << pos))
    
    def place_stone(self, r, c, color):
        """Place a stone and return new state"""
        pos = r * self.size + c
        new_state = HexGame(self.size)
        new_state.black = self.black
        new_state.white = self.white
        new_state.move_count = self.move_count + 1
        
        if color == 'b':
            new_state.black |= 1 << pos
        else:
            new_state.white |= 1 << pos
            
        new_state.turn = 'w' if color == 'b' else 'b'
        return new_state
    
    def get_legal_moves(self):
        """Get all empty cells"""
        mask = self.black | self.white
        moves = []
        for r in range(self.size):
            for c in range(self.size):
                pos = r * self.size + c
                if not (mask & (1 << pos)):
                    moves.append((r, c))
        return moves
    
    def get_relevant_moves(self, distance=2):
        """Get moves near existing stones for efficiency"""
        mask = self.black | self.white
        relevant = set()
        
        # Add all neighbor cells of occupied stones
        for r in range(self.size):
            for c in range(self.size):
                pos = r * self.size + c
                if mask & (1 << pos):
                    for nr, nc in self.neighbor_cache[(r, c)]:
                        if not (mask & (1 << (nr * self.size + nc))):
                            relevant.add((nr, nc))
        
        # If too few, add random cells
        if len(relevant) < 5:
            for r in range(self.size):
                for c in range(self.size):
                    pos = r * self.size + c
                    if not (mask & (1 << pos)):
                        relevant.add((r, c))
        
        return list(relevant)
    
    def has_player_won(self, color):
        """Check if player has won using BFS"""
        if color == 'b':
            stones = self.black
            start_side = [(0, c) for c in range(self.size)]
            target_side = [(self.size-1, c) for c in range(self.size)]
        else:
            stones = self.white
            start_side = [(r, 0) for r in range(self.size)]
            target_side = [(r, self.size-1) for r in range(self.size)]
        
        visited = set()
        queue = deque()
        
        # Start from all stones on starting side
        for r, c in start_side:
            pos = r * self.size + c
            if stones & (1 << pos):
                queue.append((r, c))
                visited.add((r, c))
        
        while queue:
            r, c = queue.popleft()
            
            # Check if reached target side
            if (r, c) in target_side:
                return True
            
            for nr, nc in self.neighbor_cache[(r, c)]:
                pos = nr * self.size + nc
                if (nr, nc) not in visited and (stones & (1 << pos)):
                    visited.add((nr, nc))
                    queue.append((nr, nc))
        
        return False
    
    def distance_to_sides(self, r, c, color):
        """Calculate minimum distance to both sides"""
        if color == 'b':
            dist_top = r
            dist_bottom = self.size - 1 - r
            return min(dist_top, dist_bottom)
        else:
            dist_left = c
            dist_right = self.size - 1 - c
            return min(dist_left, dist_right)
    
    def heuristic_value(self, r, c, color):
        """Heuristic value of a move"""
        # Distance to our sides (lower is better)
        our_dist = self.distance_to_sides(r, c, color)
        
        # Distance to opponent sides (higher is better for us)
        opp_color = 'w' if color == 'b' else 'b'
        opp_dist = self.distance_to_sides(r, c, opp_color)
        
        # Count connections to our stones
        connections = 0
        for nr, nc in self.neighbor_cache[(r, c)]:
            pos = nr * self.size + nc
            if color == 'b' and (self.black & (1 << pos)):
                connections += 1
            elif color == 'w' and (self.white & (1 << pos)):
                connections += 1
        
        # Value formula
        value = 10.0 / (our_dist + 1) + 0.5 * opp_dist + 2.0 * connections
        
        # Bonus for center control
        center_dist = abs(r - self.size//2) + abs(c - self.size//2)
        value += 5.0 / (center_dist + 1)
        
        return value


class MCTSNode:
    """Node in Monte Carlo Tree Search"""
    
    def __init__(self, game_state, move=None, parent=None):
        self.game_state = game_state
        self.move = move  # Move that led to this state
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = None
    
    def get_untried_moves(self):
        if self.untried_moves is None:
            if self.game_state.move_count < 10:
                self.untried_moves = self.game_state.get_relevant_moves()
            else:
                self.untried_moves = self.game_state.get_legal_moves()
        return self.untried_moves
    
    def ucb_score(self, exploration=1.414):
        """UCB1 formula"""
        if self.visits == 0:
            return float('inf')
        exploitation = self.wins / self.visits
        exploration_term = exploration * math.sqrt(math.log(self.parent.visits) / self.visits)
        return exploitation + exploration_term
    
    def best_child(self):
        """Select child with highest UCB score"""
        return max(self.children, key=lambda c: c.ucb_score())
    
    def expand(self):
        """Expand a random untried move"""
        untried = self.get_untried_moves()
        if not untried:
            return None
            
        move = max(untried, key=lambda m: self.game_state.heuristic_value(m[0], m[1], 
                                                                          self.game_state.turn))
        new_state = self.game_state.place_stone(move[0], move[1], self.game_state.turn)
        child = MCTSNode(new_state, move, self)
        self.children.append(child)
        self.untried_moves = [m for m in untried if m != move]
        return child
    
    def simulate(self):
        """Run a random simulation to termination"""
        state = self.game_state
        while True:
            if state.has_player_won('b'):
                return 1.0 if state.turn == 'w' else 0.0  # Previous player won
            if state.has_player_won('w'):
                return 1.0 if state.turn == 'b' else 0.0  # Previous player won
            
            moves = state.get_legal_moves()
            if not moves:
                return 0.5  # Draw (shouldn't happen in Hex)
            
            # Biased random move selection
            if random.random() < 0.7 and state.move_count < 50:
                # Heuristic bias
                move_scores = [(m, state.heuristic_value(m[0], m[1], state.turn)) 
                              for m in moves]
                move_scores.sort(key=lambda x: x[1], reverse=True)
                top_moves = move_scores[:max(3, len(move_scores)//4)]
                move = random.choice(top_moves)[0]
            else:
                move = random.choice(moves)
            
            state = state.place_stone(move[0], move[1], state.turn)
    
    def backpropagate(self, result):
        """Propagate simulation result up the tree"""
        node = self
        while node is not None:
            node.visits += 1
            node.wins += result
            result = 1.0 - result  # Alternate perspective for opponent
            node = node.parent


class HexPolicy:
    """Main policy implementation"""
    
    def __init__(self):
        self.size = 11
        self.opening_book = self._create_opening_book()
    
    def _create_opening_book(self):
        """Opening moves for 11x11 Hex"""
        book = {}
        
        # First move openings
        book[('b', 0)] = (5, 5)  # Center for black
        book[('w', 0)] = (5, 5)  # Center for white
        
        # Second move responses
        book[('b', 1)] = [
            (5, 6), (5, 4), (6, 5), (4, 5)  # Adjacent to center
        ]
        book[('w', 1)] = [
            (5, 6), (5, 4), (6, 5), (4, 5)
        ]
        
        return book
    
    def get_opening_move(self, color, move_number):
        """Get opening book move if available"""
        key = (color, move_number)
        if key in self.opening_book:
            moves = self.opening_book[key]
            if isinstance(moves, list):
                return random.choice(moves)
            return moves
        return None
    
    def policy(self, me, opp, color):
        """Main policy function"""
        start_time = time.time()
        
        # Create game state
        game = HexGame(self.size)
        if color == 'b':
            game.from_lists(me, opp)
            game.turn = 'b'
        else:
            game.from_lists(opp, me)  # We're white, opponent is black
            game.turn = 'w'
        
        move_number = len(me) + len(opp)
        
        # Try opening book for first 2 moves
        if move_number < 2:
            opening_move = self.get_opening_move(color, move_number)
            if opening_move and game.is_empty(*opening_move):
                return opening_move
        
        # Early game: use heuristic for moves 2-5
        if move_number < 5:
            moves = game.get_relevant_moves()
            if moves:
                # Use heuristic to pick best move
                best_move = max(moves, key=lambda m: game.heuristic_value(m[0], m[1], color))
                return best_move
        
        # MCTS for remaining moves
        root = MCTSNode(game)
        
        # Time-limited MCTS
        while time.time() - start_time < 0.95:  # Leave 50ms margin
            # Selection
            node = root
            while node.children and not node.get_untried_moves():
                node = node.best_child()
            
            # Expansion
            if node.get_untried_moves():
                node = node.expand()
                if node is None:
                    continue
            
            # Simulation
            result = node.simulate()
            
            # Backpropagation
            node.backpropagate(result)
        
        # Choose best move
        if root.children:
            # Select child with most visits
            best_child = max(root.children, key=lambda c: c.visits)
            return best_child.move
        
        # Fallback: heuristic move
        moves = game.get_legal_moves()
        if not moves:
            # Should never happen, but return any valid move
            for r in range(self.size):
                for c in range(self.size):
                    if game.is_empty(r, c):
                        return (r, c)
        
        # Heuristic fallback
        best_move = max(moves, key=lambda m: game.heuristic_value(m[0], m[1], color))
        return best_move


# Global policy instance
_policy_instance = HexPolicy()

def policy(me, opp, color):
    """Required API function"""
    return _policy_instance.policy(me, opp, color)
