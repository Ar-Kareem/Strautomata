
import numpy as np
from collections import deque

def policy(board: list[list[int]]) -> tuple[int, int]:
    board = np.array(board, dtype=int)
    n = 10
    
    # Find all unknown cells
    unknown = np.where(board == 0)
    unknown_cells = list(zip(unknown[0], unknown[1]))
    
    # Find all hits
    hits = np.where(board == 1)
    hit_cells = list(zip(hits[0], hits[1]))
    
    # If no hits yet, use checkerboard pattern for efficient coverage
    if len(hit_cells) == 0:
        # Prefer cells where (row + col) % 2 == 0 (checkerboard)
        checkerboard_cells = [(r, c) for r, c in unknown_cells if (r + c) % 2 == 0]
        if checkerboard_cells:
            # Pick the first one (or randomize if desired, but deterministic is fine)
            return checkerboard_cells[0]
        else:
            # If checkerboard exhausted (unlikely), fall back to any unknown
            return unknown_cells[0]
    
    # We have at least one hit - now target around hits
    # Build a priority queue of candidate cells based on adjacency to hits
    
    candidates = []
    visited = set(hit_cells)
    
    # For each hit, check neighbors
    for hr, hc in hit_cells:
        for dr, dc in [(0, 1), (1, 0), (0, -1), (-1, 0)]:  # 4 directions
            nr, nc = hr + dr, hc + dc
            if 0 <= nr < n and 0 <= nc < n and board[nr][nc] == 0:
                candidates.append((nr, nc))
                visited.add((nr, nc))
    
    # If we have adjacent candidates, choose among them
    if candidates:
        # We can use simple heuristic: pick the first candidate
        # But we can also add probability weighting based on ship length possibilities
        
        # Simple approach: pick the first candidate (deterministic and efficient)
        return candidates[0]
    
    # If no adjacent candidates, we might have isolated hits or need to restart hunt
    # Try to find any remaining unknown cell that might be part of a ship
    # Use probability estimation: count how many ways each unknown cell could be part of a remaining ship
    
    # Determine remaining ship sizes (based on hits and misses)
    # Assuming ships: [5, 4, 3, 3, 2]
    ship_lengths = [5, 4, 3, 3, 2]
    hit_count = len(hit_cells)
    # Estimate remaining ship lengths by assuming each hit belongs to a ship
    # This is an approximation - we don't know which hit belongs to which ship
    # But we can use the max possible remaining
    # For simplicity: if we have 0 hits, use checkerboard
    # If we have hits, we assume at least one ship is partially hit, so we search the board intelligently
    
    # Fall back to checkerboard again but with remaining unknowns
    remaining_unknowns = [(r, c) for r, c in unknown_cells if (r + c) % 2 == 0]
    if remaining_unknowns:
        return remaining_unknowns[0]
    else:
        # Last resort: any unknown cell
        return unknown_cells[0]
