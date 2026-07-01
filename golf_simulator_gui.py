import pygame
import sys
import math

# Initialize Pygame
pygame.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
SCREEN = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Golf Putting Simulator")

# Colors
WHITE = (255, 255, 255)
GREEN_DARK = (0, 100, 0)
GREEN_LIGHT = (0, 150, 0)
BALL_COLOR = (200, 200, 200) # Light grey for the ball
HOLE_COLOR = (0, 0, 0) # Black for the hole
RED = (255, 0, 0) # For velocity vector

# GolfBall class
class GolfBall:
    def __init__(self, x, y, radius=10):
        self.x = x
        self.y = y
        self.radius = radius
        self.velocity_x = 0
        self.velocity_y = 0
        self.friction = 0.98 # Simple friction model
        self.stopped_threshold = 0.1

    def move(self):
        # Apply friction
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction

        # Update position
        self.x += self.velocity_x
        self.y += self.velocity_y

        # Stop if velocity is very low
        if abs(self.velocity_x) < self.stopped_threshold and abs(self.velocity_y) < self.stopped_threshold:
            self.velocity_x = 0
            self.velocity_y = 0

        # Keep ball within screen bounds (simple collision)
        if self.x - self.radius < 0:
            self.x = self.radius
            self.velocity_x *= -0.5 # Bounce with some energy loss
        if self.x + self.radius > SCREEN_WIDTH:
            self.x = SCREEN_WIDTH - self.radius
            self.velocity_x *= -0.5
        if self.y - self.radius < 0:
            self.y = self.radius
            self.velocity_y *= -0.5
        if self.y + self.radius > SCREEN_HEIGHT:
            self.y = SCREEN_HEIGHT - self.radius
            self.velocity_y *= -0.5

    def draw(self, screen):
        pygame.draw.circle(screen, BALL_COLOR, (int(self.x), int(self.y)), self.radius)

    def set_velocity(self, start_pos, end_pos, power_factor=0.1):
        # Calculate vector from start_pos to end_pos
        dx = end_pos[0] - start_pos[0]
        dy = end_pos[1] - start_pos[1]
        self.velocity_x = dx * power_factor
        self.velocity_y = dy * power_factor

# GolfGreen class
class GolfGreen:
    def __init__(self, width, height, hole_pos=(0,0)):
        self.width = width
        self.height = height
        self.elevation_map = [[0 for _ in range(width // 10)] for _ in range(height // 10)] # Dummy elevation map
        self.hole_pos = hole_pos
        self.hole_radius = 15

    def draw(self, screen):
        # Draw the green surface
        # For simplicity, using a solid color.
        # To implement gradients for elevation:
        # Iterate over sections of the screen, calculate a color based on dummy elevation_map value
        # and use pygame.draw.rect or similar for smaller sections.
        # Example:
        # for y_idx, row in enumerate(self.elevation_map):
        #     for x_idx, elevation in enumerate(row):
        #         # Map elevation to color intensity
        #         color_intensity = min(255, max(0, int(elevation * 10) + 50)) # Example mapping
        #         color = (0, color_intensity, 0)
        #         pygame.draw.rect(screen, color, (x_idx*10, y_idx*10, 10, 10))
        pygame.draw.rect(screen, GREEN_LIGHT, (0, 0, self.width, self.height))

        # Draw the golf hole
        pygame.draw.circle(screen, HOLE_COLOR, self.hole_pos, self.hole_radius)

    def get_elevation(self, x, y):
        # In a real scenario, this would return elevation at (x,y)
        return 0 # Placeholder

# Game setup
ball = GolfBall(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
green = GolfGreen(SCREEN_WIDTH, SCREEN_HEIGHT, hole_pos=(SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2))

# Game state
dragging = False
drag_start_pos = (0, 0)
current_mouse_pos = (0, 0)

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1: # Left click
                if ball.velocity_x == 0 and ball.velocity_y == 0: # Only start dragging if ball is stopped
                    dragging = True
                    drag_start_pos = event.pos
                    current_mouse_pos = event.pos
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1 and dragging:
                dragging = False
                ball.set_velocity(drag_start_pos, current_mouse_pos, power_factor=0.08) # Adjust power_factor as needed
        if event.type == pygame.MOUSEMOTION:
            if dragging:
                current_mouse_pos = event.pos
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_r: # Reset ball position
                ball = GolfBall(SCREEN_WIDTH // 4, SCREEN_HEIGHT // 2)
            if event.key == pygame.K_l: # Load new layout (simple cycle for now)
                # This could involve changing green.hole_pos or even the elevation map
                if green.hole_pos == (SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2):
                    green.hole_pos = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 4)
                else:
                    green.hole_pos = (SCREEN_WIDTH * 3 // 4, SCREEN_HEIGHT // 2)


    # Game logic updates
    ball.move()

    # Drawing
    SCREEN.fill(WHITE) # Clear screen

    green.draw(SCREEN)
    ball.draw(SCREEN)

    # Draw the velocity vector if dragging
    if dragging:
        pygame.draw.line(SCREEN, RED, drag_start_pos, current_mouse_pos, 2)
        # Optional: draw an arrow head
        # Calculate angle of line
        dx = current_mouse_pos[0] - drag_start_pos[0]
        dy = current_mouse_pos[1] - drag_start_pos[1]
        angle = math.atan2(dy, dx)
        arrow_length = 20
        pygame.draw.line(SCREEN, RED, current_mouse_pos,
                         (current_mouse_pos[0] - arrow_length * math.cos(angle - math.pi / 6),
                          current_mouse_pos[1] - arrow_length * math.sin(angle - math.pi / 6)), 2)
        pygame.draw.line(SCREEN, RED, current_mouse_pos,
                         (current_mouse_pos[0] - arrow_length * math.cos(angle + math.pi / 6),
                          current_mouse_pos[1] - arrow_length * math.sin(angle + math.pi / 6)), 2)


    pygame.display.flip() # Update the full display Surface to the screen

    # Cap the frame rate
    pygame.time.Clock().tick(60)

pygame.quit()
sys.exit()
