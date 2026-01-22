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


TEST_MODE = False


class VarComInterface:
    def __init__(self, root, angle_table:KeshnerMotion|None = None):
        self.root = root
        self.root.title("VarCom Motor Controller Interface")
        self.root.geometry("800x600")
        
        self.serial_port = None
        self.connected = False

        self.angle_table = angle_table
        
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
        ttk.Button(self.cmd_shortcut_frame, text="Start", command=self.home_position).pack(side="left", padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="1 tour", command=self.one_tour).pack(side="left", padx=5)
        ttk.Button(self.cmd_shortcut_frame, text="Keshner", command=self.keshner_motion).pack(side="left", padx=5)
        
        # Script Frame
        script_frame = ttk.LabelFrame(self.root, text="Script", padding=10)
        script_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.script_text = scrolledtext.ScrolledText(script_frame, height=10)
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
    
    def keshner_motion(self, delta_t:float = 0.05) -> None:
        """
        Implement a Keshner motion to the servo.
        
        :param delta_t: the expected time difference between each time step
        :type delta_t: float
        """
        def go_jogging(voi:float, t:float) -> None:
            command = API_rotation_chair.jogging(voi)
            try:
                if not TEST_MODE:
                    self.serial_port.write((command + '\r').encode('ascii'))
                self.log_terminal("→ " + command + f"\t\t\t\tat\t{round(t, 2)} s")
            except Exception as e:
                messagebox.showerror("Send Error", str(e))


        if not self.connected and not TEST_MODE:
            messagebox.showwarning("Warning", "Not connected to motor controller")
            return
        
        # Start a recording
        self.record_motion(self.angle_table.t[-1])
        
        def motion_track() -> None:
            # Start the index
            i = 0
            
            # Time stamps
            time_start = time.time()
            time_end = time_start + self.angle_table.t[-1]
            time_curr = time.time()
            time_next = time_curr + delta_t

            # Loop of MOVEINC
            while time_curr < time_end:
                time_curr_in_task = time_curr - time_start
                vo = self.angle_table.calculate_speed(time_curr_in_task, delta_t)
                go_jogging(vo, time_curr_in_task)

                while time.time() < time_next: pass
                time_curr = time.time()
                time_next = time_curr + delta_t
            
            # End
            self.log_terminal("End of the motion.")
        
        # Start a thread for tracking the angle
        threading.Thread(target=motion_track, daemon=True).start()


    def record_motion(self, span:float) -> None:
        """
        Start a recording for SPAN seconds.\n
        Record the variable 'MECHANGLE' and 'V'.
        
        :param span: the total span of the record
        :type span: float
        """
        num_points = 2000
        sample_time_sec = span/num_points
        sample_time = sample_time_sec * 1000000 // 31.25

        self.clear_command()
        self.cmd_entry.insert(0, f'record {sample_time} {num_points} "MECHANGLE "V')
        self.send_command()

        return

    ### NEW FUNCTIONS ###



if __name__ == "__main__":
    root = tk.Tk()
    angle_table = KeshnerMotion()
    app = VarComInterface(root, angle_table)
    root.mainloop()
