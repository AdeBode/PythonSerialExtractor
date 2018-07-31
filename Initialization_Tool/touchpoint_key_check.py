import time
import serial
#import serial.tools.list_ports
import glob
import sys
from sys import platform
import csv
import os

# 1) creating/updating a CSV which associates each touchpoint device address to a touchpoint number (on the TP case) touchpoint number <-> touchpoint address
#       - This file will be our table which lets us know which device address is which touchpoint number
#       - The script will throw warnings when two touchpoints have the same TP number
#       - The script will throw warnings when a touchpoint/touchpoint address appears twice in the file
#       - If the touchpoint is not currently in the list, it is added to the list and the user is returned a generated TP number (max old TP number + 1)
#       - A seperate mode, where user will be able to provide input (the TP number they see on the connected touchpoint):
#         -- If the user input, the user TP number, does not match the TP number known on the csv file, the program throws a warning and the user can opt to:
#              --- delete the old csv line which had the TP number and update the current TP with the user TP number
#         -- If the TP does not exist on the list, add it with the user input TP number
# 2)     !!!! REMOVED IN DEMO !!!!              making a csv which associates a touchpoint number <-> touchpoint address <-> standholder/stand info
#       - the user is given the option to either create a new assocation csv or continue using the old one if it exists
#       - the user must place a reference csv with standholder/touchpoint user information
#       - the script must be continuous (like the serial extraction one) that u can just plug in touchpoints
#       - when u plug in a touchpoint, the script takes its device address and tp number (from the first tools csv) and appends the
#         standholder/touchpoint user information
#       - if the touchpoint is already associated to on the csv, a user warning is given and nothing happens. 

association_file = '../INPUTS/event_tp_users.csv'
tp_number_file = '../TP_number_key/touchpoint_key.csv'

def update_info(old, new):
    with open(tp_number_file, 'rb') as f:
        reader = csv.reader(f, delimiter=',')
        #writer = csv.writer(tempfile, delimiter=',')
        res = []
        finish = False
        for row in reader:
            if row[0] == old and finish == False:
                row[0] = new
                res.append(row)
                finish = True
            else:
                res.append(row)
        f.close()
    with open(tp_number_file, 'wb') as ff:
        writer = csv.writer(ff, delimiter=',')
        #writer = csv.writer(tempfile, delimiter=',')
        for row in res:
            writer.writerow(row)
        ff.close()

def add_new_tp(address):
    add = address.upper()[0:17]
    max = 0
    with open(tp_number_file, 'rb') as f:
        reader = csv.reader(f, delimiter=',')
        res = []
        finish = False
        for row in reader:
            if row[0] == 'TP number':
                res.append(row)
                continue
            if int(row[0]) > max:
                max = int(row[0])
            res.append(row)
        f.close()
    max += 1
    str_input = raw_input("Please enter the TP number from the back side of the case.\nPlease enter \'n\' if there is no number on the back.\n");
    if str_input == 'n':
        new_row = [str(max), add]
    else:
        new_row = [str_input, add]
    res.append(new_row)
    
    with open(tp_number_file, 'wb') as ff:
        writer = csv.writer(ff, delimiter=',')
        #writer = csv.writer(tempfile, delimiter=',')
        for row in res:
            writer.writerow(row)
        ff.close()

def get_assiciation_info(address):
    desired_tp_number = ''
    with open(tp_number_file, 'rU') as f:
        reader = csv.reader(f, delimiter=',')
        next(reader)
        for row in reader:
            if address.upper()[0:17] == row[1]:
                desired_tp_number = row[0]
    return desired_tp_number

def key_check():
    print "\n****************************************************"
    print "ensuring TP association reference file is consistent"
    
    tp_nums = []
    tp_addresses = []
    dup = False
    with open(tp_number_file, 'rU') as f:
        reader = csv.reader(f, delimiter=',')
        next(reader)
        for row in reader:
            if row[0] not in tp_nums:
                tp_nums.append(row[0])
            else:
                print '!!Touchpoint '+row[0]+ ' has a duplicate in the association file!!'
                dup = True
            if row[1] not in tp_addresses:
                tp_addresses.append(row[1])
            else:
                print '!!Touchpoint address '+row[1]+ ' has a duplicate in the association file!!'
                dup = True
    if dup == False:
        print 'association file is OK (no TP# or TP addr ducplicates).'
    print "****************************************************"

    stri = raw_input("Do you wish to check or add a touchpoint to the association file???\nPlease answer with y/n\n")
    if stri == 'y':
        while True:
            print "Please plug in a Touchpoint."
            listen_port()
    else:
        print 'Good Bye!'

