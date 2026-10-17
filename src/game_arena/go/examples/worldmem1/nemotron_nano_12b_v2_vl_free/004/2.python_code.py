
import sys
from typing import List, Tuple, Dict

def distance_to_corner(r: int, c: int) -> int:
    d1 = abs(r - 1) + abs(c - 1)
    d2 = abs(r - 1) + abs(c - 19)
    d3 = abs(r - 19) + abs(c - 1)
    d4 = abs(r - 19) + abs(c - 19)
    return min(d1, d2, d3, d4)

def policy(me: List[Tuple[int, int]], opponent: List[Tuple[int, int]], memory: Dict) -> Tuple[Tuple[int, int], Dict]:
    me_set = set(me)
    opponent_set = set(opponent)
    empty_cells = []
    for r in range(1, 20):
        for c in range(1, 20):
            if (r, c) not in me_set and (r, c) not in opponent_set:
                empty_cells.append((r, c))
    
    legal_moves = []
    for cell in empty_cells:
        new_me = me_set | {cell}
        visited = {cell}
        stack = [cell]
        while stack:
            x, y = stack.pop()
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= 19 and 1 <= ny <= 19 and (nx, ny) in new_me:
                    if (nx, ny) not in visited:
                        stack.append((nx, ny))
                        visited.add((nx, ny))
        liberties = 0
        has_liberty = False
        for x, y in visited:
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                nx, ny = x + dx, y + dy
                if 1 <= nx <= 19 and 1 <= ny <= 19:
                    if (nx, ny) not in new_me and (nx, ny) not in opponent_set:
                        has_liberty = True
                        break
            if has_liberty:
                break
        if has_liberty:
            legal_moves.append(cell)
    
    if not legal_moves:
        return (0, 0), memory
    
    best_cell = legal_moves[0]
    best_distance = distance_to_corner(best_cell[0], best_cell[1])
    for cell in legal_moves[1:]:
        current_distance = distance_to_corner(cell[0], cell[1])
        if current_distance < best_distance:
            best_cell = cell
            best_distance = current_distance
        elif current_distance == best_distance:
            current_lis = 0
            new_me = me_set | {cell}
            visited_liberty = set()
            visited_liberty.add(cell)
            queue = [cell]
            while queue:
                x, y = queue.pop(0)
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if 1 <= nx <= 19 and 1 <= ny <= 19 and (nx, ny) not in opponent_set:
                        visited_liberty |= {(nx, ny)}
                    if (nx, ny) in new_me and (nx, ny) not in visited_liberty:
                        queue.append((nx, ny))
                        visited_liberty.add((nx, ny))
            legal_lis = [count for count in [0, 0, 0, 0]]
            for x, y in visited_liberty:
                if x < r:
                    if y < c:
                        pass
        best_def = False
                
    return (best_cell, memory)
