# Python Ver:   3.13.0
# Pyserial Ver: 3.5

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time
import datetime
from keshner_motion import KeshnerMotion
import API_rotation_chair


TEST_MODE = False


class VarComInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("VarCom Motor Controller Interface")
        self.root.geometry("800x600")
        
        self.serial_port = None
        self.connected = False

        self.getting_record = False
        self.getting_speed = False
        self.quiet = False

        self.speed = 0.0

        self.cmd_history = []
        self.cmd_rollback = 0
        
        # Create GUI elements
        self.create_widgets()
        

    def create_widgets(self):
        # Connection Frame
        conn_frame = ttk.LabelFrame(self.root, text="Connection", padding=10)
        conn_frame.pack(fill="x", padx=10, pady=5)
        
        ttk.Label(conn_frame, text="Port:").grid(row=0, column=0, padx=5)
        
        self.port_combo = ttk.Combobox(conn_frame, width=15, state="readonly")
        self.port_combo.grid(row=0, column=1, padx=5)
        self.refresh_ports()
        
        ttk.Button(conn_frame, text="Refresh", command=self.refresh_ports).grid(row=0, column=2, padx=5)
        
        self.connect_btn = ttk.Button(conn_frame, text="Connect", command=self.toggle_connection)
        self.connect_btn.grid(row=0, column=3, padx=5)
        
        self.status_label = ttk.Label(conn_frame, text="Disconnected", foreground="red")
        self.status_label.grid(row=0, column=4, padx=5)
        
        # Terminal Frame
        terminal_frame = ttk.LabelFrame(self.root, text="Terminal", padding=10)
        terminal_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.terminal = scrolledtext.ScrolledText(terminal_frame, height=10, state="disabled")
        self.terminal.pack(fill="both", expand=True)
        
        # Command entry
        cmd_frame = ttk.Frame(terminal_frame)
        cmd_frame.pack(fill="x", pady=5)
        
        ttk.Label(cmd_frame, text="Command:").pack(side="left", padx=5)
        
        self.cmd_entry = ttk.Entry(cmd_frame)
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.cmd_entry.bind("<Return>", lambda e: self.send_command())
        self.cmd_entry.bind("<Up>", lambda e: self.history_up())
        self.cmd_entry.bind("<Down>", lambda e: self.history_down())
        
        ttk.Button(cmd_frame, text="Send", command=self.send_command).pack(side="left", padx=5)

        # Shortcut Buttons
        self.cmd_shortcut_frame = ttk.Frame(terminal_frame)
        big_button_style = ttk.Style()
        big_button_style.configure("Big.TButton", font=("Helvetica", 12), padding=12)

        self.cmd_shortcut_frame.pack()
        ttk.Label(self.cmd_shortcut_frame, text="Perception").grid(row=0, column=1, padx=5)

        ttk.Button(self.cmd_shortcut_frame, text="Start", command=self.home_position).grid(row=1, column=0, padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="1 tour", command=self.one_tour).grid(row=2, column=0, padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="CCW", command=lambda: self.perception()).grid(row=1, column=1, padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="CW", command=lambda: self.perception(-1)).grid(row=2, column=1, padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="Keshner", command=self.keshner_motion).grid(row=1, column=2, padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="STOP", command=self.stop_motor, style="Big.TButton").grid(row=1, column=3, padx=5, rowspan=2)
        ttk.Button(self.cmd_shortcut_frame, text="Get record", command=self.get_recorded_data).grid(row=1, column=4, padx=40)
        
        # Status Dashboard
        self.status_dashboard = ttk.Frame(terminal_frame)
        self.status_dashboard.pack()
        self.speed_label = tk.StringVar()
        self.speed_label.set(str(self.speed))
        tk.Label(self.status_dashboard, textvariable=self.speed_label).pack(side="left", padx=5)

        # Script Frame
        script_frame = ttk.LabelFrame(self.root, text="Script", padding=10)
        script_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.script_text = scrolledtext.ScrolledText(script_frame, height=5)
        self.script_text.pack(fill="both", expand=True)
        
        ttk.Button(script_frame, text="Execute Script", command=self.execute_script).pack(pady=5)

        
    def refresh_ports(self):
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo['values'] = ports
        if ports:
            self.port_combo.current(0)
    
    def toggle_connection(self):
        if not self.connected:
            self.connect()
        else:
            self.disconnect()
    
    def connect(self):
        port = self.port_combo.get()
        if not port:
            messagebox.showerror("Error", "Please select a port")
            return
        
        try:
            self.serial_port = serial.Serial(
                port=port,
                baudrate=115200,
                bytesize=8,
                parity='N',
                stopbits=1,
                timeout=1
            )
            self.connected = True
            self.connect_btn.config(text="Disconnect")
            self.status_label.config(text="Connected", foreground="green")
            self.log_terminal("Connected to " + port)
            
            # Start reading thread
            threading.Thread(target=self.read_serial, daemon=True).start()
            
        except Exception as e:
            messagebox.showerror("Connection Error", str(e))
    
    def disconnect(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
        
        self.connected = False
        self.connect_btn.config(text="Connect")
        self.status_label.config(text="Disconnected", foreground="red")
        self.log_terminal("Disconnected")
        # To check how many threads are still alive
        print(threading.enumerate())
    
    def read_serial(self):
        if TEST_MODE: return

        while self.connected and self.serial_port and not self.getting_record:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('ascii', errors='ignore').strip()
                    # if data:
                    #     self.log_terminal("← " + data)
                    self.post_process_read_data(data)
            except Exception as e:
                self.log_terminal(f"Read error: {e}")
                break
    
    def send_command(self):
        if not self.connected and not TEST_MODE:
            messagebox.showwarning("Warning", "Not connected to motor controller")
            return
        
        command = self.cmd_entry.get().strip()
        if not command:
            return
        
        try:
            if not TEST_MODE:
                self.serial_port.write((command + '\r').encode('ascii'))
            self.log_terminal("→ " + command)
            self.cmd_history.append(command)
            self.cmd_rollback = 0
            self.cmd_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Send Error", str(e))

    def clear_command(self):
        self.cmd_entry.delete(0, tk.END)
        return
    
    def history_up(self):
        if not self.cmd_history:    return
        if -self.cmd_rollback+1 > len(self.cmd_history):  return
        self.cmd_rollback -= 1
        self.clear_command()
        self.cmd_entry.insert(0, self.cmd_history[self.cmd_rollback])
        return
    
    def history_down(self):
        if not self.cmd_history:    return
        if self.cmd_rollback == 0:   return
        self.cmd_rollback += 1
        self.clear_command()
        if self.cmd_rollback < 0: self.cmd_entry.insert(0, self.cmd_history[self.cmd_rollback])
        return
    
    def execute_script(self):
        if not self.connected:
            messagebox.showwarning("Warning", "Not connected to motor controller")
            return
        
        script = self.script_text.get("1.0", tk.END).strip()
        if not script:
            return
        
        lines = [line.strip() for line in script.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        def run_script():
            for line in lines:
                if not self.connected:
                    break
                try:
                    self.serial_port.write((line + '\r').encode('ascii'))
                    self.log_terminal("→ " + line)
                    threading.Event().wait(0.5)  # Small delay between commands

                except Exception as e:
                    self.log_terminal(f"Script error: {e}")
                    break
        
        threading.Thread(target=run_script, daemon=True).start()
    
    def log_terminal(self, message):
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")


    def home_position(self) -> None:
        """
        Move the chair to the turn 0 and position 0\n
        Content of command: 'moveabs 0 15'
        """
        self._opmode_switch(8)  # switch to position control mode
        self.clear_command()
        self.log_terminal("Home")
        self.cmd_entry.insert(0, "moveabs 0 15")
        self.send_command()

        return
    
    def one_tour(self) -> None:
        """
        One-way ticket to the end of the experiment\n
        Content of command: 'moveinc 8388608 15'
        """
        self._opmode_switch(8)  # switch to position control mode
        self.clear_command()
        self.cmd_entry.insert(0, "moveinc 8388608 15")
        self.send_command()

        return
    
    def keshner_motion(self, delta_t:float = 0.02) -> None:
        """
        Implement a Keshner motion to the servo.
        
        :param delta_t: the expected time difference between each time step
        :type delta_t: float
        """

        if not self.connected and not TEST_MODE:
            messagebox.showwarning("Warning", "Not connected to motor controller")
            return
        
        self.log_terminal("Setting up Keshner motion...")
        
        #Create Keshner motion table
        Keshner = KeshnerMotion(delta_t)
        threading.Event().wait(0.5)  # Small delay between commands
        
        def motion_track() -> None:
            
            # switch the opmode to velocity control
            self._opmode_switch(0)

            # change top acceleration
            self.change_acc(360*6)

            # switch off the echo
            self._send_command(API_rotation_chair.quiet())
            self.quiet = True

            # Start the recording
            self._setup_record(delta_t/2, Keshner.TIME_TOTAL)
            next_time = time.time() + delta_t

            # Send the jogging command
            for vo, po in zip(Keshner.speed_table, Keshner.position_table):
                # t_start = time.time()
                self._send_command(API_rotation_chair.jogging(vo))
                # dt = time.time() - t_start
                # self._command_delay(round(delta_t - dt,3))

                while time.time() < next_time:  pass
                next_time = next_time + delta_t

            # Stop jogging
            self._send_command(API_rotation_chair.jogging(0))
            threading.Event().wait(6)  # Small delay between commands

            # switch on the echo
            self._send_command(API_rotation_chair.dequiet())
            self.quiet = False

            # switch the opmode back to position control.
            self._opmode_switch(8)

            self.change_acc(90)

            # go back home
            self._send_command(API_rotation_chair.moveabs(0, 20))

            # End
            self.log_terminal("End of the motion.")
            
            # Get the recorded data
            self.get_recorded_data(Keshner)

            
            # switch on the echo
            self._send_command(API_rotation_chair.dequiet())
            
        
        # Start a thread for tracking the motion
        threading.Thread(target=motion_track, daemon=True).start()


    
    def perception(self, direction: int = 1):
        if not self.connected:
            messagebox.showwarning("Warning", "Not connected to motor controller")
            return

        def run():
            self._opmode_switch(8)  # switch to position control mode

            self._setup_record(0.5, 95, ["MECHANGLE", "V"])    # record the position data with a sampling time of 0.5s and a total time of 95s

            try:
                self.log_terminal("Start Perception Experiment")
                # command 1
                self._send_command(API_rotation_chair.moveabs(direction*360*22, 90), "Start to record.")
                start_time = time.time()

            except Exception as e:
                self.log_terminal(f"Perception error: {e}")

            vel_Ts = 0.5
            total_time = 95

            self.getting_speed = True

            for _ in range(int(total_time/vel_Ts)):
                self._send_command("v")
                threading.Event().wait(vel_Ts)
                if _ < 3: continue
                if (self.speed > -0.1 and self.speed < 0.1):
                    print(f"Duration: {round(time.time() - start_time, 1)} s")
                    break

            self.getting_speed = False

        threading.Thread(target=run, daemon=True).start()


    def post_process_read_data(self, line:str) -> None:
        """
        To decide the read data should be:
         1. Log to terminal
         2. Save to a file
         3. Change the state of any label
         4. Doe niets evens
        
        :param line: The line of read data
        :type line: str
        """
        if not line: return
        
        if self.getting_speed:
            space_pos = line.find(" ")
            if space_pos != -1:
                try:
                    vel = float(line[:space_pos])
                    self._change_speed(vel)
                except:
                    print("Unreadable")
                return

        self.log_terminal("← " + line)
        return
    
    def change_acc(self, val:float) -> None:
        """
        Change accelaration and deccelaration at the same time.\r
        A short delay 0.5 s will be between 2 commands.

        :param val: Value in deg/s^2 to implement as accelaration and decelaration.
        """
    
        # change the acceleration cap
        self._send_command(API_rotation_chair.acc(val))
        threading.Event().wait(0.5)  # Small delay between commands
        self._send_command(API_rotation_chair.dec(val))
        threading.Event().wait(0.5)  # Small delay between commands
        
        return


    def enable_motor(self) -> None:
        """
        Enable function to enable the motor.
        """
        self._send_command(API_rotation_chair.enable_motor(), "Motor Enable")
        threading.Event().wait(0.5)  # Small delay between commands
        return

    def stop_motor(self) -> None:
        """
        Stop function to stop the chair immediately and disable the motor.
        """
        self._send_command(API_rotation_chair.disable_motor(), "Motor Stop")
        threading.Event().wait(0.5)  # Small delay between commands
        return
    
    def get_recorded_data(self, motion_parameter:KeshnerMotion|None = None) -> None:
        self.getting_record = True
        
        # Get the recorded data
        self._send_command(API_rotation_chair.get_recorded_data())

        # Read the serial and output the file as txt.
        self._read_serial_and_output(motion_parameter)

        threading.Thread(target=self.read_serial, daemon=True).start()

        return

    def _send_command(self, command: str, log_message: str = "") -> None:
        """
        An internal function "_send_command" to send command to the motor controller.
        
        :param command: Syntax as per manual
        :param log_message: Any message tagged
        :type log_message: str
        """
        if not self.connected and not TEST_MODE:
            messagebox.showwarning("Warning", "Not connected to motor controller")
            return

        if not command: return
        
        try:
            if not TEST_MODE:
                self.serial_port.write((command + '\r').encode('ascii'))
            if self.quiet or self.getting_speed: return
            self.log_terminal("→ " + command + "\t\t\t" + log_message)
        except Exception as e:
            messagebox.showerror("Send Error", str(e))
    
    def _setup_record(self, sampling_time:float, sampling_span:float, recording_variable:str|list[str] = "V") -> None:
        '''
        An internal function to set up the recording of the data.\r
        It will send the command to the motor controller to start the recording,
        and then call the function to read the serial data and save it to a file.

        :param sampling_time: The time difference between each recorded data point in seconds
        :type sampling_time: float
        :param sampling_span: The total time of the recording in seconds
        :type sampling_span: float
        :param recording_variable: The variable to be recorded, 'V' for velocity, 'MECHANGLE' for position. You can send command "reclist" to the motor controller to check the available variables for recording.
        :type recording_variable: str
        '''

        def format_recording_variable(var:str|list[str]) -> str:
            if isinstance(var, str):
                return '"' + var
            elif isinstance(var, list):
                new_var = []
                for v in var:
                    new_var.append('"' + v)
                return " ".join(new_var)
            else:
                raise ValueError("recording_variable should be either a string or a list of strings.")

        # set the record data to 'ascii' encode.
        self._send_command("getmode 0")

        self._send_command(API_rotation_chair.record(sampling_time, int(sampling_span//sampling_time), format_recording_variable(recording_variable)))
        print(format_recording_variable(recording_variable))
        self._send_command(API_rotation_chair.trigger_record())

        return
    
    def _opmode_switch(self, mode:int) -> None:
        '''
        Help the UI to stop the motor, change the mode, and restart the motor all at once.
        
        :param mode: 0: Velocity Control, 8: Position Control
        :type mode: int
        '''

        # deactive the motor
        self.stop_motor()

        # change opmode
        self._send_command(API_rotation_chair.opmode(mode))
        threading.Event().wait(0.5)  # Small delay between commands
        self.log_terminal("Configure the new dynamic setting......")

        # enable the motor again
        self.enable_motor()
        threading.Event().wait(2)  # Small delay between commands

        return
    
    
    
    def _read_serial_and_output(self, motion_parameter:KeshnerMotion|None = None):
        if TEST_MODE: return

        # Create a file
        recording_folder_name = "../Recorded Data"
        recording_file_name = recording_folder_name + f"/motion_record_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.txt"

        with open(recording_file_name, 'w') as newfile:
            # Writing the header
            if motion_parameter == None:
                newfile.write("Sampling Time: N/A\t\tTotal Time: N/A\r\r")
            else:
                newfile.write(f"Sampling Time: {motion_parameter.sampling_time}\t\tTotal Time: {motion_parameter.TIME_TOTAL}\r")

        while self.connected and self.serial_port and self.getting_record:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('ascii', errors='ignore')
                    if data:
                        if data == "-->":
                            self.getting_record = False
                        else:
                            with open(recording_file_name, 'a') as newfile:
                                newfile.write(data)
                        
            except Exception as e:
                self.log_terminal(f"Read error: {e}")
                break
        
        self.log_terminal(f"Created file: {recording_file_name}")

    def _command_delay(self, delay_time:float) -> None:
        """
        An internal function to introduce a delay of certain amount of seconds before the next command is executed.
        
        :param delay_time: The time of the delay in seconds
        :type delay_time: float
        """
        self._send_command(API_rotation_chair.delay(delay_time))
        return
    
    def _change_speed(self, val:float) -> None:

        self.speed = val
        self.speed_label.set(str(val))

        return

    ### NEW FUNCTIONS ###



if __name__ == "__main__":
    root = tk.Tk()
    app = VarComInterface(root)
    root.mainloop()
