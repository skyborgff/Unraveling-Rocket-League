import math
import time

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
import RL_functions as rf  # They are good AF

import progressbar


class PythonExample(BaseAgent):
    def __init__(self, name, team, index):
        # super(PythonExample, self).__init__()
        self.name = name
        self.team = team
        self.index = index
        self.packet = None
        self.controller = None
        self.throttle_list = af.float_range(add_boost=True)
        self.throttle_index = 0
        self.reset_state = False
        self.delta_t = time.time()

    def initialize_agent(self):
        # This runs once before the bot starts up
        self.controller = SimpleControllerState()

    def get_output(self, packet: GameTickPacket) -> SimpleControllerState:
        self.throttle_list = af.float_range(add_boost=True)
        tick = time.time()
        self.throttle_list = af.float_range(add_boost=True)
        packet = packet
        bot = packet.game_cars[self.index]
        friend = packet.game_cars[not self.index]
        self.delta_t = time.time() - self.delta_t
        self.delta_t = 1 / 60
        if not packet.game_info.is_kickoff_pause and not self.reset_state:
            car_state1 = CarState(
                boost_amount=100,
                physics=Physics(
                    velocity=Vector3(0, 0, 0),
                    location=Vector3(x=50, y=0),
                    rotation=Rotator(0, math.pi / 2, 0),
                    angular_velocity=Vector3(0, 0, 0),
                ),
            )
            car_state2 = CarState(
                boost_amount=100,
                physics=Physics(
                    velocity=Vector3(0, 0, 0),
                    location=Vector3(x=-50, y=0),
                    rotation=Rotator(0, math.pi / 2, 0),
                    angular_velocity=Vector3(0, 0, 0),
                ),
            )

            ball_state = BallState(Physics(location=Vector3(z=3000)))
            game_state = GameState(ball=ball_state, cars={0: car_state1, 1: car_state2})
            self.set_game_state(game_state)
            self.reset_state = True
            return self.controller

        bot_speed = bot.physics.velocity.y
        friend_speed = friend.physics.velocity.y
        bot_y = bot.physics.location.y
        friend_y = friend.physics.location.y

        closest_throttle = speed_controller_1D(bot_speed, friend_speed, bot_y, friend_y)

        if abs(closest_throttle) > 1:
            boost = True
            closest_throttle = 1
        else:
            boost = False
        throttle = closest_throttle
        # return [throttle, boost]
        self.controller.throttle = throttle
        self.controller.boost = boost
        print(time.time() - tick)
        return self.controller


def speed_controller_1D(current_vel, target_vel, current_loc, target_loc):
    distance_to_target = target_loc - current_loc
    velocity_delta = target_vel - current_vel
    throttle_list = af.float_range(add_boost=True)
    current_distance_to_break = abs((target_vel ** 2 - current_vel ** 2) / (2 * 3510))
    next_vel_lst = []
    delta_distance_list = []
    delta_velocity_list = []
    distance_break_lst = []
    sqr_diff_list = []
    for th in throttle_list:
        next_vel = rf.next_linear_velocity_V2(current_vel, th, 1 / 120)
        next_vel_lst.append(next_vel)

        distance_to_break = abs((target_vel ** 2 - next_vel ** 2) / (2 * 3510))
        distance_break_lst.append(distance_to_break)

        next_loc = current_loc + next_vel * (1 / 120)
        delta_distance = abs(target_loc - next_loc)
        delta_distance_list.append(delta_distance)

        delta_velocity = target_vel - next_vel
        delta_velocity_list.append(delta_velocity)

        sqr_diff_list.append(abs(delta_velocity))

    sorted_qr_diff_list = np.sort(sqr_diff_list)
    closest_index = sqr_diff_list.index(sorted_qr_diff_list[0])
    closest_throttle = throttle_list[closest_index]
    return closest_throttle
