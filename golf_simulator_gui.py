import pygame
import math
import numpy as np # physics module uses numpy, so GUI might need it for coordinate conversion

# --- Constants for GUI ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

# Colors
WHITE = (255, 255, 255)
GREEN_DARK = (0, 100, 0)
GREEN_LIGHT = (0, 150, 0)
GREEN_MEDIUM = (0, 125, 0) # Added for gradient
BALL_COLOR = (200, 200, 200) # Light grey for the ball
HOLE_COLOR = (0, 0, 0) # Black for the hole
RED = (255, 0, 0) # For velocity vector
BLACK = (0, 0, 0) # For text
BLUE = (0, 0, 255) # For hole editing

# Scale factor from physics coordinates (meters) to screen coordinates (pixels)
METERS_TO_PIXELS = 100

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

        # State for hole editing mode
        self.editing_hole = False

        # Pre-calculate elevation range for color mapping (assuming a typical green size)
        # This can be made more dynamic by sampling the current green.
        self.min_elevation = -0.5 # meters
        self.max_elevation = 0.5  # meters
        
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

    def draw_green(self, green_physics_obj):
        """Draws the golf green based on the physics object, with elevation-based shading."""
        # Calculate min/max elevation dynamically for better color mapping
        # This can be expensive, so doing it once per green change might be better
        # For now, let's sample a grid and find min/max
        # For performance, only sample a limited area or precompute
        # For this iteration, let's keep the fixed range or a simplified dynamic sampling.

        # Simplified dynamic min/max by sampling corners and center for typical green dimensions
        sample_points = [
            (0, 0), (green_physics_obj.hole_position[0] * 2, 0),
            (0, green_physics_obj.hole_position[1] * 2), 
            (green_physics_obj.hole_position[0] * 2, green_physics_obj.hole_position[1] * 2),
            (green_physics_obj.hole_position[0], green_physics_obj.hole_position[1])
        ]
        
        elevations = []
        for x, y in sample_points:
            # Ensure sample points are within a reasonable range for elevation_map_func
            # Assuming green typically spans from (0,0) to (SCREEN_WIDTH/METERS_TO_PIXELS, SCREEN_HEIGHT/METERS_TO_PIXELS)
            x = max(0.0, min(x, self.screen_width / METERS_TO_PIXELS))
            y = max(0.0, min(y, self.screen_height / METERS_TO_PIXELS))
            elevations.append(green_physics_obj.get_elevation(x, y))

        if elevations:
            dynamic_min_elevation = min(elevations)
            dynamic_max_elevation = max(elevations)
        else:
            dynamic_min_elevation = self.min_elevation
            dynamic_max_elevation = self.max_elevation
            
        elevation_range = dynamic_max_elevation - dynamic_min_elevation
        if elevation_range == 0: elevation_range = 1 # Avoid division by zero for flat greens

        # Draw the green using a grid of rectangles, colored by elevation
        for x_pixel in range(0, self.screen_width, self.green_draw_grid_spacing):
            for y_pixel in range(0, self.screen_height, self.green_draw_grid_spacing):
                x_meter, y_meter = self._pixels_to_meters((x_pixel, y_pixel))
                elevation = green_physics_obj.get_elevation(x_meter, y_meter)

                # Normalize elevation to a 0-1 range based on min/max
                normalized_elevation = (elevation - dynamic_min_elevation) / elevation_range
                
                # Map normalized elevation to a color (e.g., darker green for lower, lighter for higher)
                # Interpolate between GREEN_DARK and GREEN_LIGHT
                r = int(GREEN_DARK[0] + normalized_elevation * (GREEN_LIGHT[0] - GREEN_DARK[0]))
                g = int(GREEN_DARK[1] + normalized_elevation * (GREEN_LIGHT[1] - GREEN_DARK[1]))
                b = int(GREEN_DARK[2] + normalized_elevation * (GREEN_LIGHT[2] - GREEN_DARK[2]))
                color = (r, g, b)

                pygame.draw.rect(self.screen, color, (x_pixel, y_pixel, self.green_draw_grid_spacing, self.green_draw_grid_spacing))


        # Draw the golf hole
        hole_pos_pixels = self._meters_to_pixels(green_physics_obj.hole_position)
        hole_radius_pixels = int(green_physics_obj.hole_radius * METERS_TO_PIXELS)
        pygame.draw.circle(self.screen, HOLE_COLOR, hole_pos_pixels, hole_radius_pixels)
    
    def draw_ball(self, ball_physics_obj):
        """Draws the golf ball based on the physics object."""
        ball_pos_pixels = self._meters_to_pixels(ball_physics_obj.position)
        ball_radius_pixels = int(ball_physics_obj.radius * METERS_TO_PIXELS)
        pygame.draw.circle(self.screen, BALL_COLOR, ball_pos_pixels, ball_radius_pixels)

    def draw_drag_indicator(self, ball_physics_obj):
        """Draws the line indicating drag direction/force."""
        if self.dragging and self.drag_start_pos:
            pygame.draw.line(self.screen, RED, self.drag_start_pos, self.current_mouse_pos, 2)

            # Optional: draw an arrow head
            dx = self.current_mouse_pos[0] - self.drag_start_pos[0]
            dy = self.current_mouse_pos[1] - self.drag_start_pos[1]
            if dx == 0 and dy == 0:
                return # Avoid math.atan2(0,0)
            angle = math.atan2(dy, dx)
            arrow_length = 20
            pygame.draw.line(self.screen, RED, self.current_mouse_pos,
                             (self.current_mouse_pos[0] - arrow_length * math.cos(angle - math.pi / 6),
                              self.current_mouse_pos[1] - arrow_length * math.sin(angle - math.pi / 6)), 2)
            pygame.draw.line(self.screen, RED, self.current_mouse_pos,
                             (self.current_mouse_pos[0] - arrow_length * math.cos(angle + math.pi / 6),
                              self.current_mouse_pos[1] - arrow_length * math.sin(angle + math.pi / 6)), 2)

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

    def handle_input_event(self, event, ball_physics_obj):
        """Handles a single Pygame event. Returns a dictionary of actions if any."""
        actions = {}
        if event.type == pygame.QUIT:
            actions['quit'] = True
        
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                mouse_pos_meters = self._pixels_to_meters(event.pos)
                
                if self.editing_hole:
                    actions['set_hole_position'] = np.array(mouse_pos_meters)
                    # Optional: Exit editing mode after setting hole
                    # self.editing_hole = False
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
                        self.drag_start_pos = event.pos
                        self.current_mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging and not self.editing_hole:
                self.dragging = False
                end_drag_pos = event.pos
                if self.drag_start_pos:
                    # Calculate force vector in pixels, then convert to meters for physics
                    force_vector_pixels_x = self.drag_start_pos[0] - end_drag_pos[0]
                    force_vector_pixels_y = self.drag_start_pos[1] - end_drag_pos[1]
                    
                    # Convert drag vector from screen pixels to physics meters
                    # Note the y-axis inversion for screen vs physics (if physics is bottom-left origin)
                    # Scale factor needs tuning for desired putt strength
                    velocity_scale_factor = METERS_TO_PIXELS * 5 # Original was 5, now adjust if needed
                    initial_velocity_x = force_vector_pixels_x / velocity_scale_factor
                    initial_velocity_y = -force_vector_pixels_y / velocity_scale_factor # Invert Y

                    actions['set_ball_velocity'] = np.array([initial_velocity_x, initial_velocity_y])
                self.drag_start_pos = None
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.current_mouse_pos = event.pos

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r: # Reset ball position
                actions['reset_ball'] = True
            if event.key == pygame.K_l: # Load next green layout
                actions['next_layout'] = True # Changed from 'new_layout' for clarity
            if event.key == pygame.K_h: # Toggle hole editing mode
                self.editing_hole = not self.editing_hole
                actions['mode_change_message'] = f"Hole Editing Mode: {'ON' if self.editing_hole else 'OFF'}"
        
        return actions

    def quit_pygame(self):
        pygame.quit()

