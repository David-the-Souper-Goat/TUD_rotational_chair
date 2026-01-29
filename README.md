# TUD_rotational_chair
An user interface to control the rotational chair in ME, TU Delft.


### TO-DO LIST
1. Use "duration" to make jogging command pile up automatically.

    Duration should be equal to target sampling time of Keshner motion.

    Command sending rate should be higher than sampling rate of Keshner motion.

2. Try the new "get_recorded_data".

    Check if the main thread stops reading serial after "getting_record" signal has been turned off.

    Check if function "write" can be used directly to write an entire "serial.read()".

3. (Optional) To build a converter from recorded data to a csv file.