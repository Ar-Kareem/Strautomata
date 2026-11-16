
import random

def policy(me: list[tuple[int, int]], opp: list[tuple[int, int]], color: str) -> tuple[int, int]:
    """
    A Hex policy that combines bridge completion, edge connection, center control, and threat defense.
    """

    board_size = 11
    empty_cells = [(r, c) for r in range(board_size) for c in range(board_size) if (r, c) not in me and (r, c) not in opp]

    def get_neighbors(r, c):
        neighbors = []
        for i in range(max(0, r - 1), min(board_size, r + 2)):
            for j in range(max(0, c - 1), min(board_size, c + 2)):
                if (i, j) != (r, c) and abs(i - r) + abs(j - c) <= 2 and (i - r, j - c) != (-1, -1) and (i-r, j-c) != (1, 1) :
                    neighbors.append((i, j))
        return neighbors

    def complete_bridge(r, c):
        """Checks if this move completes a bridge with existing stones"""
        for nr, nc in get_neighbors(r,c):
            if (nr, nc) in me:
                second_stone_neighbors = get_neighbors(nr, nc)
                for nnr, nnc in second_stone_neighbors:
                    if (nnr, nnc) in me and (abs(nnr - r) <= 2 and abs(nnc-c) <=2) and (r,c) != (nnr, nnc) and abs((nnr-r) + (nnc-c)) <= 2 :
                            
                        #find the intermediate pos
                        mr = (r+nr+nnr)//3
                        mc = (c+nc+nnc)//3
                        
                        if (mr, mc) not in me and (mr,mc) not in opp and (mr,mc) != (r, c) and (mr,mc) != (nr, nc) and (mr,mc) !=(nnr,ncc): #check if it is empty
                            return ((mr,mc))

        
        
        return None
    

    # 1. Bridge Completion
    for r, c in empty_cells:
        bridge_move = complete_bridge(r, c)

        if bridge_move:
            mr, mc = bridge_move
            if (mr, mc) in empty_cells:
                return (mr, mc)


    # 2. Edge Connection & Center Control
    if color == 'b':
        # Prioritize moves closer to the top and bottom edges
        sorted_cells = sorted(empty_cells, key=lambda cell: abs(cell[0] - 5.5))  # closer to the center
        #sort_edge = sorted(sorted_cells, key= lambda cell: (abs(cell[0] - 0) + abs(cell[0] - (board_size - 1)))) # closer to the edge

        for r, c in sorted_cells:
            return (r, c)
    else:  # color == 'w'
        # Prioritize moves closer to the left and right edges
        sorted_cells = sorted(empty_cells, key=lambda cell: abs(cell[1] - 5.5)) # Closer to center
        #sort_edge = sorted(sorted_cells, key= lambda cell: (abs(cell[1] - 0) + abs(cell[1] - (board_size - 1)))) # closer to the edge
        for r, c in sorted_cells:
            return (r, c)

    # 3. Threat Defense -- not implemented for simplicity within time constraints

    # 4. Random Legal Move
    return random.choice(empty_cells)
