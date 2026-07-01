import pygame
import math
import numpy as np

# --- Placeholder Physics Objects (for GUI to run independently) ---
# In a real scenario, these would be imported from 'physics.py'

class PlaceholderGolfBall:
    def __init__(self, position=(0.5, 0.5), velocity=(0.0, 0.0)):
        self.position = np.array(position, dtype=float)
        self.velocity = np.array(velocity, dtype=float)
        self.radius = 0.02135 # Standard golf ball radius in meters
        self.stopped_threshold = 0.01 # m/s, threshold for ball to be considered stopped

    def reset_position(self, new_pos=(0.5, 0.5)):
        self.position = np.array(new_pos, dtype=float)
        self.velocity = np.array([0.0, 0.0])

    def set_velocity(self, new_vel):
        self.velocity = np.array(new_vel, dtype=float)

class PlaceholderGolfGreen:
    def __init__(self, hole_position=(0.9, 0.9), green_config_id=0):
        self.hole_position = np.array(hole_position, dtype=float)
        self.hole_radius = 0.054 # Standard hole radius in meters (4.25 inches)
        self.green_config_id = green_config_id
        self._set_elevation_function(green_config_id)

    def _set_elevation_function(self, config_id):
        if config_id == 0:
            # Flat green
            self.elevation_map_func = lambda x, y: 0.0
        elif config_id == 1:
            # Simple slope
            self.elevation_map_func = lambda x, y: 0.1 * x + 0.05 * y
        elif config_id == 2:
            # Gentle bowl/hill
            self.elevation_map_func = lambda x, y: 0.2 * math.sin(x * math.pi) * math.cos(y * math.pi)
        elif config_id == 3:
            # More complex terrain (e.g., a saddle)
            # Assuming a green that goes from 0 to SCREEN_WIDTH/METERS_TO_PIXELS and 0 to SCREEN_HEIGHT/METERS_TO_PIXELS
            # Example: Green width/height 10m x 7.5m (800/80 x 600/80)
            center_x = (SCREEN_WIDTH / METERS_TO_PIXELS) / 2
            center_y = (SCREEN_HEIGHT / METERS_TO_PIXELS) / 2
            self.elevation_map_func = lambda x, y: 0.2 * ( (x - center_x)**2 / 20 - (y - center_y)**2 / 15 )
        else:
            self.elevation_map_func = lambda x, y: 0.0 # Default to flat

    def get_elevation(self, x, y):
        # Ensure x, y are within a reasonable range for the elevation function
        # A typical green might be 10x10 meters.
        # Scale to a 0-1 range for easier function definition if desired, then scale back.
        # For simplicity, let's assume functions operate on physics meters directly.
        return self.elevation_map_func(x, y)

    def set_hole_position(self, new_pos):
        self.hole_position = np.array(new_pos, dtype=float)

    def set_green_config(self, config_id):
        self.green_config_id = config_id
        self._set_elevation_function(config_id)

# --- Constants for GUI ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
GREEN_DARK = (0, 100, 0)
GREEN_LIGHT = (0, 180, 0) # Lighter for higher elevation
GREEN_MEDIUM = (0, 125, 0) # Added for gradient for flat greens
BALL_COLOR = (200, 200, 200) # Light grey for the ball
HOLE_COLOR = (0, 0, 0) # Black for the hole
RED = (255, 0, 0) # For velocity vector
BLACK = (0, 0, 0) # For text
BLUE = (0, 0, 255) # For hole editing

# Scale factor from physics coordinates (meters) to screen coordinates (pixels)
METERS_TO_PIXELS = 80 # Adjust based on desired green size on screen (e.g., 10m green fits 800px)
PUTT_STRENGTH_FACTOR = 0.5 # Multiplier for converting drag distance (in meters) to initial velocity (m/s)

