"""
Traffic Flow Simulation - Main Entry Point
A comprehensive traffic simulation with vehicles, pedestrians, traffic lights, and emergency vehicles.
"""

import pygame
import sys
from simulation import TrafficSimulation
from config import *

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Advanced Traffic Flow Simulation")
    clock = pygame.time.Clock()
    
    simulation = TrafficSimulation(screen)
    
    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                simulation.handle_keypress(event.key)
        
        simulation.update(dt)
        simulation.draw()
        
        pygame.display.flip()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()