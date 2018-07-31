import time
import sys
import csv
import os
import glob
import serial
import warnings
from sys import platform

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
    """ initiate the serial port for communicating with the hardware """
    ser = serial.Serial(
    port=port_name,
    baudrate=460800,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS)
    ser.isOpen()
    print 'serial open'
    return ser

def send_command(ser, command, terminator_bool):
    """ send any of the protocol commands to the connected device """
    attempts = 0
    while True:
        attempts += 1
        ser.write(command)
        response = collect_output(ser, terminator_bool)
        if (response[0:12] != '$OVERRUN_ERR') and (len(response) != 0):
            return response
        elif attempts > 10:
            raise RuntimeError("Touchpoint is not responding to a command:" + command)
        else:
            time.sleep(1)

def collect_output(ser, terminator_bool, wait_time=0.1):
    """ uses the provided serial object (ser) and listens for any content coming
    from the touchpoint. terminator_bool, is a boolean indicating whether we are
    expecting the serial message to have an end character ('$END_OF_FILE')   """
    # to do: upgrade errors to catch/except/raise and propogate to rest of script
    # wait_time is deprecated, but left commented out in case of old firmware device.
    # in case of old hardware, uncomment the time.sleep() line
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
                # print 'bytes waiting: ' + str(bytes_waiting) # for debug only
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
                    warnings.warn("Warning... Checksum is not correct!")
                    out = 'false  ' # 'false' line is caught in post processing
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
        #ser.read(2) # clearing the remaining '\n'
        #print out # debug only
        out = out[:-2] # HARDCODED to make up for bug on firmware side..
    else:
        time.sleep(0.5)
        while ser.inWaiting() > 0:
            out += ser.read(1)
    return out

def touchpoint_string_to_csv(response_string, device_address, output_dir='../COLLECTED_DATA/'):
    """ writing touchpoint output to a csv """
    if output_dir == '/media/shake-on/':
        dir_list = os.listdir(output_dir)
        output_dir = os.path.join(output_dir, dir_list[0])
        output_dir = str(output_dir) + '/'
    target_file = output_dir + device_address.replace(':', '') + '.csv' # ':' not valid in a filename
    target_file = target_file.replace('\n', '').replace('\r', '') # replace any new line characters
    sys_flag = False
    if output_dir == '../SYS_LOG/':
        sys_flag = True

    if not os.path.exists(target_file): # check if csv already exists, else create it
        with open(target_file, "ab") as csv_out_file:
            writer = csv.writer(csv_out_file, delimiter=',')
            writer.writerow(['timestamp', 'bracelet address', 'name', 'bracelet time', 'general record'])

    with open(target_file, "ab") as csv_out_file: # append to file
        writer = csv.writer(csv_out_file, delimiter=',')
        response_array = response_string.split("\r\n")
        for item in response_array:
            itemcommasplit = item.split(',')
            if sys_flag == True:
                writer.writerow(itemcommasplit)
                continue
            if (len(itemcommasplit) >= 2) and (len(itemcommasplit) <= 10):
                writer.writerow(itemcommasplit)
            elif len(itemcommasplit) < 2 and (''.join(itemcommasplit) != 'None' and ''.join(itemcommasplit) != ''):
                if ''.join(itemcommasplit)[:12] != '$END_OF_FILE' and ''.join(itemcommasplit)[:16] != '$NUMBER_OF_LINES' and item.isdigit() != True:
                    print '\n >> WARNING <<'
                    print 'fewer columns than expected in device' + device_address.replace('\r','').replace('\n','') + ', row: ' + str(response_array.index(item))
            elif len(itemcommasplit) > 10 and (''.join(itemcommasplit) != 'None' and ''.join(itemcommasplit) != ''):
                print '\n >> WARNING <<'
                print 'more columns than expected in device ' + device_address.replace('\r','').replace('\n','') + ', row: ' + str(response_array.index(item))
                print '\t' + ''.join(itemcommasplit)

