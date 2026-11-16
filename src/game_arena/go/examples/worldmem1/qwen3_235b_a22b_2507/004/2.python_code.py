
import numpy as np
from typing import List, Tuple, Dict, Set

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    # Initialize the board
    board = np.zeros((19, 19), dtype=int)
    my_stone = 1
    opp_stone = 2

    # Fill the board
    for r, c in me:
        board[r-1, c-1] = my_stone
    for r, c in opponent:
        board[r-1, c-1] = opp_stone

    # Directions for adjacent intersections
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]

    def get_group_and_liberties(r: int, c: int) -> Tuple[Set[Tuple[int, int]], int]:
        """Returns the group (set of stones) and liberty count for a stone at (r, c)."""
        if board[r, c] == 0:
            return set(), 0
        color = board[r, c]
        visited = set()
        group = set()
        stack = [(r, c)]
        liberties = 0

        while stack:
            cr, cc = stack.pop()
            if (cr, cc) in visited:
                continue
            visited.add((cr, cc))
            if board[cr, cc] == 0:
                liberties += 1
            elif board[cr, cc] == color:
                group.add((cr, cc))
                for dr, dc in directions:
                    nr, nc = cr + dr, cc + dc
                    if 0 <= nr < 19 and 0 <= nc < 19 and (nr, nc) not in visited:
                        stack.append((nr, nc))
        return group, liberties

    def count_liberties(r: int, c: int) -> int:
        """Count liberties of the group that would be formed if placing at (r, c)."""
        if board[r, c] != 0:
            return 0
        board[r, c] = my_stone
        _, libs = get_group_and_liberties(r, c)
        board[r, c] = 0
        return libs

    def is_legal(r: int, c: int) -> bool:
        """Check if move at (r,c) is legal (not suicidal, respects ko - simplified)."""
        if board[r, c] != 0:
            return False
        # Check for capture
        board[r, c] = my_stone
        for dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == opp_stone:
                _, libs = get_group_and_liberties(nr, nc)
                if libs == 0:
                    board[r, c] = 0
                    return True  # Can capture
        # Otherwise, must not self-capture
        _, libs = get_group_and_liberties(r, c)
        board[r, c] = 0
        if libs > 0:
            return True
        return False

    def capture_opponent_moves() -> List[Tuple[int, int]]:
        """Find all moves that capture opponent stones."""
        captures = []
        for r in range(19):
            for c in range(19):
                if board[r, c] == 0:
                    board[r, c] = my_stone
                    for dr, dc in directions:
                        nr, nc = r + dr, c + dc
                        if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == opp_stone:
                            _, libs = get_group_and_liberties(nr, nc)
                            if libs == 0:
                                captures.append((r, c))
                                break
                    board[r, c] = 0
        return captures

    def endangered_own_groups() -> List[Tuple[int, int]]:
        """Find groups with 1 liberty and return liberties (vital points) to save them."""
        endangered = []
        visited = set()
        for r in range(19):
            for c in range(19):
                if (r, c) not in visited and board[r, c] == my_stone:
                    group, libs = get_group_and_liberties(r, c)
                    if libs == 1:
                        # Find the shared liberty
                        for dr, dc in directions:
                            for gr, gc in group:
                                nr, nc = gr + dr, gc + dc
                                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                                    if is_legal(nr, nc):
                                        # Check if playing here increases liberty
                                        endangered.append((nr, nc))
                        visited.update(group)
        return endangered

    # Strategy:
    # 1. If we can capture, do it
    captures = capture_opponent_moves()
    if captures:
        # Prioritize captures that capture more stones
        capture_scores = []
        for r, c in captures:
            score = 0
            for dr, dc in directions:
                nr, nc = r + dr, c + dc
                if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == opp_stone:
                    group, _ = get_group_and_liberties(nr, nc)
                    if len(group) > 0:
                        _, libs_after = get_group_and_liberties(nr, nc)
                        if libs_after == 0:  # About to be captured
                            score += len(group)
            capture_scores.append((score, r, c))
        _, r, c = max(capture_scores)
        return (r+1, c+1), memory

    # 2. If we have endangered groups, try to save them
    endangered_liberties = endangered_own_groups()
    if endangered_liberties:
        # Count how many groups each liberty saves
        liberty_priority = {}
        for r, c in endangered_liberties:
            key = (r, c)
            liberty_priority[key] = liberty_priority.get(key, 0) + 1
        action_r, action_c = max(liberty_priority.keys(), key=lambda x: liberty_priority[x])
        return (action_r+1, action_c+1), memory

    # 3. Play near own stones for influence and connection
    candidate_moves = []
    for mr, mc in me:
        for dr, dc in directions:
            nr, nc = mr + dr, mc + dc
            if 0 <= nr < 19 and 0 <= nc < 19 and board[nr, nc] == 0:
                liberties = count_liberties(nr, nc)
                if is_legal(nr, nc):
                    # Bonus for proximity and liberties
                    score = 0
                    # Count neighbors (friends and enemies)
                    friend_count = 0
                    opp_count = 0
                    for dr2, dc2 in directions:
                        nr2, nc2 = nr + dr2, nc + dc2
                        if 0 <= nr2 < 19 and 0 <= nc2 < 19:
                            if board[nr2, nc2] == my_stone:
                                friend_count += 1
                            elif board[nr2, nc2] == opp_stone:
                                opp_count += 1
                    score = friend_count * 2 - opp_count + liberties
                    candidate_moves.append((score, nr, nc))
    if candidate_moves:
        # Get the best move
        best_score = max(candidate_moves, key=lambda x: x[0])[0]
        best_moves = [move for move in candidate_moves if move[0] == best_score]
        # Prefer center-biased
        center_r, center_c = 9, 9
        best_move = max(best_moves, key=lambda x: -(abs(x[1]-center_r)**2 + abs(x[2]-center_c)**2))
        _, r, c = best_move
        return (r+1, c+1), memory

    # 4. If no other good options, play near opponent or center
    for r in range(19):
        for c in range(19):
            if board[r, c] == 0:
                if is_legal(r, c):
                    return (r+1, c+1), memory

    # 5. If nothing else, pass
    return (0, 0), memory