class GUIManager:
    def __init__(self, screen_width, screen_height):
        pygame.init()
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        pygame.display.set_caption("Golf Putting Simulator")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36) # For displaying text
        self.small_font = pygame.font.Font(None, 24) # For smaller text

        # State for dragging input
        self.dragging = False
        self.drag_start_pos = (0, 0) # Screen coordinates
        self.current_mouse_pos = (0, 0) # Screen coordinates

        # State for green and hole editing
        self.editing_hole = False
        self.current_green_config_id = 0 # Default green

        # For pre-rendering the green surface
        self.green_surface = pygame.Surface((self.screen_width, self.screen_height))
        self.needs_green_rerender = True # Flag to indicate if green surface needs update

        # Grid density for drawing green (e.g., every 5 pixels)
        self.green_draw_grid_spacing = 5

    def _meters_to_pixels(self, position_meters):
        """Converts physics coordinates (meters) to screen coordinates (pixels)."""
        # Physics (0,0) is bottom-left, screen (0,0) is top-left
        return (int(position_meters[0] * METERS_TO_PIXELS),
                int(self.screen_height - (position_meters[1] * METERS_TO_PIXELS)))

    def _pixels_to_meters(self, position_pixels):
        """Converts screen coordinates (pixels) to physics coordinates (meters)."""
        return (position_pixels[0] / METERS_TO_PIXELS,
                (self.screen_height - position_pixels[1]) / METERS_TO_PIXELS)

    def _get_elevation_color(self, elevation, min_elevation, max_elevation):
        """Maps an elevation value to a color based on the min/max elevation range."""
        if max_elevation == min_elevation: # Flat green, use medium green
            return GREEN_MEDIUM

        normalized_elevation = (elevation - min_elevation) / (max_elevation - min_elevation)
        # Clamp to 0-1 range to avoid issues with elevations outside the computed min/max
        normalized_elevation = max(0.0, min(1.0, normalized_elevation)) 
        
        r = int(GREEN_DARK[0] + normalized_elevation * (GREEN_LIGHT[0] - GREEN_DARK[0]))
        g = int(GREEN_DARK[1] + normalized_elevation * (GREEN_LIGHT[1] - GREEN_DARK[1]))
        b = int(GREEN_DARK[2] + normalized_elevation * (GREEN_LIGHT[2] - GREEN_DARK[2]))
        return (r, g, b)

    def _precompute_green_surface(self, green_physics_obj):
        """Precomputes the green's heightmap visualization onto a surface for performance."""
        # Clear the surface
        self.green_surface.fill(GREEN_DARK) # Base color

        # Determine min/max elevation for color mapping over the visible area
        elevations = []
        for x_pixel in range(0, self.screen_width, self.green_draw_grid_spacing):
            for y_pixel in range(0, self.screen_height, self.green_draw_grid_spacing):
                x_meter, y_meter = self._pixels_to_meters((x_pixel, y_pixel))
                # Make sure to pass valid coordinates to get_elevation
                # Assuming the green covers the area from (0,0) to (screen_width/METERS_TO_PIXELS, screen_height/METERS_TO_PIXELS)
                if x_meter >= 0 and y_meter >= 0: # Basic boundary check
                    elevations.append(green_physics_obj.get_elevation(x_meter, y_meter))

        if elevations:
            dynamic_min_elevation = min(elevations)
            dynamic_max_elevation = max(elevations)
        else:
            dynamic_min_elevation = 0.0
            dynamic_max_elevation = 0.0

        # Draw the green using a grid of rectangles, colored by elevation
        for x_pixel in range(0, self.screen_width, self.green_draw_grid_spacing):
            for y_pixel in range(0, self.screen_height, self.green_draw_grid_spacing):
                x_meter, y_meter = self._pixels_to_meters((x_pixel, y_pixel))
                if x_meter >= 0 and y_meter >= 0: # Basic boundary check
                    elevation = green_physics_obj.get_elevation(x_meter, y_meter)
                    color = self._get_elevation_color(elevation, dynamic_min_elevation, dynamic_max_elevation)
                    pygame.draw.rect(self.green_surface, color, (x_pixel, y_pixel, self.green_draw_grid_spacing, self.green_draw_grid_spacing))

        self.needs_green_rerender = False

    def draw_green(self, green_physics_obj):
        """Draws the golf green based on the physics object, with elevation-based shading."""
        if self.needs_green_rerender:
            self._precompute_green_surface(green_physics_obj)
        
        self.screen.blit(self.green_surface, (0, 0))

        # Draw the golf hole
        hole_pos_pixels = self._meters_to_pixels(green_physics_obj.hole_position)
        hole_radius_pixels = int(green_physics_obj.hole_radius * METERS_TO_PIXELS)
        pygame.draw.circle(self.screen, HOLE_COLOR, hole_pos_pixels, hole_radius_pixels)
        # Draw a white outline for visibility
        pygame.draw.circle(self.screen, WHITE, hole_pos_pixels, hole_radius_pixels, 1)

    def draw_ball(self, ball_physics_obj):
        """Draws the golf ball based on the physics object."""
        ball_pos_pixels = self._meters_to_pixels(ball_physics_obj.position)
        ball_radius_pixels = int(ball_physics_obj.radius * METERS_TO_PIXELS)
        pygame.draw.circle(self.screen, BALL_COLOR, ball_pos_pixels, ball_radius_pixels)
        # Draw a black outline for visibility
        pygame.draw.circle(self.screen, BLACK, ball_pos_pixels, ball_radius_pixels, 1)

    def draw_drag_indicator(self, ball_physics_obj):
        """Draws the line indicating drag direction/force."""
        if self.dragging and self.drag_start_pos:
            # Draw line from ball position to current mouse position
            ball_pos_pixels = self._meters_to_pixels(ball_physics_obj.position)
            pygame.draw.line(self.screen, RED, ball_pos_pixels, self.current_mouse_pos, 2)

            # Draw arrow head
            dx = self.current_mouse_pos[0] - ball_pos_pixels[0]
            dy = self.current_mouse_pos[1] - ball_pos_pixels[1]
            if dx == 0 and dy == 0:
                return # Avoid math.atan2(0,0)
            angle = math.atan2(dy, dx)
            arrow_length = 20
            arrow_angle = math.pi / 6 # 30 degrees for arrow wings

            pygame.draw.line(self.screen, RED, self.current_mouse_pos,
                             (self.current_mouse_pos[0] - arrow_length * math.cos(angle - arrow_angle),
                              self.current_mouse_pos[1] - arrow_length * math.sin(angle - arrow_angle)), 2)
            pygame.draw.line(self.screen, RED, self.current_mouse_pos,
                             (self.current_mouse_pos[0] - arrow_length * math.cos(angle + arrow_angle),
                              self.current_mouse_pos[1] - arrow_length * math.sin(angle + arrow_angle)), 2)

            # Display potential velocity magnitude (optional, for feedback)
            ball_pos_meters = self._pixels_to_meters(ball_pos_pixels) # Ball position is the start of drag
            current_mouse_meters = self._pixels_to_meters(self.current_mouse_pos)
            
            drag_distance_meters = math.sqrt(
                (current_mouse_meters[0] - ball_pos_meters[0])**2 +
                (current_mouse_meters[1] - ball_pos_meters[1])**2
            )
            projected_velocity_magnitude = drag_distance_meters * PUTT_STRENGTH_FACTOR
            self.display_message(f"Velocity: {projected_velocity_magnitude:.2f} m/s",
                                 position=(self.screen_width - 180, 10), color=RED, font_size="small")

    def display_message(self, message, position=(10, 10), color=BLACK, font_size="normal"):
        """Displays a message on the screen."""
        if font_size == "small":
            text_surface = self.small_font.render(message, True, color)
        else:
            text_surface = self.font.render(message, True, color)
        self.screen.blit(text_surface, position)

    def update_display(self):
        """Updates the full display Surface to the screen."""
        pygame.display.flip()

    def tick(self):
        """Caps the frame rate and returns milliseconds since last tick."""
        return self.clock.tick(FPS)

    def toggle_hole_editing(self):
        self.editing_hole = not self.editing_hole
        print(f"Hole editing mode: {'ON' if self.editing_hole else 'OFF'}")

    def set_green_configuration(self, config_id):
        if self.current_green_config_id != config_id:
            self.current_green_config_id = config_id
            self.needs_green_rerender = True
            print(f"Green configuration set to: {config_id}")
        
    def handle_input_event(self, event, ball_physics_obj, green_physics_obj):
        """Handles a single Pygame event. Returns a dictionary of actions if any."""
        actions = {}
        if event.type == pygame.QUIT:
            actions['quit'] = True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                mouse_pos_meters = self._pixels_to_meters(event.pos)
                
                if self.editing_hole:
                    actions['set_hole_position'] = np.array(mouse_pos_meters)
                    self.needs_green_rerender = True # Redraw green to update hole position visually
                else:
                    # Check if click is on the ball (in screen coordinates)
                    ball_pos_pixels = self._meters_to_pixels(ball_physics_obj.position)
                    ball_radius_pixels = int(ball_physics_obj.radius * METERS_TO_PIXELS)
                    
                    distance_to_ball_center = math.sqrt(
                        (event.pos[0] - ball_pos_pixels[0])**2 +
                        (event.pos[1] - ball_pos_pixels[1])**2
                    )
                    
                    # Only start dragging if ball is stopped and clicked on
                    if np.linalg.norm(ball_physics_obj.velocity) < ball_physics_obj.stopped_threshold and \
                       distance_to_ball_center <= ball_radius_pixels:
                        self.dragging = True
                        self.drag_start_pos = ball_pos_pixels # Drag starts from ball's center
                        self.current_mouse_pos = event.pos

        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.current_mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging and not self.editing_hole:
                self.dragging = False
                end_drag_pos = self.current_mouse_pos # Use current_mouse_pos from MOUSEMOTION

                # Calculate initial velocity from drag
                # Drag starts from the ball's position (self.drag_start_pos - screen pixels)
                # and ends at the mouse release position (end_drag_pos - screen pixels).
                # The velocity should be in the opposite direction of the drag vector.

                ball_pos_meters = self._pixels_to_meters(self.drag_start_pos)
                end_drag_meters = self._pixels_to_meters(end_drag_pos)

                drag_vector_x = end_drag_meters[0] - ball_pos_meters[0]
                drag_vector_y = end_drag_meters[1] - ball_pos_meters[1]

                initial_velocity_x = -drag_vector_x * PUTT_STRENGTH_FACTOR
                initial_velocity_y = -drag_vector_y * PUTT_STRENGTH_FACTOR

                actions['set_ball_velocity'] = np.array([initial_velocity_x, initial_velocity_y])
                actions['reset_ball_to_start'] = True # Request main loop to handle ball state change
                self.drag_start_pos = (0, 0)
                self.current_mouse_pos = (0, 0)
        
        elif event.type == pygame.KEYUP:
            if event.key == pygame.K_r:
                actions['reset_ball_position'] = True
            elif event.key == pygame.K_h:
                self.toggle_hole_editing()
            elif event.key == pygame.K_1:
                self.set_green_configuration(0)
                actions['set_green_config'] = 0
            elif event.key == pygame.K_2:
                self.set_green_configuration(1)
                actions['set_green_config'] = 1
            elif event.key == pygame.K_3:
                self.set_green_configuration(2)
                actions['set_green_config'] = 2
            elif event.key == pygame.K_4:
                self.set_green_configuration(3)
                actions['set_green_config'] = 3 # Added config 3 for demonstration

        return actions

