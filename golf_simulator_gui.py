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
BALL_COLOR = (200, 200, 200) # Light grey for the ball
HOLE_COLOR = (0, 0, 0) # Black for the hole
RED = (255, 0, 0) # For velocity vector

# Scale factor from physics coordinates (meters) to screen coordinates (pixels)
# Assuming 1 meter = 100 pixels, adjust as necessary
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

        # State for dragging input
        self.dragging = False
        self.drag_start_pos = (0, 0) # Screen coordinates
        self.current_mouse_pos = (0, 0) # Screen coordinates

    def _meters_to_pixels(self, position_meters):
        """Converts physics coordinates (meters) to screen coordinates (pixels)."""
        # Assuming origin (0,0) for physics is bottom-left and screen origin (0,0) is top-left
        # and also scaling for the screen size.
        # This conversion might need careful adjustment based on the physics module's coordinate system.
        # For simplicity, let's assume physics (0,0) maps to screen (0, SCREEN_HEIGHT) or similar,
        # and scale appropriately.
        # Let's map physics (0,0) to screen (50, SCREEN_HEIGHT - 50) for a border,
        # and scale such that 1m = METERS_TO_PIXELS pixels.
        # This is a placeholder and will likely need tuning.
        
        # Simple direct mapping for now, assuming physics coordinates are somewhat aligned with screen.
        # If physics coordinates are small (e.g., 0-10m) and screen is 0-800 pixels:
        return (int(position_meters[0] * METERS_TO_PIXELS), 
                int(self.screen_height - (position_meters[1] * METERS_TO_PIXELS)))

    def _pixels_to_meters(self, position_pixels):
        """Converts screen coordinates (pixels) to physics coordinates (meters)."""
        return (position_pixels[0] / METERS_TO_PIXELS,
                (self.screen_height - position_pixels[1]) / METERS_TO_PIXELS)

    def draw_green(self, green_physics_obj):
        """Draws the golf green based on the physics object."""
        # For simplicity, using a solid color.
        # Advanced drawing could involve sampling elevation_map_func from green_physics_obj
        # and rendering a textured or shaded surface.
        self.screen.fill(GREEN_LIGHT)

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

    def display_message(self, message, position=(10, 10), color=BLACK):
        """Displays a message on the screen."""
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
                # Check if click is on the ball (in screen coordinates)
                ball_pos_pixels = self._meters_to_pixels(ball_physics_obj.position)
                ball_radius_pixels = int(ball_physics_obj.radius * METERS_TO_PIXELS)
                
                distance_to_ball_center = math.sqrt(
                    (event.pos[0] - ball_pos_pixels[0])**2 +
                    (event.pos[1] - ball_pos_pixels[1])**2
                )
                
                # Only start dragging if ball is stopped and clicked on
                # Check ball velocity from physics object
                if np.linalg.norm(ball_physics_obj.velocity) < ball_physics_obj.stopped_threshold and \
                   distance_to_ball_center <= ball_radius_pixels:
                    self.dragging = True
                    self.drag_start_pos = event.pos
                    self.current_mouse_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging:
                self.dragging = False
                end_drag_pos = event.pos
                if self.drag_start_pos:
                    # Calculate force vector in pixels, then convert to meters for physics
                    force_vector_pixels_x = self.drag_start_pos[0] - end_drag_pos[0]
                    force_vector_pixels_y = self.drag_start_pos[1] - end_drag_pos[1]
                    
                    # A power factor might be needed here to convert drag distance to initial velocity magnitude
                    # Let's say 10 pixels of drag = 1 m/s velocity, but this needs tuning.
                    # Or, treat drag directly as force direction and magnitude.
                    # For now, let's scale it based on pixels to meters directly.
                    
                    # Convert drag distance (pixels) to a force/impulse in meters/physics units
                    # This power_factor needs to be tuned for a good feel.
                    # Let's consider 100 pixels of drag maps to some 'impulse' that results in initial velocity.
                    # The physics module expects a force or an initial velocity.
                    # For simplicity, let's treat the drag as setting an initial velocity.
                    # The magnitude of velocity will be proportional to the drag distance.
                    
                    # This is still a bit simplified. A better approach would be to
                    # calculate an 'impulse' based on drag and then apply it to the ball.
                    # For now, let's set velocity directly.
                    
                    # Convert drag vector from screen pixels to physics meters
                    # Note the y-axis inversion for screen vs physics (if physics is bottom-left origin)
                    initial_velocity_x = force_vector_pixels_x / (METERS_TO_PIXELS * 5) # Scale factor to get reasonable velocity
                    initial_velocity_y = -force_vector_pixels_y / (METERS_TO_PIXELS * 5) # Invert Y and scale
                    
                    actions['set_ball_velocity'] = np.array([initial_velocity_x, initial_velocity_y])
                self.drag_start_pos = None
        
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.current_mouse_pos = event.pos

        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r: # Reset ball position
                actions['reset_ball'] = True
            if event.key == pygame.K_l: # Load new layout (for the green)
                actions['new_layout'] = True # Signal to the simulator to change green layout
        
        return actions

    def quit_pygame(self):
        pygame.quit()

