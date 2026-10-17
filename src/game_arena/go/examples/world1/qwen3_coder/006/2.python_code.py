
import random
import math
import time
from typing import List, Tuple

class GoState:
    def __init__(self, me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], player_to_move: int = 1):
        self.board = [[0 for _ in range(21)] for _ in range(21)]  # Extended board for easier neighbor calculation
        self.captured_stones = {1: 0, 2: 0}
        self.ko_point = None
        self.player_to_move = player_to_move
        
        # Place stones on board
        for r, c in me:
            self.board[r][c] = 1
        for r, c in opponent:
            self.board[r][c] = 2
    
    def get_neighbors(self, r: int, c: int) -> List[Tuple[int, int]]:
        return [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
    
    def get_group(self, r: int, c: int) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]]]:
        if self.board[r][c] == 0:
            return [], []
        
        player = self.board[r][c]
        visited = set()
        queue = [(r, c)]
        group = []
        liberties = set()
        
        while queue:
            curr_r, curr_c = queue.pop()
            if (curr_r, curr_c) in visited:
                continue
            visited.add((curr_r, curr_c))
            
            if self.board[curr_r][curr_c] == player:
                group.append((curr_r, curr_c))
                for nr, nc in self.get_neighbors(curr_r, curr_c):
                    if 1 <= nr <= 19 and 1 <= nc <= 19:
                        if self.board[nr][nc] == 0:
                            liberties.add((nr, nc))
                        elif self.board[nr][nc] == player and (nr, nc) not in visited:
                            queue.append((nr, nc))
        
        return group, list(liberties)
    
    def is_valid_move(self, r: int, c: int, player: int) -> bool:
        if self.board[r][c] != 0:
            return False
            
        if (r, c) == self.ko_point:
            return False
            
        # Temporarily place the stone
        self.board[r][c] = player
        
        # Check if move captures opponent stones
        captured = []
        opponent = 3 - player
        for nr, nc in self.get_neighbors(r, c):
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if self.board[nr][nc] == opponent:
                    group, liberties = self.get_group(nr, nc)
                    if not liberties:
                        captured.extend(group)
        
        # Check for suicide
        group, liberties = self.get_group(r, c)
        valid = bool(liberties or captured)
        
        # Restore board
        self.board[r][c] = 0
        return valid
    
    def play_move(self, r: int, c: int, player: int) -> bool:
        if not self.is_valid_move(r, c, player):
            return False
            
        self.board[r][c] = player
        captured = []
        opponent = 3 - player
        
        # Capture opponent stones
        for nr, nc in self.get_neighbors(r, c):
            if 1 <= nr <= 19 and 1 <= nc <= 19:
                if self.board[nr][nc] == opponent:
                    group, liberties = self.get_group(nr, nc)
                    if not liberties:
                        captured.extend(group)
                        for cr, cc in group:
                            self.board[cr][cc] = 0
        
        self.captured_stones[player] += len(captured)
        
        # Set ko point if exactly one stone was captured
        self.ko_point = None
        if len(captured) == 1:
            # Check if the move creates a ko
            group, liberties = self.get_group(r, c)
            if len(group) == 1 and len(liberties) == 1:
                self.ko_point = captured[0]
                
        self.player_to_move = 3 - player
        return True
    
    def get_legal_moves(self) -> List[Tuple[int, int]]:
        moves = [(0, 0)]  # Pass move
        for r in range(1, 20):
            for c in range(1, 20):
                if self.is_valid_move(r, c, self.player_to_move):
                    moves.append((r, c))
        return moves
    
    def is_game_over(self) -> bool:
        # Simplified termination condition
        return False
    
    def simulate_random_game(self) -> int:
        state = GoState([], [])  # Create a copy of current state
        for r in range(1, 20):
            for c in range(1, 20):
                state.board[r][c] = self.board[r][c]
        state.player_to_move = self.player_to_move
        
        # Simulate until game ends (simplified)
        moves_played = 0
        while not state.is_game_over() and moves_played < 100:  # Prevent infinite games
            moves = state.get_legal_moves()
            if not moves:
                break
            move = random.choice(moves)
            if move != (0, 0):  # Not passing
                state.play_move(move[0], move[1], state.player_to_move)
            else:
                state.player_to_move = 3 - state.player_to_move
            moves_played += 1
            
        # Evaluate final position (simplified)
        score_p1 = sum(1 for r in range(1, 20) for c in range(1, 20) if state.board[r][c] == 1)
        score_p2 = sum(1 for r in range(1, 20) for c in range(1, 20) if state.board[r][c] == 2)
        if score_p1 > score_p2:
            return 1
        elif score_p2 > score_p1:
            return 2
        else:
            return 0  # Draw

class MCTSNode:
    def __init__(self, state: GoState, move: Tuple[int, int] = None, parent=None):
        self.state = state
        self.move = move
        self.parent = parent
        self.children = []
        self.visits = 0
        self.wins = 0
        self.untried_moves = state.get_legal_moves()
    
    def ucb1(self, exploration_param=1.41):
        if self.visits == 0:
            return float('inf')
        return self.wins / self.visits + exploration_param * math.sqrt(math.log(self.parent.visits) / self.visits)
    
    def select_child(self):
        return max(self.children, key=lambda c: c.ucb1())
    
    def expand(self):
        move = self.untried_moves.pop()
        new_state = GoState([], [])  # Create a copy
        for r in range(1, 20):
            for c in range(1, 20):
                new_state.board[r][c] = self.state.board[r][c]
        new_state.player_to_move = self.state.player_to_move
        if move != (0, 0):
            new_state.play_move(move[0], move[1], self.state.player_to_move)
        else:
            new_state.player_to_move = 3 - self.state.player_to_move
            
        child = MCTSNode(new_state, move, self)
        self.children.append(child)
        return child
    
    def simulate(self):
        return self.state.simulate_random_game()
    
    def backpropagate(self, result):
        self.visits += 1
        if result == self.state.player_to_move:
            self.wins += 1
        if self.parent:
            self.parent.backpropagate(result)

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]]) -> Tuple[int, int]:
    # Initialize MCTS
    root_state = GoState(me, opponent)
    root = MCTSNode(root_state)
    
    # Set time limit
    start_time = time.time()
    time_limit = 0.9  # 900ms to leave some buffer
    
    # MCTS loop
    while time.time() - start_time < time_limit:
        node = root
        
        # Selection
        while not node.untried_moves and node.children:
            node = node.select_child()
        
        # Expansion
        if node.untried_moves:
            node = node.expand()
        
        # Simulation
        result = node.simulate()
        
        # Backpropagation
        node.backpropagate(result)
    
    # Choose best move
    if not root.children:
        # If no simulations were completed, play a random valid move
        legal_moves = root_state.get_legal_moves()
        if legal_moves:
            return random.choice(legal_moves)
        else:
            return (0, 0)  # Pass if no legal moves
    
    # Select child with highest visit count
    best_child = max(root.children, key=lambda c: c.visits)
    return best_child.move
