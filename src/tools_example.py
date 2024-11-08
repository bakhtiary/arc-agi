tools_example = {'identify_shapes': {'signature': 'identify_shapes(grid: List[List[int]]) -> List[List[Tuple[int, int, int]]]', 'code': '''from typing import List, Tuple

def identify_shapes(grid: List[List[int]]) -> List[List[Tuple[int, int, int]]]:
    def flood_fill(x: int, y: int, color: int, visited: List[List[bool]]) -> List[Tuple[int, int, int]]:
        stack = [(x, y)]
        shape = []
        while stack:
            cx, cy = stack.pop()
            if visited[cx][cy]:
                continue
            visited[cx][cy] = True
            shape.append((cx, cy, color))
            # Check all 4 directions (up, down, left, right)
            for nx, ny in [(cx-1, cy), (cx+1, cy), (cx, cy-1), (cx, cy+1)]:
                if 0 <= nx < len(grid) and 0 <= ny < len(grid[0]) and not visited[nx][ny] and grid[nx][ny] == color:
                    stack.append((nx, ny))
        return shape

    if not grid or not grid[0]:
        return []

    visited = [[False for _ in range(len(grid[0]))] for _ in range(len(grid))]
    shapes = []

    for x in range(len(grid)):
        for y in range(len(grid[0])):
            if not visited[x][y]:
                color = grid[x][y]
                shape = flood_fill(x, y, color, visited)
                if shape:
                    shapes.append(shape)

    return shapes

# Test cases
def test_identify_shapes():
    grid1 = [
        [1, 1, 0, 0],
        [1, 0, 0, 2],
        [0, 0, 2, 2],
        [3, 3, 3, 2]
    ]
    expected1 = [
        [(0, 0, 1), (0, 1, 1), (1, 0, 1)],
        [(0, 2, 0), (0, 3, 0), (1, 1, 0), (1, 2, 0), (2, 0, 0), (2, 1, 0)],
        [(1, 3, 2), (2, 2, 2), (2, 3, 2), (3, 3, 2)],
        [(3, 0, 3), (3, 1, 3), (3, 2, 3)]
    ]
    result1 = identify_shapes(grid1)
    assert sorted([sorted(shape) for shape in result1]) == sorted([sorted(shape) for shape in expected1]), f"Test 1 failed: {result1}"

    grid2 = [
        [0, 0, 0],
        [0, 1, 1],
        [0, 1, 2]
    ]
    expected2 = [
        [(0, 0, 0), (0, 1, 0), (0, 2, 0), (1, 0, 0), (2, 0, 0)],
        [(1, 1, 1), (1, 2, 1), (2, 1, 1)],
        [(2, 2, 2)]
    ]
    result2 = identify_shapes(grid2)
    assert sorted([sorted(shape) for shape in result2]) == sorted([sorted(shape) for shape in expected2]), f"Test 2 failed: {result2}"

    grid3 = [
        [5, 5, 5],
        [5, 5, 5],
        [5, 5, 5]
    ]
    expected3 = [
        [(0, 0, 5), (0, 1, 5), (0, 2, 5), (1, 0, 5), (1, 1, 5), (1, 2, 5), (2, 0, 5), (2, 1, 5), (2, 2, 5)]
    ]
    result3 = identify_shapes(grid3)
    assert sorted([sorted(shape) for shape in result3]) == sorted([sorted(shape) for shape in expected3]), f"Test 3 failed: {result3}"

    print("All tests passed!")

test_identify_shapes()'''},
    'is_hollow_square': {'signature': 'is_hollow_square(shape: List[Tuple[int, int, int]]) -> bool:', 'code': '''from typing import List, Tuple

def is_hollow_square(shape: List[Tuple[int, int, int]]) -> bool:
    if not shape:
        return False

    # Extract all x and y coordinates
    x_coords = [x for x, y, color in shape]
    y_coords = [y for x, y, color in shape]

    # Determine the bounding box of the shape
    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    # Check if the bounding box forms a square
    if (max_x - min_x) != (max_y - min_y):
        return False

    # Create a set of all points in the shape
    shape_points = set((x, y) for x, y, color in shape)

    # Check the border of the square
    for x in range(min_x, max_x + 1):
        if (x, min_y) not in shape_points or (x, max_y) not in shape_points:
            return False

    for y in range(min_y, max_y + 1):
        if (min_x, y) not in shape_points or (max_x, y) not in shape_points:
            return False

    # Check the inner part of the square
    for x in range(min_x + 1, max_x):
        for y in range(min_y + 1, max_y):
            if (x, y) in shape_points:
                return False

    return True

# Test cases
def test_is_hollow_square():
    # Test case 1: A simple 3x3 hollow square
    shape1 = [
        (1, 1, 1), (1, 2, 1), (1, 3, 1),
        (2, 1, 1),         (2, 3, 1),
        (3, 1, 1), (3, 2, 1), (3, 3, 1)
    ]
    assert is_hollow_square(shape1) == True

    # Test case 2: A filled 3x3 square (not hollow)
    shape2 = [
        (1, 1, 1), (1, 2, 1), (1, 3, 1),
        (2, 1, 1), (2, 2, 1), (2, 3, 1),
        (3, 1, 1), (3, 2, 1), (3, 3, 1)
    ]
    assert is_hollow_square(shape2) == False

    # Test case 3: A non-square shape
    shape3 = [
        (1, 1, 1), (1, 2, 1), (1, 3, 1),
        (2, 1, 1),         (2, 3, 1)
    ]
    assert is_hollow_square(shape3) == False

    # Test case 4: A 4x4 hollow square
    shape4 = [
        (0, 0, 1), (0, 1, 1), (0, 2, 1), (0, 3, 1),
        (1, 0, 1),                     (1, 3, 1),
        (2, 0, 1),                     (2, 3, 1),
        (3, 0, 1), (3, 1, 1), (3, 2, 1), (3, 3, 1)
    ]
    assert is_hollow_square(shape4) == True

    # Test case 5: An empty shape
    shape5 = []
    assert is_hollow_square(shape5) == False

    print("All tests passed.")

# Run the tests
test_is_hollow_square()'''},
    'change_color_of_shape': {'signature': 'change_color_of_shape(shape: List[Tuple[int, int, int]], new_color: int) -> List[Tuple[int, int, int]]', 'code': '''from typing import List, Tuple

def change_color_of_shape(shape: List[Tuple[int, int, int]], new_color: int) -> List[Tuple[int, int, int]]:
    # Create a new list with the updated color
    updated_shape = [(x, y, new_color) for x, y, _ in shape]
    return updated_shape

# Test cases
def test_change_color_of_shape():
    # Test case 1: Simple square shape
    shape1 = [(0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]
    new_color1 = 2
    expected1 = [(0, 0, 2), (0, 1, 2), (1, 0, 2), (1, 1, 2)]
    assert change_color_of_shape(shape1, new_color1) == expected1, "Test case 1 failed"

    # Test case 2: L-shape
    shape2 = [(0, 0, 3), (1, 0, 3), (2, 0, 3), (2, 1, 3)]
    new_color2 = 4
    expected2 = [(0, 0, 4), (1, 0, 4), (2, 0, 4), (2, 1, 4)]
    assert change_color_of_shape(shape2, new_color2) == expected2, "Test case 2 failed"

    # Test case 3: Single pixel shape
    shape3 = [(5, 5, 7)]
    new_color3 = 9
    expected3 = [(5, 5, 9)]
    assert change_color_of_shape(shape3, new_color3) == expected3, "Test case 3 failed"

    # Test case 4: No change in color
    shape4 = [(3, 3, 5), (3, 4, 5)]
    new_color4 = 5
    expected4 = [(3, 3, 5), (3, 4, 5)]
    assert change_color_of_shape(shape4, new_color4) == expected4, "Test case 4 failed"

    print("All test cases passed!")

# Run the tests
test_change_color_of_shape()'''},
    'apply_transformation_to_grid': {'signature': 'apply_transformation_to_grid(grid: List[List[int]], shapes: List[List[Tuple[int, int, int]]], new_color: int) -> List[List[int]]', 'code': '''from typing import List, Tuple

def apply_transformation_to_grid(grid: List[List[int]], shapes: List[List[Tuple[int, int, int]]], new_color: int) -> List[List[int]]:
    # Create a copy of the grid to avoid modifying the original grid
    transformed_grid = [row[:] for row in grid]

    # Iterate over each shape
    for shape in shapes:
        # Iterate over each cell in the shape
        for x, y, color in shape:
            # Check if the current cell in the grid matches the shape's color
            if 0 <= x < len(grid) and 0 <= y < len(grid[0]) and grid[x][y] == color:
                # Apply the new color
                transformed_grid[x][y] = new_color

    return transformed_grid

# Test cases
def test_apply_transformation_to_grid():
    # Test case 1: Simple 3x3 grid with one shape
    grid1 = [
        [0, 1, 2],
        [1, 1, 2],
        [2, 2, 2]
    ]
    shapes1 = [
        [(0, 1, 1), (1, 1, 1)]  # Shape that matches color 1
    ]
    new_color1 = 9
    expected1 = [
        [0, 9, 2],
        [1, 9, 2],
        [2, 2, 2]
    ]
    assert apply_transformation_to_grid(grid1, shapes1, new_color1) == expected1

    # Test case 2: 4x4 grid with two shapes
    grid2 = [
        [0, 1, 2, 3],
        [1, 1, 2, 3],
        [2, 2, 2, 3],
        [3, 3, 3, 3]
    ]
    shapes2 = [
        [(0, 1, 1), (1, 1, 1)],  # Shape that matches color 1
        [(2, 2, 2), (2, 1, 2)]   # Shape that matches color 2
    ]
    new_color2 = 8
    expected2 = [
        [0, 8, 2, 3],
        [1, 8, 2, 3],
        [2, 8, 8, 3],
        [3, 3, 3, 3]
    ]
    assert apply_transformation_to_grid(grid2, shapes2, new_color2) == expected2

    # Test case 3: No matching shapes
    grid3 = [
        [0, 1, 2],
        [1, 1, 2],
        [2, 2, 2]
    ]
    shapes3 = [
        [(0, 0, 3)]  # Shape that does not match any color
    ]
    new_color3 = 7
    expected3 = [
        [0, 1, 2],
        [1, 1, 2],
        [2, 2, 2]
    ]
    assert apply_transformation_to_grid(grid3, shapes3, new_color3) == expected3

    print("All test cases passed!")

# Run the tests
test_apply_transformation_to_grid()'''}
}