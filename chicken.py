import sys
import pygame
import numpy as np

# Import physics components
from physics import GolfBall, GolfGreen, calculate_physics, check_ball_in_hole

# Import GUI components
from golf_simulator_gui import GUIManager, SCREEN_WIDTH, SCREEN_HEIGHT


# --- Elevation Map Functions (can be moved to a dedicated module later if complex) ---
def simple_elevation_flat(x, y):
    """A completely flat green."""
    return 0.0

def simple_elevation_slope(x, y):
    """A simple linear slope across the green."""
    return 0.05 * x + 0.03 * y  # Gentle slope in x and y

def simple_elevation_hill(x, y):
    """A small hill or dip in the middle."""
    center_x, center_y = 4.0, 3.0  # Center of the green in meters
    distance_from_center_sq = (x - center_x)**2 + (y - center_y)**2
    return -0.01 * distance_from_center_sq + 0.1 # A slight peak at the center, then dips


class Simulator:
    """Manages the overall golf putting simulation, orchestrating physics and GUI."""

    def __init__(self):
        self.gui_manager = GUIManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Initialize physics objects
        # Starting ball position (meters), adjusting for screen coordinate mapping
        # assuming physics (0,0) is bottom-left of the usable area and ball starts near GUI left edge.
        # Let's say the green is roughly 8m x 6m (based on SCREEN_WIDTH/HEIGHT and METERS_TO_PIXELS=100)
        self.ball = GolfBall(x=1.0, y=3.0) # Start 1m from left, 3m from bottom (approx middle height)
        self.current_elevation_func_idx = 0
        self.elevation_functions = [
            simple_elevation_flat,
            simple_elevation_slope,
            simple_elevation_hill
        ]
        self.green = self._initialize_green()
        self.running = False
        self.game_over = False

    def _initialize_green(self, layout_index=0):
        """Initializes or re-initializes the GolfGreen with a specific layout."""
        elevation_func = self.elevation_functions[layout_index % len(self.elevation_functions)]
        # Hole position in meters (e.g., 7m from left, 3m from bottom, adjusted to be towards the right)
        hole_x = 7.0
        hole_y = 3.0
        # Example: vary hole position for different layouts
        if layout_index == 1: # Slope
            hole_x = 7.5
            hole_y = 5.0
        elif layout_index == 2: # Hill
            hole_x = 6.0
            hole_y = 2.0

        self.current_elevation_func_idx = layout_index % len(self.elevation_functions)
        return GolfGreen(elevation_map_func=elevation_func, hole_x=hole_x, hole_y=hole_y)

    def _reset_ball(self):
        """Resets the ball to its initial position and stops its velocity."""
        self.ball = GolfBall(x=1.0, y=3.0) # Reset to initial position
        self.game_over = False # Allow new strokes

    def run(self):
        """Main simulation loop."""
        self.running = True
        while self.running:
            dt_ms = self.gui_manager.tick() # Get time since last frame in milliseconds
            dt_s = dt_ms / 1000.0          # Convert to seconds for physics calculations

            # --- Event Handling ---
            for event in pygame.event.get():
                actions = self.gui_manager.handle_input_event(event, self.ball)
                
                if 'quit' in actions:
                    self.running = False
                
                if 'set_ball_velocity' in actions and not self.game_over:
                    self.ball.velocity = actions['set_ball_velocity']
                
                if 'reset_ball' in actions:
                    self._reset_ball()
                    self.green = self._initialize_green(self.current_elevation_func_idx) # Keep same green layout

                if 'new_layout' in actions:
                    self._reset_ball()
                    self.green = self._initialize_green(self.current_elevation_func_idx + 1) # Cycle to next layout

            # --- Physics Update ---
            # Only update physics if ball is moving
            if np.linalg.norm(self.ball.velocity) > self.ball.stopped_threshold and not self.game_over:
                calculate_physics(self.ball, self.green, dt_s)

                # Check for ball in hole
                if check_ball_in_hole(self.ball, self.green):
                    print("Ball in hole! You win!")
                    self.game_over = True
            elif np.linalg.norm(self.ball.velocity) <= self.ball.stopped_threshold and not self.game_over:
                # If ball has just stopped (and wasn't already game over)
                # Set velocity to zero to ensure it's completely stopped for next stroke
                self.ball.velocity = np.array([0.0, 0.0])

            # --- Rendering ---
            self.gui_manager.screen.fill((200, 255, 200)) # Clear screen with a light green background

            self.gui_manager.draw_green(self.green)
            self.gui_manager.draw_ball(self.ball)
            self.gui_manager.draw_drag_indicator(self.ball) # Pass the ball object for its velocity property

            # Display messages
            self.gui_manager.display_message(f"Ball Pos: ({self.ball.position[0]:.2f}m, {self.ball.position[1]:.2f}m)", (10, 10))
            self.gui_manager.display_message(f"Velocity: {np.linalg.norm(self.ball.velocity):.2f} m/s", (10, 40))
            self.gui_manager.display_message(f"Layout: {self.current_elevation_func_idx + 1}/{len(self.elevation_functions)}", (10, 70))

            if self.game_over:
                self.gui_manager.display_message("GAME OVER - Ball in Hole! (Press 'R' to Reset)", (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2), (0,0,255))

            self.gui_manager.update_display()

        self.gui_manager.quit_pygame()
        sys.exit()


if __name__ == "__main__":
    simulator = Simulator()
    simulator.run()
