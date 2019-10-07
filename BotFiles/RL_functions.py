import numpy as np
import analisis_functions as af


def next_linear_velocity(current_speed, current_throttle, delta_t):
    a = 16.8361251
    b = 1.03569487
    c = 10
    d = 1400
    possible_throttle = af.float_range()
    coast_throttle = [
        possible_throttle[int(256 / 2 - 1)],
        possible_throttle[int(256 / 2 + 0)],
        possible_throttle[int(256 / 2 + 1)],
    ]
    sign_th = np.sign(current_throttle)
    sign_vl = np.sign(current_throttle)
    x = d + c - current_speed
    if x < c:  # big throttle
        acc = ((x - c) * b + c * a) * (abs(current_throttle - 1 / 255)) * sign_th
    else:  # small thottle
        acc = x * a * abs(current_throttle - 1 / 255) * sign_th
    if sign_th * sign_vl < 1:  # braking
        acc = 3510 * sign_th
    if current_throttle in coast_throttle:  # costing
        acc = 525 * sign_th * 0
    if current_throttle > 1:  # Boost
        if x >= c:  # big throttle
            acc = ((x - c) * b + c * a) * (abs(current_throttle - 1 / 255)) + 991.667
        else:  # small thottle
            acc = x * a * abs(current_throttle - 1 / 255) + 991.667
        if current_speed > d + c + b:
            acc = 991.667
        if sign_th * sign_vl < 1:
            acc = 3510 + 991.667

    next_speed = current_speed + acc * delta_t

    return next_speed


def next_linear_velocity_V2(current_speed, throttle, delta_t):
    # possible_throttle = af.float_range()
    # coast_throttle = [possible_throttle[int(256 / 2 - 1)],
    #                   possible_throttle[int(256 / 2 + 0)],
    #                   possible_throttle[int(256 / 2 + 1)]]
    coast_throttle = [0, 0.0117647058823529, -0.0117647058823529]
    sign_th = np.sign(throttle)
    sign_vl = np.sign(current_speed)
    if sign_vl == 0:
        sign_vl = 1
    if throttle <= 1:
        if current_speed < 1400:  # big throttle
            acc = (
                (1600 - ((1600 - 160) * current_speed) / 1400)
                * (abs(throttle - 1 / 255))
                * sign_th
            )
        elif current_speed > 1410:
            acc = 0
        else:  # small throttle
            acc = (
                (160 - 160 * (current_speed - 1400))
                / 10
                * abs(throttle - 1 / 255)
                * sign_th
            )
        if sign_th * sign_vl <= 0:  # braking
            acc = 3500 * sign_th
        if throttle in coast_throttle:  # costing
            acc = 525 * -1 * sign_vl

        next_speed = current_speed + acc * delta_t
    else:
        next_linear_velocity_V2(current_speed, 1, delta_t) + 991.667

    if throttle > 1:  # Boost
        acc = next_linear_velocity_V2(current_speed, 1, delta_t)
        next_speed = current_speed + acc * delta_t / 3

    return next_speed
