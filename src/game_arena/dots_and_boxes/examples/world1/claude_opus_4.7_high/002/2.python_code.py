
import numpy as np

def policy(horizontal: np.ndarray, vertical: np.ndarray, capture: np.ndarray) -> str:
    H = horizontal.copy().astype(int)
    V = vertical.copy().astype(int)

    def count_sides(H, V, r, c):
        return int(H[r,c]!=0) + int(H[r+1,c]!=0) + int(V[r,c]!=0) + int(V[r,c+1]!=0)

    def adj_boxes(d, r, c):
        boxes = []
        if d == 'H':
            if r > 0: boxes.append((r-1, c))
            if r < 4: boxes.append((r, c))
        else:
            if c > 0: boxes.append((r, c-1))
            if c < 4: boxes.append((r, c))
        return boxes

    def apply_edge(H, V, d, r, c):
        if d == 'H': H[r,c] = 1
        else: V[r,c] = 1

    def classify(H, V, d, r, c):
        H2 = H.copy(); V2 = V.copy()
        apply_edge(H2, V2, d, r, c)
        comp = 0; gives = 0
        for br, bc in adj_boxes(d, r, c):
            s = count_sides(H2, V2, br, bc)
            if s == 4: comp += 1
            elif s == 3: gives += 1
        return comp, gives

    def simulate_take(H, V):
        H = H.copy(); V = V.copy()
        taken = 0
        while True:
            found = False
            for br in range(4):
                for bc in range(4):
                    if count_sides(H, V, br, bc) == 3:
                        if H[br,bc] == 0: H[br,bc] = 1
                        elif H[br+1,bc] == 0: H[br+1,bc] = 1
                        elif V[br,bc] == 0: V[br,bc] = 1
                        else: V[br,bc+1] = 1
                        taken += 1
                        found = True
                        break
                if found: break
            if not found: break
        return taken, H, V

    legal = []
    for r in range(5):
        for c in range(4):
            if H[r,c] == 0:
                legal.append(('H', r, c))
    for r in range(4):
        for c in range(5):
            if V[r,c] == 0:
                legal.append(('V', r, c))

    if not legal:
        return "0,0,H"

    completing = []
    safe = []
    unsafe = []
    for d, r, c in legal:
        comp, gives = classify(H, V, d, r, c)
        if comp > 0:
            completing.append((d, r, c))
        elif gives > 0:
            unsafe.append((d, r, c))
        else:
            safe.append((d, r, c))

    if completing:
        # Pick completing move that starts with the highest chain gain
        best = None; best_score = -1
        for d, r, c in completing:
            H2 = H.copy(); V2 = V.copy()
            apply_edge(H2, V2, d, r, c)
            extra, _, _ = simulate_take(H2, V2)
            score = 1 + extra
            if score > best_score:
                best_score = score
                best = (d, r, c)
        d, r, c = best
        return f"{r},{c},{d}"

    if safe:
        # Prefer moves that don't push adjacent boxes to 2 sides
        best = None; best_val = 10**9
        for d, r, c in safe:
            H2 = H.copy(); V2 = V.copy()
            apply_edge(H2, V2, d, r, c)
            val = 0
            for br, bc in adj_boxes(d, r, c):
                s2 = count_sides(H2, V2, br, bc)
                if s2 == 2: val += 5
                elif s2 == 1: val += 1
            if val < best_val:
                best_val = val
                best = (d, r, c)
        d, r, c = best
        return f"{r},{c},{d}"

    # Must open a chain - pick shortest
    best = None; best_len = 10**9
    for d, r, c in unsafe:
        H2 = H.copy(); V2 = V.copy()
        apply_edge(H2, V2, d, r, c)
        length, _, _ = simulate_take(H2, V2)
        if length < best_len:
            best_len = length
            best = (d, r, c)
    d, r, c = best if best else unsafe[0]
    return f"{r},{c},{d}"
