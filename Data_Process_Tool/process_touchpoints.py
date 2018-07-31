import glob
import time
import shutil
import os
import csv
from datetime import datetime
import sys
import calendar

preproccessed_data_dir = './data_split_by_day'
result_csv = '../OUTPUT/result.csv'

def check_output_dirs():
    if not os.path.exists(preproccessed_data_dir):
        print "creating preprocessed data dir"
        os.makedirs(preproccessed_data_dir)
    for the_file in os.listdir('../OUTPUT'):
        file_path = os.path.join('../OUTPUT', the_file)
        try:
            if os.path.isfile(file_path):
                os.unlink(file_path)
        except Exception as e:
            print e
    with open(result_csv, 'wb') as resfile:
        reswriter = csv.writer(resfile, delimiter=',')
        reswriter.writerow(['email','first name','last name'])

def preprocess_csvs():
    # go through all CSVs in the raw data directory and split by days
 
    for filename in os.listdir(raw_data_dir):
	file_path = raw_data_dir+'/'+filename
        tp_add = filename[0:2]+':'+filename[2:4]+':'+filename[4:6]+':'+filename[6:8]+':'+filename[8:10]+':'+filename[10:12]
        with open(file_path, 'rb') as tempfile:
       	    tempreader = csv.reader(tempfile, delimiter=',')
            next(tempreader) # skip header
            for row in tempreader:
                # index 0 is the timestemp in new frameware
                unixtime = int(row[0].replace('\'',''))
                date = datetime.fromtimestamp(unixtime)
                if len(str(date.month)) == 1:
                    month = '0'+str(date.month)
                else:
                    month = str(date.month)
                if len(str(date.day)) == 1:
                   day = '0'+str(date.day)
                else:
                    day = str(date.day)
                if month == correct_mon and day in correct_days:
                    date_str = preproccessed_data_dir+'/'+str(date.year)+'-'+month+'-'+day+'.csv'
                    #row add device address for first elements
                    row.insert(0,tp_add)
                    with open(date_str, 'ab+') as tempfile:
                        tempwriter = csv.writer(tempfile, delimiter=',')
                        tempwriter.writerow(row)
                else:
                    print 'Wrong time.'

def output_maker(registration_file, preprocessed_file):
    # output a result.csv file which has the scanned touchpoint stands for every attendee
    with open(registration_file, 'rb') as regfile:
        regreader = csv.reader(regfile, delimiter=',')

        with open(result_csv, 'ab+') as resfile:
            reswriter = csv.writer(resfile, delimiter=',')

            for regrow in regreader:
                bracelet = regrow[0]
                prephits = [regrow[1], regrow[2], regrow[4]] # for hits in the preprocessed files, we start with the bracelet itself for the first row
                with open(preprocessed_file, 'rb') as prepfile:
                    prepreader = csv.reader(prepfile, delimiter=',')

                    for preprow in prepreader:
                        if bracelet.lower() == preprow[2].replace('\'', '').lower():
                            with open('../TP_number_key/touchpoint_key.csv', 'rb') as keyfile:
                                keyreader = csv.reader(keyfile, delimiter = ',')
                                for keyrow in keyreader:
                                    if keyrow[1].lower().replace('\'', '') == preprow[0].replace('\'', ''):
                                        prephits.append(keyrow[0])
                                        break
                    if len(prephits) > 3:
                        reswriter.writerow(prephits)

def output_conversion():
    with open('../OUTPUT/stands_per_attendees.csv','w+') as finalcsv:
        finalwriter = csv.writer(finalcsv, delimiter=',')
        finalwriter.writerow(['email','first name','last name'])
        with open(result_csv, 'rb') as rescsv:
            resreader = csv.reader(rescsv, delimiter=',')
            next(resreader)
            for resrow in resreader:
                #print resrow
                #print '\n'
                conversions = resrow[0:3]
                for i in resrow[3:]:
                    # match TP device address with TP stand + email
                    with open('../INPUTS/event_tp_users.csv', 'rb') as tpregistration:
                        tpregreader = csv.reader(tpregistration, delimiter=',')
                        for ii in tpregreader:
                            if i == ii[0]:
                                append_list1 = ii[3]
                                append_list2 = ii[5]
                                conversions.append(append_list1)
                                conversions.append(append_list2)
                finalwriter.writerow(conversions)
    os.unlink(result_csv)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print 'please invoke this script with arguments, i.e. :\npython process_touchpoints.py 2017-05-21 2017-05-22\n'
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

check_output_dirs()
for day in dates:
    output_maker('../INPUTS/BRACELET_KEYS/'+day+'.csv', preproccessed_data_dir+'/'+day+'.csv')
output_conversion()
