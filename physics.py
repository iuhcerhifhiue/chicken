import numpy as np
import json

class GolfBall:
    def __init__(self, x, y, mass=0.045, radius=0.02135, kinetic_friction_coefficient=0.1, static_friction_coefficient=0.15):
        self.position = np.array([float(x), float(y)])
        self.velocity = np.array([0.0, 0.0])
        self.acceleration = np.array([0.0, 0.0])
        self.mass = mass # kg (standard golf ball mass)
        self.radius = radius # meters (standard golf ball radius)
        self.kinetic_friction_coefficient = kinetic_friction_coefficient
        self.static_friction_coefficient = static_friction_coefficient
        self.is_moving = False

    def apply_force(self, force):
        self.acceleration += force / self.mass

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt

        # Reset acceleration after applying
        self.acceleration = np.array([0.0, 0.0])

        # Check if ball is moving. A small threshold to account for floating point inaccuracies
        # This will be refined in calculate_physics for stopping.
        if np.linalg.norm(self.velocity) > 1e-4:
            self.is_moving = True
        else:
            self.is_moving = False
            self.velocity = np.array([0.0, 0.0]) # Ensure it's truly stopped


class GolfGreen:
    def __init__(self, elevation_grid, hole_x, hole_y, hole_radius=0.05,
                 gravity_constant=9.81, velocity_threshold_for_hole=0.2,
                 x_min=-10.0, x_max=10.0, y_min=-10.0, y_max=10.0):
        if not isinstance(elevation_grid, np.ndarray) or elevation_grid.ndim != 2:
            raise ValueError("elevation_grid must be a 2D numpy array.")
        self.elevation_grid = elevation_grid
        self.grid_rows, self.grid_cols = elevation_grid.shape # (num_y, num_x)

        self.hole_position = np.array([float(hole_x), float(hole_y)])
        self.hole_radius = hole_radius
        self.gravity_constant = gravity_constant
        self.velocity_threshold_for_hole = velocity_threshold_for_hole
        self.x_min, self.x_max = float(x_min), float(x_max)
        self.y_min, self.y_max = float(y_min), float(y_max)

        # Calculate grid spacing; handle cases where grid_cols or grid_rows is 1
        self.grid_x_spacing = (self.x_max - self.x_min) / (self.grid_cols - 1) if self.grid_cols > 1 else (self.x_max - self.x_min)
        self.grid_y_spacing = (self.y_max - self.y_min) / (self.grid_rows - 1) if self.grid_rows > 1 else (self.y_max - self.y_min)

        # Handle single point grid case for spacing correctly (avoid division by zero if grid_cols/rows is 1)
        if self.grid_cols == 1 and self.grid_rows == 1:
            self.grid_x_spacing = self.x_max - self.x_min if self.x_max != self.x_min else 1.0 # arbitrary non-zero
            self.grid_y_spacing = self.y_max - self.y_min if self.y_max != self.y_min else 1.0 # arbitrary non-zero
        elif self.grid_cols == 1:
            self.grid_x_spacing = self.x_max - self.x_min if self.x_max != self.x_min else 1.0
        elif self.grid_rows == 1:
            self.grid_y_spacing = self.y_max - self.y_min if self.y_max != self.y_min else 1.0


    def get_elevation(self, x, y):
        # Clamp physical coordinates to green boundaries
        x_clamped = np.clip(x, self.x_min, self.x_max)
        y_clamped = np.clip(y, self.y_min, self.y_max)

        # Map physical coordinates to grid indices (0 to grid_cols-1, 0 to grid_rows-1)
        # Note: numpy array indexing is (row, col) which corresponds to (y, x)
        grid_x_float = (x_clamped - self.x_min) / self.grid_x_spacing if self.grid_x_spacing > 0 else 0
        grid_y_float = (y_clamped - self.y_min) / self.grid_y_spacing if self.grid_y_spacing > 0 else 0

        # Handle edge cases for single column/row grids for interpolation
        if self.grid_cols == 1:
            return self.elevation_grid[int(np.clip(grid_y_float, 0, self.grid_rows - 1)), 0]
        if self.grid_rows == 1:
            return self.elevation_grid[0, int(np.clip(grid_x_float, 0, self.grid_cols - 1))]

        # Bilinear interpolation
        x0, y0 = int(grid_x_float), int(grid_y_float)
        x1, y1 = min(x0 + 1, self.grid_cols - 1), min(y0 + 1, self.grid_rows - 1)

        # fractional parts
        fx = grid_x_float - x0
        fy = grid_y_float - y0

        # Get elevations at four corners
        # Ensure y-index is row and x-index is col
        e00 = self.elevation_grid[y0, x0]
        e01 = self.elevation_grid[y0, x1]
        e10 = self.elevation_grid[y1, x0]
        e11 = self.elevation_grid[y1, x1]

        # Interpolate
        e_y0 = e00 * (1 - fx) + e01 * fx
        e_y1 = e10 * (1 - fx) + e11 * fx

        return e_y0 * (1 - fy) + e_y1 * fy


    def get_slope(self, x, y, delta=0.001): # Reduced delta for potentially finer grid
        # Calculate approximate slope (gradient) using central difference
        # Ensure delta is not too small to avoid numerical instability on very flat greens

        # Clamp x, y to green boundaries before calculating slope
        x_clamped = np.clip(x, self.x_min, self.x_max)
        y_clamped = np.clip(y, self.y_min, self.y_max)

        # Adjust delta if it's too large for the grid resolution
        # delta should not exceed half the smallest grid spacing to ensure points remain within interpolation range
        # Also ensure delta is not zero
        effective_delta_x = min(delta, self.grid_x_spacing / 2) if self.grid_x_spacing > 0 else delta
        effective_delta_y = min(delta, self.grid_y_spacing / 2) if self.grid_y_spacing > 0 else delta

        if effective_delta_x == 0: effective_delta_x = delta # Fallback for single-point grids or zero spacing
        if effective_delta_y == 0: effective_delta_y = delta # Fallback for single-point grids or zero spacing


        dz_dx = (self.get_elevation(x_clamped + effective_delta_x, y_clamped) -
                 self.get_elevation(x_clamped - effective_delta_x, y_clamped)) / (2 * effective_delta_x)
        dz_dy = (self.get_elevation(x_clamped, y_clamped + effective_delta_y) -
                 self.get_elevation(x_clamped, y_clamped - effective_delta_y)) / (2 * effective_delta_y)

        # The gradient vector points in the direction of steepest ascent.
        # Gravity pulls in the direction of steepest descent.
        return np.array([-dz_dx, -dz_dy])

    def to_json(self, filepath):
        """Saves the GolfGreen configuration to a JSON file."""
        config = {
            "elevation_grid": self.elevation_grid.tolist(), # Convert numpy array to list
            "hole_position": self.hole_position.tolist(),
            "hole_radius": self.hole_radius,
            "gravity_constant": self.gravity_constant,
            "velocity_threshold_for_hole": self.velocity_threshold_for_hole,
            "x_min": self.x_min,
            "x_max": self.x_max,
            "y_min": self.y_min,
            "y_max": self.y_max,
        }
        with open(filepath, 'w') as f:
            json.dump(config, f, indent=4)

    @classmethod
    def from_json(cls, filepath):
        """Loads a GolfGreen configuration from a JSON file."""
        with open(filepath, 'r') as f:
            config = json.load(f)

        elevation_grid = np.array(config["elevation_grid"])
        hole_x, hole_y = config["hole_position"]
        return cls(elevation_grid=elevation_grid,
                   hole_x=hole_x,
                   hole_y=hole_y,
                   hole_radius=config.get("hole_radius", 0.05),
                   gravity_constant=config.get("gravity_constant", 9.81),
                   velocity_threshold_for_hole=config.get("velocity_threshold_for_hole", 0.2),
                   x_min=config.get("x_min", -10.0),
                   x_max=config.get("x_max", 10.0),
                   y_min=config.get("y_min", -10.0),
                   y_max=config.get("y_max", 10.0))


