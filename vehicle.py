"""
Vehicle classes for traffic simulation
Includes normal cars, trucks, sports cars, and emergency vehicles
"""

import pygame
import random
from config import *

class Vehicle:
    """Base vehicle class with car-following behavior"""
    
    def __init__(self, x, y, lane, direction, length, width, max_speed, acceleration, color, vehicle_type):
        self.x = x
        self.y = y
        self.lane = lane
        self.direction = direction  # 1 for right, -1 for left
        self.length = length
        self.width = width
        self.max_speed = max_speed
        self.acceleration = acceleration
        self.color = color
        self.vehicle_type = vehicle_type
        
        self.speed = max_speed * 0.8  # Start at 80% max speed
        self.target_speed = self.max_speed
        self.lane_change_cooldown = 0
        self.passed_intersection = False
        self.stopped_at_light = False
        
    def get_rect(self):
        """Return pygame rect for collision detection"""
        if self.direction == 1:
            return pygame.Rect(self.x, self.y, self.length, self.width)
        else:
            return pygame.Rect(self.x - self.length, self.y, self.length, self.width)
    
    def get_front_x(self):
        """Get x position of vehicle front"""
        return self.x if self.direction == 1 else self.x - self.length
    
    def update(self, dt, vehicles, traffic_light, time_scale):
        """Update vehicle position and behavior"""
        dt *= time_scale
        
        # Update cooldowns
        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= dt
        
        # Check for vehicle ahead
        vehicle_ahead = self.find_vehicle_ahead(vehicles)
        
        # Check traffic light
        light_distance = self.distance_to_light(traffic_light)
        should_stop_at_light = False
        
        if light_distance is not None and light_distance > 0 and light_distance < 150:
            if traffic_light.get_light_state(self.direction) in ['red', 'yellow']:
                should_stop_at_light = True
                self.stopped_at_light = True
        
        # Determine target speed
        if should_stop_at_light and light_distance < 100:
            # Decelerate for red/yellow light
            stop_distance = max(light_distance - 10, 0)
            if stop_distance < 50:
                self.target_speed = 0
            else:
                self.target_speed = self.max_speed * (stop_distance / 100)
        elif vehicle_ahead:
            # Car following behavior
            gap = self.distance_to_vehicle(vehicle_ahead)
            if gap < SAFE_DISTANCE:
                # Too close, slow down
                self.target_speed = vehicle_ahead.speed * 0.9
            elif gap < SAFE_DISTANCE * 2:
                # Maintain safe distance
                self.target_speed = vehicle_ahead.speed
            else:
                # Speed up to max
                self.target_speed = self.max_speed
        else:
            # No obstacles, go max speed
            self.target_speed = self.max_speed
            if self.stopped_at_light and light_distance and light_distance > 50:
                self.stopped_at_light = False
        
        # Accelerate/decelerate smoothly
        if self.speed < self.target_speed:
            self.speed = min(self.speed + self.acceleration * dt, self.target_speed)
        elif self.speed > self.target_speed:
            decel = self.acceleration * 1.5  # Brake harder than accelerate
            self.speed = max(self.speed - decel * dt, self.target_speed, 0)
        
        # Move vehicle
        self.x += self.speed * dt * self.direction
        
        # Mark if passed intersection
        if self.direction == 1 and self.x > INTERSECTION_X + INTERSECTION_WIDTH:
            self.passed_intersection = True
        elif self.direction == -1 and self.x < INTERSECTION_X:
            self.passed_intersection = True
    
    def find_vehicle_ahead(self, vehicles):
        """Find the nearest vehicle ahead in the same lane"""
        nearest = None
        min_distance = float('inf')
        
        for v in vehicles:
            if v == self or v.lane != self.lane or v.direction != self.direction:
                continue
            
            distance = self.distance_to_vehicle(v)
            if distance > 0 and distance < min_distance:
                min_distance = distance
                nearest = v
        
        return nearest
    
    def distance_to_vehicle(self, other):
        """Calculate distance to another vehicle (front to rear)"""
        if self.direction == 1:
            return other.x - (self.x + self.length)
        else:
            return (self.x - self.length) - other.x
    
    def distance_to_light(self, traffic_light):
        """Calculate distance to traffic light stop line"""
        if self.direction == 1:
            stop_line = INTERSECTION_X
            return stop_line - (self.x + self.length)
        else:
            stop_line = INTERSECTION_X + INTERSECTION_WIDTH
            return (self.x - self.length) - stop_line
    
    def can_change_lane(self, target_lane, vehicles):
        """Check if lane change is safe"""
        if self.lane_change_cooldown > 0:
            return False
        
        if target_lane < 0 or target_lane >= NUM_LANES:
            return False
        
        # Check for vehicles in target lane
        for v in vehicles:
            if v == self or v.lane != target_lane or v.direction != self.direction:
                continue
            
            # Calculate overlap
            if self.direction == 1:
                gap_front = v.x - (self.x + self.length)
                gap_rear = self.x - (v.x + v.length)
            else:
                gap_front = (self.x - self.length) - v.x
                gap_rear = v.x - v.length - self.x
            
            if gap_front > -self.length and gap_rear > -self.length:
                # Vehicles overlap, check gap
                if abs(gap_front) < LANE_CHANGE_MIN_GAP or abs(gap_rear) < LANE_CHANGE_MIN_GAP:
                    return False
        
        return True
    
    def attempt_lane_change(self, vehicles):
        """Try to change lanes if current lane is slow"""
        vehicle_ahead = self.find_vehicle_ahead(vehicles)
        
        if not vehicle_ahead:
            return  # No need to change lanes
        
        gap = self.distance_to_vehicle(vehicle_ahead)
        if gap > SAFE_DISTANCE * 2:
            return  # Comfortable gap, no need to change
        
        # Try adjacent lanes
        lanes_to_try = []
        if self.direction == 1:  # Right-moving traffic (lanes 0, 1)
            if self.lane == 0:
                lanes_to_try = [1]
            elif self.lane == 1:
                lanes_to_try = [0]
        else:  # Left-moving traffic (lanes 2, 3)
            if self.lane == 2:
                lanes_to_try = [3]
            elif self.lane == 3:
                lanes_to_try = [2]
        
        for target_lane in lanes_to_try:
            if self.can_change_lane(target_lane, vehicles):
                self.lane = target_lane
                self.y = ROAD_Y_START + target_lane * LANE_WIDTH + (LANE_WIDTH - self.width) // 2
                self.lane_change_cooldown = LANE_CHANGE_COOLDOWN
                break
    
    def draw(self, screen):
        """Draw the vehicle"""
        if self.direction == 1:
            rect = pygame.Rect(self.x, self.y, self.length, self.width)
        else:
            rect = pygame.Rect(self.x - self.length, self.y, self.length, self.width)
        
        pygame.draw.rect(screen, self.color, rect)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)  # Border


