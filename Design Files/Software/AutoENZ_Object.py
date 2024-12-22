from machine import Pin, PWM # type: ignore
import time
import math
# from stepper import Stepper

class AutoENZ:
    
    def __init__(self, a, b, c, d, e):
        self.DIST_EDGE_TO_WELL = a # represents distance from close edge of glass slide to edge of 
        self.DIST_BETWEEN_WELLS = b # represent distance between adjacent wells, or well pitch
        self.LSP1_VOLUME = c #values based on user callibration of lsp pump 1, in ul
        self.LSP2_VOLUME = d #values based on user callibration of lsp pump 2, in ul
        self.LSP3_VOLUME = e #values based on user callibration of lsp pump 3, in ul

        self.DIST_BETWEEN_PUMPS = 8.5 # represents distance between lsp pump tips, intrinsic property of robot
        self.DIST_LSP1_EDGE = 8.5 # represent distance from lsp pump 1 to the edge of glass slide, intrinsic property of robot
        self.LINEAR_SPEED_MM_S = 14.01 # adjusted manually, speed of linear actuator under no load in mm/s, taken from website info of 0.59"/sec
        self.MAX_DISTANCE = 94 # represents the distance the linear actuator can move before hitting the wall, intrinsic property of robot, in mm
        self.PERISTALTIC_FLOW_RATE = 0.83333333333 #represents flow rate in ml/second, taken from manufacturers specification of 50ml/min
        
        self.lsp1 = Pin(17, Pin.OUT)
        self.lsp1.off()
        self.lsp2 = Pin(16, Pin.OUT)
        self.lsp2.off()
        self.lsp3 = Pin(4, Pin.OUT)
        self.lsp3.off()

        self.pPump1 = Pin(27, Pin.OUT)
        self.pPump1.off()
        self.pPump2 = Pin(14, Pin.OUT)
        self.pPump2.off()
        self.pPump3 = Pin(13, Pin.OUT)
        self.pPump3.off()

        self.linear_in1 = Pin(18, Pin.OUT)  # IN2 control pin
        self.linear_in2 = Pin(26, Pin.OUT)  # IN1 control pin
        self.linear_in1.off()
        self.linear_in2.off()

        self.LED = Pin(2, Pin.OUT)
        self.LED.off()

        self.drying_pin_num = 19

    # # Function to set linear actuator direction
    def calculate_well_distance(self, well_location, pump_number):
        distance = ((well_location - 1) * self.DIST_BETWEEN_WELLS) + self.DIST_EDGE_TO_WELL + self.DIST_LSP1_EDGE + ((pump_number - 1) * self.DIST_BETWEEN_PUMPS)
        if distance > self.MAX_DISTANCE:
            raise ValueError(f"attempted distance to move: {distance} is greater than limit: {self.MAX_DISTANCE}")
        return distance
    
    def move_actuator(self, direction, distance):
        # on and on initiates break
        # off and off is coasting and powered off
        duration = (distance / self.LINEAR_SPEED_MM_S)
        if direction == "forward":
            self.linear_in1.on()
            self.linear_in2.off()
            time.sleep(duration)    # duration for how long actuator moves
            self.linear_in1.on()   # put brake on actuator
            self.linear_in2.on()

        elif direction == "backward":
            self.linear_in1.off()
            self.linear_in2.on()
            time.sleep(duration)
            self.linear_in1.on()
            self.linear_in2.on()

        time.sleep(0.5) # delay to ensure fully stopped, then turn off the linear actuator
        self.linear_in1.off()
        self.linear_in2.off()

    def home_actuator(self):
        self.move_actuator("backward", 110)

    #completed function, need to test
    def dispense(self, lsp_pump, well_num, liquid_amount):
        # sets correct LSP pump values to function
        if lsp_pump == 1:
            pump = self.lsp1
            num_pump = 1
            volume_per_pump = self.LSP1_VOLUME
        elif lsp_pump == 2:
            pump = self.lsp2
            num_pump = 2
            volume_per_pump = self.LSP2_VOLUME
        elif lsp_pump == 3:
            pump = self.lsp3
            num_pump = 3
            volume_per_pump = self.LSP3_VOLUME
        else:
            raise ValueError(f"{lsp_pump} pump is not labeled correctly")
        print(f"liquid_amount: {liquid_amount}, type: {type(liquid_amount)}")
        print(f"volume_per_pump: {volume_per_pump}, type: {type(volume_per_pump)}")
        cycles = math.ceil(liquid_amount / volume_per_pump)
        print(f"dispensing {liquid_amount} from lsp pump #{num_pump} to well #{well_num}")
        dist = self.calculate_well_distance(well_num, num_pump)
        self.move_actuator('forward', dist)
        for i in range(cycles):
            pump.on()
            time.sleep(.25)
            pump.off()
            time.sleep(.25)
        self.move_actuator('backward', dist + 10) #moving backwards to go home, with addition 10mm mock buffer to ensure correct homing
        return[]

    def wash(self, peristaltic_pump, well_num, liquid_volume):
        if peristaltic_pump == 1:
            pump = self.pPump1
            num_pump = 1
        elif peristaltic_pump == 2:
            pump = self.pPump2
            num_pump = 2
        elif peristaltic_pump == 3:
            pump = self.pPump3
            num_pump = 3

        wash_time = math.ceil(liquid_volume / self.PERISTALTIC_FLOW_RATE)
        print(f"dispensing {liquid_volume}ml over {wash_time} seconds from persitaltic pump#{num_pump} to well #{well_num}")
        dist = self.calculate_well_distance(well_num, num_pump)
        self.move_actuator('forward', dist)
        pump.on()
        time.sleep(wash_time)
        pump.off()
        time.sleep(0.5) # little delay to make sure no fluid is still flowing
        self.move_actuator('backward', dist + 10) #moving backwards to go home, with addition 10mm mock buffer to ensure correct homing
        return[]

    def drying_step(self, drying_time):
        self.drying_pin = PWM(Pin(self.drying_pin_num), freq = 50, duty = 0) #setup pin 
        self.drying_pin.duty(1023)  # Turn the motor on by setting the GPIO pin high
        print("start drying")
        time.sleep(drying_time)         # Run dryer for drying_time seconds
        self.drying_pin.duty(0)         #turn pin off
        self.drying_pin.deinit()        #de initialize drying_pin
        print("end drying")

    def prime_all_tubes(self):
        lsp_priming_volume = 920 # volume in uL to go fill lsp pumps, tested from 80 cycles of 11.5 uL
        lsp1_cycles = math.ceil(lsp_priming_volume / self.LSP1_VOLUME)
        lsp2_cycles = math.ceil(lsp_priming_volume / self.LSP2_VOLUME)
        lsp3_cycles = math.ceil(lsp_priming_volume / self.LSP3_VOLUME)
        lsp1_count = 0
        lsp2_count = 0
        lsp3_count = 0
        while ((lsp1_count < lsp1_cycles) or (lsp2_count < lsp2_cycles) or (lsp3_count < lsp3_cycles)):
            if (lsp1_count < lsp1_cycles):
                self.lsp1.on()
                lsp1_count+=1
            if (lsp2_count < lsp2_cycles):
                self.lsp2.on()
                lsp2_count+=1
            if (lsp3_count < lsp3_cycles):
                self.lsp3.on()
                lsp3_count+=1
            time.sleep(0.25)
            self.lsp1.off()
            self.lsp2.off()
            self.lsp3.off()
            time.sleep(0.25)
        self.pPump1.on()
        self.pPump2.on()
        self.pPump3.on()
        time.sleep(8)
        self.pPump1.off()
        self.pPump2.off()
        self.pPump3.off()