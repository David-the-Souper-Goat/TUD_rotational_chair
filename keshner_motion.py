from math import sin, cos, pi

class KeshnerMotion:
    
    # CONSTANT
    FUNDAMENTAL_FREQ = 0.005    #[Hz]
    HOMONICS = [37, 49, 71, 101, 143, 211, 295, 419, 589, 823]
    ANG_SPEED_HOMONICS = [20, 20, 20, 19, 19, 19, 16, 16, 15, 13]   #[deg/s]
    TIME_TOTAL = 400            #[s]

    def __init__(self, sampling_time:float = 0.1):
        self.sampling_time = sampling_time
        self.t = []
        self.gear_ratio = 2**23
        self.speed_ratio = 6.0      #deg/s * speed_ratio -> rpm

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
        for i in range(len(self.HOMONICS)):
            A_i = self.ANG_SPEED_HOMONICS[i]
            f_i_rad = 2 * pi * self.FUNDAMENTAL_FREQ * self.HOMONICS[i]
            ans = ans - A_i * cos(f_i_rad*t) / f_i_rad

        return ans
    
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
        ans = sum([A*sin(2*pi*h*self.FUNDAMENTAL_FREQ*t) for A, h in zip(self.ANG_SPEED_HOMONICS, self.HOMONICS)])

        return ans
    

if __name__ == "__main__":
    test = KeshnerMotion()
    print(test.position(0))
    print(test.position(0.5))