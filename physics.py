
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
        # A small threshold to account for floating point inaccuracies
        if np.linalg.norm(self.velocity) > 1e-4:
            self.is_moving = True
        else:
            self.is_moving = False
            self.velocity = np.array([0.0, 0.0]) # Ensure it's truly stopped
        
        self.acceleration = np.array([0.0, 0.0]) # Reset acceleration after applying

class GolfGreen:
    def __init__(self, elevation_map_func, hole_x, hole_y, hole_radius=0.05, 
                 gravity_constant=9.81, velocity_threshold_for_hole=0.2,
                 x_min=-10.0, x_max=10.0, y_min=-10.0, y_max=10.0):
        # elevation_map_func: A function that takes (x, y) and returns elevation (z)
        self.elevation_map_func = elevation_map_func
        self.hole_position = np.array([float(hole_x), float(hole_y)])
        self.hole_radius = hole_radius
        self.gravity_constant = gravity_constant
        self.velocity_threshold_for_hole = velocity_threshold_for_hole # Max velocity for ball to be considered "in the hole"
        self.x_min, self.x_max = x_min, x_max
        self.y_min, self.y_max = y_min, y_max

    def get_elevation(self, x, y):
        # Clamp x, y to green boundaries before calculating elevation
        x = np.clip(x, self.x_min, self.x_max)
        y = np.clip(y, self.y_min, self.y_max)
        return self.elevation_map_func(x, y)

    def get_slope(self, x, y, delta=0.01):
        # Calculate approximate slope (gradient) using central difference
        # Ensure delta is not too small to avoid numerical instability on very flat greens
        
        # Clamp x, y to green boundaries before calculating slope
        x = np.clip(x, self.x_min, self.x_max)
        y = np.clip(y, self.y_min, self.y_max)

        dz_dx = (self.get_elevation(x + delta, y) - self.get_elevation(x - delta, y)) / (2 * delta)
        dz_dy = (self.get_elevation(x, y + delta) - self.get_elevation(x, y - delta)) / (2 * delta)
        
        # The gradient vector points in the direction of steepest ascent.
        # Gravity pulls in the direction of steepest descent.
        return np.array([-dz_dx, -dz_dy])

