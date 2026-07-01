
import numpy as np

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
        
        # Check if ball is moving
        self.is_moving = np.linalg.norm(self.velocity) > 1e-3 # Threshold for "moving"
        
        self.acceleration = np.array([0.0, 0.0]) # Reset acceleration after applying

class GolfGreen:
    def __init__(self, elevation_map_func, hole_x, hole_y, hole_radius=0.05, gravity_constant=9.81, velocity_threshold_for_hole=0.2):
        # elevation_map_func: A function that takes (x, y) and returns elevation (z)
        self.elevation_map_func = elevation_map_func
        self.hole_position = np.array([float(hole_x), float(hole_y)])
        self.hole_radius = hole_radius
        self.gravity_constant = gravity_constant
        self.velocity_threshold_for_hole = velocity_threshold_for_hole # Max velocity for ball to be considered "in the hole"

    def get_elevation(self, x, y):
        return self.elevation_map_func(x, y)

    def get_slope(self, x, y, delta=0.01):
        # Calculate approximate slope using central difference
        # Ensure delta is not too small to avoid numerical instability on very flat greens
        # A slightly larger delta might be more robust for typical golf green scales
        # For a smooth elevation function, smaller delta is more accurate. Let's keep it at 0.01 for now.
        
        # Check for non-scalar x, y (e.g., if ball.position is passed directly)
        if isinstance(x, np.ndarray): x = x[0]
        if isinstance(y, np.ndarray): y = y[1]

        dz_dx = (self.get_elevation(x + delta, y) - self.get_elevation(x - delta, y)) / (2 * delta)
        dz_dy = (self.get_elevation(x, y + delta) - self.get_elevation(x, y - delta)) / (2 * delta)
        
        # Negative gradient indicates the direction of steepest descent, which is the direction gravity pulls
        return np.array([-dz_dx, -dz_dy])

def calculate_physics(ball: GolfBall, green: GolfGreen, dt: float):
    # Calculate gravitational force due to slope
    slope = green.get_slope(ball.position[0], ball.position[1])
    # The normal force is effectively mass * gravity_constant, assuming small slopes
    # Gravity force acts in the direction of the steepest descent (slope vector)
    gravity_force = ball.mass * green.gravity_constant * slope
    ball.apply_force(gravity_force)

    # Calculate and apply friction force
    normal_force_magnitude = ball.mass * green.gravity_constant # Assuming flat ground for normal force magnitude

    if ball.is_moving:
        # Kinetic friction opposes motion
        speed = np.linalg.norm(ball.velocity)
        if speed > 1e-6: # Avoid division by zero
            kinetic_friction_magnitude = ball.kinetic_friction_coefficient * normal_force_magnitude
            friction_force = -kinetic_friction_magnitude * (ball.velocity / speed)
            ball.apply_force(friction_force)
        
        # If the ball is almost stopped by friction, bring it to a full stop
        # This prevents tiny oscillations when speed is very low
        if speed < 0.1: # If very slow, check if current friction can stop it
            # Projected velocity after current forces
            projected_velocity = ball.velocity + (ball.acceleration / ball.mass) * dt # acceleration here is from gravity
            
            # The force that is trying to move the ball (gravity_force)
            force_trying_to_move_ball = gravity_force # Without friction applied yet
            
            # If the magnitude of the force trying to move the ball is less than static friction, stop it
            if np.linalg.norm(force_trying_to_move_ball) < ball.static_friction_coefficient * normal_force_magnitude:
                ball.velocity = np.array([0.0, 0.0])
                ball.acceleration = np.array([0.0, 0.0])
                ball.is_moving = False
                return # Ball has stopped, no need to update further in this step
    else:
        # Ball is not moving, apply static friction logic
        # Check if gravity force is strong enough to overcome static friction
        force_trying_to_move_ball = gravity_force
        static_friction_limit = ball.static_friction_coefficient * normal_force_magnitude

        if np.linalg.norm(force_trying_to_move_ball) < static_friction_limit:
            # Static friction holds the ball in place
            ball.velocity = np.array([0.0, 0.0])
            ball.acceleration = np.array([0.0, 0.0])
            ball.is_moving = False
            return # Ball remains stopped
        else:
            # Gravity overcomes static friction, ball starts moving
            ball.is_moving = True
            # No explicit static friction force needs to be applied, as gravity will now accelerate it

    ball.update(dt)

def check_ball_in_hole(ball: GolfBall, green: GolfGreen) -> bool:
    distance_to_hole = np.linalg.norm(ball.position - green.hole_position)
    # Ball is in the hole if it's within the hole radius AND its velocity is below a threshold
    if distance_to_hole <= green.hole_radius and np.linalg.norm(ball.velocity) < green.velocity_threshold_for_hole:
        return True
    return False

# Example Usage (for testing purposes, not part of the module itself)
if __name__ == "__main__":
    def simple_elevation(x, y):
        # A simple linear slope for testing with a slight dip near the hole
        # Hole at (5,5)
        # return 0.05 * x + 0.02 * y # Simple slope
        
        # More complex elevation: general slope with a slight bowl near the hole
        return (0.05 * x + 0.03 * y) - (0.5 * np.exp(-((x-5)**2 + (y-5)**2)/2))

    # Create a green with a hole at (5, 5)
    green = GolfGreen(elevation_map_func=simple_elevation, hole_x=5.0, hole_y=5.0, hole_radius=0.1, velocity_threshold_for_hole=0.2)

    # Create a golf ball
    ball = GolfBall(x=0.0, y=0.0)
    ball.velocity = np.array([3.0, 2.0]) # Give it some initial velocity

    dt = 0.05 # time step
    time_elapsed = 0.0
    max_time = 30.0 # Simulate for 30 seconds

    print("Starting simulation...")
    positions = []
    velocities = []

    while time_elapsed < max_time:
        positions.append(ball.position.copy())
        velocities.append(ball.velocity.copy())

        calculate_physics(ball, green, dt)
        
        if check_ball_in_hole(ball, green):
            print(f"Ball entered hole at position {ball.position} after {time_elapsed:.2f} seconds!")
            break
        
        # Check if ball has truly stopped
        if not ball.is_moving and np.linalg.norm(ball.velocity) < 1e-4:
            print(f"Ball stopped at position {ball.position} after {time_elapsed:.2f} seconds.")
            break
            
        time_elapsed += dt

        if int(time_elapsed*100) % 50 == 0: # Print every 0.5 seconds
            current_elevation = green.get_elevation(ball.position[0], ball.position[1])
            print(f"Time: {time_elapsed:.2f}s, Pos: ({ball.position[0]:.2f}, {ball.position[1]:.2f}), Vel: {np.linalg.norm(ball.velocity):.2f}, Elev: {current_elevation:.3f}")

    if time_elapsed >= max_time:
        print(f"Simulation ended after {max_time} seconds. Ball did not enter hole.")
        print(f"Final Position: {ball.position}, Final Velocity: {ball.velocity}")

    print("\nSimulation complete.")
