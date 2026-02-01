from math import sin, cos, pi
from time import sleep

class KeshnerMotion:
    
    # CONSTANT
    FUNDAMENTAL_FREQ = 0.005    #[Hz]
    HOMONICS = [37, 49, 71, 101, 143, 211, 295, 419, 589, 823]
    ANG_SPEED_HOMONICS = [20, 20, 20, 19, 19, 19, 16, 16, 15, 13]   #[deg/s]
    TIME_TOTAL = 20            #[s]
    TIME_SHIFT = 443.714675       #[s] to make speed(0)=0

    def __init__(self, sampling_time:float = 0.5, total_time:float = TIME_TOTAL) -> None:
        self.TIME_TOTAL = total_time
        self.reset_sampling_time(sampling_time)

    ### EXTERNAL FUNCTIONS
    def next_step(self, i:int) -> tuple[int, float, float]:
        if i==len(self.time):
            i = -1
        else:
            i_next = i+1
        return (i_next, self.time[i], self.speed_table[i])
    
    def reset_sampling_time(self, sampling_time:float) -> None:
        self.sampling_time = sampling_time
        self._generate_time_table()
        self._generate_speed_table()
        return

    def position(self, t:float) -> float:
        """
        Calculate the position at a certain time.
        By adding all the influeces from each sinusoidal signal.
        ans = sum(-A_i * cos(2*pi*f_i*t + d_i) / (2*pi*f_i)) for i = 0 to 9
        :param t: The time of the query in [s]
        :type t: float
        :return: The position in [deg]
        :rtype: float
        """

        ans = 0.0
        t = t - self.TIME_SHIFT
        for i in range(len(self.HOMONICS)):
            A_i = self.ANG_SPEED_HOMONICS[i]
            f_i_rad = 2 * pi * self.FUNDAMENTAL_FREQ * self.HOMONICS[i]
            ans = ans - A_i * cos(f_i_rad*t) / f_i_rad

        return round(ans,2)
    
    def speed(self, t:float) -> float:
        """
        Calculate the speed at a certain time.
        By adding all the influeces from each sinusoidal signal.
        ans = sum(A_i * sin(2*pi*f_i*t + d_i)) for i = 0 to 9
        :param t: The time of the query in [s]
        :type t: float
        :return: The position in [deg/s]
        :rtype: float
        """
        t = t - self.TIME_SHIFT
        ans = sum([A*sin(2*pi*h*self.FUNDAMENTAL_FREQ*t) for A, h in zip(self.ANG_SPEED_HOMONICS, self.HOMONICS)])

        return round(ans,2)
    

    ### INTERNAL FUNCTIONS  
    def _generate_time_table(self) -> None:
        self.time = [self.sampling_time * i for i in range(int(self.TIME_TOTAL // self.sampling_time)+1)]
        return
    
    def _generate_speed_table(self) -> None:
        self.speed_table = [self.speed(t) for t in self.time]
        return
    

if __name__ == "__main__":
    test = KeshnerMotion()
    distance = test.position(0)
    for k in range(100):
        t_now = round(0.1*k, 2)
        now_speed = test.speed(t_now)
        print(f"t={t_now}, theta_i={round(distance,2)}, theta_c={test.position(t_now)}, w={now_speed}")
        distance += now_speed*0.1
        sleep(0.1)