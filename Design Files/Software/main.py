from AutoENZ_Object import AutoENZ
from read_protocol import SDCardReader
from machine import Pin # type: ignore
import time
import sys


try:
    # Initialize SD card reader
    sd_reader = SDCardReader()
    # List files in the SD card root directory
    files = sd_reader.list_files()
    print(f"SD Card contains: {files}")

    # Define the target filename
    filename = 'protocol.csv'

    # Check if the file exists
    if filename not in files:
        raise OSError(f"Error: {filename} not found on the SD card.")  # Raise OSError

    print(f"Reading {filename}...")

    # Read and parse the protocol file
    table = sd_reader.read_csv_protocol_file(filename)
    if not table:  # Check if commands are empty
        raise ValueError(f"The file {filename} is empty or contains invalid data.")

    print("Parsed Commands:")
    for row in table:
        print(row)

    # Initialize the robot if file reading was successful
    robot_parameters = table[0][0:6]
    if robot_parameters[0] != "setup":
        raise Exception(f"setup commands need to be on the first line!")
    commands = table[1:len(table)]
    if commands[len(commands) - 1][0] != "end":
        raise Exception(f"end command needs to be the final line!")
    robot = AutoENZ(float(robot_parameters[1]), float(robot_parameters[2]), float(robot_parameters[3]), float(robot_parameters[4]), float(robot_parameters[5]))
    sd_reader.unmount_sd_card()
    robot.home_actuator()
    for step in commands:
        print(f"now running step {step[0]}")
        if step[0] == "dispense":
            robot.dispense(int(step[1]), int(step[2]), int(step[3]))
        elif step[0] == "wash":
            robot.wash(int(step[1]), int(step[2]), int(step[3]))
        elif step[0] == "dry":
            robot.drying_step(int(step[1]))
        elif step[0] == "wait":
            robot.LED.on()
            time.sleep(int(step[1]))
            robot.LED.off()
        elif step[0] == "prime":
            robot.prime_all_tubes()
        elif step[0] == "end":
            print("Reached end of commands, exiting system")
            time.sleep(1)
            sys.exit()
        else:
            raise Exception(f"not a valid command name")
    
except OSError as os_error:  # Catch SD card-related errors
    print(os_error)
except ValueError as ve:
    print(f"Value error detected: {ve}")
except Exception as e:
    print(f"Failed to initialize the SD card reader or process files: {e}")