def calculate_physics(ball: GolfBall, green: GolfGreen, dt: float):
    # Calculate gravitational force due to slope
    slope_vector = green.get_slope(ball.position[0], ball.position[1])

    slope_magnitude = np.linalg.norm(slope_vector)

    gravity_force = np.array([0.0, 0.0])
    angle_of_slope = 0.0 # Effectively flat

    if slope_magnitude > 1e-6: # Avoid division by zero if slope_magnitude is extremely small
        direction_of_descent = slope_vector / slope_magnitude
        angle_of_slope = np.arctan(slope_magnitude)
        gravity_force_magnitude = ball.mass * green.gravity_constant * np.sin(angle_of_slope)
        gravity_force = gravity_force_magnitude * direction_of_descent

    # Calculate normal force. On a slope, Normal Force = m * g * cos(theta)
    normal_force_magnitude = ball.mass * green.gravity_constant * np.cos(angle_of_slope)

    # Accumulate all forces *except* friction initially
    net_force_no_friction = gravity_force.copy() # Start with gravity

    # Determine friction behavior
    if ball.is_moving:
        # Ball is currently moving, apply kinetic friction
        speed = np.linalg.norm(ball.velocity)
        if speed > 1e-6: # Apply friction only if actually moving
            kinetic_friction_magnitude = ball.kinetic_friction_coefficient * normal_force_magnitude
            # Ensure kinetic friction doesn't make the ball accelerate backwards if it's already nearly stopped by friction
            # The friction force should not exceed the current momentum it's trying to stop.
            # This is implicitly handled by the standard model, but good to keep in mind for stability.
            friction_force = -kinetic_friction_magnitude * (ball.velocity / speed)
            net_force_no_friction += friction_force # Add kinetic friction to net force
        # If speed is already very low, the ball.update and subsequent check will handle stopping it.
    else: # Ball is not moving (is_moving is False)
        # Check if the force trying to move the ball (gravity) is strong enough to overcome static friction
        force_trying_to_move_ball_magnitude = np.linalg.norm(net_force_no_friction)
        static_friction_limit = ball.static_friction_coefficient * normal_force_magnitude

        if force_trying_to_move_ball_magnitude > static_friction_limit:
            # Gravity overcomes static friction, ball starts moving.
            ball.is_moving = True
            # No explicit static friction force is applied; the ball will accelerate
            # based on net_force_no_friction, and kinetic friction will apply in the next step.
        else:
            # Static friction holds the ball in place
            ball.velocity = np.array([0.0, 0.0])
            ball.acceleration = np.array([0.0, 0.0])
            ball.is_moving = False
            return # Ball remains stopped, no further updates needed for this dt

    ball.apply_force(net_force_no_friction) # Apply the calculated net force
    ball.update(dt) # Update position and velocity based on net force

    # After ball.update(), check if it's truly stopped by checking velocity
    # This covers cases where kinetic friction brought it to a halt.
    if np.linalg.norm(ball.velocity) < 1e-4: # A small threshold
        ball.velocity = np.array([0.0, 0.0])
        ball.acceleration = np.array([0.0, 0.0])
        ball.is_moving = False

    # Boundary collision detection and response
    if not (green.x_min <= ball.position[0] <= green.x_max and
            green.y_min <= ball.position[1] <= green.y_max):

        # Clamp position to boundary
        ball.position[0] = np.clip(ball.position[0], green.x_min, green.x_max)
        ball.position[1] = np.clip(ball.position[1], green.y_min, green.y_max)

        # Stop the ball
        ball.velocity = np.array([0.0, 0.0])
        ball.acceleration = np.array([0.0, 0.0])
        ball.is_moving = False


