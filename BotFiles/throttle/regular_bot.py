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
import sys
import os

path = os.path.dirname(os.path.abspath(__file__))
path = path.split("throttle")[0]
sys.path.insert(0, path)
import analisis_functions as af  # They are good AF

import progressbar


class PythonExample(BaseAgent):
    def __init__(self, name, team, index):
        # super(PythonExample, self).__init__()
        self.name = name
        self.team = team
        self.index = index
        self.packet = None
        self.controller = None
        # Index for the throttle list
        self.throttle_index = 0
        # List that will hold each runs data before creating a np.array
        self.data_list = []
        # self.packet.game_info.seconds_elapsed at which a new run is started (so they all start at 0)
        self.reset_time = 0
        # Location of the folder where the data will be stored
        self.data_file_loc = os.path.dirname(os.path.realpath(__file__)) + r"\tt"
        self.throttle_list = af.float_range()
        self.throttle_index = 0
        # Creating a progress bar
        # self.bar = progressbar.ProgressBar(max_value=len(self.throttle_list))

        self.max_y = 166000
        self.max_x = 94000

        self.status = af.GatherStatus()
        self.stagnation = af.Stagnation(stagnation_threshold=2)

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.controller = SimpleControllerState()

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.packet = packet
        bot = self.packet.game_cars[self.index]
        speed = bot.physics.velocity

        if self.status.status == 5:
            self.status.reset(packet=self.packet)
        else:
            self.status.stat(packet=self.packet)

        if self.status.status == 0 or self.status.status == 2:
            self.controller.throttle = 0
            self.controller.boost = 0
            return self.controller

        if self.status.status == 1:
            self.reset_state()
            self.stagnation.reset()
            self.controller.throttle = 0
            self.controller.boost = 0
            return self.controller

        if self.status.status == 3:
            if self.reset_time == 0:
                self.reset_time = self.packet.game_info.seconds_elapsed
                self.controller.throttle = 0
                self.controller.boost = 0
                print(self.controller.throttle)
                return self.controller

            # Setting the throttle value
            self.controller.throttle = self.throttle_list[self.throttle_index]
            print(self.controller.throttle)
            if abs(self.controller.throttle) > 1:
                self.controller.boost = 1
                self.controller.throttle = 1 * np.sign(self.controller.throttle)
            else:
                self.controller.boost = 0
            # Setting this ticks time
            relative_time = self.packet.game_info.seconds_elapsed - self.reset_time
            # Appending this ticks data to the list
            self.data_list.append([relative_time, speed.y])

            if (
                self.stagnation.stagnated(speed.y)
                and self.stagnation.stagnating_counter >= 100
            ):
                # Create the np.array with this runs data
                data_array = np.array(self.data_list)
                # Get this runs file name
                str_throttle = str(self.throttle_list[self.throttle_index]).replace(
                    ".", "_"
                )
                # Get this runs file path
                file_path = self.data_file_loc + os.path.sep + str_throttle + ".npy"
                # Save the np.array to the ile_path
                np.save(file_path, data_array)
                # Increment throttle index
                self.throttle_index += 1
                self.status.reset(self.packet)
                # Reset the list o data
                self.data_list = []

            # Check if throttle index is exceeding the possible values, and if so, stop the run
            if self.throttle_list[self.throttle_index] > 1:
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
                for process in (
                    process
                    for process in psutil.process_iter()
                    if process.name() == "obs.exe"
                ):
                    process.kill()

        # Updating the progress bar
        # self.bar.update(self.throttle_index)
        print(self.controller.throttle)
        return self.controller

    def reset_state(self):
        # If car is moving backwards, set it on the front goal, and vice versa
        if self.throttle_list[self.throttle_index] <= 0:
            speed_multiplier = 1
        else:
            speed_multiplier = -1

        car_state = CarState(
            boost_amount=100,
            physics=Physics(
                velocity=Vector3(0, 10000 * speed_multiplier, 0),
                location=Vector3(x=0, y=0),
                rotation=Rotator(0, math.pi / 2, 0),
                angular_velocity=Vector3(0, 0, 0),
            ),
        )
        # Setting the run start time
        self.reset_time = 0

        ball_state = BallState(Physics(location=Vector3(z=3000)))

        game_state = GameState(ball=ball_state, cars={self.index: car_state})

        self.set_game_state(game_state)
