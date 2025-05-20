import csv
import re

APCSA_CSV = 'APCSA.csv'
JAVAPROG_CSV = 'JavaProg.csv'

"""
H: Present
T: Tardy
A: Absent Excused
U: Absent Unexcused
?: Absent Unknown
"""

def isAbsent(key):
    return key == 'A' or key == 'U' or key == '?'

class attendance:
    def __len__(self):
        return self.size
    def __init__(self):
        self.attendance = {
            'H': 0,
            'T': 0,
            'A': 0,
            'U': 0,
            '?': 0,
        }
        self.size = 0
    def add(self, key):
        if key == '':
            key = 'H'
        if key in self.attendance:
            self.attendance[key] += 1
            self.size += 1
        else:
            raise ValueError(f"Invalid attendance code {key}.")
    def getTotalAbsent(self):
        total = 0
        for key, value in self.attendance.items():
            if isAbsent(key):
                total += value
        return total
    def getTardy(self):
        return self.attendance['T']
        
    def combine(self, other):
        self.size += len(other)
        for key, value in other.attendance.items():
            if key in self.attendance:
                self.attendance[key] += value
            else:
                raise ValueError(f"Invalid attendance code {key}.")
    def getAttendance(self) -> dict[str, int]:
        return self.attendance

class period:
    def __len__(self):
        return self.size
    def __init__(self, name, dates):
        self.name = name
        self.dates = dates
        self.dateToIndex = {date: i for i, date in enumerate(dates) }
        self.students = {}
        self.size = 0
    def addStudent(self, studentID,attendance):
        self.size += 1
        self.students[studentID] = attendance
    def getAttendanceOnData(self, date)-> attendance:
        if not date in self.dateToIndex:
            raise ValueError(f"Date {date} not found in attendance records.")
        id = self.dateToIndex[date]
        data = attendance()
        for _, value in self.students.items():
            key =  value[id]
            data.add(key)
        return data
            
    def getAllAttendance(self)-> attendance:
        data = attendance()
        for studentID, value in self.students.items():
            for key in value:
                data.add(key)
        return data
    def getStudents(self)-> dict[str, list[str]]:
        return self.students
    
class subject(period):
    def __init__(self, name):
        super().__init__(name, [])
        self.periods = []
    def addDates(self, dates):
        self.dates = dates
        self.dateToIndex = {date: i for i, date in enumerate(dates) }
    def addPeriod(self, period):
        self.periods.append(period)
    def getPeriods(self)-> list[period]:
        return self.periods
    
def parse(path):
    with open(path, mode ='r')as file:
        csvFile = csv.reader(file)
        classes = subject(path[:-4])
        dates = []
        for i,v in enumerate(csvFile):
            if i == 0:
                dates = v[2:]
                classes.addDates(dates)
            elif re.match(r'\d\)',v[0]):
                classData = period(v[0], dates)
                classes.addPeriod(classData)
            elif re.match(r'\d+',v[0]):
                data = v[2:]
                classData.addStudent(v[0], data)
                classes.addStudent(v[0], data)
        return classes

data = parse(APCSA_CSV)
class_ = data.getPeriods()[0]
print(data.getAllAttendance().getAttendance())