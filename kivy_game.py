# -*- coding: utf-8 -*-
"""
Created on Fri Feb 25 09:06:48 2022

@author: Mathias
"""

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.properties import NumericProperty
from kivy.core.window import Window
from kivy.clock import Clock
from random import randrange
import math
from kivy.animation import Animation
kv = Builder.load_file("kivy_game.kv")


class Player(Label):
    age = NumericProperty(0)
    generation = NumericProperty(0)
    
    player_speed = NumericProperty(0)
    player_size = NumericProperty(10)
    energy = NumericProperty(350)
    energy_needed_to_replicate = NumericProperty(150)
    energy_used_to_replicate = NumericProperty(30)
    max_speed_time = NumericProperty(10)
    
    attack_bomb_speed = NumericProperty(0)
    attack_bomb_range = NumericProperty(0)
    attack_bomb_frequency = NumericProperty(0) # divided by 10
    attack_bomb_time = NumericProperty(0) # divided by 10
    attack_bomb_radius = NumericProperty(0)
    attack_bomb_knockback = NumericProperty(0)
    attack_bomb_stun = NumericProperty(0)
    attack_bomb_wait = NumericProperty(0)
    
    boost_bomb_speed = NumericProperty(25)
    boost_bomb_frequency = NumericProperty(6) # divided by 10
    boost_bomb_time = NumericProperty(8) # divided by 10
    boost_bomb_radius = NumericProperty(40)
    boost_bomb_knockback = NumericProperty(500)
    boost_bomb_wait = NumericProperty(2)
    
    
    def __init__(self, **kwargs):
        super(Player, self).__init__(**kwargs)
        self.type = "player"
        self.kinetic_energy = 1
        self.speed = 0
        self.knockback_energy = 0
        self.stunned = False
        self.stun_time = 0
        self.schedule_clocks()
        self.print_stats()
        
        
    def schedule_clocks(self):
        Clock.schedule_once(self.update_direction, 0.01)
        
        self.boost_clock = Clock.schedule_interval(self.boost, self.boost_bomb_frequency/10)
        self.attack_clock = Clock.schedule_interval(self.attack, self.attack_bomb_frequency/10)
        self.boost_clock.cancel()
        self.attack_clock.cancel
        self.enable_boost_clock = Clock.schedule_once(self.enable_boost, self.boost_bomb_wait)
        self.enable_attack_clock = Clock.schedule_once(self.enable_attack, self.attack_bomb_wait)
        
        self.update_clock = Clock.schedule_interval(self.update, 1.0/60.0)
        self.update_direction_clock = Clock.schedule_interval(self.update_direction, 0.1)
        self.temporary_slow_clock = Clock.schedule_interval(self.increase_speed, 0.25)
        self.knockback_clock = Clock.schedule_interval(self.knockback_move, 1.0/60)
        
        
    def update(self, dt, *args):
        if self.energy < 0:
            self.remove()
            return
        elif self.energy > self.energy_needed_to_replicate:
            self.replicate()
        
        self.int_energy = self.energy//1
        self.text = str(int(self.int_energy))
        self.age += dt
        self.move(dt)
        self.color = (100/255, (self.energy/self.energy_needed_to_replicate), 0/255, 1)
            
        
        if self.find_target_distance(self.target) < self.width/2 + 2:
            self.eat(self.target)
        elif self.target.type == "player" and self.find_target_distance(self.closest_food) < 4 + self.width/2:
            self.eat(self.closest_food)
        
        
    def enable_boost(self, *args):
        self.boost_clock()
    
    def enable_attack(self, *args):
        self.attack_clock()

    
    def boost(self, dt):
        energy_cost_knockback = self.boost_bomb_knockback**(2/5)
        energy_cost_radius = self.boost_bomb_radius/5
        self.energy -= (energy_cost_knockback + energy_cost_radius)
        bomb = Bomb(size_hint_x = None,
                    size_hint_y = None,
                    height = 4,
                    width = 4,
                    pos = (self.x+self.player_size/2, self.y+self.player_size/2),
                    color = (50/255, 50/255, 255/255, 1),
                    speed = self.boost_bomb_speed,
                    direction = self.direction + math.pi,
                    time = self.boost_bomb_time/10,
                    radius = self.boost_bomb_radius,
                    knockback = self.boost_bomb_knockback * math.log(self.player_size, 5),
                    stun = 0
                    )
        self.parent.parent.ids.FL.add_widget(bomb)
        

    def attack(self, dt):
        try:
            if self.stunned == True:
                return
            if self.find_target_distance(self.closest_player) > self.attack_bomb_range:
                return
            if self.target.type == "food" and self.closest_player.player_size < self.player_size * 1.4:
                return
            energy_cost_knockback = self.attack_bomb_knockback**(1/5)
            energy_cost_radius = self.attack_bomb_radius/5
            energy_cost_stun = self.attack_bomb_stun/2
            self.energy -= (energy_cost_knockback + energy_cost_radius + energy_cost_stun)
            bomb = Bomb(size_hint_x = None,
                        size_hint_y = None,
                        height = 4,
                        width = 4,
                        pos = (self.x+self.player_size/2, self.y+self.player_size/2),
                        color = (255/255, 0/255, 0/255, 1),
                        speed = self.attack_bomb_speed,
                        direction = self.find_target_direction(self.closest_player),
                        time = self.attack_bomb_time/10,
                        radius = self.attack_bomb_radius,
                        knockback = self.attack_bomb_knockback * math.log(self.player_size, 3),
                        stun = self.attack_bomb_stun
                        )
            self.parent.parent.ids.FL.add_widget(bomb)
        except AttributeError:
            self.update_direction()
    
    
    def knockback(self, distance, direction, knockback, stun):
        self.knockback_direction = direction
        self.knockback_energy += knockback
        try:
            self.knockback_speed = math.sqrt(2*self.knockback_energy/((self.player_size+1)**(1/3))) * 1.75
        except ValueError:
            self.knockback_speed = 0
        self.knockback_speed_x = self.knockback_speed * math.cos(direction)
        self.knockback_speed_y = self.knockback_speed * math.sin(direction)
        self.stun_time += stun
        # print(self.knockback_energy)
        if self.stun_time >= 1:
            self.boost_clock.cancel()
            self.stunned = True

    
    def knockback_update(self, dt):
        if self.knockback_energy > 0:
            self.knockback_energy -= (self.player_size**(6/7)) * dt * 50
            try:
                self.knockback_speed = math.sqrt(2*self.knockback_energy/((self.player_size+1)**(1/3))) * 1.75
                #math.sqrt(2*self.kinetic_energy/((self.player_size+1)**(1/3)))
            except ValueError:
                self.knockback_speed = 0
            self.knockback_speed_x = self.knockback_speed * math.cos(self.knockback_direction)
            self.knockback_speed_y = self.knockback_speed * math.sin(self.knockback_direction)
    
    
    def knockback_move(self, dt):
        if self.knockback_energy <= 0:
            return
        self.x += self.knockback_speed_x*dt
        self.y += self.knockback_speed_y*dt
        self.knockback_update(dt)
    
    
    def replicate(self, *args):
        self.energy -= self.energy_needed_to_replicate*self.energy_used_to_replicate/100
        speed = self.player_speed
        size = self.player_size
        ETR = self.energy_needed_to_replicate
        ETG = self.energy_used_to_replicate
        MST = self.max_speed_time
        gen = self.generation
        AB_speed = self.attack_bomb_speed
        AB_range = self.attack_bomb_range
        AB_frequency = self.attack_bomb_frequency
        AB_time = self.attack_bomb_time
        AB_radius = self.attack_bomb_radius
        AB_knockback = self.attack_bomb_knockback
        AB_stun = self.attack_bomb_stun
        AB_wait = self.attack_bomb_wait
        BB_speed = self.boost_bomb_speed
        BB_frequency = self.boost_bomb_frequency
        BB_time = self.boost_bomb_time
        BB_radius = self.boost_bomb_radius
        BB_knockback = self.boost_bomb_knockback
        BB_wait = self.boost_bomb_wait
        self.parent.parent.make_player(1, speed, size, ETR, ETG, self.pos, MST, gen, 
                                       AB_speed, AB_range, AB_frequency, AB_time, AB_radius, AB_knockback, AB_stun, AB_wait,
                                       BB_speed, BB_frequency, BB_time, BB_radius, BB_knockback, BB_wait)
        
        
    def print_stats(self):
        return
        print("\n")
        print(f"age: {self.age}")
        print(f"Generation: {self.generation}")
        print(f"speed: {self.player_speed}")
        print(f"size: {self.player_size}")
        print(f"ETR: {self.energy_needed_to_replicate}")
        print(f"ETG: {self.energy_used_to_replicate}")
        print(f"MST: {self.max_speed_time}")
        
        
    def move(self, dt):
        energy_cost_movement = dt * self.kinetic_energy * 0.05
        energy_cost_passive = dt * (4*self.player_size+1)**(3/5) * 0.75

        if self.stunned == True:
            self.stun_time -= dt
            self.energy -= energy_cost_passive / 2
            if self.stun_time <= 0:
                self.stun_time = 0
                self.boost_clock()
                self.stunned = False
            return
        self.y += self.speed_y*dt
        self.x += self.speed_x*dt
        self.energy -= (energy_cost_movement + energy_cost_passive)

        
    def eat(self, target):
        if self.find_target_distance(target) > self.width/2 + 2:
            return
        try:
            target_energy = target.energy
            target.remove(target)
            self.energy += target_energy
        except AttributeError:
            # print("already deleted smh")
            pass
        Clock.schedule_once(self.update_direction, 0)
        
        
    def update_direction(self, *args):
        closest_food = self.find_closest_food()
        closest_player = self.find_closest_player()
        try:
            if self.player_size > closest_player.player_size * 1.5 and self.find_target_distance(closest_food) < self.find_target_distance(closest_player) + 100:
                self.target = closest_player
                self.closest_player = closest_player
                self.closest_food = closest_food
            else:
                self.target = closest_food
                self.closest_player = closest_player
        except AttributeError: #if there are no players
            self.target = closest_food
            self.closest_player = closest_player
        self.direction = self.find_target_direction(self.target)
        self.speed_x = self.speed * math.cos(self.direction)
        self.speed_y = self.speed * math.sin(self.direction)


    def find_closest_food(self):
        # Finds and sets self.target to the closest food
        # Also makes 1 food if it cant find any
        shortest_distance = 1000000
        try:
            if len(self.parent.parent.food_list) < 1:
                self.parent.parent.make_food("random")
            for food in self.parent.parent.food_list:
                distance = self.find_target_distance(food)
                if distance < shortest_distance:
                    shortest_distance = distance
                    closest_food = food
            return closest_food
        except:
            return # This should only happen if this player is deleted


    def find_target_distance(self, target):
        try:
            xd = (target.x + target.width/2) - (self.x + self.width/2)
            yd = (target.y + target.height/2) - (self.y + self.height/2)
            return math.sqrt(xd**2 + yd**2)
        except AttributeError:
            self.update_direction()
            return 0
    
    
    def find_target_direction(self, target):
        # Finds the direction to the target
        try:
            target_pos = (target.x+target.width/2, target.y+target.height/2)
            target_difference = [target_pos[0]-(self.x+self.height/2), target_pos[1]-(self.y+self.height/2)]
            direction = math.atan(target_difference[1]/target_difference[0])
        except ZeroDivisionError:
            target_difference[0] += 2
            direction = math.atan(target_difference[1]/target_difference[0])
        except UnboundLocalError:
            return
        except AttributeError:
            Clock.schedule_once(self.update_direction, 0)
            return 0
            print("test oh no")
        if target_difference[0] < 0:
            direction += math.pi
        return direction
    
        
    def find_closest_player(self):
        shortest_distance = 1000000
        try:
            if len(self.parent.parent.player_list) < 2:
                if self.randrange(4) > 0:
                    self.parent.parent.make_player(1, "top")
                    print("special")
                else:
                    self.parent.parent.make_player(1, "random")
                    print("random")
        except AttributeError:
            return
        for player in self.parent.parent.player_list:
            if player == self:
                continue  
            distance = self.find_target_distance(player)
            if distance < shortest_distance:
                shortest_distance = distance
                closest_player = player
        return closest_player

        # print(shortest_distance, self.closest_player)
    
    

    
    def increase_speed(self, dt):
        self.kinetic_energy += self.player_speed*dt/self.max_speed_time
        self.speed = math.sqrt(2*self.kinetic_energy/((self.player_size+1)**(1/3)))
        self.update_direction()
        if self.kinetic_energy >= self.player_speed:
            self.kinetic_energy = self.player_speed
            self.speed = math.sqrt(2*self.kinetic_energy/((self.player_size+1)**(1/3)))
            self.temporary_slow_clock.cancel()
    
    
    def add_to_top_ten_list(self):
        for i in range(len(self.parent.parent.top_ten_players)):
            if self.age > self.parent.parent.top_ten_players[i].age:
                self.parent.parent.top_ten_players.insert(i, self)
                self.parent.parent.top_ten_players.pop()
                return
        
    
    def remove(self, *args):
        self.enable_boost_clock.cancel()
        self.enable_attack_clock.cancel()
        self.boost_clock.cancel()
        self.attack_clock.cancel()
        self.update_clock.cancel()
        self.update_direction_clock.cancel()
        self.temporary_slow_clock.cancel()
        self.knockback_clock.cancel()
        try:
            if self.age > self.parent.parent.top_ten_players[9].age:
                self.add_to_top_ten_list()
                print("Top 10 players:")
                for i in self.parent.parent.top_ten_players:
                    print(int(i.age//1))
                print("\n")
        except IndexError:
            self.parent.parent.top_ten_players.insert(0, self)
            for i in self.parent.parent.top_ten_players:
                print(int(i.age//1))
            print("\n")
        self.parent.parent.player_list.remove(self)
        self.parent.remove_widget(self)


class Bomb(Label):
    speed = NumericProperty(0)
    direction = NumericProperty(0)
    time = NumericProperty(0)
    radius = NumericProperty(0)
    knockback = NumericProperty(0)
    stun = NumericProperty(0)
    def __init__(self, **kwargs):
        super(Bomb, self).__init__(**kwargs)
        self.speed_x = self.speed * math.cos(self.direction)
        self.speed_y = self.speed * math.sin(self.direction)
        self.moving = Clock.schedule_interval(self.move, 1.0/60)
        Clock.schedule_once(self.explode, self.time)
        
        
    def move(self, dt):
        self.y += self.speed_y*dt
        self.x += self.speed_x*dt
    
    
    def find_players_in_radius(self):
        player_list = self.parent.parent.player_list
        self.players_in_radius = []
        for player in player_list:
            xd = (player.pos[0] + player.width/2) - (self.pos[0] + self.width/2)
            yd = (player.pos[1] + player.height/2) - (self.pos[1] + self.height/2)
            player_distance = math.sqrt(xd**2 + yd**2)
            
            if player_distance <= self.radius:
                try:
                    player_direction = math.atan(yd/xd)
                except ZeroDivisionError:
                    player_direction = math.atan(yd/(xd+2))
                # except UnboundLocalError:
                #     return
                if xd < 0:
                    player_direction += math.pi
                self.players_in_radius.append((player, player_distance, player_direction))
            
            
    def explode(self, dt):
        self.find_players_in_radius()
        for player in self.players_in_radius:
            player[0].knockback(player[1], player[2], self.knockback, self.stun)
        # print(len(self.players_in_radius))
        
        
        self.moving.cancel()
        self.parent.remove_widget(self)
        pass
        
    
class Food(Label):
    energy = NumericProperty(30)
    generation = NumericProperty(1)
    def __init__(self, **kwargs):
        super(Food, self).__init__(**kwargs)
        self.type = "food"
        self.replication_amt = 0
        if self.energy >= 4:
            self.replicate_clock = Clock.schedule_once(self.replicate, randrange(1, 75*self.generation))
        else:
            self.replicate_clock = Clock.schedule_once(self.replicate, 99999)
    
    
    def replicate(self, *args):
        self.replication_amt += 1
        self.parent.parent.make_food(self.pos, self.energy, self.generation)
        self.replicate_clock = Clock.schedule_once(self.replicate, randrange(1, 150*self.generation*self.replication_amt))
    
    
    def remove(self, food_list_target):
        #print("deleted woo")
        self.replicate_clock.cancel()
        self.parent.parent.food_list.remove(food_list_target)
        self.parent.remove_widget(self)


class MyLayout(FloatLayout):
    def __init__(self, **kwargs):
        super(MyLayout, self).__init__(**kwargs)
        self.game_time = 0.0
        Clock.schedule_interval(self.update, 1.0/3.0)
        self.food_list = []
        self.player_list = []
        self.top_ten_players = []
        self.make_player(8, "random")
        # Clock.schedule_interval(lambda dt: self.make_player(1, "random"), 1/3)
        for i in range(90):
            self.make_food("random")
        # self.make_player(1, 30, 100, 3000, 20, (250, 250), 30, 1, 
        #                                30, 50, 30, 8, 60, 100, 1, 0,
        #                                30, 30, 10, 60, 200, 5)


    def update(self, dt, *args):
        self.game_time += dt
        self.make_food("random")
        if len(self.player_list) == 0:
            if randrange(4) > 0:
                                        # does not work, dead players dont have parent
                self.make_player(1, "top")
                print("special")
            else:
                self.make_player(1, "random")
                print("random")
        
        
    def make_food(self, *args):
        if args[0] == "random":
            if len(self.food_list) > 900:
                return
            pos_x = randrange(-150, Window.width + 150)
            pos_y = randrange(-150, Window.height + 150)
            energy = 128
            gen = 1
        else:
            if len(self.food_list) > 1500:
                return
            pos_x = args[0][0] + randrange(-15, 16)
            pos_y = args[0][1] + randrange(-15, 16)
            energy = args[1]*0.25
            gen = args[2] + 1
        color_r = randrange(0, 256)
        color_g = randrange(0, 256)
        color_b = randrange(0, 256)

        food = Food(size_hint_x = None,
                    size_hint_y = None,
                    height = 6,
                    width = 6,
                    pos = (pos_x, pos_y),
                    energy = energy,
                    generation = gen,
                    color = (color_r/255, color_g/255, color_b/255, 1)
                    #color = (100/255, (energy-10)/30, 0/255)
                    )
        self.ids.FL.add_widget(food)
        self.food_list.append(food)
        
    
    def mutate(self, *args):
        mutation_chance = 50 # out of 1000
        mutated_args = [args[0][0]]
        for i in range(1, len(args[0])):
            #print(i)
            if randrange(1, 1001) > 1000 - mutation_chance:
                # print(f"Mutate! {i}")
                if i in (5, 7):
                    mutated_args.append(args[0][i])
                else:
                    mutated_args.append(int(args[0][i]*(2**(randrange(-175, 176)/100))//1) + randrange(-3, 4))
            else:
                mutated_args.append(args[0][i])
        return mutated_args
                    
    
    def make_player(self, *args): # amt, speed, size, ETR, ETG, pos, MST, gen, 
                                  # AB_speed, AB_range, AB_frequency, AB_time, AB_radius, AB_knockback, AB_stun, AB_wait,
                                  # BB_speed, BB_frequency, BB_time, BB_radius, BB_knockback, BB_wait
        for i in range(args[0]):
            if args[1] == "random":
                size = randrange(8, 21)
                speed = randrange(1, 30*size)
                ETR = randrange(50, 1501)
                ETG = randrange(10, 91)
                energy = 500
                pos_x = randrange(0, Window.width)
                pos_y = randrange(0, Window.height)
                MST = randrange(1, 61)
                gen = 1
                AB_speed = randrange(1, 91)
                AB_range = randrange(1, 131)
                AB_frequency = randrange(1, 31) # seconds divided by 10
                AB_time = randrange(1, 41) # seconds divided by 10
                AB_radius = randrange(10, 61)
                AB_knockback = randrange(1, 1001)
                AB_stun = randrange(1, 31) # seconds divided by 10
                AB_wait = randrange(1, 11)
                BB_speed = randrange(1, 41)
                BB_frequency = randrange(1, 41) # seconds divided by 10
                BB_time = randrange(1, 26) # seconds divided by 10
                BB_radius = randrange(50, 126)
                BB_knockback = randrange(1, 1001)
                BB_wait = randrange(1, 11)
                
                
            elif args[1] == "top":
                number = randrange(10)
                size = self.top_ten_players[number].player_size
                speed = self.top_ten_players[number].player_speed
                ETR = self.top_ten_players[number].energy_needed_to_replicate
                ETG = self.top_ten_players[number].energy_used_to_replicate
                energy = 500
                pos_x = randrange(0, Window.width)
                pos_y = randrange(0, Window.height)
                MST = self.top_ten_players[number].max_speed_time
                gen = 1
                AB_speed = self.top_ten_players[number].attack_bomb_speed
                AB_range = self.top_ten_players[number].attack_bomb_range
                AB_frequency = self.top_ten_players[number].attack_bomb_frequency # seconds divided by 10
                AB_time = self.top_ten_players[number].attack_bomb_time # seconds divided by 10
                AB_radius = self.top_ten_players[number].attack_bomb_radius
                AB_knockback = self.top_ten_players[number].attack_bomb_knockback
                AB_stun = self.top_ten_players[number].attack_bomb_stun # seconds divided by 10
                AB_wait = self.top_ten_players[number].attack_bomb_wait
                BB_speed = self.top_ten_players[number].boost_bomb_speed
                BB_frequency = self.top_ten_players[number].boost_bomb_frequency # seconds divided by 10
                BB_time = self.top_ten_players[number].boost_bomb_time # seconds divided by 10
                BB_radius = self.top_ten_players[number].boost_bomb_radius
                BB_knockback = self.top_ten_players[number].boost_bomb_knockback
                BB_wait = self.top_ten_players[number].boost_bomb_wait
                
                
            else:
                energy = args[3]*args[4]/100
                argsM = self.mutate(args)
                speed = int((argsM[1]*randrange(90, 111)/100)//1) + randrange(-20, 21)
                size = int((argsM[2]*randrange(94, 107)/100)//1) + randrange(-1, 2)
                ETR = int((argsM[3]*randrange(95, 106)/100)//1) + randrange(-5, 6)
                ETG = argsM[4] + randrange(-2, 3)
                pos_x = argsM[5][0] + randrange(-25, 26)
                pos_y = argsM[5][1] + randrange(-25, 26)
                MST = int((argsM[6]*randrange(90, 111)/100)//1) + randrange(-3, 4)
                gen = argsM[7] + 1
                AB_speed = int((argsM[8]*randrange(95, 106)/100)//1) + randrange(-1, 2)
                AB_range = abs(int((argsM[9]*randrange(95, 106)/100)//1) + randrange(-3, 4))
                AB_frequency = abs(int((argsM[10]*randrange(90, 111)/100)//1) + randrange(-2, 3))
                AB_time = abs(int((argsM[11]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                AB_radius = abs(int((argsM[12]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                AB_knockback = abs(int((argsM[13]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                AB_stun = abs(int((argsM[14]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                AB_wait = abs(int((argsM[15]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                BB_speed = int((argsM[16]*randrange(95, 106)/100)//1) + randrange(-1, 2)
                BB_frequency = abs(int((argsM[17]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                BB_time = abs(int((argsM[18]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                BB_radius = abs(int((argsM[19]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                BB_knockback = abs(int((argsM[20]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                BB_wait = abs(int((argsM[21]*randrange(95, 106)/100)//1) + randrange(-1, 2))
                if speed <= 0:
                    speed = 1
                if size < 3:
                    size = 3
                elif size > 140:
                    size = 140
                if ETR < 50:
                    ETR = 50
                if ETG < 2:
                    ETG = 2
                elif ETG > 99:
                    ETG = 95
                if MST < 1:
                    MST = 1

                
            player = Player(size_hint_x = None,
                        size_hint_y = None,
                        height = size,
                        width = size,
                        #source = r"images\blank.png",
                        text = "o/",
                        pos = (pos_x, pos_y),
                        player_speed = speed,
                        player_size = size,
                        energy = energy,
                        energy_needed_to_replicate = ETR,
                        energy_used_to_replicate = ETG,
                        max_speed_time = MST,
                        generation = gen,
                        color = (100/255, energy/(ETR), 0/255, 1),
                        
                        attack_bomb_speed = AB_speed,
                        attack_bomb_range = AB_range,
                        attack_bomb_frequency = AB_frequency,
                        attack_bomb_time = AB_time,
                        attack_bomb_radius = AB_radius,
                        attack_bomb_knockback = AB_knockback,
                        attack_bomb_stun = AB_stun,
                        attack_bomb_wait = AB_wait,
                        
                        boost_bomb_speed = BB_speed,
                        boost_bomb_frequency = BB_frequency,
                        boost_bomb_time = BB_time,
                        boost_bomb_radius = BB_radius,
                        boost_bomb_knockback = BB_knockback,
                        boost_bomb_wait = BB_wait
                        )
            
            self.ids.FL.add_widget(player)
            self.player_list.append(player)
            


class gameApp(App):
    def build(self):
        return MyLayout()


if __name__ == "__main__":
    gameApp().run()