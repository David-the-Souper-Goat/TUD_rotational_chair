import csv
import math

EulerAngle = []


def quaternion_to_euler(q_w, q_x, q_y, q_z):
    # Roll (x-axis rotation)
    roll = math.atan2(2 * (q_w * q_x + q_y * q_z), 1 - 2 * (q_x**2 + q_y**2))
    
    # Pitch (y-axis rotation)
    pitch = math.asin(2 * (q_w * q_y - q_z * q_x))
    
    # Yaw (z-axis rotation)
    yaw = math.atan2(2 * (q_w * q_z + q_x * q_y), 1 - 2 * (q_y**2 + q_z**2))
    
    return roll, pitch, yaw

def wrap_angle(angle):
    # Wraps the angle to the range [-pi, pi)

    return (angle + 2 * math.pi) % (2 * math.pi) - math.pi


with open("camera_physics_timeline.csv", mode="r", encoding="utf-8") as file:
    csv_reader = csv.reader(file)
    
    # Optional: Skip the header row
    header = next(csv_reader)
    print(f"Headers: {header}")
    
    # Loop through each row
    for _ in range(12000):
        next_row = next(csv_reader)
        r,p,y = quaternion_to_euler(
            float(next_row[4]),
            float(next_row[5]),
            float(next_row[6]),
            float(next_row[7]))
        EulerAngle.append([float(next_row[0]),math.degrees(wrap_angle(y))])
    
    print(EulerAngle[1210])
