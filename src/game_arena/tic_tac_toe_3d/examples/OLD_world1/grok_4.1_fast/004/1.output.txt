```python
WIN_LINES = []

def idx(z, y, x):
    return z * 9 + y * 3 + x

# Straight lines along x
for z in range(3):
    for y in range(3):
        WIN_LINES.append([idx(z, y, 0), idx(z, y, 1), idx(z, y, 2)])

# Straight lines along y
for z