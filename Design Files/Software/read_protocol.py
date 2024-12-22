import os
from machine import Pin, SoftSPI # type: ignore
from sdcard import SDCard

class SDCardReader:
    # # Pin assignment for SPI and SD card
    # sck_pin = 32
    # mosi_pin = 33
    # miso_pin = 34
    # cs_pin = 25
    def __init__(self, miso_pin=34, mosi_pin=33, sck_pin=32, cs_pin=25):
        self.spi = SoftSPI(-1,
                           miso=Pin(miso_pin),
                           mosi=Pin(mosi_pin),
                           sck=Pin(sck_pin))
        self.sd = SDCard(self.spi, Pin(cs_pin))
        self.mount_point = '/sd'
        
        # Mount the SD card
        self.mount_sd_card()

    def mount_sd_card(self):
        try:
            vfs = os.VfsFat(self.sd)
            os.mount(vfs, self.mount_point)
            os.chdir(self.mount_point)
            print(f'SD Card mounted at {self.mount_point}.')
        except Exception as e:
            print('Failed to mount SD card:', e)

    def unmount_sd_card(self):
        try:
            os.chdir('/')
            os.umount(self.mount_point)
            print(f'SD Card unmounted from {self.mount_point}.')
        except Exception as e:
            print('Failed to unmount SD card:', e)
            
    def list_files(self):
        try:
            files = os.listdir()
            print(f'SD Card contains: {files}')
            return files
        except Exception as e:
            print('Failed to list files:', e)
            return []

    def read_csv_protocol_file(self,filename):
        command_queue = []  # Mx6 array to store commands and parameters

        try:
            with open(filename, 'r') as file:
                # Skip the headers
                file.readline()  # Assumes first line contains column headers

                for line in file:
                    # Split the line into columns
                    row = line.strip().split(',')

                    # Ensure the row has exactly 6 elements
                    if len(row) >= 6:
                        # Take the first six elements or pad with None if fewer
                        parsed_row = row[:6]
                        command_queue.append(parsed_row)
                    else:
                        # If fewer than 6, pad with None to maintain consistency
                        parsed_row = row + [None] * (6 - len(row))
                        command_queue.append(parsed_row)
                    # Check if the file is empty
            if not command_queue:
                print("Error: File is empty or contains no valid commands.")
                return []
            if (command_queue[0][0]!='setup'):
                print(f"Error: setup command not found first.")
                return[]
            elif (command_queue[len(command_queue)-1][0] != 'end'):
                print(f"Error: end command not found last.")
                return[]
            else:
                return command_queue

        except FileNotFoundError:
            print(f"Error: File {filename} not found.")
            return []
        except Exception as e:
            print(f"An error occurred: {e}")
            return []
        except Exception as e:
            print('Failed to read file:', e)