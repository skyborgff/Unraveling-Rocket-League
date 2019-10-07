import RL_functions as rf
import analisis_functions as af
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
import numpy as np

fig = plt.figure()

start_v = 0
finish_v = 1500
start_y = 0
finish_y = 5000


class TestBot:
    def __init__(self, target_v, target_y):
        self.target_v = target_v
        self.target_y = target_y

    def tick(self, current_v, current_y):
        bot_speed = current_v
        friend_speed = self.target_v
        bot_y = current_y
        friend_y = self.target_y
        closest_throttle = self.speed_controller_1D(
            bot_speed, friend_speed, bot_y, friend_y
        )

        if abs(closest_throttle) > 1:
            boost = True
            closest_throttle = 1
        else:
            boost = False
        throttle = closest_throttle
        return [throttle, boost]

    def speed_controller_1D(self, current_vel, target_vel, current_loc, target_loc):
        distance_to_target = target_loc - current_loc
        velocity_delta = target_vel - current_vel
        throttle_list = af.float_range(add_boost=True)
        current_distance_to_break = abs(
            (target_vel ** 2 - current_vel ** 2) / (2 * 3510)
        )
        next_vel_lst = []
        delta_distance_list = []
        delta_velocity_list = []
        distance_break_lst = []
        sqr_diff_list = []
        for th in throttle_list:
            if th > float(1.0):
                print()
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

        # if current_distance_to_break >= abs(distance_to_target) and abs(velocity_delta) >= 100 and abs(distance_to_target) > 10:
        #     if distance_to_target > 0:
        #         return -1
        #     else:
        #         return 1
        # else:
        #     if abs(current_v) < 10:
        #         print('x')
        #     sorted_delta_distance_list = np.sort(delta_distance_list)
        #     closest_index = delta_distance_list.index(sorted_delta_distance_list[0])
        #     closest_throttle = throttle_list[closest_index]
        #
        #     #if np.sign(closest_throttle) * np.sign(current_v) < 1 or (abs(velocity_delta) <= 10 and abs(distance_to_target) < 5):
        #     if np.sign(closest_throttle) * np.sign(current_v) < 1 and abs(distance_to_target) <= 10:
        #         # check future if braking
        #         # next_vel = rf.next_linear_velocity_V2(current_vel, closest_throttle, 1 / 120)
        #         # next_loc = current_loc + next_vel * (1 / 120)
        #         # delta_distance = abs(target_loc - next_loc)
        #         # delta_distance_list.append(delta_distance)
        #         sorted_delta_velocity_list = np.sort(np.abs(delta_velocity_list))
        #         try:
        #             closest_index = delta_velocity_list.index(sorted_delta_velocity_list[0])
        #         except:
        #             closest_index = delta_velocity_list.index(-1 * sorted_delta_velocity_list[0])
        #         closest_throttle = throttle_list[closest_index]
        #     return closest_throttle


tick_n = 0
max_tick = 120 * 5
current_v = start_v
current_y = start_y
bot = TestBot(finish_v, finish_y)

v_list = []
y_list = []
tick_list = []

while tick_n <= max_tick:
    controller = bot.tick(current_v, current_y)
    throttle = controller[0]
    boost = controller[1]
    if boost:
        throttle = 2
    next_v = rf.next_linear_velocity_V2(current_v, throttle, 1 / 120)
    v_list.append(next_v)
    next_y = current_y + next_v * (1 / 120)
    y_list.append(next_y)
    tick_list.append(tick_n)
    tick_n += 1
    current_v = next_v
    current_y = next_y

# plt.plot(tick_list, v_list)
# plt.plot([tick_list[0], tick_list[-1]], [finish_v, finish_v])
# plt.plot([finish_y, finish_y], [v_list[0], v_list[-1]])

ax = fig.add_subplot(111, projection="3d")
ax.plot(tick_list, v_list, y_list)
ax.set_xlabel("tick")
ax.set_ylabel("v")
ax.set_zlabel("y")
ax.plot([tick_list[0], tick_list[-1]], [finish_v, finish_v], [finish_y, finish_y])
plt.show()