class NormalCar(Vehicle):
    def __init__(self, x, y, lane, direction):
        color = (random.randint(50, 200), random.randint(50, 200), random.randint(100, 255))
        super().__init__(x, y, lane, direction, CAR_NORMAL_LENGTH, CAR_NORMAL_WIDTH,
                         CAR_NORMAL_MAX_SPEED, CAR_NORMAL_ACCELERATION, color, "car")


class Truck(Vehicle):
    def __init__(self, x, y, lane, direction):
        super().__init__(x, y, lane, direction, TRUCK_LENGTH, TRUCK_WIDTH,
                         TRUCK_MAX_SPEED, TRUCK_ACCELERATION, COLOR_CAR_TRUCK, "truck")


class SportsCar(Vehicle):
    def __init__(self, x, y, lane, direction):
        super().__init__(x, y, lane, direction, SPORTS_LENGTH, SPORTS_WIDTH,
                         SPORTS_MAX_SPEED, SPORTS_ACCELERATION, COLOR_CAR_SPORTS, "sports")


class Ambulance(Vehicle):
    """Emergency vehicle with special behavior"""
    
    def __init__(self, x, y, lane, direction):
        super().__init__(x, y, lane, direction, AMBULANCE_LENGTH, AMBULANCE_WIDTH,
                         AMBULANCE_MAX_SPEED, AMBULANCE_ACCELERATION, COLOR_AMBULANCE, "ambulance")
        self.siren_state = 0
    
    def update(self, dt, vehicles, traffic_light, time_scale):
        """Emergency vehicles can pass through red lights"""
        dt *= time_scale
        
        # Update siren animation
        self.siren_state = (self.siren_state + dt * 5) % 2
        
        if self.lane_change_cooldown > 0:
            self.lane_change_cooldown -= dt
        
        # Clear path for ambulance
        self.clear_path(vehicles)
        
        # Ambulances ignore red lights but slow down slightly
        light_distance = self.distance_to_light(traffic_light)
        should_slow_at_light = False
        
        if light_distance is not None and light_distance > 0 and light_distance < 80:
            if traffic_light.get_light_state(self.direction) == 'red':
                should_slow_at_light = True
        
        vehicle_ahead = self.find_vehicle_ahead(vehicles)
        
        if should_slow_at_light and light_distance < 60:
            self.target_speed = self.max_speed * 0.5
        elif vehicle_ahead:
            gap = self.distance_to_vehicle(vehicle_ahead)
            if gap < SAFE_DISTANCE * 0.5:
                self.target_speed = vehicle_ahead.speed * 0.95
            else:
                self.target_speed = self.max_speed
        else:
            self.target_speed = self.max_speed
        
        # Smooth acceleration
        if self.speed < self.target_speed:
            self.speed = min(self.speed + self.acceleration * dt, self.target_speed)
        elif self.speed > self.target_speed:
            self.speed = max(self.speed - self.acceleration * 1.5 * dt, self.target_speed, 0)
        
        self.x += self.speed * dt * self.direction
        
        if self.direction == 1 and self.x > INTERSECTION_X + INTERSECTION_WIDTH:
            self.passed_intersection = True
        elif self.direction == -1 and self.x < INTERSECTION_X:
            self.passed_intersection = True
    
    def clear_path(self, vehicles):
        """Make other vehicles move aside"""
        for v in vehicles:
            if v == self or v.vehicle_type == "ambulance":
                continue
            
            # Check if vehicle is ahead and close
            if v.lane == self.lane and v.direction == self.direction:
                distance = self.distance_to_vehicle(v)
                if 0 < distance < 150:
                    # Try to make vehicle change lanes
                    v.attempt_lane_change(vehicles)
    
    def draw(self, screen):
        """Draw ambulance with flashing lights"""
        if self.direction == 1:
            rect = pygame.Rect(self.x, self.y, self.length, self.width)
        else:
            rect = pygame.Rect(self.x - self.length, self.y, self.length, self.width)
        
        # Main body
        pygame.draw.rect(screen, self.color, rect)
        
        # Red stripes
        stripe_color = COLOR_AMBULANCE_STRIPE if self.siren_state < 1 else (200, 0, 0)
        stripe_width = self.length // 4
        if self.direction == 1:
            stripe1 = pygame.Rect(self.x + stripe_width, self.y, 8, self.width)
            stripe2 = pygame.Rect(self.x + stripe_width * 2.5, self.y, 8, self.width)
        else:
            stripe1 = pygame.Rect(self.x - stripe_width * 2, self.y, 8, self.width)
            stripe2 = pygame.Rect(self.x - stripe_width * 3.5, self.y, 8, self.width)
        
        pygame.draw.rect(screen, stripe_color, stripe1)
        pygame.draw.rect(screen, stripe_color, stripe2)
        pygame.draw.rect(screen, (0, 0, 0), rect, 2)