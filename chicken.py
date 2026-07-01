#!/usr/bin/env python3

import pygame
import sys
import math

# --- Constants ---
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
WHITE = (255, 255, 255)
GREEN = (0, 100, 0)
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# --- GolfBall Class ---
class GolfBall:
    def __init__(self, x, y, radius=10, color=WHITE):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.velocity_x = 0
        self.velocity_y = 0
        self.friction = 0.98 # Simple friction model

    def apply_force(self, force_x, force_y):
        # This will be used to simulate a "putt"
        # For simplicity, we directly update velocity for now.
        self.velocity_x += force_x
        self.velocity_y += force_y

    def update(self, dt):
        # Apply friction
        self.velocity_x *= self.friction
        self.velocity_y *= self.friction

        # Update position
        self.x += self.velocity_x * dt
        self.y += self.velocity_y * dt

        # Stop if velocity is very low
        if abs(self.velocity_x) < 0.1:
            self.velocity_x = 0
        if abs(self.velocity_y) < 0.1:
            self.velocity_y = 0

    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.radius)

# --- GolfGreen Class ---
class GolfGreen:
    def __init__(self, width, height, hole_pos=(width - 50, height / 2), hole_radius=15, color=GREEN):
        self.width = width
        self.height = height
        self.color = color
        self.hole_pos = hole_pos
        self.hole_radius = hole_radius

    def draw(self, screen):
        # Draw the green background
        screen.fill(self.color)
        # Draw the hole
        pygame.draw.circle(screen, BLACK, (int(self.hole_pos[0]), int(self.hole_pos[1])), self.hole_radius)
        # Draw a red flag pole for visibility
        pygame.draw.line(screen, RED, (int(self.hole_pos[0]), int(self.hole_pos[1] - self.hole_radius - 30)),
                         (int(self.hole_pos[0]), int(self.hole_pos[1] - self.hole_radius)), 3)


# --- Simulator Class ---
class Simulator:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Python Golf Putting Simulator")
        self.clock = pygame.time.Clock()

        self.green = GolfGreen(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.ball = GolfBall(50, SCREEN_HEIGHT / 2) # Start ball on the left

        self.running = True
        self.putting = False # State to check if a putt is in progress
        self.start_putt_pos = None # Position where the mouse was clicked to start the putt

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: # Left click
                    self.putting = True
                    self.start_putt_pos = event.pos
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1 and self.putting:
                    end_putt_pos = event.pos
                    if self.start_putt_pos:
                        # Calculate the force vector based on mouse drag
                        # The longer the drag, the stronger the putt.
                        # Direction is opposite to drag for intuitive "pull back" action.
                        force_x = (self.start_putt_pos[0] - end_putt_pos[0]) * 0.1 # Scale factor
                        force_y = (self.start_putt_pos[1] - end_putt_pos[1]) * 0.1
                        self.ball.apply_force(force_x, force_y)
                    self.putting = False
                    self.start_putt_pos = None

    def update(self, dt):
        self.ball.update(dt)

        # Check for collision with hole
        distance_to_hole = math.hypot(self.ball.x - self.green.hole_pos[0], self.ball.y - self.green.hole_pos[1])
        if distance_to_hole < self.green.hole_radius - self.ball.radius:
            print("Ball in hole! Game Over.")
            self.running = False # End simulation when ball enters hole

        # Basic boundary collision
        if self.ball.x - self.ball.radius < 0 or self.ball.x + self.ball.radius > SCREEN_WIDTH:
            self.ball.velocity_x *= -0.5 # Bounce with some energy loss
            if self.ball.x - self.ball.radius < 0: self.ball.x = self.ball.radius
            if self.ball.x + self.ball.radius > SCREEN_WIDTH: self.ball.x = SCREEN_WIDTH - self.ball.radius

        if self.ball.y - self.ball.radius < 0 or self.ball.y + self.ball.radius > SCREEN_HEIGHT:
            self.ball.velocity_y *= -0.5 # Bounce with some energy loss
            if self.ball.y - self.ball.radius < 0: self.ball.y = self.ball.radius
            if self.ball.y + self.ball.radius > SCREEN_HEIGHT: self.ball.y = SCREEN_HEIGHT - self.ball.radius


    def draw(self):
        self.green.draw(self.screen)
        self.ball.draw(self.screen)

        # Draw putting indicator
        if self.putting and self.start_putt_pos:
            current_mouse_pos = pygame.mouse.get_pos()
            pygame.draw.line(self.screen, BLACK, self.start_putt_pos, current_mouse_pos, 2)
            # Draw an arrow indicating direction of force
            arrow_vec_x = self.start_putt_pos[0] - current_mouse_pos[0]
            arrow_vec_y = self.start_putt_pos[1] - current_mouse_pos[1]
            # Normalize and scale for arrow head
            length = math.hypot(arrow_vec_x, arrow_vec_y)
            if length > 0:
                norm_x = arrow_vec_x / length
                norm_y = arrow_vec_y / length
                arrow_end_x = self.start_putt_pos[0] + norm_x * 20 # Arrow head length
                arrow_end_y = self.start_putt_pos[1] + norm_y * 20
                pygame.draw.line(self.screen, BLACK, self.start_putt_pos, (arrow_end_x, arrow_end_y), 2)


        pygame.display.flip()

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0 # Delta time in seconds
            self.handle_input()
            self.update(dt)
            self.draw()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    simulator = Simulator()
    simulator.run()
