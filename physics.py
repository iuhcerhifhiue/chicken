
import numpy as np

class GolfBall:
    def __init__(self, x, y, mass=0.045, radius=0.02135, friction_coefficient=0.1):
        self.position = np.array([float(x), float(y)])
        self.velocity = np.array([0.0, 0.0])
        self.acceleration = np.array([0.0, 0.0])
        self.mass = mass # kg (standard golf ball mass)
        self.radius = radius # meters (standard golf ball radius)
        self.friction_coefficient = friction_coefficient

    def apply_force(self, force):
        self.acceleration += force / self.mass

    def update(self, dt):
        self.velocity += self.acceleration * dt
        self.position += self.velocity * dt
        self.acceleration = np.array([0.0, 0.0]) # Reset acceleration after applying

class GolfGreen:
    def __init__(self, elevation_map_func, hole_x, hole_y, hole_radius=0.05, gravity_constant=9.81):
        # elevation_map_func: A function that takes (x, y) and returns elevation (z)
        self.elevation_map_func = elevation_map_func
        self.hole_position = np.array([float(hole_x), float(hole_y)])
        self.hole_radius = hole_radius
        self.gravity_constant = gravity_constant
        self.HoleTolerance = 0.01 # A small tolerance for the ball to be considered "in the hole"

    def get_elevation(self, x, y):
        return self.elevation_map_func(x, y)

    def get_slope(self, x, y, delta=0.01):
        # Calculate approximate slope using central difference
        dz_dx = (self.get_elevation(x + delta, y) - self.get_elevation(x - delta, y)) / (2 * delta)
        dz_dy = (self.get_elevation(x, y + delta) - self.get_elevation(x, y - delta)) / (2 * delta)
        return np.array([-dz_dx, -dz_dy]) # Negative gradient for force direction

def calculate_physics(ball: GolfBall, green: GolfGreen, dt: float):
    # Apply gravity force based on slope
    slope = green.get_slope(ball.position[0], ball.position[1])
    gravity_force = ball.mass * green.gravity_constant * slope
    ball.apply_force(gravity_force)

    # Apply friction force
    if np.linalg.norm(ball.velocity) > 0:
        friction_magnitude = ball.friction_coefficient * ball.mass * green.gravity_constant # Simplified model
        friction_force = -friction_magnitude * (ball.velocity / np.linalg.norm(ball.velocity))
        ball.apply_force(friction_force)
        # Stop ball if friction overcomes remaining velocity
        if np.linalg.norm(ball.velocity + ball.acceleration * dt) < 0.01 and np.linalg.norm(friction_force) >= np.linalg.norm(ball.acceleration * ball.mass):
            ball.velocity = np.array([0.0, 0.0])
            ball.acceleration = np.array([0.0, 0.0])

    ball.update(dt)

def check_ball_in_hole(ball: GolfBall, green: GolfGreen) -> bool:
    distance_to_hole = np.linalg.norm(ball.position - green.hole_position)
    # Check if ball is within hole radius and has low enough velocity to fall in
    if distance_to_hole <= green.hole_radius and np.linalg.norm(ball.velocity) < green.HoleTolerance:
        return True
    return False

# Example Usage (for testing purposes, not part of the module itself)
if __name__ == "__main__":
    def simple_elevation(x, y):
        # A simple linear slope for testing
        return 0.1 * x + 0.05 * y + np.sin(x*5) * 0.01

    # Create a green with a hole at (5, 5)
    green = GolfGreen(elevation_map_func=simple_elevation, hole_x=5.0, hole_y=5.0, hole_radius=0.1)

    # Create a golf ball
    ball = GolfBall(x=0.0, y=0.0)
    ball.velocity = np.array([1.0, 0.5]) # Give it some initial velocity

    dt = 0.01 # time step
    time_elapsed = 0.0
    max_time = 20.0 # Simulate for 20 seconds

    print("Starting simulation...")
    while time_elapsed < max_time:
        calculate_physics(ball, green, dt)
        if check_ball_in_hole(ball, green):
            print(f"Ball entered hole at position {ball.position} after {time_elapsed:.2f} seconds!")
            break
        if np.linalg.norm(ball.velocity) < 0.001 and np.linalg.norm(ball.acceleration) < 0.001:
            print(f"Ball stopped at position {ball.position} after {time_elapsed:.2f} seconds.")
            break
        time_elapsed += dt

        if int(time_elapsed*100) % 100 == 0: # Print every second
            print(f"Time: {time_elapsed:.2f}s, Position: {ball.position}, Velocity: {ball.velocity}, Elevation: {green.get_elevation(ball.position[0], ball.position[1]):.3f}")

    if time_elapsed >= max_time:
        print(f"Simulation ended after {max_time} seconds. Ball did not enter hole.")
        print(f"Final Position: {ball.position}, Final Velocity: {ball.velocity}")
