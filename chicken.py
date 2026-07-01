
"""
chicken.py

This file serves as the main entry point and orchestrator for the golf putting simulator.
It imports and integrates the physics engine (from `physics.py`) and the graphical user interface
components (from `golf_simulator_gui.py`) to create a cohesive simulation experience.

The `Simulator` class encapsulates the entire application logic, including:
- Initializing Pygame and GUI elements.
- Setting up golf ball and green physics objects.
- Managing different green elevation layouts.
- Handling user input for ball strokes, resets, layout changes, and hole editing.
- Running the main simulation loop, which processes events, updates physics, and renders the scene.

To run the simulation, execute this file directly.
"""

import sys
import pygame
import numpy as np

# Import physics components: GolfBall, GolfGreen classes, and physics calculation functions.
from physics import GolfBall, GolfGreen, calculate_physics, check_ball_in_hole

# Import GUI components: GUIManager class and screen dimensions for setup.
from golf_simulator_gui import GUIManager, SCREEN_WIDTH, SCREEN_HEIGHT, GREEN_MEDIUM


# --- Elevation Map Functions ---
# These functions define different golf green terrains by returning an elevation (z) for a given (x, y) coordinate.
# They are currently defined here as they are directly used by the Simulator for green initialization.
# For a more complex application, these could be moved to a dedicated 'terrain_definitions.py' module
# to further separate concerns and improve modularity.
def simple_elevation_flat(x, y):
    """A completely flat green, returning a constant elevation of 0.0."""
    return 0.0

def simple_elevation_slope(x, y):
    """A simple linear slope across the green, gradually increasing elevation."""
    return 0.05 * x + 0.03 * y  # Gentle slope in x and y

def simple_elevation_hill(x, y):
    """A small hill or dip, with its peak/dip centered at (4.0, 3.0) meters."""
    center_x, center_y = 4.0, 3.0  # Center of the green in meters
    distance_from_center_sq = (x - center_x)**2 + (y - center_y)**2
    return -0.01 * distance_from_center_sq + 0.1 # A slight peak at the center, then dips