if __name__ == '__main__':
    # Simple test of the GUI Manager
    # This block won't run when imported by chicken.py
    # It demonstrates how GUIManager would be used in a main loop
    from physics import GolfBall, GolfGreen, calculate_physics, check_ball_in_hole

    def simple_elevation(x, y):
        return 0.1 * x + 0.05 * y # Simple slope

    gui_manager = GUIManager(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # Initialize physics objects for testing
    physics_ball = GolfBall(x=0.5, y=0.5, radius=0.02135) # Meters
    physics_green = GolfGreen(elevation_map_func=simple_elevation, hole_x=7.0, hole_y=4.0, hole_radius=0.1) # Meters

    running = True
    simulation_active = False # True when ball is moving
    
    while running:
        dt_ms = gui_manager.tick()
        dt_s = dt_ms / 1000.0 # Convert to seconds

        for event in pygame.event.get():
            actions = gui_manager.handle_input_event(event, physics_ball)
            if 'quit' in actions:
                running = False
            if 'set_ball_velocity' in actions:
                physics_ball.velocity = actions['set_ball_velocity']
                simulation_active = True
            if 'reset_ball' in actions:
                physics_ball = GolfBall(x=0.5, y=0.5, radius=0.02135) # Reset ball
                simulation_active = False
            if 'new_layout' in actions:
                # Example: change hole position
                if np.array_equal(physics_green.hole_position, np.array([7.0, 4.0])):
                    physics_green.hole_position = np.array([2.0, 6.0])
                else:
                    physics_green.hole_position = np.array([7.0, 4.0])

        if simulation_active:
            calculate_physics(physics_ball, physics_green, dt_s)
            if check_ball_in_hole(physics_ball, physics_green):
                print(f"Test: Ball in hole! Position: {physics_ball.position}")
                simulation_active = False
            elif np.linalg.norm(physics_ball.velocity) < physics_ball.stopped_threshold:
                simulation_active = False
        
        gui_manager.screen.fill(WHITE) # Clear screen

        gui_manager.draw_green(physics_green)
        gui_manager.draw_ball(physics_ball)
        gui_manager.draw_drag_indicator(physics_ball)

        # Display some info
        gui_manager.display_message(f"Ball Pos: ({physics_ball.position[0]:.2f}m, {physics_ball.position[1]:.2f}m)", (10,10))
        gui_manager.display_message(f"Velocity: {np.linalg.norm(physics_ball.velocity):.2f} m/s", (10,40))
        gui_manager.display_message(f"Dragging: {gui_manager.dragging}", (10,70))


        gui_manager.update_display()

    gui_manager.quit_pygame()
    import sys
    sys.exit()
