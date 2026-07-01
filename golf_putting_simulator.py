import pygame
import math
import numpy as np

# --- Configuration ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
GREEN_COLOR_LOW = (0, 100, 0)   # Dark green for low elevation
GREEN_COLOR_HIGH = (0, 200, 0)  # Bright green for high elevation
HOLE_COLOR = (0, 0, 0)          # Black
BALL_COLOR = (255, 255, 255)    # White
BALL_RADIUS = 5
HOLE_RADIUS = 10

# --- GolfGreen Class ---
class GolfGreen:
    def __init__(self, width, height, num_points_x=50, num_points_y=50):
        self.width = width
        self.height = height
        self.num_points_x = num_points_x
        self.num_points_y = num_points_y
        self.green_data = self._generate_flat_green()
        self.ball_start_pos = (width // 4, height // 2)
        self.hole_pos = (width * 3 // 4, height // 2)

    def _generate_flat_green(self):
        """Generates a flat green for initial testing."""
        return np.zeros((self.num_points_y, self.num_points_x))

    def _generate_hills_green(self):
        """Generates a green with some hills and valleys."""
        green = np.zeros((self.num_points_y, self.num_points_x))
        x = np.linspace(0, self.width, self.num_points_x)
        y = np.linspace(0, self.height, self.num_points_y)
        X, Y = np.meshgrid(x, y)

        # Add some sine waves for elevation changes
        green += 5 * np.sin(X / 50) * np.cos(Y / 50)
        green += 3 * np.cos(X / 100 + Y / 70)
        
        # Normalize to a 0-1 range for color mapping
        green = (green - np.min(green)) / (np.max(green) - np.min(green))
        return green

    def _generate_slope_green(self):
        """Generates a green with a simple slope."""
        green = np.zeros((self.num_points_y, self.num_points_x))
        x_coords = np.linspace(0, 1, self.num_points_x)
        for i in range(self.num_points_y):
            green[i, :] = x_coords  # Simple slope from left (0) to right (1)
        return green

    def set_layout(self, layout_type):
        if layout_type == 'flat':
            self.green_data = self._generate_flat_green()
        elif layout_type == 'hills':
            self.green_data = self._generate_hills_green()
        elif layout_type == 'slope':
            self.green_data = self._generate_slope_green()
        # Reset ball position when layout changes
        self.ball_start_pos = (self.width // 4, self.height // 2)
        self.hole_pos = (self.width * 3 // 4, self.height // 2)

    def get_elevation(self, x, y):
        """Returns the elevation at a given (x, y) coordinate."""
        # Scale coordinates to green_data array indices
        idx_x = int(np.clip(x / self.width * self.num_points_x, 0, self.num_points_x - 1))
        idx_y = int(np.clip(y / self.height * self.num_points_y, 0, self.num_points_y - 1))
        return self.green_data[idx_y, idx_x]

    def draw(self, screen):
        # Draw green with color gradient based on elevation
        for y_idx in range(self.num_points_y):
            for x_idx in range(self.num_points_x):
                elevation_normalized = self.green_data[y_idx, x_idx]
                
                # Interpolate color between low and high
                r = int(GREEN_COLOR_LOW[0] + elevation_normalized * (GREEN_COLOR_HIGH[0] - GREEN_COLOR_LOW[0]))
                g = int(GREEN_COLOR_LOW[1] + elevation_normalized * (GREEN_COLOR_HIGH[1] - GREEN_COLOR_LOW[1]))
                b = int(GREEN_COLOR_LOW[2] + elevation_normalized * (GREEN_COLOR_HIGH[2] - GREEN_COLOR_LOW[2]))
                
                color = (r, g, b)
                
                # Calculate screen coordinates for this point
                rect_width = self.width / self.num_points_x
                rect_height = self.height / self.num_points_y
                
                pygame.draw.rect(screen, color, 
                                 (x_idx * rect_width, y_idx * rect_height, 
                                  math.ceil(rect_width), math.ceil(rect_height)))
        
        # Draw the hole
        pygame.draw.circle(screen, HOLE_COLOR, (int(self.hole_pos[0]), int(self.hole_pos[1])), HOLE_RADIUS)


# --- GolfBall Class ---
class GolfBall:
    def __init__(self, x, y):
        self.pos = np.array([float(x), float(y)])
        self.velocity = np.array([0.0, 0.0])
        self.radius = BALL_RADIUS
        self.in_hole = False

    def update(self, dt, green):
        if self.in_hole:
            self.velocity = np.array([0.0, 0.0])
            return

        # Simple friction model (can be expanded with green elevation/slope later)
        friction_coeff = 0.98 # Reduce velocity by 2% per frame
        self.velocity *= friction_coeff

        # Stop if velocity is very small
        if np.linalg.norm(self.velocity) < 0.1:
            self.velocity = np.array([0.0, 0.0])

        self.pos += self.velocity * dt

        # Check if ball is in hole
        distance_to_hole = np.linalg.norm(self.pos - np.array(green.hole_pos))
        if distance_to_hole < HOLE_RADIUS - self.radius:
            self.in_hole = True
            print("Ball in hole!")

    def draw(self, screen):
        if not self.in_hole:
            pygame.draw.circle(screen, BALL_COLOR, (int(self.pos[0]), int(self.pos[1])), self.radius)


# --- Main Game Class ---
class GolfSimulator:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Golf Putting Simulator")
        self.clock = pygame.time.Clock()
        self.running = True

        self.green = GolfGreen(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.ball = GolfBall(self.green.ball_start_pos[0], self.green.ball_start_pos[1])

        self.putting_mode = False
        self.putt_start_pos = None
        self.putt_current_pos = None
        
        self.font = pygame.font.Font(None, 36)

    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    if not self.putting_mode and np.linalg.norm(self.ball.velocity) < 0.1: # Only putt if ball is stopped
                        self.putting_mode = True
                        self.putt_start_pos = event.pos
                        self.putt_current_pos = event.pos
            elif event.type == pygame.MOUSEMOTION:
                if self.putting_mode:
                    self.putt_current_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.putting_mode:
                    self.putting_mode = False
                    if self.putt_start_pos and self.putt_current_pos:
                        # Calculate putt vector (from current mouse pos to start pos)
                        # This makes dragging away from the ball set the direction of the putt
                        putt_vector = np.array(self.putt_start_pos) - np.array(self.putt_current_pos)
                        
                        # Scale velocity based on drag distance
                        putt_strength = np.linalg.norm(putt_vector) * 0.1 # Adjust multiplier for sensitivity
                        
                        if putt_strength > 0:
                            # Apply velocity
                            self.ball.velocity = (putt_vector / np.linalg.norm(putt_vector)) * putt_strength
                            self.ball.in_hole = False # Reset in_hole state when a new putt is made
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    self.green.set_layout('flat')
                    self.ball = GolfBall(self.green.ball_start_pos[0], self.green.ball_start_pos[1])
                elif event.key == pygame.K_2:
                    self.green.set_layout('hills')
                    self.ball = GolfBall(self.green.ball_start_pos[0], self.green.ball_start_pos[1])
                elif event.key == pygame.K_3:
                    self.green.set_layout('slope')
                    self.ball = GolfBall(self.green.ball_start_pos[0], self.green.ball_start_pos[1])
                elif event.key == pygame.K_r: # Reset ball position
                    self.ball = GolfBall(self.green.ball_start_pos[0], self.green.ball_start_pos[1])
                    self.ball.in_hole = False


    def _update_game_state(self, dt):
        self.ball.update(dt, self.green)

    def _draw_elements(self):
        self.screen.fill((0, 0, 0))  # Clear screen with black

        self.green.draw(self.screen)
        self.ball.draw(self.screen)

        # Draw putting line if in putting mode and ball is stopped
        if self.putting_mode and self.putt_start_pos and self.putt_current_pos and np.linalg.norm(self.ball.velocity) < 0.1:
            pygame.draw.line(self.screen, (255, 255, 255), self.ball.pos, self.putt_current_pos, 2)
            # Draw a directional arrow (simplified)
            arrow_length = 20
            direction = np.array(self.ball.pos) - np.array(self.putt_current_pos)
            if np.linalg.norm(direction) > 0:
                direction = direction / np.linalg.norm(direction)
                end_point = self.ball.pos + direction * arrow_length
                pygame.draw.line(self.screen, (255, 0, 0), self.ball.pos, end_point, 3) # Red arrow

        # Display instructions
        instruction_text = self.font.render("1: Flat, 2: Hills, 3: Slope, R: Reset Ball, Drag: Putt", True, (255, 255, 255))
        self.screen.blit(instruction_text, (10, 10))

        if self.ball.in_hole:
            win_text = self.font.render("Ball in Hole! Press 'R' to reset or change layout.", True, (255, 255, 0))
            text_rect = win_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
            self.screen.blit(win_text, text_rect)


        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0 # Delta time in seconds
            self._handle_input()
            self._update_game_state(dt)
            self._draw_elements()

        pygame.quit()


if __name__ == "__main__":
    game = GolfSimulator()
    game.run()
