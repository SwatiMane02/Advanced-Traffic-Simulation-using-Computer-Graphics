"""
Traffic light system with fixed-time and adaptive control
"""

import pygame
from config import *

class TrafficLight:
    """Traffic light controller for intersection"""
    
    def __init__(self):
        self.state = "ew_green"  # ew_green, ew_yellow, ns_green, ns_yellow
        self.timer = 0
        self.adaptive_mode = False
        
        # Light positions
        self.lights = {
            'north': (INTERSECTION_X + INTERSECTION_WIDTH // 2, ROAD_Y_START - 40),
            'south': (INTERSECTION_X + INTERSECTION_WIDTH // 2, ROAD_Y_START + ROAD_WIDTH + 40),
            'east': (INTERSECTION_X + INTERSECTION_WIDTH + 40, ROAD_Y_START + ROAD_WIDTH // 2),
            'west': (INTERSECTION_X - 40, ROAD_Y_START + ROAD_WIDTH // 2)
        }
    
    def update(self, dt, vehicles, time_scale):
        """Update traffic light state"""
        dt *= time_scale
        self.timer += dt
        
        # Determine transition times
        if self.adaptive_mode:
            green_time = self.calculate_adaptive_time(vehicles)
        else:
            green_time = LIGHT_GREEN_TIME
        
        # State machine
        if self.state == "ew_green":
            if self.timer >= green_time:
                self.state = "ew_yellow"
                self.timer = 0
        
        elif self.state == "ew_yellow":
            if self.timer >= LIGHT_YELLOW_TIME:
                self.state = "ns_green"
                self.timer = 0
        
        elif self.state == "ns_green":
            if self.timer >= green_time:
                self.state = "ns_yellow"
                self.timer = 0
        
        elif self.state == "ns_yellow":
            if self.timer >= LIGHT_YELLOW_TIME:
                self.state = "ew_green"
                self.timer = 0
    
    def calculate_adaptive_time(self, vehicles):
        """Calculate green light duration based on queue length"""
        # Count vehicles waiting in each direction
        ew_queue = 0
        ns_queue = 0
        
        for v in vehicles:
            if v.speed < 10:  # Vehicle is stopped or very slow
                if v.direction == 1 or v.direction == -1:
                    if abs(v.get_front_x() - INTERSECTION_X) < 200:
                        if v.lane in [0, 1]:  # East-west lanes
                            ew_queue += 1
                        else:  # North-south lanes
                            ns_queue += 1
        
        # Adjust time based on queue
        base_time = LIGHT_GREEN_TIME
        if self.state in ["ew_green", "ew_yellow"]:
            if ew_queue > ADAPTIVE_LIGHT_THRESHOLD:
                return base_time * 1.5
        elif self.state in ["ns_green", "ns_yellow"]:
            if ns_queue > ADAPTIVE_LIGHT_THRESHOLD:
                return base_time * 1.5
        
        return base_time
    
    def get_light_state(self, direction):
        """Get light color for a given direction (1=right, -1=left)"""
        # Direction 1 is east (right), -1 is west (left)
        if self.state == "ew_green":
            return "green"
        elif self.state == "ew_yellow":
            return "yellow"
        elif self.state in ["ns_green", "ns_yellow"]:
            return "red"
        return "red"
    
    def toggle_adaptive(self):
        """Toggle between fixed and adaptive timing"""
        self.adaptive_mode = not self.adaptive_mode
    
    def draw(self, screen):
        """Draw traffic lights at intersection"""
        for position, coords in self.lights.items():
            # Determine light color based on position and state
            if position in ['east', 'west']:
                if self.state == "ew_green":
                    color = COLOR_LIGHT_GREEN
                elif self.state == "ew_yellow":
                    color = COLOR_LIGHT_YELLOW
                else:
                    color = COLOR_LIGHT_RED
            else:  # north, south
                if self.state == "ns_green":
                    color = COLOR_LIGHT_GREEN
                elif self.state == "ns_yellow":
                    color = COLOR_LIGHT_YELLOW
                else:
                    color = COLOR_LIGHT_RED
            
            # Draw light housing
            housing = pygame.Rect(coords[0] - LIGHT_RADIUS - 5, coords[1] - LIGHT_RADIUS - 5,
                                LIGHT_RADIUS * 2 + 10, LIGHT_RADIUS * 2 + 10)
            pygame.draw.rect(screen, (40, 40, 40), housing, border_radius=5)
            
            # Draw light
            pygame.draw.circle(screen, color, coords, LIGHT_RADIUS)
            pygame.draw.circle(screen, (0, 0, 0), coords, LIGHT_RADIUS, 3)