def check_ball_in_hole(ball: GolfBall, green: GolfGreen) -> bool:
    distance_to_hole = np.linalg.norm(ball.position - green.hole_position)
    # Ball is in the hole if it's within the hole radius AND its velocity is below a threshold
    if distance_to_hole <= green.hole_radius and np.linalg.norm(ball.velocity) < green.velocity_threshold_for_hole:
        return True
    return False

# Example Usage (for testing purposes, not part of the module itself)
if __name__ == "__main__":
    # Example usage for new GolfGreen with grid and save/load
    print("Testing GolfGreen with elevation grid and save/load...")

    # Create a sample elevation grid (e.g., a simple slope)
    grid_cols = 100
    grid_rows = 100
    x_range = np.linspace(0, 10, grid_cols) # 0 to 10 meters
    y_range = np.linspace(0, 10, grid_rows) # 0 to 10 meters
    X, Y = np.meshgrid(x_range, y_range)

    # Example: a slope with a dip near the center
    elevation_data = 0.05 * X + 0.03 * Y - 0.5 * np.exp(-((X-5)**2 + (Y-5)**2)/(2*1**2))
    print(f"Elevation grid shape: {elevation_data.shape}")

    # Create a GolfGreen instance
    test_green = GolfGreen(
        elevation_grid=elevation_data,
        hole_x=5.0, hole_y=5.0, hole_radius=0.1,
        x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0
    )

    # Save to JSON
    json_filepath = "test_green_config.json"
    test_green.to_json(json_filepath)
    print(f"Green configuration saved to {json_filepath}")

    # Load from JSON
    loaded_green = GolfGreen.from_json(json_filepath)
    print(f"Green configuration loaded from {json_filepath}")

    # Verify loaded data (simple checks)
    print(f"Original hole position: {test_green.hole_position}, Loaded hole position: {loaded_green.hole_position}")
    print(f"Original grid shape: {test_green.elevation_grid.shape}, Loaded grid shape: {loaded_green.elevation_grid.shape}")
    print(f"Elevation at (1,1) original: {test_green.get_elevation(1,1):.4f}, loaded: {loaded_green.get_elevation(1,1):.4f}")
    print(f"Slope at (1,1) original: {test_green.get_slope(1,1)}, loaded: {loaded_green.get_slope(1,1)}")
    assert np.allclose(test_green.hole_position, loaded_green.hole_position)
    assert np.allclose(test_green.elevation_grid, loaded_green.elevation_grid)
    print("Loaded green matches original green.")

    print("\nTesting ball physics...")
    # Initialize ball at a position
    ball = GolfBall(x=1.0, y=1.0)
    # Give it an initial velocity
    ball.velocity = np.array([2.0, 2.0]) # m/s

    print(f"Initial Ball Position: {ball.position}, Velocity: {ball.velocity}")

    time_step = 0.01 # seconds
    total_time = 0.0
    max_simulation_time = 10.0
    print_interval = 0.5

    while total_time < max_simulation_time and not check_ball_in_hole(ball, loaded_green) and np.linalg.norm(ball.velocity) > 0:
        calculate_physics(ball, loaded_green, time_step)
        total_time += time_step

        if total_time >= print_interval:
            print(f"Time: {total_time:.2f}s, Pos: {ball.position}, Vel: {ball.velocity}, Moving: {ball.is_moving}")
            print_interval += 0.5
        if total_time > max_simulation_time: # Prevent infinite loop if ball never stops
             print("Max simulation time reached.")
             break


    if check_ball_in_hole(ball, loaded_green):
        print(f"Ball entered hole at {ball.position} with velocity {np.linalg.norm(ball.velocity):.4f} m/s")
    else:
        print(f"Ball stopped at {ball.position}, Final Velocity: {ball.velocity}, Moving: {ball.is_moving}")
