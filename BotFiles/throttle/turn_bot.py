import math
from rlbot.agents.base_agent import BaseAgent, SimpleControllerState
from rlbot.utils.structures.game_data_struct import GameTickPacket
from rlbot.utils.game_state_util import (
    GameState,
    BallState,
    CarState,
    Physics,
    Vector3,
    Rotator,
    GameInfoState,
)
import numpy as np
import os
import sys

import progressbar

path = os.path.dirname(os.path.abspath(__file__))
path = path.split("throttle")[0]
sys.path.insert(0, path)
import analisis_functions as af  # They are good AF


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
        # List that will hold each runs data before creating a np.array
        self.data_list = []
        # self.packet.game_info.seconds_elapsed at which a new run is started (so they all start at 0)
        self.reset_time = 0
        # Speed of the previous tick
        self.prev_speed = 100000
        # Location of the folder where the data will be stored
        # self.data_file_loc = os.path.dirname(os.path.realpath(__file__)) + r'\data\steer'
        self.data_file_loc = r"D:\Data\Program Data" + r"\tt"
        # Index for the throttle list
        self.throttle_index = 0
        self.throttle_list = af.float_range(pos=True)
        self.throttle_list = np.arange(0, 2, 0.001) - 1
        # Index for the steer list
        self.steer_index = 0
        self.steer_list = af.float_range(pos=True)
        self.steer_list.pop(0)
        self.steer_list = [0]

        self.max_y = 166000
        self.max_x = 94000

        # Creating a progress bar
        self.bar = progressbar.ProgressBar(
            max_value=len(self.throttle_list) * len(self.steer_list)
        )
        self.bar.update(0)
        self.render_values()

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.packet = packet
        self.bot = self.packet.game_cars[self.index]
        self.speed = self.bot.physics.velocity
        self.pos = self.bot.physics.location
        self.ang_speed = self.bot.physics.angular_velocity
        self.rot = self.bot.physics.rotation

        # Setting the throttle and steer value
        self.controller_state.throttle = self.throttle_list[self.throttle_index]
        self.controller_state.steer = self.steer_list[self.steer_index]

        # Waiting counter for the start and for in between runs
        if self.waiting and self.tick_counter < self.waiting_ticks:
            self.tick_counter += 1
            if self.tick_counter == self.waiting_ticks - 1:
                # Stop waiting and reset position
                self.waiting = False
                self.reset_state()
            # Setting throttle 0 so it does not move on the reset tick
            self.controller_state.throttle = 0
            # Setting reset time so the next run starts at t=0
            self.reset_time = self.packet.game_info.seconds_elapsed
            return self.controller_state

        # Setting this ticks time
        relative_time = self.packet.game_info.seconds_elapsed - self.reset_time
        # Appending this ticks data to the list
        self.data_list.append(
            [
                relative_time,
                self.pos.x,
                self.pos.y,
                self.pos.z,
                self.speed.x,
                self.speed.y,
                self.speed.z,
                self.ang_speed.x,
                self.ang_speed.y,
                self.ang_speed.z,
                self.rot.pitch,
                self.rot.yaw,
                self.rot.roll,
            ]
        )

        self.out_of_bounds()

        # Wait until speed is maintained for self.speed_repeat_amount ticks to make sure the car reached its max speed
        if self.prev_speed == math.sqrt(
            abs(self.speed.x) + abs(self.speed.y) + abs(self.speed.z)
        ):
            self.speed_counter += 1
            if self.speed_counter == self.speed_repeat_amount:
                # Create the np.array with this runs data
                data_array = np.array(self.data_list)
                # Get this runs file name
                str_throttle = str(self.throttle_list[self.throttle_index]).replace(
                    ".", "_"
                )
                str_steer = str(self.steer_list[self.steer_index]).replace(".", "_")
                # Get this runs file path
                file_path = (
                    self.data_file_loc
                    + os.path.sep
                    + str_throttle
                    + "."
                    + str_steer
                    + ".npy"
                )
                # Save the np.array to the ile_path
                np.save(file_path, data_array)
                # Increment throttle index
                self.waiting = True
                # Reset the speed counter
                self.speed_counter = 0
                # Reset the list o data
                self.data_list = []
                # Reset the position
                self.reset_state()
                # Add the counter headstart to make waiting times between runs smaller
                self.tick_counter = self.tick_counter_headstart
                # Updating the progress bar
                self.bar.update(
                    self.steer_index * len(self.throttle_list) + self.throttle_index
                )
                self.render_values()
                self.throttle_index += 1
            # Check if throttle index is exceeding the possible values, and if so, stop the run
            if self.throttle_index >= len(self.throttle_list):
                self.throttle_index = 0
                self.steer_index += 1
                self.render_values()
                if self.steer_index > len(self.steer_list):
                    import psutil

                    # Close rocket league
                    for process in (
                        process
                        for process in psutil.process_iter()
                        if process.name() == "RocketLeague.exe"
                    ):
                        process.kill()
                        # Close RLBot
                    for process in (
                        process
                        for process in psutil.process_iter()
                        if process.name() == "python.exe"
                    ):
                        process.kill()
        # Save previous speed so we are able to compare
        self.prev_speed = math.sqrt(
            abs(self.speed.x) + abs(self.speed.y) + abs(self.speed.z)
        )

        return self.controller_state

    def reset_state(self, keep_speed=False):

        # We may want to keep the speed if we run out of field
        if keep_speed:
            car_state = CarState(
                boost_amount=0,
                physics=Physics(
                    location=Vector3(x=0, y=0),
                    rotation=Rotator(0, math.pi / 2, 0),
                    angular_velocity=Vector3(0, 0, 0),
                ),
            )
        else:
            car_state = CarState(
                boost_amount=0,
                physics=Physics(
                    velocity=Vector3(0, 0, 0),
                    location=Vector3(x=0, y=0),
                    rotation=Rotator(0, math.pi / 2, 0),
                    angular_velocity=Vector3(0, 0, 0),
                ),
            )
            # Setting the run start time
            self.reset_time = self.packet.game_info.seconds_elapsed

        ball_state = BallState(Physics(location=Vector3(z=3000)))

        game_state = GameState(ball=ball_state, cars={self.index: car_state})

        self.set_game_state(game_state)

    def out_of_bounds(self):
        loc = None
        if abs(self.pos.x) > self.max_x:
            x = -self.max_x * np.sign(self.pos.x)
            loc = Vector3(x=x)
        if abs(self.pos.y) > self.max_y:
            y = -self.max_y * np.sign(self.pos.y)
            loc = Vector3(y=y)
        if loc is not None:
            car_state = CarState(boost_amount=0, physics=Physics(location=loc))

            game_state = GameState(cars={self.index: car_state})

            self.set_game_state(game_state)

    def render_values(self):
        self.renderer.begin_rendering()
        self.renderer.draw_string_2d(
            0,
            0,
            2,
            2,
            f"Current Throttle: {self.throttle_index} out of {len(self.throttle_list)}\nValue: {self.throttle_list[self.throttle_index]}",
            self.renderer.black(),
        )
        self.renderer.draw_string_2d(
            0,
            100,
            2,
            2,
            f"Current Steer: {self.steer_index} out of {len(self.steer_list)}\nValue: {self.steer_list[self.steer_index]}",
            self.renderer.black(),
        )
        percentage = (
            (self.steer_index * len(self.throttle_list) + self.throttle_index)
            / (len(self.throttle_list) * len(self.steer_list))
        ) * 100
        self.renderer.draw_string_2d(
            0,
            200,
            2,
            2,
            f"Current Run: {self.steer_index * len(self.throttle_list) + self.throttle_index} out of {len(self.throttle_list)*len(self.steer_list)}\n{percentage} %",
            self.renderer.black(),
        )
        self.renderer.end_rendering()
