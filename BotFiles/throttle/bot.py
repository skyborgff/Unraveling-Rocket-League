import math

from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import GameState, BallState, CarState, Physics, Vector3, Rotator, GameInfoState\

import numpy as np
import sys
from os.path import sep, dirname, realpath

import time
import progressbar

class PythonExample(BaseAgent):

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.controller_state = SimpleControllerState()
        # True when the bot is waiting for its suspension to settle
        self.waiting = True
        # Counts ticks. Used for waiting timers
        self.tick_counter = 0
        # In between runs we dont need to wait as much, so this is the counter headstart
        self.tick_counter_headstart = 120 * 4
        # Counts the amount of ticks that the speed has been equal for
        self.speed_counter = 0
        # Amount of repeated ticks with the same speed (to make sure it has settled)
        self.speed_repeat_amount = 10
        # Waiting ticks for the start of the game. Used to make sure that the game has indeed started.
        # self.tick_counter_headstart is deducted from it to make waiting times shorter in between runs.
        self.waiting_ticks = 120 * 5
        # Index for the throttle list
        self.throttle_index = 0
        # List taht will hold each runs data before creating a np.array
        self.data_list = []
        # self.packet.game_info.seconds_elapsed at which a new run is started (so they all start at 0)
        self.reset_time = 0
        # Speed of the previous tick
        self.prev_speed = 100000
        # Location of the folder where the data will be stored
        self.data_file_loc = dirname(realpath(__file__)) + r'\data'
        # Floats are packed from -1, 1 to 0, 255 for networking purposes. we only need to analyze those.
        # Any in between will result in repeated data
        # Float delta for each run
        delta_float = 2 / 255
        #List o throttle values that the game "accepts"
        self.throttle_list = list(np.arange(-1, 1, delta_float))
        # Adding 1 to the end. This is more reliable than doing np.arange(-1, 1 + delta_float, delta_float)
        self.throttle_list.append(1)
        # Creating a progress bar
        self.bar = progressbar.ProgressBar(max_value=len(self.throttle_list))

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.packet = packet
        self.bot = self.packet.game_cars[self.index]
        self.speed = self.bot.physics.velocity

        # Updating the progress bar
        self.bar.update(self.throttle_index)

        # Setting the throttle value
        self.controller_state.throttle = self.throttle_list[self.throttle_index]

        # Waiting counter for the start and for in between runs
        if self.waiting and self.tick_counter < self.waiting_ticks:
            self.tick_counter += 1
            if self.tick_counter == self.waiting_ticks-1:
                # Stop waiting and reset position
                self.waiting = False
                self.reset_state()
            # Setting throttle 0 so it does not move on the reset tick
            self.controller_state.throttle = 0
            # Setting reset time so the next run starts at t=0
            self.reset_time = self.packet.game_info.seconds_elapsed
            return self.controller_state

        # If the bot is entering the goal, reset it to the opposing corner and keep its speed
        if -5000 > self.bot.physics.location.y or self.bot.physics.location.y > 5000:
            self.reset_state(keep_speed=True)

        # Setting this ticks time
        relative_time = self.packet.game_info.seconds_elapsed - self.reset_time
        # Appending this ticks data to the list
        self.data_list.append([relative_time, self.speed.y])

        # Wait until speed is maintained for self.speed_repeat_amount ticks to make sure the car reached its max speed
        if self.prev_speed == self.speed.y:
            self.speed_counter += 1
            if self.speed_counter == self.speed_repeat_amount:
                # Create the np.array with this runs data
                data_array = np.array(self.data_list)
                # Get this runs file name
                strt_hrottle = str(self.throttle_list[self.throttle_index]).replace('.', '_') + '.npy'
                # Get this runs file path
                file_path = self.data_file_loc + sep + strt_hrottle
                # Save the np.array to the ile_path
                np.save(file_path, data_array)
                # Increment throttle index
                self.throttle_index += 1
                self.waiting = True
                # Reset the speed counter
                self.speed_counter = 0
                # Reset the list o data
                self.data_list = []
                # Reset the position
                self.reset_state()
                # Add the counter headstart to make waiting times between runs smaller
                self.tick_counter = self.tick_counter_headstart
            # Check if throttle index is exceeding the possible values, and if so, stop the run
            if self.throttle_index >= len(self.throttle_list):
                import psutil
                # Close rocket league
                for process in (process for process in psutil.process_iter() if process.name() == "RocketLeague.exe"):
                    process.kill()
                    # Close RLBot
                for process in (process for process in psutil.process_iter() if process.name() == "python.exe"):
                    process.kill()
        # Save previous speed so we are able to compare
        self.prev_speed = self.speed.y

        return self.controller_state


    def reset_state(self, keep_speed = False):
        # If car is moving backwards, set it on the front goal, and vice versa
        if self.throttle_list[self.throttle_index] <= 0:
            location_multiplier = -1
        else:
            location_multiplier = 1

        # We may want to keep the speed if we run out of field
        if keep_speed:
            car_state = CarState(boost_amount=0,
                                 physics=Physics(location=Vector3(x=0, y=-5000*location_multiplier),
                                                 rotation=Rotator(0, math.pi / 2, 0),
                                                 angular_velocity=Vector3(0, 0, 0)))
        else:
            car_state = CarState(boost_amount=0,
                                 physics=Physics(velocity=Vector3(0, 0, 0),
                                                 location=Vector3(x=0, y=-5000*location_multiplier),
                                                 rotation=Rotator(0, math.pi / 2, 0),
                                                 angular_velocity=Vector3(0, 0, 0)))
            # Setting the run start time
            self.reset_time = self.packet.game_info.seconds_elapsed

        ball_state = BallState(Physics(location=Vector3(z=3000)))

        game_state = GameState(ball=ball_state, cars={self.index: car_state})

        self.set_game_state(game_state)
