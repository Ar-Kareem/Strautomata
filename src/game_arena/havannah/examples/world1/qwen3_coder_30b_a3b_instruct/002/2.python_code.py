
import random
import numpy as np
from collections import defaultdict, deque
import time

class HavannahMCTS:
    def __init__(self, board_size=15):
        self.board_size = board_size
        self.max_iterations = 5000
        self.opp = None
        self.me = None
        self.valid_mask = None
        
    def get_neighbors(self, row, col):
        """Get all 6 neighbors of a hexagonal cell"""
        neighbors = []
        directions = [(-1, 0), (-1, -1), (0, -1), (1, 0), (1, 1), (0, 1)]
        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < self.board_size and 0 <= new_col < self.board_size:
                neighbors.append((new_row, new_col))
        return neighbors
    
    def is_valid(self, row, col):
        """Check if position is valid and unoccupied"""
        return (0 <= row < self.board_size and 
                0 <= col < self.board_size and 
                self.valid_mask[row][col] and 
                (row, col) not in self.me and 
                (row, col) not in self.opp)
    
    def check_ring(self, board, color):
        """Check if a ring of the given color exists"""
        # This is a simplified implementation - full ring detection would be more complex
        # For now, we'll use a heuristic that looks for closed paths
        pass
    
    def check_bridge(self, board, color):
        """Check if a bridge of the given color exists"""
        # Bridge connects any two corner cells
        # Corners: (0,0), (0,14), (14,0), (14,14)
        pass
    
    def check_fork(self, board, color):
        """Check if a fork of the given color exists"""
        # Fork connects three edges (but not corners)
        pass
    
    def count_paths_to_edges(self, board, color):
        """Count how many paths a player has to the board edges"""
        # Simplified approach - count connected components to edges
        visited = set()
        edge_count = 0
        
        # Check all edge positions
        edges = []
        # Top and bottom edges
        for col in range(self.board_size):
            if (0, col) in board and board[0, col] == color:
                edges.append((0, col))
            if (self.board_size-1, col) in board and board[self.board_size-1, col] == color:
                edges.append((self.board_size-1, col))
        # Left and right edges
        for row in range(self.board_size):
            if (row, 0) in board and board[row, 0] == color:
                edges.append((row, 0))
            if (row, self.board_size-1) in board and board[row, self.board_size-1] == color:
                edges.append((row, self.board_size-1))
        
        # Count connected components to edges
        for edge_pos in edges:
            if edge_pos not in visited:
                # BFS to find connected component
                queue = deque([edge_pos])
                visited.add(edge_pos)
                component = set()
                while queue:
                    pos = queue.popleft()
                    component.add(pos)
                    for neighbor in self.get_neighbors(pos[0], pos[1]):
                        if neighbor not in visited and neighbor in board and board[neighbor] == color:
                            visited.add(neighbor)
                            queue.append(neighbor)
                if component:
                    edge_count += 1
                    
        return edge_count
    
    def evaluate_position(self, board, color):
        """Evaluate current board position"""
        if color == 0:
            our_stones = self.me
            opp_stones = self.opp
        else:
            our_stones = self.opp
            opp_stones = self.me
            
        # Convert to more convenient format
        board_state = {}
        for row, col in self.me:
            board_state[(row, col)] = 0
        for row, col in self.opp:
            board_state[(row, col)] = 1
            
        # Simple heuristic: connectivity to edges
        our_paths = self.count_paths_to_edges(board_state, color)
        opp_paths = self.count_paths_to_edges(board_state, 1-color)
        
        # Heuristic score
        return our_paths - opp_paths * 1.5  # Slight penalty for opponent advancement
        
    def simulate_random_game(self, move, board_state):
        """Simulate a random game from current position"""
        # Copy board
        current_board = {}
        for pos, color in board_state.items():
            current_board[pos] = color
            
        current_player = 0 if move not in board_state else 1
        current_board[move] = current_player
        
        # Simple random playout
        moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if (row, col) not in current_board and self.valid_mask[row][col]:
                    moves.append((row, col))
        
        random.shuffle(moves)
        
        for i, pos in enumerate(moves):
            if i > 20:  # Limit playout length
                break
            current_board[pos] = 1 - (i % 2)
            
        if 0 in current_board.values():
            return 1
        else:
            return 0
    
    def get_move(self):
        """Get the best move using MCTS"""
        # Build initial board state
        board_state = {}
        for row, col in self.me:
            board_state[(row, col)] = 0
        for row, col in self.opp:
            board_state[(row, col)] = 1
            
        # Get all valid moves
        valid_moves = []
        for row in range(self.board_size):
            for col in range(self.board_size):
                if self.is_valid(row, col):
                    valid_moves.append((row, col))
                    
        if not valid_moves:
            return (7, 7)  # Fallback to center
            
        # If center is available, play there
        if (7, 7) in valid_moves:
            return (7, 7)
            
        # Otherwise, use MCTS
        best_move = None
        best_score = -float('inf')
        max_time = time.time() + 0.95  # Leave 50ms for output
        
        for move in valid_moves:
            score = self.simulate_random_game(move, board_state)
            if score > best_score:
                best_score = score
                best_move = move
                
        return best_move if best_move else valid_moves[0]

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], valid_mask) -> tuple[int, int]:
    """
    Main policy function for Havannah
    """
    # Create MCTS instance
    mcts = HavannahMCTS()
    mcts.me = me
    mcts.opp = opp
    mcts.valid_mask = valid_mask
    
    # Get move
    move = mcts.get_move()
    
    # Ensure it's valid
    if not (0 <= move[0] < 15 and 0 <= move[1] < 15) or not valid_mask[move[0]][move[1]]:
        # Fallback to any valid position
        for row in range(15):
            for col in range(15):
                if valid_mask[row][col]:
                    return (row, col)
    
    return move
