
def moveinc(angle:float, angular_velocity:float, blending_mode:int = 2) -> None:
    '''
    MOVEINC function to rotate the chair by a specified INCREMENTAL angle with given target angular velocity and blending mode.
    
    :param angle: Incremental angle to rotate (in rev/2**23)
    :type angle: float
    :param angular_velocity: Target angular velocity (in rpm)
    :type angular_velocity: float
    :param blending_mode: The mode to define the blending behavior (default is 2).\r
    1: The new command will interupt the original command immediately.\r
    2: The new command will be pending until the previous commands in queue are popped.
    :type blending_mode: int
    '''
    
    return