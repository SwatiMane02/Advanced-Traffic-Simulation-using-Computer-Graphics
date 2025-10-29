"""
Pedestrian class for crosswalk simulation
"""

import pygame
from config import *

class Pedestrian:
    """Pedestrian that crosses at crosswalks"""
    
    def __init__(self, side, direction):
        """
        side: 'top' or 'bottom' (which side of road)
        direction: 1 for crossing right, -1 for crossing left
        """
        self.side = side
        self.direction = direction
        self.state = "waiting"  # waiting, crossing, done
        self.wait_timer = 0
        
        # Position pedestrian at crosswalk
        if side == "top":
            self.y = ROAD_Y_START - 30
            self.target_y = ROAD_Y_START + ROAD_WIDTH + 30
        else:
            self.y = ROAD_Y_START + ROAD_WIDTH + 30
            self.target_y = ROAD_Y_START - 30
        
        # Start from the side
        if direction == 1:
            self.x = INTERSECTION_X - 50
        else:
            self.x = INTERSECTION_X + INTERSECTION_WIDTH + 50
        
        self.color = COLOR_PEDESTRIAN
    
    def update(self, dt, traffic_light, time_scale):
        """Update pedestrian behavior"""
        dt *= time_scale
        
        if self.state == "waiting":
            self.wait_timer += dt
            # Wait a bit, then check if safe to cross
            if self.wait_timer > CROSSWALK_WAIT_TIME:
                # Pedestrians cross when light is red for their crossing direction
                # For simplicity, they cross when vertical traffic has green
                if traffic_light.state in ['ns_green', 'ns_yellow']:
                    self.state = "crossing"
        
        elif self.state == "crossing":
            # Cross the road
            if self.side == "top":
                self.y += PEDESTRIAN_SPEED * dt
                if self.y >= self.target_y:
                    self.state = "done"
            else:
                self.y -= PEDESTRIAN_SPEED * dt
                if self.y <= self.target_y:
                    self.state = "done"
    
    def draw(self, screen):
        """Draw pedestrian as a simple figure"""
        if self.state == "done":
            return
        
        # Draw as circle (head) and rectangle (body)
        head_radius = PEDESTRIAN_SIZE // 2
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), head_radius)
        
        body_rect = pygame.Rect(
            int(self.x - head_radius // 2),
            int(self.y + head_radius),
            head_radius,
            head_radius * 2
        )
        pygame.draw.rect(screen, self.color, body_rect)
        
        # Draw legs
        leg_height = head_radius
        pygame.draw.line(screen, self.color,
                        (int(self.x - head_radius // 3), int(self.y + head_radius * 3)),
                        (int(self.x - head_radius // 3), int(self.y + head_radius * 3 + leg_height)), 3)
        pygame.draw.line(screen, self.color,
                        (int(self.x + head_radius // 3), int(self.y + head_radius * 3)),
                        (int(self.x + head_radius // 3), int(self.y + head_radius * 3 + leg_height)), 3)
    
    def is_done(self):
        """Check if pedestrian finished crossing"""
        return self.state == "done"