def get_time(ser):
    """ get the device time """
    response = send_command(ser, '$RD_11_TIME.\r\n', False)
    print 'device time: ' + response
    return response

def get_sd_list(ser):
    """ get the list of all files stored on device """
    response = send_command(ser, '$RD_11_SD_LIST.\r\n', False)
    print '------- SD FILE LIST -------\n'
    print response + '\n'
    return response

def get_sd_file(ser,file_index,print_bool=False):
    """ request a specific file from the list index 
    print_bool determines if the response is printed """
    while True:
        response = send_command(ser, '$RD_11_SD_FILE.' + str(file_index) + '\r\n', True)
        if response != 'false':
            break
        else:
            print 'Try again for file [ '+str(file_index)+' ] .'
            time.sleep(1)
    if print_bool == True:
        print response
    return response

def get_device_address(ser):
    """ request the connected device's DeviceAddress """
    response = send_command(ser, '$RD_11_DEVADDR.\r\n', False)
    print 'the device address is: ' + response
    return response

def get_battery_level(ser):
    """ get the device's battery level """
    response = send_command(ser, '$RD_11_BAT.\r\n', False)
    print 'battery information: \n' + response
    return response

def close_port(ser):
    ser.close()
    print '--- serial port closed - bye! --\n'

def delete_sd_file(ser,file_index):
    response = send_command(ser, '$SET_SD_DELETE.' + str(file_index) + '\r\n', False)
    print '--- SD File '+ str(file_index) +' deleted! ---\n'

def clear_all_sd_files(ser):
    response = send_command(ser, '$SET_SD_DELETE_ALL.\r\n', False)
    print '--- All SD Files Cleared! ---\n'

def set_abort(ser):
    ser.write('$SET_ABORT.' + '\r\n')
    print 'Abort command. \n'

def get_all_sd_data_files(ser,device_address):
    t0 = time.clock()
    print '------- copying all files -------'
    print '----- omnomnomonomonomnomno -----\n'
    sd_list_response = send_command(ser, '$RD_11_SD_LIST.\r\n', False)
    nlines = sd_list_response.count('\n')
    split_list = sd_list_response.split("\n")
    if nlines > 2:
        total_response = ''
        sys_response = ''
        for i in range(1, int(nlines)-1): # we go through all the listed files, but ignore logs and system info
            split_list_line = split_list[i]
            split_list_line_letter = split_list_line.split('\t')[1][0:6]
            if split_list_line_letter == 'SYS_LO':
                print 'copying data from: ' + split_list_line
                sys_response = get_sd_file(ser, i-1)
                resplines = sys_response.count('\n')-1
                print 'copied data from:  ' + split_list_line + " - " + str(resplines) + " rows"
                continue
            if split_list_line_letter != 'N11-10':
                print 'skipped file: ' + split_list_line
                # this is an old corrupted file from bad firmware
                continue
            else:
                print 'copying data from: ' + split_list_line
                response = get_sd_file(ser, i-1)
                total_response = total_response + response
                resplines = response.count('\n')-1
                print 'copied data from:  ' + split_list_line + " - " + str(resplines) + " rows"
        touchpoint_string_to_csv(total_response, device_address) # saves to COLLECTED dir
        touchpoint_string_to_csv(sys_response, 'SYS_LOG-'+device_address, '../SYS_LOG/') # saves to SYS_LOG
    else:
        print 'no data files identified'
    print time.clock() - t0, "seconds process time"

    #print response
    print '\n------- files extracted --------'

def listen_port():
    """ listens continuously to your ports, looking for a compative serial device """
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
                    print "\n"+address+"\n"
                    print "================================"
                    print "******* Start transfer. ********"
                    print "================================\n"
                    old_add = address
                    get_all_sd_data_files(ser,address)
                    print "================================"
                    print "******** Transfer done. ********"
                    print "================================\n"
                ser.close()
        except Exception, e:
            if isinstance(e, IOError):
                pass
            else:
                print e
