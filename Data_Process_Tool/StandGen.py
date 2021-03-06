import csv
import glob
import urllib
import os
from unidecode import unidecode
from datetime import datetime
import calendar
import sys

prepprocessfile_f = './data_split_by_day/'
bracelet_reg_f = '../INPUTS/BRACELET_KEYS/'

reference_file = '../INPUTS/event_tp_users.csv'
tp_key = '../TP_number_key/touchpoint_key.csv'

class Touchpoint:
    def __init__(self, TPaddress, contact_name, stand_title, email, url):
        self.TPaddress = TPaddress
        self.contact_name = contact_name
        self.stand_title = stand_title
        self.email = email
        self.url = url

def generate_tp_list_dict():
    # create a list and dictionary for the touchpoints
    tp_list = []
    tp_dict = {}
    with open(reference_file, 'rb') as tp_reference_csv:
        tp_ref_csv_reader = csv.reader(tp_reference_csv, delimiter=',')
        next(tp_ref_csv_reader)
        for row in tp_ref_csv_reader:
            tp_list.append(row[0]) # append the tp number
            with open(tp_key, 'rb') as keyfile:
                keyreader = csv.reader(keyfile, delimiter = ',')
                for keyrow in keyreader:
                    if keyrow[0] == row[0]:
                        add = keyrow[1].lower()
                        break
            tp_dict[row[0]] = Touchpoint(add,row[2],row[3],row[4],row[5])
    return tp_list, tp_dict

def generate_tp_files(tp_list, tp_dict, prepprocessfile, bracelet_reg):
    for tp in tp_list: 
        tpp = tp_dict[tp]
        file_name = (tpp.stand_title + '.csv').replace(':','').replace('/','').decode('utf-8')
        file_name = unidecode(file_name)
        #print './output/stands/'+file_name
 
        if not os.path.exists('../OUTPUT/stands/'+file_name):
            with open('../OUTPUT/stands/'+file_name, 'wb+') as standoutput:
                standoutputwriter = csv.writer(standoutput, delimiter=',')
                standoutputwriter.writerow(['Scanning time','Attendee First Name','Attendee Last Name','Attendee Organization','Attendee Role','Attendee Email','Attendee Phone'])
        row_list = []
        with open('../OUTPUT/stands/'+file_name, 'ab+') as standoutput:
            standoutputwriter = csv.writer(standoutput, delimiter=',')
            with open(prepprocessfile, 'rb') as preprocesscsv:
                prepprocessreader = csv.reader(preprocesscsv, delimiter=',')
                for preprocessrow in prepprocessreader:
                    if preprocessrow[0].replace('\'','') == tpp.TPaddress.lower():
                        bracelet = preprocessrow[2].lower()
                        scan_date = preprocessrow[1]
                        with open(bracelet_reg, 'rb') as bracelet_reg_csv:
                            bracelet_reg_reader = csv.reader(bracelet_reg_csv, delimiter=',')
                            for bracelet_row in bracelet_reg_reader:
                                # print bracelet_row[0]
                                # print bracelet
                                if bracelet_row[0].lower() == bracelet.replace('\'',''):
                                    # print 'hit'
                                    append_list = []
                                    reg_data = [datetime.fromtimestamp(int(scan_date)), bracelet_row[2], bracelet_row[4], bracelet_row[5], bracelet_row[6], bracelet_row[1], bracelet_row[7]]
                                    for ii in reg_data:
                                        append_list.append(ii)
                                    if append_list not in row_list:
                                        row_list.append(append_list)
                                        standoutputwriter.writerow(append_list)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print 'input should be like :\npython StandGen.py 2017-05-21 2017-05-22\n'
        sys.exit(0)
    else: 
        start_input = sys.argv[1]
        end_input = sys.argv[2]

start_unix = int(calendar.timegm(datetime.strptime(start_input+'T06:00','%Y-%m-%dT%H:%M').utctimetuple()))
end_unix = int(calendar.timegm(datetime.strptime(end_input+'T06:00','%Y-%m-%dT%H:%M').utctimetuple()))
days = (end_unix - start_unix) / 86400 + 1
dates = []
for i in range(0, days):
    date = datetime.fromtimestamp(int(start_unix))
    start_unix += 86400
    y =  str(date.year)
    m = str(date.month)
    if int(m) < 10:
        m = '0' + m
    d = str(date.day)
    if int(d) < 10:
        d = '0' + d
    dates.append(y+'-'+m+'-'+d)

# clean the output folder
for the_file in os.listdir('../OUTPUT/stands'):
    file_path = os.path.join('../OUTPUT/stands', the_file)
    try:
        if os.path.isfile(file_path):
            os.unlink(file_path)
    except Exception as e:
        print e

# run
tp_list, tp_dict = generate_tp_list_dict()
for day in dates:
    prepprocessfile = prepprocessfile_f+day+'.csv'
    bracelet_reg = bracelet_reg_f+day+'.csv'
    generate_tp_files(tp_list, tp_dict, prepprocessfile, bracelet_reg)

#clear empty
for filename in os.listdir('../OUTPUT/stands'):
    file_path = '../OUTPUT/stands/'+filename
    with open(file_path, 'rb') as tempfile:
        tempreader = csv.reader(tempfile, delimiter=',')
        templist = list(tempreader)
        if(len(templist) == 1):
            print 'File ' + file_path + ' removed.'
            os.unlink(file_path)
            continue
                