"""
chicken.py

This file serves as the absolute main entry point for the golf putting simulator.
It initializes Pygame and launches the GolfPuttingSimulator from golf_putting_simulator.py.
"""

import pygame
from golf_putting_simulator import GolfPuttingSimulator

if __name__ == "__main__":
    pygame.init()
    simulator = GolfPuttingSimulator()
    simulator.run()