class Simulator:
    """
    The core simulation class responsible for orchestrating the golf putting game.
    It manages the game state, integrates physics and GUI, and controls the main game loop.
    """

    def __init__(self):
        """Initializes the simulator, setting up the GUI, ball, and green."""
        self.gui_manager = GUIManager(SCREEN_WIDTH, SCREEN_HEIGHT)

        # Initialize physics objects
        # Ball starts at (1.0m, 3.0m) within the green's coordinate system.
        self.ball = GolfBall(x=1.0, y=3.0)

        # Define available elevation functions and set the initial green layout.
        self.current_elevation_func_idx = 0
        self.elevation_functions = [
            simple_elevation_flat,
            simple_elevation_slope,
            simple_elevation_hill
        ]
        self.green = self._initialize_green() # Initialize with the default green layout.

        self.running = False  # Flag to control the main game loop.
        self.game_over = False # Flag to indicate if the ball is in the hole or stopped.

    def _initialize_green(self, layout_index=None):
        """
        Initializes or re-initializes the GolfGreen with a specific layout.
        Cycles through predefined elevation functions.
        """
        if layout_index is None:
            layout_index = self.current_elevation_func_idx # Use current layout if none specified.
        
        # Cycle the layout index to stay within the bounds of elevation_functions.
        self.current_elevation_func_idx = layout_index % len(self.elevation_functions)
        elevation_func = self.elevation_functions[self.current_elevation_func_idx]

        # Default hole position for a new green layout.
        hole_x = 7.0
        hole_y = 3.0
        
        # If re-initializing the *same* layout (e.g., after a ball reset),
        # preserve the existing hole position. Otherwise, set default for new layouts.
        if hasattr(self, 'green') and layout_index == self.current_elevation_func_idx: 
            hole_x = self.green.hole_position[0]
            hole_y = self.green.hole_position[1]
        else: 
            # Specific default hole positions for different pre-defined layouts.
            if self.current_elevation_func_idx == 1: # Slope green
                hole_x = 7.5
                hole_y = 5.0
            elif self.current_elevation_func_idx == 2: # Hill green
                hole_x = 6.0
                hole_y = 2.0

        return GolfGreen(elevation_map_func=elevation_func, hole_x=hole_x, hole_y=hole_y)

    def _reset_ball(self):
        """Resets the ball to its initial starting position and clears its velocity."""
        self.ball = GolfBall(x=1.0, y=3.0) # Reset to initial physics position.
        self.game_over = False # Allow new strokes after reset.

    def run(self):
        """
        The main simulation loop of the game.
        This loop continuously handles user input, updates the physics state,
        and renders the current game scene until the application is closed.
        """
        self.running = True
        while self.running:
            dt_ms = self.gui_manager.tick() # Get elapsed time in milliseconds for frame rate capping.
            dt_s = dt_ms / 1000.0          # Convert to seconds for physics calculations.

            # --- Event Handling ---
            # Process all pending Pygame events.
            for event in pygame.event.get():
                actions = self.gui_manager.handle_input_event(event, self.ball)
                
                if 'quit' in actions:
                    self.running = False
                
                if 'set_ball_velocity' in actions and not self.game_over:
                    self.ball.velocity = actions['set_ball_velocity']
                
                if 'reset_ball' in actions:
                    self._reset_ball()
                    # Re-initialize green to refresh internal state, but keep the same layout and hole position.
                    self.green = self._initialize_green(self.current_elevation_func_idx)

                if 'next_layout' in actions:
                    self._reset_ball()
                    self.green = self._initialize_green(self.current_elevation_func_idx + 1) # Cycle to next layout.

                if 'set_hole_position' in actions:
                    new_hole_pos = actions['set_hole_position']
                    self.green.hole_position = new_hole_pos # Update the existing green's hole position.
                    print(f"Hole position updated to: {new_hole_pos}") # Log the change.

                if 'mode_change_message' in actions:
                    print(actions['mode_change_message']) # Log messages related to mode changes.

            # --- Physics Update ---
            # Physics only updates if the ball is currently moving and the game is not over.
            if np.linalg.norm(self.ball.velocity) > self.ball.stopped_threshold and not self.game_over:
                calculate_physics(self.ball, self.green, dt_s)

                # Check if the ball has entered the hole after physics update.
                if check_ball_in_hole(self.ball, self.green):
                    print("Ball in hole! You win!")
                    self.game_over = True # End the current game.
            elif np.linalg.norm(self.ball.velocity) <= self.ball.stopped_threshold and not self.game_over:
                # If the ball has just come to a stop (and was not already game over),
                # explicitly set its velocity to zero to ensure complete stop for the next stroke.
                self.ball.velocity = np.array([0.0, 0.0])

            # --- Rendering ---
            # Draw the game elements using the GUI manager.
            self.gui_manager.draw_green(self.green)
            self.gui_manager.draw_ball(self.ball)
            self.gui_manager.draw_drag_indicator(self.ball)

            # Display various informational messages on the screen.
            self.gui_manager.display_message(f"Ball Pos: ({self.ball.position[0]:.2f}m, {self.ball.position[1]:.2f}m)", (10, 10))
            self.gui_manager.display_message(f"Velocity: {np.linalg.norm(self.ball.velocity):.2f} m/s", (10, 40))
            self.gui_manager.display_message(f"Layout: {self.current_elevation_func_idx + 1}/{len(self.elevation_functions)} (L to change)", (10, 70))
            self.gui_manager.display_message("'H' to Toggle Hole Editing Mode", (10, 100))

            # Display game over message if applicable.
            if self.game_over:
                self.gui_manager.display_message("GAME OVER - Ball in Hole! (Press 'R' to Reset)", (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT // 2), (0,0,255))

            # Display hole editing mode specific messages if active.
            if self.gui_manager.editing_hole:
                current_mouse_pos_meters = self.gui_manager._pixels_to_meters(pygame.mouse.get_pos())
                self.gui_manager.display_message(f"HOLE EDITING MODE: ON - Click to place hole", (SCREEN_WIDTH // 2 - 200, 10), color=(0, 0, 255), font_size="normal")
                self.gui_manager.display_message(f"Mouse (m): ({current_mouse_pos_meters[0]:.2f}, {current_mouse_pos_meters[1]:.2f})", (SCREEN_WIDTH // 2 - 200, 40), color=(0, 0, 255), font_size="small")

            self.gui_manager.update_display() # Refresh the display.

        self.gui_manager.quit_pygame() # Clean up Pygame resources upon exiting the loop.
        sys.exit() # Terminate the application.


if __name__ == "__main__":
    """
    Main execution block for the golf simulation application.
    This ensures that the `Simulator` is initialized and run only when `chicken.py`
    is executed directly, not when imported as a module.
    """
    simulator = Simulator()
    simulator.run()