def get_port():
    """ list all ports. If only one serial port is found it will be automatically returned.
    If multiple are present the user will be prompted to choose one."""
    if platform == "linux" or platform == "linux2": # Linux
        print 'searching linux dir'
        ports = glob.glob('/dev/ttyUSB*')
    elif platform == "darwin": # OSX
        print 'searching darwin dir'
        ports = glob.glob('/dev/tty.usb*')
    print 'available ports: '
    for p in ports:
        print str(ports.index(p)) + ' ' + str(p)
    
    # selecting a port
    if len(ports) == 1:
        print 'only 1 USB port has been detected and will be used'
        port_name = str(ports[0])
    elif len(ports) == 0:
        print 'no ports found'
        port_name = '' # check for this return with exception when calling this function
    else:
        input_number = raw_input("select a port (index number from list) >> ")
        port_name = str(ports[int(input_number)])
    return port_name

def start_communication(port_name):
    ser = serial.Serial(
    port=port_name,
    baudrate=460800,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)
    ser.isOpen()
    print 'serial open'
    return ser

def send_command(ser, command, terminator_bool):
    while True:
        ser.write(command)
        response = collect_output(ser, terminator_bool)
        if (response[0:12] != '$OVERRUN_ERR') and (len(response) != 0):
            return response
        else:
            time.sleep(1)

def collect_output(ser, terminator_bool, wait_time=0.1):
    # terminator_bool is a true/false indicating whether we are expecting
    # the serial message to have an end character ('$END_OF_FILE')
    out = ''
    checksum = 0
    if terminator_bool:
        # time.sleep(wait_time) # wait for serial buffer to fill
        feedback_threshold = 300000
        max_waiting = 0
        while True:
            max_waiting += 1
            bytes_waiting = ser.inWaiting()
            if bytes_waiting > 0:
                # print 'bytes waiting: ' + str(bytes_waiting)
                next_char = ser.read(bytes_waiting) # reading the serial bytes
                out += next_char # append it to previous content
            if out[-14:-2] == '$END_OF_FILE': # identiftying the end of a file
                check_list = out.split("\r\n")
                sent_check = int(check_list[len(check_list)-2])
                out = out[:-14] + '  '
                # checksum for received data
                for i in range(0,len(check_list)-2):
                    one_string = check_list[i]
                    for j in range(0,len(one_string)):
                        checksum += int(ord(one_string[j]))
                if checksum != sent_check:
                    out = 'false  '
                print max_waiting
                break
            if out[0:12] == '$OVERRUN_ERR':
                out = '$OVERRUN_ERR  '
                break
            if len(out) > feedback_threshold:
                feedback_threshold = feedback_threshold + 300000
                print '\t recieving ...' #feedback for long files
                print '\t char so far: ' + str(len(out))
            if (max_waiting == 1000000):
                out = '  '
                break
        out = out[:-2]
    else:
        time.sleep(0.5)
        while ser.inWaiting() > 0:
            out += ser.read(1)
    return out

def get_time(ser):
    response = send_command(ser, '$RD_11_TIME.\r\n', False)
    print 'device time: ' + response
    return response

def get_device_address(ser):
    response = send_command(ser, '$RD_11_DEVADDR.\r\n', False)
    print 'the device address is: ' + response
    return response

def close_port(ser):
    ser.close()
    print '--- serial port closed - bye! --\n'

def set_abort(ser):
    ser.write('$SET_ABORT.' + '\r\n')
    print 'Abort command. \n'

def listen_port():
    old_add = " "
    while True :
        try:
            time.sleep(2)
            if platform == "linux" or platform == "linux2": # Linux
                ports = glob.glob('/dev/ttyUSB*')
            elif platform == "darwin": # OSX
                ports = glob.glob('/dev/tty.usb*')
            if len(ports) == 1:
                port_name = str(ports[0])
                ser = serial.Serial(port=port_name, baudrate=460800,
                      stopbits=serial.STOPBITS_ONE, bytesize=serial.EIGHTBITS)
                ser.isOpen()
                address = send_command(ser, '$RD_11_DEVADDR.\r\n', False)
                if address != old_add:
                    print "\n========================================"
                    print "connected address: " + address
                    print "setting time"

                    print 
                    old_time = send_command(ser, '$RD_11_TIME.'+'\r\n', False)
                    print "old time: " + str(old_time)
                    current_time = str(time.time())[0:10]
                    time_out = send_command(ser, '$SET_TIME.' + current_time + '\r\n', False)
                    print "time updated to: " + time_out

                    old_add = address
                    tp_num = get_assiciation_info(address)
                    if tp_num == '':
                        add_new_tp(address)
                        print 'Added a new touchpoint into the key table.'
                        print "========================================"
                        continue
                    #do next with tp_num
                    str_num = raw_input("Please enter the TP number from the back side:\n");
                    if tp_num != str_num:
                        update_info(tp_num, str_num)
                        print '! NEW ASSOCIATION ! This TP number did not match the previous hardware association. The association has been updated with the new TP number .' + tp_num
                    else:
                        print 'The TP number matches the previous hardware association. No updates necessary'
                    print "========================================"
                ser.close()
        except Exception, e:
            if isinstance(e, IOError):
                pass
            else:
                print e

if __name__ == "__main__":

    key_check()
    print "--------------------------------"
    print "*********** FINISHED ***********"
    print "--------------------------------"
    print '\n'
