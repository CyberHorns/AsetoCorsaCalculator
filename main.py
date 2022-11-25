# importing required modules
import re
import PyPDF2  #check the version. newest can not work. !
import os
from datetime import datetime
import logging

logger = logging.getLogger("PyPDF2")
logger.setLevel(logging.ERROR)


class pdf:
    def __init__(self, pdfname):
        self.pdfname = pdfname
        self.extract_pdf_data()

    def extract_pdf_data(self):
        # creating a pdf file object
        pdfFileObj = open(self.pdfname, 'rb')
        # creating a pdf reader object
        pdfReader = PyPDF2.PdfFileReader(pdfFileObj)
        # printing number of pages in pdf file
        #print(pdfReader.numPages)
        # creating a page object
        #pageObj = pdfReader.getPage(0)
        numpages = pdfReader.getNumPages()
        # extracting text from page
        #text = pageObj.extractText()
        #if numpages > 1:
        for i in range(numpages):
            pageObj = pdfReader.getPage(i)
            if i == 0:
                text = pageObj.extractText()
            else:
                text = text + "\n" + pageObj.extractText()
        pdfFileObj.close()
        count = len(text.split("\n"))  # number of lines:
        hour = text.splitlines()[0]
        date = text.splitlines()[1]
        track = text.splitlines()[2]
        try:
            time_difference = text.splitlines()[3]
            general_names = text.splitlines()[4]
            general_data = text.splitlines()[5]
            detail_names = text.splitlines()[6]
            detail_values = []
            for i in range(count):
                if i + 7 == count:
                    break
                detail_values.append(text.splitlines()[i + 7])
        except:
            pass
        try:
            best_time_lst = re.findall('[0-9]:[0-9]{2}.[0-9]{3}', general_data)
            best_time_str = str(best_time_lst[0])
            print("TEST")
            self.best_time = datetime.strptime(best_time_str, '%M:%S.%f')
            self.best_time_ms = int(self.best_time.microsecond)/1000 + int(self.best_time.second)*1000 + int(self.best_time.minute)*60000
            #print(str(self.best_time[0]) + " in " + self.pdfname)
            datetime_str = date + ' ' + hour
            self.datetime_obj = datetime.strptime(datetime_str, '%d %b %Y %H:%M')
            self.driver = str(general_data.split()[0]) + " " + str(general_data.split()[1])
            self.laps = int(general_data.split()[-1])
            self.car = re.sub(' [0-9]:[0-9]{2}.[0-9]{3} [0-9]', ' ', general_data.split(' ', 2)[2])
            self.lap_times = []
            self.lap_times_ms = []
            self.lap_times_not_valid = []
            self.lap_times_ms_not_valid = []
            self.lap_times.append(self.best_time)
            self.lap_times_ms.append(self.best_time_ms)
            for i in range(self.laps):
                # in version 2.0 we should add to formated_data_from_this_pdf every lape time to sort
                str_lap_time = re.findall('[0-9][^ ]*[0-9] ', detail_values[i])[-1]
                datetime_lap_time = datetime.strptime(str_lap_time, '%M:%S.%f ')
                print(str(i))
                if detail_values[i][-1] != '-':
                    self.lap_times.append(datetime_lap_time)
                    self.lap_times_ms.append(int(datetime_lap_time.microsecond)/1000 + int(datetime_lap_time.second)*1000 + int(datetime_lap_time.minute) * 60000)
                else:
                    self.lap_times_not_valid.append(datetime_lap_time)
                    self.lap_times_ms_not_valid.append(int(datetime_lap_time.microsecond) + int(datetime_lap_time.second) * 1000 + int(datetime_lap_time.minute) * 60000)
            self.valid = True
        except Exception as e:
            print(e)
            print("no best time in " + self.pdfname)
            print(" ! this file is skipped")
            self.valid = False


def create_valid_list(list):
    files_not_valid = []
    files_valid = []
    for i in list:
        if i.valid == True:
            print(i.pdfname)
            files_valid.append(i)
        else:
            files_not_valid.append(i)
    return files_valid, files_not_valid

def first_step_write_result_to_file(valid, not_valid):
    with open("step1_results.txt", mode="wt", encoding="utf8") as f:
        position = 0
        f.write("POSITION | TIME ms | TIME | CAR | DRIVER | FILENAME \n")
        for i in valid:
            position = position + 1
            f.write("\n" + str(position) + " | " + str(i.best_time_ms) + " | " + \
                    str(i.best_time.minute) + ":" + str(i.best_time.second) + ":" + str(i.best_time.microsecond) + \
                    " | " + i.car + " | " + i.driver + " | " + i.pdfname)
        f.write("\n\nNot taken to calculation: \n")
        for i in not_valid:
            try:
                f.write(i.pdfname + " ")
            except:
                print("\nERROR with " + i.pdfname)
    print("Result saved")

