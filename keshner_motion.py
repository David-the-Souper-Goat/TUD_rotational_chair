
import csv

foldername_keshner = ""
filename_keshner = "SeatRotationRad_15s_test.csv"
path_keshner = foldername_keshner + "/" + filename_keshner if foldername_keshner else filename_keshner


class KeshnerMotion:
    def __init__(self, filename:str = path_keshner):
        self.t = []
        self.ang_in_rad = []
        self.ang_in_rev = []
        self.filename = filename
        self.gear_ratio = 2**23
        self.speed_ratio = 64.0
        
        self.read_csv()

        self.delta_t = self.t[1] - self.t[0]

    def read_csv(self) -> None:
        with open(self.filename, mode='r') as file:
            csvFile = csv.reader(file, delimiter=";")
            for line in csvFile:
                
                t = float(line[0])
                self.t.append(t)
                
                pos = float(line[1])
                self.ang_in_rad.append(pos)
                self.ang_in_rev.append(pos*self.gear_ratio/6.28318530718)

            self.l = len(self.t)
        return
    
    def calculate_speed(self, t1:float, dt:float) -> float:
        ang_start = self.expected_location_in_rev(t1)
        ang_end = self.expected_location_in_rev(t1+dt)
        return (ang_end - ang_start) * self.speed_ratio / (self.gear_ratio * dt)
    
    def calculate_step(self, t1:float, dt:float) -> float:
        return self.expected_location_in_rev(t1+dt) - self.expected_location_in_rev(t1)
    
    def expected_location_in_rev(self, t:float) -> float:
        i = int(t//self.delta_t)
        if i < self.l:
            return self.ang_in_rev[i]
        return self.ang_in_rev[-1]
