RESOLUTION_MOTOR = 2**16                            # [counts/rev_motor]
GEAR_RATIO = 2**7                                   # [rev_motor/rev_output]
RES_TOTAL = RESOLUTION_MOTOR * GEAR_RATIO           # Total Resolution per Revolution [counts/rev_output]

def opmode(mode:int) -> str:
    """
    Change the operation mode of the rotation chair.
    
    :param mode: 0: Velocity Control\r
                 8: Position Control
    :type mode: int
    """
    return f"opmode {mode}"

def enable_motor() -> str:
    """
    Enables the motor of the rotation chair.
    """
    return "en"

def disable_motor() -> str:
    """
    Disables the motor of the rotation chair.
    """
    return "k"

def record(sample_time:float, num_points:int, var:str = '"MECHANGLE "V') -> str:
    """
    Capture real-time variables from the rotation chair at specified intervals.
    
    :param sample_time: 0 to 31.25 seconds
    :type sample_time: float
    :param num_points: 1 to 2000
    :type num_points: int
    :param var: Name of recordable variable (default is "MECHANGLE V"). Must be preceded by a quotation mark.
    :type var: str
    """
    sampling_time = int(round(sample_time * 1000000 / 31.25))  # Convert seconds to units of 31.25 microseconds
    return f"record {sampling_time} {num_points} {var}"

def trigger_record() -> str:
    """
    Triggers the start of data recording on the rotation chair when the next 'command' is sent.
    """
    return 'rectrig "CMD'

def get_recorded_data() -> str:
    """
    Retrieves the recorded data from the rotation chair.
    Please set the "GETMODE" to mode 0.
    """
    return 'get'


def moveabs(angle:float, angular_velocity:float) -> str:
    '''
    Executes an absolute position movement according to the acceleration settings that are in effect.
    
    :param angle: Absolute angle to move to (in degrees)
    :type angle: float
    :param angular_velocity: Target angular velocity (in deg/s)
    :type angular_velocity: float
    :return: Command string for the movement
    :rtype: str
    '''
    return f"moveabs {_deg2counts(angle)} {_degs2rpm(angular_velocity)}"


def moveinc(angle:float, angular_velocity:float, blending_mode:int = 2) -> str:
    '''
    MOVEINC function to rotate the chair by a specified INCREMENTAL angle with given target angular velocity and blending mode.
    
    :param angle: Incremental angle to rotate (in degrees)
    :type angle: float
    :param angular_velocity: Target angular velocity (in deg/s)
    :type angular_velocity: float
    :param blending_mode: The mode to define the blending behavior (default is 2).\r
    1: The new command will interupt the original command immediately.\r
    2: The new command will be pending until the previous commands in queue are popped.
    :type blending_mode: int
    '''

    return f"moveinc {_deg2counts(angle)} {_degs2rpm(angular_velocity)} {blending_mode}"


def acc(val:float|None=None) -> str:
    """
    Gets/sets the acceleration value of the rotation chair.
    
    :param val: If provided, sets the acceleration to this value (in deg/s**2). If None, returns the current acceleration value.
    :type val: float | None
    """
    if val:
        return f"acc {_degs2rpm(val)}"
    return "acc"


def jogging(angular_velocity:float, duration:float|None=None) -> str:
    '''
    JOGGING function to rotate the chair continuously at a specified angular velocity.
    
    :param angular_velocity: Target angular velocity (in deg/s)
    :type angular_velocity: float
    :param duration: Optional duration for jogging (in seconds). If None, jogging continues indefinitely.
    :type duration: float | None
    '''

    if duration is not None:
        duration *= 1000  # Convert seconds to milliseconds
        return f"j {_degs2rpm(angular_velocity)} {round(duration)}"
    return f"j {_degs2rpm(angular_velocity)}"


def _deg2counts(angle:float) -> int:
    '''
    Converts an angle in degrees to counts based on the total resolution of the rotation chair.
    
    :param angle: Angle in degrees
    :type angle: float
    :return: Angle in counts
    :rtype: int
    '''
    angle *= RES_TOTAL          # Convert deg to deg*counts/rev
    angle //= 360               # Convert deg*counts/rev to counts
    return int(angle)


def _degs2rpm(angular_velocity:float) -> float:
    '''
    Converts an angular velocity in degrees per second to revolutions per minute (rpm).
    
    :param angular_velocity: Angular velocity in degrees per second
    :type angular_velocity: float
    :return: Angular velocity in revolutions per minute (rpm), rounded to 2 decimal places
    :rtype: int
    '''
    angular_velocity *= 60    # Convert deg/s to deg/min
    angular_velocity /= 360  # Convert deg/min to rev/min (rpm)
    return round(angular_velocity, 2)