def second_step_write_result_to_file(list, not_valid):
    with open("step2_results.txt", mode="wt", encoding="utf8") as f:
        position = 0
        f.write("POSITION | NAME | SUM_TIME ms | TIME1 | TIME2 | SUM  \n")
        for i in list:
            position = position + 1
            f.write("\n" + str(position) + " | " + i + " | " + str(list[i][2]) + " | " + \
                    miliseconds_convert(list[i][0]) + " | " + miliseconds_convert(list[i][1]) + " | " + \
                    miliseconds_convert(list[i][2]))
        f.write("\n\nNot taken to calculation: \n")
        for i in not_valid:
            try:
                f.write(i.pdfname + " ")
            except:
                print("\nERROR with " + i.pdfname)
    print("Result saved")

def miliseconds_convert(millis):
    seconds = (millis / 1000) % 60
    seconds = int(seconds)
    if seconds < 10:
        str_seconds = "0" + str(seconds)
    else:
        str_seconds = str(seconds)
    minutes = (millis / (1000 * 60)) % 60
    minutes = int(minutes)
    if minutes < 10:
        str_minutes = "0" + str(minutes)
    else:
        str_minutes = str(minutes)
    miliseconds = millis % 1000
    miliseconds = int(miliseconds)
    return(str_minutes + ":" + str_seconds + "." + str(miliseconds))

def put_to_one_list_all_laps(pdfs):
    all_valid_laps = []
    for i in (range(len(pdfs))):
        for lap in (range(len(pdfs[i].lap_times_ms))):
            all_valid_laps.append({'driver' : pdfs[i].driver, 'time_ms': pdfs[i].lap_times_ms[lap],\
                                   'time_datetime' : pdfs[i].lap_times[lap], \
                                  'car' : pdfs[i].car, 'filename' : pdfs[i].pdfname})
    return all_valid_laps

def make_list_of_two_laps_for_one_driver(list):
    drivers_list = []
    for i in range(len(list)):
        if list[i]['driver'] not in drivers_list:
            drivers_list.append(list[i]['driver'])
    board = {}
    for driver in drivers_list:
        driver_time = []
        driver_time_ms = []
        for i in range(len(list)):
            if driver is list[i]['driver']:
                driver_time.append(list[i]["time_ms"])
        driver_time.sort()
        best_two_laps_and_sum = driver_time[:2]
        best_two_laps_and_sum.append(best_two_laps_and_sum[0]+best_two_laps_and_sum[1])
        board[driver] = best_two_laps_and_sum

    sorted_board = dict(sorted(board.items(), key=lambda item: item[1][2]))
    return sorted_board


def main():
    print('Python results generator for DM Racing 2.0 Alpha\nCreated by CyberHorns \nRelease date: 28/10/2022\n')
    try:
        print("version of PyPDF2 is: " + PyPDF2.__version__)
    except:
        pass

    files = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.pdf')]
    print(files)
    pdfs = []
    for i in range(len(files)):
        pdfs.append(pdf(files[i]))

    choice = -1
    while choice != 0:
        print("Please choose one of the following options")
        print("0. Exit")
        print("1. Create table with best results (one result for one pdf) from all pdf's")
        print("2. Create table with best results (SUM of two best laps) from all pdf's")
        #print("3. Create table with best results (average of two best laps) from all pdf's")
        #print("2. Open GUI #not ready")
        #print("3. Create table with best results (every lap)")

        try:
            choice = int(input())
        except:
            choice = -1

        if choice == 0:
            print("Goodbay...")
        elif choice == 1:
            print("Calculation started")
            files_valid, files_not_valid = create_valid_list(pdfs)
            files_valid.sort(key=lambda x: x.best_time_ms, reverse=False)
            first_step_write_result_to_file(files_valid, files_not_valid)
        elif choice == 2:
            print("Calculation started")
            files_valid, files_not_valid = create_valid_list(pdfs)
            liderboard = make_list_of_two_laps_for_one_driver(put_to_one_list_all_laps(files_valid))
            second_step_write_result_to_file(liderboard, files_not_valid)

        else:
            print("Invalid choice...")


if __name__ == '__main__':
    main()
