"""
Main simulation class that manages all components
"""

import pygame
import random
from config import *
from vehicle import NormalCar, Truck, SportsCar, Ambulance
from pedestrian import Pedestrian
from traffic_light import TrafficLight

class TrafficSimulation:
    """Main simulation manager"""
    
    def __init__(self, screen):
        self.screen = screen
        self.vehicles = []
        self.pedestrians = []
        self.traffic_light = TrafficLight()
        
        # Simulation state
        self.paused = False
        self.time_scale = 1.0
        self.spawn_timer = 0
        self.pedestrian_spawn_timer = 0
        
        # Metrics
        self.total_cars_passed = 0
        self.total_distance_traveled = 0
        self.simulation_time = 0
        
        # Fonts
        self.font_large = pygame.font.Font(None, 36)
        self.font_medium = pygame.font.Font(None, 28)
        self.font_small = pygame.font.Font(None, 22)
        
        # Spawn initial vehicles
        self.spawn_initial_vehicles()
    
    def spawn_initial_vehicles(self):
        """Spawn initial vehicles for demonstration"""
        spacing = 200
        for i in range(INITIAL_SPAWN_COUNT // 2):
            # Spawn right-moving vehicles in lanes 0 and 1
            lane = random.choice([0, 1])
            x = i * spacing - 300
            y = ROAD_Y_START + lane * LANE_WIDTH + (LANE_WIDTH - CAR_NORMAL_WIDTH) // 2
            vehicle = self.create_random_vehicle(x, y, lane, 1)
            self.vehicles.append(vehicle)
        
        for i in range(INITIAL_SPAWN_COUNT // 2):
            # Spawn left-moving vehicles in lanes 2 and 3
            lane = random.choice([2, 3])
            x = SCREEN_WIDTH - i * spacing + 300
            y = ROAD_Y_START + lane * LANE_WIDTH + (LANE_WIDTH - CAR_NORMAL_WIDTH) // 2
            vehicle = self.create_random_vehicle(x, y, lane, -1)
            self.vehicles.append(vehicle)
    
    def create_random_vehicle(self, x, y, lane, direction):
        """Create a random vehicle type"""
        rand = random.random()
        
        if rand < AMBULANCE_SPAWN_CHANCE:
            return Ambulance(x, y, lane, direction)
        elif rand < 0.15:
            return Truck(x, y, lane, direction)
        elif rand < 0.25:
            return SportsCar(x, y, lane, direction)
        else:
            return NormalCar(x, y, lane, direction)
    
    def spawn_vehicle(self):
        """Spawn a new vehicle at road entrance"""
        # Randomly choose direction
        if random.random() < 0.5:
            # Right-moving vehicle
            direction = 1
            lane = random.choice([0, 1])
            x = -100
        else:
            # Left-moving vehicle
            direction = -1
            lane = random.choice([2, 3])
            x = SCREEN_WIDTH + 100
        
        y = ROAD_Y_START + lane * LANE_WIDTH + (LANE_WIDTH - CAR_NORMAL_WIDTH) // 2
        
        # Check if spawn position is clear
        can_spawn = True
        for v in self.vehicles:
            if v.lane == lane and v.direction == direction:
                if direction == 1 and v.x < 200:
                    can_spawn = False
                elif direction == -1 and v.x > SCREEN_WIDTH - 200:
                    can_spawn = False
        
        if can_spawn:
            vehicle = self.create_random_vehicle(x, y, lane, direction)
            self.vehicles.append(vehicle)
    
    def spawn_pedestrian(self):
        """Spawn a new pedestrian"""
        side = random.choice(["top", "bottom"])
        direction = random.choice([1, -1])
        pedestrian = Pedestrian(side, direction)
        self.pedestrians.append(pedestrian)
    
    def update(self, dt):
        """Update simulation state"""
        if self.paused:
            return
        
        self.simulation_time += dt * self.time_scale
        
        # Update traffic light
        self.traffic_light.update(dt, self.vehicles, self.time_scale)
        
        # Update vehicles
        for vehicle in self.vehicles:
            vehicle.update(dt, self.vehicles, self.traffic_light, self.time_scale)
            
            # Attempt lane changes
            if random.random() < 0.01 and vehicle.vehicle_type != "ambulance":
                vehicle.attempt_lane_change(self.vehicles)
        
        # Update pedestrians
        for pedestrian in self.pedestrians:
            pedestrian.update(dt, self.traffic_light, self.time_scale)
        
        # Remove off-screen vehicles and count passed
        self.vehicles = [v for v in self.vehicles if not self.is_offscreen(v)]
        
        # Remove finished pedestrians
        self.pedestrians = [p for p in self.pedestrians if not p.is_done()]
        
        # Spawn new vehicles
        self.spawn_timer += dt * self.time_scale
        if self.spawn_timer >= SPAWN_INTERVAL:
            self.spawn_vehicle()
            self.spawn_timer = 0
        
        # Spawn new pedestrians
        self.pedestrian_spawn_timer += dt * self.time_scale
        if self.pedestrian_spawn_timer >= PEDESTRIAN_SPAWN_INTERVAL:
            if random.random() < 0.6:  # 60% chance
                self.spawn_pedestrian()
            self.pedestrian_spawn_timer = 0
    
    def is_offscreen(self, vehicle):
        """Check if vehicle is off screen and count it"""
        if vehicle.direction == 1 and vehicle.x > SCREEN_WIDTH + 100:
            if vehicle.passed_intersection:
                self.total_cars_passed += 1
            return True
        elif vehicle.direction == -1 and vehicle.x < -100:
            if vehicle.passed_intersection:
                self.total_cars_passed += 1
            return True
        return False
    
    def draw(self):
        """Draw all simulation elements"""
        # Background
        self.screen.fill(COLOR_BG)
        
        # Draw road
        self.draw_road()
        
        # Draw intersection
        self.draw_intersection()
        
        # Draw crosswalks
        self.draw_crosswalks()
        
        # Draw traffic lights
        self.traffic_light.draw(self.screen)
        
        # Draw vehicles
        for vehicle in self.vehicles:
            vehicle.draw(self.screen)
        
        # Draw pedestrians
        for pedestrian in self.pedestrians:
            pedestrian.draw(self.screen)
        
        # Draw UI
        self.draw_ui()
    
    def draw_road(self):
        """Draw the road with lane markings"""
        # Main road surface
        road_rect = pygame.Rect(0, ROAD_Y_START, SCREEN_WIDTH, ROAD_WIDTH)
        pygame.draw.rect(self.screen, COLOR_ROAD, road_rect)
        
        # Lane markings
        for i in range(1, NUM_LANES):
            y = ROAD_Y_START + i * LANE_WIDTH
            x = 0
            while x < SCREEN_WIDTH:
                # Skip markings in intersection
                if not (INTERSECTION_X <= x <= INTERSECTION_X + INTERSECTION_WIDTH):
                    line_rect = pygame.Rect(x, y - LANE_MARKING_WIDTH // 2,
                                          LANE_MARKING_LENGTH, LANE_MARKING_WIDTH)
                    pygame.draw.rect(self.screen, COLOR_LANE_MARKING, line_rect)
                x += LANE_MARKING_LENGTH + LANE_MARKING_GAP
        
        # Center divider (double yellow line between opposing traffic)
        center_y = ROAD_Y_START + (NUM_LANES // 2) * LANE_WIDTH
        pygame.draw.line(self.screen, (255, 255, 0),
                        (0, center_y - 3), (SCREEN_WIDTH, center_y - 3), 3)
        pygame.draw.line(self.screen, (255, 255, 0),
                        (0, center_y + 3), (SCREEN_WIDTH, center_y + 3), 3)
    
    def draw_intersection(self):
        """Draw the intersection area"""
        intersection_rect = pygame.Rect(INTERSECTION_X, ROAD_Y_START,
                                       INTERSECTION_WIDTH, ROAD_WIDTH)
        pygame.draw.rect(self.screen, COLOR_ROAD, intersection_rect)
        
        # Draw stop lines
        # East approach
        pygame.draw.line(self.screen, COLOR_LANE_MARKING,
                        (INTERSECTION_X, ROAD_Y_START),
                        (INTERSECTION_X, ROAD_Y_START + ROAD_WIDTH // 2 - 5), 5)
        
        # West approach
        pygame.draw.line(self.screen, COLOR_LANE_MARKING,
                        (INTERSECTION_X + INTERSECTION_WIDTH, ROAD_Y_START + ROAD_WIDTH // 2 + 5),
                        (INTERSECTION_X + INTERSECTION_WIDTH, ROAD_Y_START + ROAD_WIDTH), 5)
    
    def draw_crosswalks(self):
        """Draw pedestrian crosswalks"""
        # North crosswalk
        self.draw_crosswalk_stripes(INTERSECTION_X + (INTERSECTION_WIDTH - CROSSWALK_WIDTH) // 2,
                                   ROAD_Y_START - CROSSWALK_WIDTH,
                                   CROSSWALK_WIDTH, CROSSWALK_WIDTH, 'horizontal')
        
        # South crosswalk
        self.draw_crosswalk_stripes(INTERSECTION_X + (INTERSECTION_WIDTH - CROSSWALK_WIDTH) // 2,
                                   ROAD_Y_START + ROAD_WIDTH,
                                   CROSSWALK_WIDTH, CROSSWALK_WIDTH, 'horizontal')
    
    def draw_crosswalk_stripes(self, x, y, width, height, orientation):
        """Draw zebra crossing stripes"""
        stripe_width = CROSSWALK_STRIPE_WIDTH
        if orientation == 'horizontal':
            num_stripes = width // (stripe_width * 2)
            for i in range(num_stripes):
                stripe_x = x + i * stripe_width * 2
                stripe_rect = pygame.Rect(stripe_x, y, stripe_width, height)
                pygame.draw.rect(self.screen, COLOR_CROSSWALK, stripe_rect)
        else:  # vertical
            num_stripes = height // (stripe_width * 2)
            for i in range(num_stripes):
                stripe_y = y + i * stripe_width * 2
                stripe_rect = pygame.Rect(x, stripe_y, width, stripe_width)
                pygame.draw.rect(self.screen, COLOR_CROSSWALK, stripe_rect)
    
    def draw_ui(self):
        """Draw user interface with metrics and controls"""
        # Semi-transparent background for UI
        ui_surface = pygame.Surface((400, 380))
        ui_surface.set_alpha(200)
        ui_surface.fill((30, 30, 30))
        self.screen.blit(ui_surface, (10, 10))
        
        y_offset = 20
        
        # Title
        title = self.font_large.render("Traffic Simulation", True, COLOR_TEXT)
        self.screen.blit(title, (20, y_offset))
        y_offset += 50
        
        # Metrics
        metrics = [
            f"Active Vehicles: {len(self.vehicles)}",
            f"Cars Passed: {self.total_cars_passed}",
            f"Avg Speed: {self.calculate_avg_speed():.1f} px/s",
            f"Queue Length: {self.calculate_queue_length()}",
            f"Pedestrians: {len(self.pedestrians)}",
            f"Time Scale: {self.time_scale:.2f}x",
            f"Light Mode: {'Adaptive' if self.traffic_light.adaptive_mode else 'Fixed'}",
            f"Light State: {self.traffic_light.state.upper()}"
        ]
        
        for metric in metrics:
            text = self.font_medium.render(metric, True, COLOR_TEXT)
            self.screen.blit(text, (20, y_offset))
            y_offset += 35
        
        # Controls
        y_offset += 10
        controls_title = self.font_medium.render("Controls:", True, (255, 255, 100))
        self.screen.blit(controls_title, (20, y_offset))
        y_offset += 35
        
        controls = [
            "SPACE - Pause/Resume",
            "UP/DOWN - Speed/Slow Time",
            "A - Toggle Adaptive Lights",
            "R - Reset Simulation"
        ]
        
        for control in controls:
            text = self.font_small.render(control, True, COLOR_TEXT)
            self.screen.blit(text, (20, y_offset))
            y_offset += 28
        
        # Pause indicator
        if self.paused:
            pause_text = self.font_large.render("PAUSED", True, (255, 100, 100))
            text_rect = pause_text.get_rect(center=(SCREEN_WIDTH // 2, 50))
            self.screen.blit(pause_text, text_rect)
    
    def calculate_avg_speed(self):
        """Calculate average speed of all vehicles"""
        if not self.vehicles:
            return 0
        total_speed = sum(v.speed for v in self.vehicles)
        return total_speed / len(self.vehicles)
    
    def calculate_queue_length(self):
        """Calculate number of stopped/slow vehicles near intersection"""
        queue = 0
        for v in self.vehicles:
            if v.speed < 20:  # Nearly stopped
                distance = abs(v.get_front_x() - INTERSECTION_X)
                if distance < 150:
                    queue += 1
        return queue
    
    def handle_keypress(self, key):
        """Handle keyboard input"""
        if key == pygame.K_SPACE:
            self.paused = not self.paused
        
        elif key == pygame.K_UP:
            self.time_scale = min(self.time_scale + TIME_SCALE_STEP, TIME_SCALE_MAX)
        
        elif key == pygame.K_DOWN:
            self.time_scale = max(self.time_scale - TIME_SCALE_STEP, TIME_SCALE_MIN)
        
        elif key == pygame.K_a:
            self.traffic_light.toggle_adaptive()
        
        elif key == pygame.K_r:
            self.reset_simulation()
    
    def reset_simulation(self):
        """Reset the simulation"""
        self.vehicles.clear()
        self.pedestrians.clear()
        self.total_cars_passed = 0
        self.simulation_time = 0
        self.spawn_timer = 0
        self.pedestrian_spawn_timer = 0
        self.traffic_light = TrafficLight()
        self.spawn_initial_vehicles()