# --- Main Simulation Loop (for demonstration purposes of the GUI) ---
# In a real application, this loop would be external, orchestrating GUI and physics.
def run_simulation():
    gui_manager = GUIManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Initial physics objects (placeholders)
    # Start ball at a known position, e.g., 1 meter from bottom-left corner
    ball = PlaceholderGolfBall(position=(1.0, 1.0)) 
    # Hole at a different position, e.g., 8 meters x 5 meters
    green = PlaceholderGolfGreen(hole_position=(8.0, 5.0), green_config_id=gui_manager.current_green_config_id)
    
    running = True
    while running:
        for event in pygame.event.get():
            actions = gui_manager.handle_input_event(event, ball, green)
            if 'quit' in actions:
                running = False
            if 'set_hole_position' in actions:
                green.set_hole_position(actions['set_hole_position'])
            if 'set_ball_velocity' in actions:
                ball.set_velocity(actions['set_ball_velocity'])
            if 'reset_ball_position' in actions:
                ball.reset_position(new_pos=(1.0, 1.0)) # Reset to a default start position
            if 'set_green_config' in actions:
                green.set_green_config(actions['set_green_config'])


        # --- Update Physics (Placeholder) ---
        # In a real simulation, this is where a physics engine would update the ball's state
        # based on its current velocity and the green's elevation.
        dt = gui_manager.tick() / 1000.0  # Convert milliseconds to seconds

        if np.linalg.norm(ball.velocity) > ball.stopped_threshold:
            # Simple friction/deceleration for demonstration
            friction_factor = 0.98 # Reduce velocity by 2% each frame
            ball.velocity *= friction_factor
            
            # Apply some 'gravity' based on green slope (very simplified)
            # This would come from physics.py
            x_meter, y_meter = ball.position[0], ball.position[1]
            
            # Boundary check for elevation sampling
            # The green is assumed to occupy the visible screen area in meters.
            max_x_meter = SCREEN_WIDTH / METERS_TO_PIXELS
            max_y_meter = SCREEN_HEIGHT / METERS_TO_PIXELS

            # Ensure sampling points are within the green's "playable" area for elevation calculation
            sample_x = max(0.0, min(x_meter, max_x_meter))
            sample_y = max(0.0, min(y_meter, max_y_meter))


            # Estimate slope using a tiny delta
            delta = 0.01 # meter
            
            # Ensure delta points are also within bounds
            elev_x_plus = green.get_elevation(max(0.0, min(sample_x + delta, max_x_meter)), sample_y)
            elev_x_minus = green.get_elevation(max(0.0, min(sample_x - delta, max_x_meter)), sample_y)
            elev_y_plus = green.get_elevation(sample_x, max(0.0, min(sample_y + delta, max_y_meter)))
            elev_y_minus = green.get_elevation(sample_x, max(0.0, min(sample_y - delta, max_y_meter)))


            slope_x = (elev_x_plus - elev_x_minus) / (2 * delta)
            slope_y = (elev_y_plus - elev_y_minus) / (2 * delta)

            # A very crude approximation of how slope affects acceleration
            slope_effect_factor = 0.5 # How much slope influences acceleration
            # Acceleration due to gravity on slope is g * sin(theta) ~ g * tan(theta) = g * slope
            # In our simplified model, let's just directly apply a scaled slope to velocity change
            ball.velocity[0] -= slope_x * slope_effect_factor * dt
            ball.velocity[1] -= slope_y * slope_effect_factor * dt

            ball.position += ball.velocity * dt
            
            # Stop the ball if velocity is very low
            if np.linalg.norm(ball.velocity) < ball.stopped_threshold:
                ball.velocity = np.array([0.0, 0.0])

        # --- Render GUI ---
        gui_manager.screen.fill(WHITE) # Clear screen with white background
        gui_manager.draw_green(green)
        gui_manager.draw_ball(ball)
        gui_manager.draw_drag_indicator(ball)
        
        # Display messages
        gui_manager.display_message(f"Ball Position: ({ball.position[0]:.2f}, {ball.position[1]:.2f})m", position=(10, 10))
        gui_manager.display_message(f"Ball Velocity: ({ball.velocity[0]:.2f}, {ball.velocity[1]:.2f})m/s", position=(10, 40))
        gui_manager.display_message(f"Green Config: {green.green_config_id}", position=(10, 70))
        
        if gui_manager.editing_hole:
            gui_manager.display_message("HOLE EDITING MODE (Click to set hole)", position=(SCREEN_WIDTH // 2 - 200, 10), color=BLUE)
        else:
            gui_manager.display_message("Drag ball to putt. R: Reset, H: Hole Edit, 1-4: Greens", position=(SCREEN_WIDTH // 2 - 270, 10), font_size="small")


        gui_manager.update_display()

    pygame.quit()

if __name__ == '__main__':
    run_simulation()