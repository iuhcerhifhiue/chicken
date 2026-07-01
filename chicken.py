'''
chicken.py

This is the main entry point for the Python golf putting simulator.
It defines the core classes for the simulation and sets up basic Pygame rendering.
'''

import pygame
import sys
import math

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60

WHITE = (255, 255, 255)
GREEN = (0, 128, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# --- Classes ---

class GolfBall:
    """Represents the golf ball in the simulation."""
    def __init__(self, x, y, radius=5, color=WHITE):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.velocity_x = 0.0
        self.velocity_y = 0.0

    def update(self, dt):
        """Update ball position based on velocity and apply friction."""
        # Placeholder for physics logic (friction, gravity if applicable, etc.)
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

        # Apply simple friction (reduce velocity over time)
        friction_coeff = 0.98 # Adjust as needed
        self.velocity_x *= friction_coeff
        self.velocity_y *= friction_coeff

        # Stop if velocity is very low
        if math.sqrt(self.velocity_x**2 + self.velocity_y**2) < 0.1:
            self.velocity_x = 0.0
            self.velocity_y = 0.0

    def draw(self, screen):
        """Draw the golf ball on the screen."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)


class GolfGreen:
    """Represents the putting green, including the hole."""
    def __init__(self, width, height, hole_pos=(0,0), hole_radius=10):
        self.width = width
        self.height = height
        self.hole_pos = hole_pos
        self.hole_radius = hole_radius

    def draw(self, screen):
        """Draw the green and the hole."""
        # Draw the green background
        screen.fill(GREEN)
        # Draw the hole
        pygame.draw.circle(screen, BLACK, self.hole_pos, self.hole_radius)
        pygame.draw.circle(screen, WHITE, self.hole_pos, self.hole_radius - 2) # Inner ring for visual effect


class Simulator:
    """Manages the overall simulation, game state, and rendering."""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Golf Putting Simulator")
        self.clock = pygame.time.Clock()
        self.running = False

        self.golf_green = GolfGreen(SCREEN_WIDTH, SCREEN_HEIGHT, hole_pos=(SCREEN_WIDTH - 100, SCREEN_HEIGHT // 2))
        self.golf_ball = GolfBall(x=100, y=SCREEN_HEIGHT // 2)

        self.dragging_ball = False
        self.start_drag_pos = None

    def handle_input(self, event):
        """Handle user input for striking the ball."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                ball_rect = pygame.Rect(self.golf_ball.x - self.golf_ball.radius, 
                                        self.golf_ball.y - self.golf_ball.radius, 
                                        self.golf_ball.radius * 2, 
                                        self.golf_ball.radius * 2)
                if ball_rect.collidepoint(event.pos):
                    self.dragging_ball = True
                    self.start_drag_pos = event.pos

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and self.dragging_ball:
                self.dragging_ball = False
                end_drag_pos = event.pos
                if self.start_drag_pos:
                    # Calculate force/velocity based on drag distance and direction
                    force_vector_x = (self.start_drag_pos[0] - end_drag_pos[0]) * 0.1
                    force_vector_y = (self.start_drag_pos[1] - end_drag_pos[1]) * 0.1
                    self.golf_ball.velocity_x = force_vector_x
                    self.golf_ball.velocity_y = force_vector_y
                self.start_drag_pos = None

    def update(self, dt):
        """Update game state."""
        self.golf_ball.update(dt)
        # Check if ball is in the hole
        distance_to_hole = math.sqrt((self.golf_ball.x - self.golf_green.hole_pos[0])**2 + 
                                     (self.golf_ball.y - self.golf_green.hole_pos[1])**2)
        if distance_to_hole < self.golf_green.hole_radius - self.golf_ball.radius and \
           math.sqrt(self.golf_ball.velocity_x**2 + self.golf_ball.velocity_y**2) < 2: # Ball must be slow enough to "fall in"
            print("Ball in hole! You win!")
            self.running = False # End simulation

    def render(self):
        """Render game elements to the screen."""
        self.golf_green.draw(self.screen)
        self.golf_ball.draw(self.screen)

        # Optionally draw a line indicating drag direction/force
        if self.dragging_ball and self.start_drag_pos:
            current_mouse_pos = pygame.mouse.get_pos()
            pygame.draw.line(self.screen, RED, self.start_drag_pos, current_mouse_pos, 2)

        pygame.display.flip()

    def run(self):
        """Main simulation loop."""
        self.running = True
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0 # Time since last frame in seconds

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                self.handle_input(event)

            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    simulator = Simulator()
    simulator.run()