if __name__ == '__main__':
    # Simple test of the GUI Manager
    from physics import GolfBall, GolfGreen, calculate_physics, check_ball_in_hole

    def simple_elevation(x, y):
        return 0.1 * x + 0.05 * y # Simple slope

    gui_manager = GUIManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Initialize physics objects for testing
    test_green = GolfGreen(elevation_map_func=simple_elevation, hole_x=7.0, hole_y=3.0)
    test_ball = GolfBall(x=1.0, y=3.0)

    running = True
    while running:
        dt_ms = gui_manager.tick()
        dt_s = dt_ms / 1000.0

        for event in pygame.event.get():
            actions = gui_manager.handle_input_event(event, test_ball)
            if 'quit' in actions:
                running = False
            if 'set_ball_velocity' in actions:
                test_ball.velocity = actions['set_ball_velocity']
            if 'reset_ball' in actions:
                test_ball = GolfBall(x=1.0, y=3.0)
            if 'next_layout' in actions:
                # In a real sim, this would load a new green, for test we just acknowledge
                print("Next layout requested (test mode)")
            if 'set_hole_position' in actions:
                test_green.hole_position = actions['set_hole_position']
                print(f"Hole position set to: {test_green.hole_position}")
            if 'mode_change_message' in actions:
                print(actions['mode_change_message'])


        # Physics update (simplified for GUI test)
        if np.linalg.norm(test_ball.velocity) > 0.01: # Check against a small threshold
             calculate_physics(test_ball, test_green, dt_s)
             if check_ball_in_hole(test_ball, test_green):
                 print("Ball in hole! (test mode)")
                 test_ball.velocity = np.array([0.0, 0.0]) # Stop ball for test

        gui_manager.screen.fill(GREEN_MEDIUM) # Clear with a base green before drawing detailed green
        gui_manager.draw_green(test_green)
        gui_manager.draw_ball(test_ball)
        gui_manager.draw_drag_indicator(test_ball)

        # Display messages
        gui_manager.display_message(f"Ball Pos: ({test_ball.position[0]:.2f}m, {test_ball.position[1]:.2f}m)", (10, 10))
        gui_manager.display_message(f"Velocity: {np.linalg.norm(test_ball.velocity):.2f} m/s", (10, 40))
        gui_manager.display_message("Press 'R' to Reset Ball, 'L' for Next Layout (test)", (10, SCREEN_HEIGHT - 30), font_size="small")
        gui_manager.display_message("Press 'H' to Toggle Hole Editing Mode", (10, SCREEN_HEIGHT - 60), font_size="small")

        if gui_manager.editing_hole:
            current_mouse_pos_meters = gui_manager._pixels_to_meters(pygame.mouse.get_pos())
            gui_manager.display_message(f"HOLE EDITING MODE: ON - Click to place hole", (SCREEN_WIDTH // 2 - 200, 10), color=BLUE)
            gui_manager.display_message(f"Mouse (m): ({current_mouse_pos_meters[0]:.2f}, {current_mouse_pos_meters[1]:.2f})", (SCREEN_WIDTH // 2 - 200, 40), color=BLUE, font_size="small")


        gui_manager.update_display()

    gui_manager.quit_pygame()
    