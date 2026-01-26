# Python Ver:   3.13.0
# Pyserial Ver: 3.5

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import serial
import serial.tools.list_ports
import threading
import time
from keshner_motion import KeshnerMotion
import API_rotation_chair


TEST_MODE = True


class VarComInterface:
    def __init__(self, root):
        self.root = root
        self.root.title("VarCom Motor Controller Interface")
        self.root.geometry("800x600")
        
        self.serial_port = None
        self.connected = False
        
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
        
        ttk.Button(cmd_frame, text="Send", command=self.send_command).pack(side="left", padx=5)

        # Shortcut Buttons
        self.cmd_shortcut_frame = ttk.Frame(terminal_frame)
        self.cmd_shortcut_frame.pack()
        ttk.Button(self.cmd_shortcut_frame, text="Start", command=self.home_position).grid(row=0, column=0, padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="1 tour", command=self.one_tour).grid(row=1, column=0, padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="Keshner", command=self.keshner_motion).grid(row=2, column=0, padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="STOP", command=self.stop_motor).grid(row=0, column=1, padx=5, rowspan=3)
        
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
            self.read_thread = threading.Thread(target=self.read_serial, daemon=True)
            self.read_thread.start()
            
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
    
    def read_serial(self):
        if TEST_MODE: return

        while self.connected and self.serial_port:
            try:
                if self.serial_port.in_waiting:
                    data = self.serial_port.readline().decode('ascii', errors='ignore').strip()
                    if data:
                        self.log_terminal("← " + data)
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
            self.cmd_entry.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Send Error", str(e))

    def clear_command(self):
        self.cmd_entry.delete(0, tk.END)
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
                start_time = time.time_ns()
                if not self.connected:
                    break
                try:
                    self.serial_port.write((line + '\r').encode('ascii'))
                    self.log_terminal("→ " + line)
                    threading.Event().wait(0.5)  # Small delay between commands
                    end_time = time.time_ns()

                except Exception as e:
                    self.log_terminal(f"Script error: {e}")
                    break
        
        threading.Thread(target=run_script, daemon=True).start()
    
    def log_terminal(self, message):
        self.terminal.config(state="normal")
        self.terminal.insert(tk.END, message + "\n")
        self.terminal.see(tk.END)
        self.terminal.config(state="disabled")

    
    ### NEW FUNCTIONS ###
    
    def home_position(self) -> None:
        """
        Move the chair to the turn 0 and position 0\n
        Content of command: 'moveabs 0 15'
        """
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
        self.clear_command()
        self.cmd_entry.insert(0, "moveinc 8388608 15")
        self.send_command()

        return
    
    def keshner_motion(self, delta_t:float = 0.1) -> None:
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
        Keshner = KeshnerMotion(delta_t, 15)
        threading.Event().wait(0.5)  # Small delay between commands

        # disable the motor
        self.stop_motor()
        
        # change opmode to 0 (Velocity control)
        self._send_command(API_rotation_chair.opmode(0))
        threading.Event().wait(0.5)  # Small delay between commands

        # enable the motor again
        self.enable_motor()

        # change the acceleration
        self._send_command(API_rotation_chair.acc(360*4))

        # Start a recording
        self._send_command(API_rotation_chair.record(Keshner.TIME_TOTAL, 2000, '"MECHANGLE "V'))
        self._send_command(API_rotation_chair.trigger_record())
        
        def motion_track() -> None:
            # Start the index
            i = 0
            
            # Time stamps
            time_start = time.time()
            time_end = time_start + Keshner.time[-1]
            time_curr = time.time()
            time_next = time_curr + delta_t

            # Loop of MOVEINC
            while time_curr < time_end:
                i, t_now, vo = Keshner.next_step(i)
                if i==-1: break
                self._send_command(API_rotation_chair.jogging(vo), f"at t={round(t_now,2)}s")

                while time.time() < time_next: pass
                time_curr = time.time()
                time_next = time_curr + delta_t

            # Stop jogging
            self._send_command(API_rotation_chair.jogging(0))
            threading.Event().wait(0.5)  # Small delay between commands

            # disactive
            self.stop_motor()

            # change opmode to 8 (Position control)
            self._send_command(API_rotation_chair.opmode(8))
            threading.Event().wait(0.5)  # Small delay between commands

            # enable the motor again
            self.enable_motor()

            # change the acceleration
            self._send_command(API_rotation_chair.acc(90))

            # go back home
            self._send_command(API_rotation_chair.moveabs(0, 2))

            # End
            self.log_terminal("End of the motion.")
            
            # Get the recorded data
            self._send_command(API_rotation_chair.get_recorded_data())
        
        # Start a thread for tracking the angle
        threading.Thread(target=motion_track, daemon=True).start()

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

    def _send_command(self, command, log_message: str = "") -> None:
        """
        An internal function "_send_command" to send command to the motor controller.
        
        :param self: Description
        :param command: Description
        :param log_message: Description
        :type log_message: str
        """
        if not self.connected and not TEST_MODE:
            messagebox.showwarning("Warning", "Not connected to motor controller")
            return
        
        if not command: return
        
        try:
            if not TEST_MODE:
                self.serial_port.write((command + '\r').encode('ascii'))
            self.log_terminal("→ " + command + "\t\t\t" + log_message)
        except Exception as e:
            messagebox.showerror("Send Error", str(e))

    ### NEW FUNCTIONS ###



if __name__ == "__main__":
    root = tk.Tk()
    app = VarComInterface(root)
    root.mainloop()
