
import random
import time

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    A Monte Carlo Tree Search (MCTS) based policy for Hex.
    """
    board_size = 11
    start_time = time.time()
    time_limit = 0.9  # seconds
    max_iterations = 1000

    def get_empty_cells(me, opp):
        all_cells = set((r, c) for r in range(board_size) for c in range(board_size))
        my_cells = set(me)
        opp_cells = set(opp)
        return list(all_cells - my_cells - opp_cells)
    
    def get_neighbors(row, col):
        neighbors = []
        for r in range(max(0, row - 1), min(board_size, row + 2)):
            for c in range(max(0, col - 1), min(board_size, col + 2)):
                if (r, c) != (row, col) and (r, c) != (row - 1, col -1) and (r,c) != (row + 1, col + 1):
                    neighbors.append((r, c))
        return neighbors

    def check_win(board, color):
        visited = set()
        
        def dfs(row, col):
            if (row, col) in visited:
                return False
            if row < 0 or row >= board_size or col < 0 or col >= board_size:
                return False
            if (row, col) not in board:
                return False
            
            visited.add((row, col))
            if color == 'b':
                if row == board_size - 1:
                    return True
            else:
                if col == board_size - 1:
                    return True
            
            for r, c in get_neighbors(row, col):
                if (r,c) in board:
                  if dfs(r,c):
                    return True
            return False

        if color == 'b':
            for col in range(board_size):
                if (0, col) in board:
                    visited = set()
                    if dfs(0, col):
                        return True
        else:
            for row in range(board_size):
                if (row, 0) in board:
                    visited = set()
                    if dfs(row, 0):
                        return True
        return False


    class Node:
        def __init__(self, state, parent=None, move=None):
            self.state = state  # (me, opp)
            self.parent = parent
            self.move = move  # The move that led to this state
            self.children = {}  # move: Node
            self.wins = 0
            self.visits = 0
            self.untried_moves = get_empty_cells(self.state[0], self.state[1])

        def expand(self, move):
            me, opp = self.state
            if len(me) == len(opp):
                new_me = me + [move]  # It's my turn
                new_opp = opp

            else:
                new_me = me
                new_opp = opp + [move] # Its opponent's turn
                
            new_state = (new_me, new_opp)
            child_node = Node(new_state, parent=self, move=move)
            self.children[move] = child_node
            self.untried_moves.remove(move)
            return child_node

        def select_child(self, exploration_weight=1.0):
            """Select a child node based on UCT value."""
            best_score = -float('inf')
            best_child = None
            for move, child in self.children.items():
                exploitation_term = child.wins / (child.visits + 1e-6)  # Avoid division by zero
                exploration_term = exploration_weight * (2*math.log(self.visits + 1) / (child.visits + 1e-6))**0.5
                uct_value = exploitation_term + exploration_term
                if uct_value > best_score:
                    best_score = uct_value
                    best_child = child
            
            return best_child
        
        def update(self, result):
          self.visits += 1
          self.wins += result
          

    import math

    def mcts(me, opp, color, time_limit=1.0, max_iterations = 1000):
        """Monte Carlo Tree Search."""
        root = Node((me, opp))
        
        iterations = 0
        while time.time() - start_time < time_limit and iterations < max_iterations:
            node = root

            # Selection
            while node.untried_moves == [] and node.children != {}:  #Fully expanded node
                node = node.select_child()
            
            # Expansion
            if node.untried_moves:
                move = random.choice(node.untried_moves)
                node = node.expand(move)
            
            # Simulation
            me_sim, opp_sim = node.state
            empty_cells = get_empty_cells(me_sim, opp_sim)
            turn = len(me_sim) == len(opp_sim) #True if my turn, false if opp turn

            while empty_cells:
                move = random.choice(empty_cells)
                if turn:
                    me_sim = me_sim + [move]
                else:
                    opp_sim = opp_sim + [move]
                
                empty_cells = get_empty_cells(me_sim, opp_sim)
                turn = not turn
                
                if check_win(set(me_sim), color):
                  break
                if check_win(set(opp_sim), 'w' if color == 'b' else 'b'):
                    break

            # Backpropagation
            if check_win(set(me_sim), color):
                reward = 1
            elif check_win(set(opp_sim), 'w' if color == 'b' else 'b'):
                reward = 0
            else:
                reward = 0.5


            while node is not None:
              node.update(reward)
              node = node.parent
            
            iterations += 1 #increment iteration count

        # Choose the best move from the root node
        best_move = None
        best_win_rate = -1

        for move, child in root.children.items():
            win_rate = child.wins / child.visits
            if win_rate > best_win_rate:
                best_win_rate = win_rate
                best_move = move

        if best_move is None:
            # Fallback strategy if no moves have been explored
            empty_cells = get_empty_cells(me, opp)
            if empty_cells:
                best_move = random.choice(empty_cells)
            else:
                # Should never happen if the board isn't full
                best_move = (0, 0) # Return a default move if board is full

        return best_move

    best_move = mcts(me, opp, color, time_limit, max_iterations)
    return best_move