def calculate_physics(ball: GolfBall, green: GolfGreen, dt: float):
    # Calculate gravitational force due to slope
    slope_vector = green.get_slope(ball.position[0], ball.position[1])
    
    # The magnitude of the slope vector is tan(theta) where theta is the angle of the steepest descent.
    slope_magnitude = np.linalg.norm(slope_vector)
    
    # Avoid division by zero if slope_magnitude is extremely small
    if slope_magnitude > 1e-6:
        # Normalize the slope vector to get the direction of steepest descent
        direction_of_descent = slope_vector / slope_magnitude
        
        # Calculate the angle of the slope (theta)
        # For small angles, tan(theta) approx theta, and sin(theta) approx theta
        # Here, slope_magnitude is tan(theta)
        # The component of gravity along the slope is m * g * sin(theta)
        # Using atan for more accuracy
        angle_of_slope = np.arctan(slope_magnitude)
        
        # Gravitational force component along the slope
        gravity_force_magnitude = ball.mass * green.gravity_constant * np.sin(angle_of_slope)
        gravity_force = gravity_force_magnitude * direction_of_descent
    else:
        gravity_force = np.array([0.0, 0.0])
        angle_of_slope = 0.0 # Effectively flat

    ball.apply_force(gravity_force)

    # Calculate normal force. On a slope, Normal Force = m * g * cos(theta)
    normal_force_magnitude = ball.mass * green.gravity_constant * np.cos(angle_of_slope)
    
    # Apply friction force
    if ball.is_moving:
        # Kinetic friction opposes motion
        speed = np.linalg.norm(ball.velocity)
        if speed > 1e-6: # Avoid division by zero
            kinetic_friction_magnitude = ball.kinetic_friction_coefficient * normal_force_magnitude
            friction_force = -kinetic_friction_magnitude * (ball.velocity / speed)
            ball.apply_force(friction_force)
        
        # If the ball's speed is very low, consider stopping it
        # This helps prevent tiny oscillations or infinite rolling at very low speeds
        if speed < 0.1: # Threshold for potentially stopping
            # Check if the combined force (gravity + applied_forces, excluding friction) is less than static friction
            # If so, static friction would hold it.
            # Here, we already applied gravity. So if current acceleration would lead to very low velocity, check against static.
            # A more robust approach: sum all forces *except* friction, then check against static friction limit.
            
            # Let's consider the net force *before* applying friction, to determine if static friction should apply.
            # This is tricky because we've already applied gravity.
            # A simpler heuristic for kinetic-to-static transition: if speed is low and net force (excluding friction)
            # is not strong enough to overcome static friction, stop it.

            # We've already applied gravity. Let's find the effective force trying to move the ball
            # This is a bit of a simplification, as acceleration is divided by mass.
            # force_trying_to_move_ball = gravity_force # Only gravity applied so far
            # If the ball is moving, friction is kinetic. But if it's very slow, we can transition to static.
            
            # Re-evaluating. If moving, apply kinetic friction. After that, if speed is tiny, stop.
            # The more correct way: if speed is below threshold, calculate net force without kinetic friction.
            # If this net force is less than static friction, set velocity to zero.

            net_force_without_kinetic_friction = gravity_force # + any other external forces, which are not present here
            if np.linalg.norm(net_force_without_kinetic_friction) < ball.static_friction_coefficient * normal_force_magnitude:
                 ball.velocity = np.array([0.0, 0.0])
                 ball.acceleration = np.array([0.0, 0.0])
                 ball.is_moving = False
                 # Skip the update() call as ball is now definitively stopped
                 return 
            
    else: # Ball is not moving
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

    # Boundary collision detection and response
    # If the ball goes out of bounds, stop it at the boundary
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
    def simple_elevation(x, y):
        # A simple linear slope for testing with a slight dip near the hole
        # Hole at (5,5)
        
        # More complex elevation: general slope with a slight bowl near the hole
        # This function should be defined over the green's domain.
        # Let's make it a gentle slope with a dip near the hole
        
        # Ensure x,y are within bounds for elevation calculation or handle outside appropriately.
        # The get_elevation function in GolfGreen already clips, so this func can assume domain.
        
        # Example: a slope towards the hole, with a depression around the hole itself
        return (0.02 * x + 0.01 * y) - (0.8 * np.exp(-((x-5)**2 + (y-5)**2)/(2*0.5**2)))


    # Create a green with a hole at (5, 5) and boundaries
    green = GolfGreen(elevation_map_func=simple_elevation, 
                      hole_x=5.0, hole_y=5.0, hole_radius=0.1, 
                      velocity_threshold_for_hole=0.2,
                      x_min=0.0, x_max=10.0, y_min=0.0, y_max=10.0)

    # Create a golf ball starting at (1, 1)
    ball = GolfBall(x=1.0, y=1.0)
    # Give it some initial velocity towards the hole area
    ball.velocity = np.array([2.0, 1.5]) 

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
            ball.velocity = np.array([0.0, 0.0]) # Stop ball once in hole
            ball.is_moving = False
            break
        
        # Check if ball has truly stopped
        # Re-check is_moving as calculate_physics might stop it due to friction or boundary
        if not ball.is_moving and np.linalg.norm(ball.velocity) < 1e-4: # Added an extra check just in case
            print(f"Ball stopped at position {ball.position} after {time_elapsed:.2f} seconds.")
            break
            
        time_elapsed += dt

        if int(time_elapsed*100) % 50 == 0: # Print every 0.5 seconds
            current_elevation = green.get_elevation(ball.position[0], ball.position[1])
            print(f"Time: {time_elapsed:.2f}s, Pos: ({ball.position[0]:.2f}, {ball.position[1]:.2f}), Vel: {np.linalg.norm(ball.velocity):.2f}, Elev: {current_elevation:.3f}")

    if time_elapsed >= max_time:
        print(f"Simulation ended after {max_time} seconds. Ball did not enter hole or stop.")
        print(f"Final Position: {ball.position}, Final Velocity: {ball.velocity}")

    print("
Simulation complete.")
