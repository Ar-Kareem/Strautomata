```python
from typing import List, Tuple, Optional, Dict

LINES: List[List[int]] = []
IMP: List[int] = []
memo: Dict[Tuple[Tuple[int, ...], int], int] = {}

def get_lines(n: int = 3) -> List[List[int]]:
    lines = []
    nn = n * n
    # x-direction lines
    for z in range(n):
        for y in range(n):
            lines.append([z * nn + y * n + x for x in range(n)])
    # y-direction lines
    for z in range(n):
        for x in range(n):
            lines.append([z * nn + y * n + x for y in range(n)])
    # z-direction lines
    for y in range(n):
        for x in range(n):
            lines.append([z * nn + y * n + x for z in range(n)])
    # xy-plane diagonals (fixed