
import time
import random
import math

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    Monte Carlo Tree Search (MCTS) policy for Hex on an 11x11 board.
    Includes immediate win detection and forced blocking.
    """
    
    # --- Constants ---
    BOARD_SIZE = 11
    TIME_LIMIT = 0.9  # Seconds (leaving buffer for overhead)
    
    # --- Helper Functions ---
    
    # Precompute neighbors for speed
    NEIGHBORS = {}
    for r in range(BOARD_SIZE):
        for c in range(BOARD_SIZE):
            # Standard Hex adjacency (offset coordinates)
            # Assuming axial/cube coordinates mapping to 2D grid:
            # Neighbors are (r-1, c), (r+1, c), (r, c-1), (r, c+1), (r-1, c+1), (r+1, c-1)
            # Or the variation depending on orientation. 
            # Given the prompt's description "touching top/bottom", let's stick to standard:
            # Top-Left: (r-1, c)
            # Top-Right: (r-1, c+1)
            # Right: (r, c+1)
            # Bottom-Right: (r+1, c)
            # Bottom-Left: (r+1, c-1)
            # Left: (r, c-1)
            # This is a common mapping for "pointy top" hexes rotated to fit a grid.
            
            n_list = []
            # Up-Left / Top
            if r > 0: n_list.append((r-1, c))
            # Up-Right
            if r > 0 and c < BOARD_SIZE - 1: n_list.append((r-1, c+1))
            # Right
            if c < BOARD_SIZE - 1: n_list.append((r, c+1))
            # Down-Right / Bottom
            if r < BOARD_SIZE - 1: n_list.append((r+1, c))
            # Down-Left
            if r < BOARD_SIZE - 1 and c > 0: n_list.append((r+1, c-1))
            # Left
            if c > 0: n_list.append((r, c-1))
            
            NEIGHBORS[(r, c)] = n_list

    def get_neighbors(r, c):
        return NEIGHBORS.get((r, c), [])

    def is_valid(r, c):
        return 0 <= r < BOARD_SIZE and 0 <= c < BOARD_SIZE

    def check_win(stones, color):
        """BFS to check if stones connect the two target sides."""
        if not stones:
            return False
        
        # Convert list to set for O(1) lookup
        stone_set = set(stones)
        
        # Determine start and end based on color
        # Black (b): Connect Top (Row 0) to Bottom (Row 10)
        # White (w): Connect Left (Col 0) to Right (Col 10)
        
        if color == 'b':
            starts = [s for s in stone_set if s[0] == 0]
            targets = set(s for s in stone_set if s[0] == 10)
            # If no stone touches start or end, no win yet
            if not starts: return False
        else: # 'w'
            starts = [s for s in stone_set if s[1] == 0]
            targets = set(s for s in stone_set if s[1] == 10)
            if not starts: return False

        # BFS
        queue = list(starts)
        visited = set(starts)
        
        while queue:
            curr = queue.pop(0)
            
            # Check if reached target side
            if color == 'b':
                if curr in targets and curr[0] == 10:
                    return True
            else:
                if curr in targets and curr[1] == 10:
                    return True
            
            # Expand
            for neighbor in get_neighbors(curr[0], curr[1]):
                if neighbor in stone_set and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    
        return False

    def check_winning_move(my_stones, opp_stones, color):
        """Checks if placing a stone immediately wins the game."""
        all_used = set(my_stones) | set(opp_stones)
        # Optimization: Only check empty cells connected to my stones
        candidates = set()
        for s in my_stones:
            for n in get_neighbors(s[0], s[1]):
                if n not in all_used:
                    candidates.add(n)
        
        # Also check border starts if empty
        if color == 'b':
            for c in range(BOARD_SIZE):
                if (0, c) not in all_used: candidates.add((0, c))
        else:
            for r in range(BOARD_SIZE):
                if (r, 0) not in all_used: candidates.add((r, 0))

        for r, c in candidates:
            # Simulate
            if check_win(my_stones + [(r, c)], color):
                return (r, c)
        return None

    def check_blocking_move(my_stones, opp_stones, color):
        """Checks if opponent is about to win, and returns the blocking move."""
        all_used = set(my_stones) | set(opp_stones)
        opp_color = 'w' if color == 'b' else 'b'
        
        candidates = set()
        for s in opp_stones:
            for n in get_neighbors(s[0], s[1]):
                if n not in all_used:
                    candidates.add(n)
        
        # Check border
        if opp_color == 'b':
            for c in range(BOARD_SIZE):
                if (0, c) not in all_used: candidates.add((0, c))
        else:
            for r in range(BOARD_SIZE):
                if (r, 0) not in all_used: candidates.add((r, 0))

        for r, c in candidates:
            # Simulate opp move
            if check_win(opp_stones + [(r, c)], opp_color):
                return (r, c)
        return None

    # --- MCTS Implementation ---

    class GameState:
        def __init__(self, me, opp, color):
            self.me = set(me)
            self.opp = set(opp)
            self.color = color
            self.turn = 'me' if len(me) == len(opp) else 'opp' # Assumption: I always move first or parity is even
            
            # Precompute valid moves
            occupied = self.me | self.opp
            self.all_moves = []
            for r in range(BOARD_SIZE):
                for c in range(BOARD_SIZE):
                    if (r, c) not in occupied:
                        self.all_moves.append((r, c))

        def is_terminal(self):
            return check_win(self.me, self.color) or check_win(self.opp, 'w' if self.color == 'b' else 'b')

        def get_result(self):
            if check_win(self.me, self.color): return 1
            if check_win(self.opp, 'w' if self.color == 'b' else 'b'): return -1
            return 0

        def get_next_state(self, move):
            new_me = set(self.me)
            new_opp = set(self.opp)
            if self.turn == 'me':
                new_me.add(move)
                return GameState(list(new_me), list(new_opp), self.color)
            else:
                new_opp.add(move)
                return GameState(list(new_me), list(new_opp), self.color)

    class MCTSNode:
        def __init__(self, state, parent=None, move=None):
            self.state = state
            self.parent = parent
            self.move = move
            self.children = []
            self.wins = 0
            self.visits = 0
            self.untried_moves = state.all_moves[:] # Shallow copy

        def ucb(self):
            if self.visits == 0:
                return float('inf')
            return (self.wins / self.visits) + (1.41 * math.sqrt(math.log(self.parent.visits) / self.visits))

        def select_child(self):
            return max(self.children, key=lambda c: c.ucb())

        def expand(self):
            move = self.untried_moves.pop(random.randrange(len(self.untried_moves)))
            next_state = self.state.get_next_state(move)
            child = MCTSNode(next_state, self, move)
            self.children.append(child)
            return child

        def simulate(self):
            current_state = self.state
            depth = 0
            # Fast simulation: Random rollout
            # Optimization: Check terminal immediately
            if current_state.is_terminal():
                return current_state.get_result()

            # Create local copies for simulation to avoid modifying tree state
            sim_me = set(current_state.me)
            sim_opp = set(current_state.opp)
            sim_turn = current_state.turn
            
            # Limit simulation depth to avoid infinite loops in rare cases or long drawn games
            max_depth = BOARD_SIZE * BOARD_SIZE - len(sim_me) - len(sim_opp)
            
            while depth < max_depth:
                if check_win(sim_me, self.state.color):
                    return 1
                if check_win(sim_opp, 'w' if self.state.color == 'b' else 'b'):
                    return -1
                
                # Determine valid moves
                occupied = sim_me | sim_opp
                # Heuristic: Prefer moves near existing stones to speed up game
                # But for pure random, just pick from empty. 
                # To make it faster, we generate a list of empty cells on demand or random sampling.
                # Random sampling is faster than generating full list if board is sparse.
                
                while True:
                    r = random.randint(0, BOARD_SIZE - 1)
                    c = random.randint(0, BOARD_SIZE - 1)
                    if (r, c) not in occupied:
                        break
                
                if sim_turn == 'me':
                    sim_me.add((r, c))
                    sim_turn = 'opp'
                else:
                    sim_opp.add((r, c))
                    sim_turn = 'me'
                
                depth += 1
            
            # Timeout or depth limit reached, evaluate heuristic (territory)
            # Simple heuristic: Who has more stones? (Often correlated with win in Hex)
            # But we must check actual connection first.
            if check_win(sim_me, self.state.color): return 1
            if check_win(sim_opp, 'w' if self.state.color == 'b' else 'b'): return -1
            
            # Draw/Heuristic
            return 0

        def backpropagate(self, result):
            self.visits += 1
            # If it was my turn when I visited this node, I want this result.
            # But wait: result is relative to the root player.
            # Actually, if result is 1 (Root Player Win), then all nodes on path 
            # leading to Root Player's moves should be encouraged.
            # MCTS usually accumulates wins for the player who just moved at the node?
            # Standard: Propagate result as is. 
            # If I am simulating from a node, and the result is +1 (Root Win), then I add +1.
            # If result is -1 (Root Loss), I add 0? Or add -1? 
            # Usually: Wins = sum of results from perspective of player who just moved at THIS node?
            # Let's stick to simple: sum of results where 1 is Root Win, -1 is Root Loss.
            # If this node's turn was 'me' (root), +1 is good. If node's turn was 'opp', +1 is bad (win for root).
            # Wait, if root is 'me', and I reach a node where it's 'opp's turn. 
            # If simulation result is 1 (me win), then 'opp' made a move leading to my win (bad move for opp).
            # So for the child node (which is opp's move), I want to penalize it.
            
            if self.state.turn == 'me':
                # Node represents state where I am to move. Result +1 is good.
                self.wins += result
            else:
                # Node represents state where opp is to move. Result +1 is good for me, bad for opp.
                # So if I win (1), it means opp made a bad move previously? 
                # Let's stick to: Wins counts how good the state is for the player whose turn it is NOT?
                # Standard UCT: Wins counts how often the player who just moved WON.
                # Let's use: Wins accumulates the result (1, -1) relative to the root.
                # If root is 'me', and I am at a node where it was 'opp's turn.
                # If result is 1 (me win), then opp's move was bad. I subtract from wins?
                # To simplify: Wins counts good outcomes for ROOT player.
                # If node.turn == 'me', add result.
                # If node.turn == 'opp', subtract result (because opp wants to minimize my win).
                self.wins -= result 
            
            if self.parent:
                self.parent.backpropagate(result)

    # --- Main Logic Flow ---

    # 1. Immediate Win / Block Check (Critical for 1-move threats)
    winning_move = check_winning_move(me, opp, color)
    if winning_move:
        return winning_move

    blocking_move = check_blocking_move(me, opp, color)
    if blocking_move:
        return blocking_move

    # 2. MCTS
    start_time = time.time()
    
    # Initial State
    root_state = GameState(me, opp, color)
    root = MCTSNode(root_state)
    
    iterations = 0
    while time.time() - start_time < TIME_LIMIT:
        node = root
        
        # Selection
        while node.untried_moves == [] and node.children != []:
            node = node.select_child()
        
        # Expansion
        if node.untried_moves != []:
            node = node.expand()
        
        # Simulation
        result = node.simulate()
        
        # Backpropagation
        node.backpropagate(result)
        iterations += 1

    # Select best move from root
    if not root.children:
        # Fallback: if MCTS failed (shouldn't happen), pick random
        occupied = set(me) | set(opp)
        while True:
            r = random.randint(0, 10)
            c = random.randint(0, 10)
            if (r, c) not in occupied:
                return (r, c)

    # Choose child with highest visit count (robustness)
    best_child = max(root.children, key=lambda c: c.visits)
    return best_child.move
