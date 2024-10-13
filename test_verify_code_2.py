

def test_hassan():
    t = '''
    def solve(input_grid):\n    # Get the dimensions of the input grid\n    rows = len(input_grid)\n    cols = len(input_grid[0])\n    \n    # Initialize the output grid with zeros\n    output_grid = [[0 for _ in range(cols)] for _ in range(rows)]\n    \n    # Find the blue square (value 1) and red square (value 2) in the input grid\n    blue_coords = []\n    red_coords = []\n    for r in range(rows):\n        for c in range(cols):\n            if input_grid[r][c] == 1:\n                blue_coords.append((r, c))\n            elif input_grid[r][c] == 2:\n                red_coords.append((r, c))\n    \n    # Determine the bounding box for the blue square\n    min_r_blue = min(r for r, c in blue_coords)\n    max_r_blue = max(r for r, c in blue_coords)\n    min_c_blue = min(c for r, c in blue_coords)\n    max_c_blue = max(c for r, c in blue_coords)\n    \n    # Determine the bounding box for the red square\n    min_r_red = min(r for r, c in red_coords)\n    max_r_red = max(r for r, c in red_coords)\n    min_c_red = min(c for r, c in red_coords)\n    max_c_red = max(c for r, c in red_coords)\n    \n    # Stretch the blue square vertically to form a rectangle\n    for r in range(min_r_blue, max_r_blue + 1):\n        for c in range(min_c_blue, max_c_blue + 1):\n            for new_r in range(min_r_blue, rows - 1):\n                output_grid[new_r][c] = 1\n    \n    # Stretch the red square vertically to form a rectangle\n    for r in range(min_r_red, max_r_red + 1):\n        for c in range(min_c_red, max_c_red + 1):\n            for new_r in range(min_r_red, rows - 1):\n                output_grid[new_r][c] = 2\n    \n    return output_grid\n\n# Example usage\ninput_grid = [\n    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],\n    [0, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0],\n    [0, 2, 1, 1, 2, 0, 0, 0, 0, 0, 0],\n    [0, 2, 1, 1, 2, 0, 0, 0, 0, 0, 0],\n    [0, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0],\n    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],\n    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],\n    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],\n    [0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0],\n    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],\n    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]\n]\n\noutput_grid = solve(input_grid)\nfor row in output_grid:\n    print(row)\n
    '''
    print(t)

def solve(input_grid):

    # Get the dimensions of the input grid
    rows = len(input_grid)
    cols = len(input_grid[0])

    # Initialize the output grid with zeros
    output_grid = [[0 for _ in range(cols)] for _ in range(rows)]

    # Find the blue square (value 1) and red square (value 2) in the input grid
    blue_coords = []
    red_coords = []
    for r in range(rows):
        for c in range(cols):
            if input_grid[r][c] == 1:
                blue_coords.append((r, c))
            elif input_grid[r][c] == 2:
                red_coords.append((r, c))

    # Determine the bounding box for the blue square
    min_r_blue = min(r for r, c in blue_coords)
    max_r_blue = max(r for r, c in blue_coords)
    min_c_blue = min(c for r, c in blue_coords)
    max_c_blue = max(c for r, c in blue_coords)

    # Determine the bounding box for the red square
    min_r_red = min(r for r, c in red_coords)
    max_r_red = max(r for r, c in red_coords)
    min_c_red = min(c for r, c in red_coords)
    max_c_red = max(c for r, c in red_coords)

    # Stretch the blue square vertically to form a rectangle
    for r in range(min_r_blue, max_r_blue + 1):
        for c in range(min_c_blue, max_c_blue + 1):
            for new_r in range(min_r_blue, rows - 1):
                output_grid[new_r][c] = 1

    # Stretch the red square vertically to form a rectangle
    for r in range(min_r_red, max_r_red + 1):
        for c in range(min_c_red, max_c_red + 1):
            for new_r in range(min_r_red, rows - 1):
                output_grid[new_r][c] = 2

    return output_grid


# Example usage
input_grid = [
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0],
    [0, 2, 1, 1, 2, 0, 0, 0, 0, 0, 0],
    [0, 2, 1, 1, 2, 0, 0, 0, 0, 0, 0],
    [0, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 8, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
]

output_grid = solve(input_grid)
for row in output_grid:
    print(row)