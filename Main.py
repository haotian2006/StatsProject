import csv
import re
from scipy.stats import norm
import tabulate



APCSA_CSV = 'APCSA.csv'
JAVAPROG_CSV = 'JAVAPROG.csv'
TestDates = 'TestDates.txt'

"""
H: Present
T: Tardy
A: Absent Excused
U: Absent Unexcused
?: Absent Unknown
"""
EXCUSED_ONLY = False # Should only excused absences be included in the calculation of the probability of absence?
INCLUDE_EXCUSED_ABSENT = True # Should excused absences be included in the calculation of the probability of absence? 
INCLUDE_QUIZZES= True # Should quizzes be included in the calculation of the probability of absence? (Only JAVA)
QUIZ_ONLY = False # Should only quizzes be included in the calculation of the probability of absence? (Only JAVA)

Tests = {} 
with open(TestDates, mode ='r')as file:
    test = {}
    for line in file:
        line = line.strip()
        if line.startswith('#'):
            continue
        if line[:4] == '----':
            test = {}
            Tests[line[4:]] = test
        elif line.find('|') != -1:
            date = line.split('|')
            test[date[1].strip()] = date[0].strip()
 

def isAbsent(key):
    if EXCUSED_ONLY:
        return key == 'A'
    return  (INCLUDE_EXCUSED_ABSENT and key == 'A') or key == 'U' or key == '?' 

def calculatePooled(x1,n1,x2,n2):
    return (x1 + x2) / (n1 + n2)


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
    def getProbOfAbs(self):
        total = self.getTotalAbsent()
        return total / self.size 
    def getData(self) -> dict[str, int]:
        return self.attendance

class period:
    def __len__(self):
        return self.size
    def __init__(self, name, dates,testDates):
        self.testDates = testDates
        self.name = name
        self.dates = dates
        self.dateToIndex = {date: i for i, date in enumerate(dates) }
        self.students = {}
        self.size = 0
    def addStudent(self, studentID,attendance):
        self.size += 1
        self.students[studentID] = attendance
    def getAttendanceOnDates(self, dates:list[str])-> attendance:
        data = attendance()
        for date in dates:
            if not date in self.dateToIndex:
                raise ValueError(f"Date {date} not found in attendance records.")
            id = self.dateToIndex[date]
            for _, value in self.students.items():
                key =  value[id]
                data.add(key)
        return data
            
    def getTestDates(self,includeQuiz = False,includeOptional = False)-> list[str]:
        testDates = []
        for key, value in self.testDates.items():
            if includeQuiz or not value.startswith('Quiz'):
                if includeOptional or not value.find('Optional') != -1:
                    testDates.append(key)
        return testDates
    def getQuizDates(self)-> list[str]:
        quizDates = []
        for key, value in self.testDates.items():
            if value.startswith('Quiz'):
                quizDates.append(key)
        return quizDates
    def getAttendance(self,exclude = [])-> attendance:
        data = attendance()
        for i,date in enumerate(self.dates):
            if date in exclude:
                continue
            for _, val in self.students.items():
                key =  val[i]
                data.add(key)
        return data
    def getStudents(self)-> dict[str, list[str]]:
        return self.students
    def calculate2ZTest(self,getFullStats = False)-> float:
        testDates = self.getTestDates(INCLUDE_QUIZZES) if not QUIZ_ONLY else self.getQuizDates()
        normalDays = self.getAttendance(testDates)
        testDays = self.getAttendanceOnDates(testDates)
        p1 = testDays.getProbOfAbs()
        p2 = normalDays.getProbOfAbs()
        n1 = testDays.size
        n2 = normalDays.size
        nAbsent_test = testDays.getTotalAbsent()
        nAbsent_normal = normalDays.getTotalAbsent()
        p_pooled = calculatePooled(p1*n1,n1,p2*n2,n2)
        q_pooled = 1 - p_pooled
        SE_pooled = ((q_pooled*p_pooled)/n1 + (p_pooled*q_pooled)/n2)**0.5
        z = (p1 - p2) / SE_pooled
        p = 1-norm.cdf(z)
        return {
            'p_value': p,
            'z': z,
            'p_test': p1,
            'p_normal': p2,
            'n_test': n1,
            'n_normal': n2,
            'nAbsent_test': nAbsent_test,
            'nAbsent_normal': nAbsent_normal,
            'p_pooled': p_pooled,
            'q_pooled': q_pooled,
            'SE_pooled': SE_pooled,
            'normal_attendance': normalDays,
            'test_attendance': testDays,
            'dates': testDates,
        } if getFullStats else p
    def getAbsentOnTests(self):
        dates = self.getTestDates(INCLUDE_QUIZZES) if not QUIZ_ONLY else self.getQuizDates()
        numAbsentOnTest = {}
        for date in dates:
            attendanceOnDate = self.getAttendanceOnDates([date])
            totalAbsent = attendanceOnDate.getTotalAbsent()
            numAbsentOnTest[date] = [self.testDates[date],totalAbsent/attendanceOnDate.size,totalAbsent,attendanceOnDate.size]
        return numAbsentOnTest
    def printChartStats(self):
        col = ''
        row = ''
        for date in self.dates:
            attendanceOnDate = self.getAttendanceOnDates([date])
            name = date in self.testDates and f'{date}({self.testDates[date]})' or date
            col += name + '\n'
            row += f'{attendanceOnDate.getTotalAbsent()}\n'
        with open('chartCOL.txt', 'w') as f:
            f.write(col)
        with open('chartROW.txt', 'w') as f:
            f.write(row)
               
class subject(period):
    def __init__(self, name,testDates):
        super().__init__(name, [],testDates)
        self.periods = []
    def addDates(self, dates):
        self.dates = dates
        self.dateToIndex = {date: i for i, date in enumerate(dates) }
    def addPeriod(self, period):
        self.periods.append(period)
    def getPeriods(self)-> list[period]:
        return self.periods
    def printStats(self):
        dates = self.getTestDates(INCLUDE_QUIZZES) if not QUIZ_ONLY else self.getQuizDates()
        strBuilder = []
        strBuilder.append(f"Attendance for {self.name}")
        strBuilder.append(f"Total Students: {self.size}")
        zData = self.calculate2ZTest(getFullStats = True)
        strBuilder.append(f"P-Value: {zData['p_value']}")
        strBuilder.append(f"Z-Score: {zData['z']}")
        strBuilder.append(f"p_Test: {zData['p_test']}")
        strBuilder.append(f"p_Normal: {zData['p_normal']}")
        strBuilder.append(f"Test Ratio: {zData['nAbsent_test']}:{zData['n_test']}")
        strBuilder.append(f"Normal Ratio: {zData['nAbsent_normal']}:{zData['n_normal']}") 
        strBuilder.append(f"Total Students: {self.size}")

        strBuilder.append("----PERIOD STATS-----")
        periodData = []
        for period in self.periods:
            zPeriodData = period.calculate2ZTest(getFullStats = True)
            periodData.append([
                period.name,
                zPeriodData['p_value'],
                zPeriodData['z'],
                zPeriodData['p_test'],
                zPeriodData['p_normal'],
                f'{zPeriodData["nAbsent_test"]}:{zPeriodData["n_test"]}',
                f'{zPeriodData["nAbsent_normal"]}:{zPeriodData["n_normal"]}',
                period.size,
            ])
        strBuilder.append(tabulate.tabulate(periodData, headers=['Period', 'P-Value', 'Z-Score', 'p_Test', 'p_Normal', 'Test Ratio', 'Normal Ratio', 'Total Students']))
        strBuilder.append("----TEST ATTENDANCE STATS-----")
        testData = []
        for date in dates:
            attendanceOnDate = self.getAttendanceOnDates([date])
            totalAbsent = attendanceOnDate.getTotalAbsent()
            dateData = [self.testDates[date],date, totalAbsent]
            for period in self.periods: 
                periodAttendanceOnDate = period.getAttendanceOnDates([date])
                totalAbsentOnPeriod = periodAttendanceOnDate.getTotalAbsent()
                dateData.append(totalAbsentOnPeriod)
            testData.append(dateData)
        headers = ['Date', 'Date','Total Absent'] 
        for period in self.periods:
            headers.append(f"P{period.name} Total Absent")
        strBuilder.append(tabulate.tabulate(testData, headers=headers))

        strBuilder.append("----Days With Absent Students-----")
        absentData = []
        for date in self.dates:
            attendanceOnDate = self.getAttendanceOnDates([date])
            totalAbsent = attendanceOnDate.getTotalAbsent()
            if totalAbsent == 0:
                continue
            name = date in self.testDates and f'{date}({self.testDates[date]})' or date
            absentData.append([name, totalAbsent])
        strBuilder.append(tabulate.tabulate(absentData, headers=['Date', 'Total Absent']))
        strBuilder.append("--------------------------------------------------------------------------------------\n\n")
        built = '\n'.join(strBuilder)
        print(built)

 
def parse(path):
    with open(path, mode ='r')as file:
        csvFile = csv.reader(file)
        name = path[:-4]
        classes = subject(name, Tests[name])
        dates = []
        for i,v in enumerate(csvFile):
            if i == 0:
                dates = v[2:]
                classes.addDates(dates)
            elif re.match(r'\d\)',v[0]):
                classData = period(v[0][:1], dates,Tests[name])
                classes.addPeriod(classData)
            elif re.match(r'\d+',v[0]):
                data = v[2:]
                classData.addStudent(v[0], data)
                classes.addStudent(v[0], data)
        return classes
print("CONFIGURATION")
print("Included Excused Only:", EXCUSED_ONLY)
print("Included Quizzes:", INCLUDE_QUIZZES)
print("Included Excused Absences:", INCLUDE_EXCUSED_ABSENT)
print("Only Quizzes:", QUIZ_ONLY)
print("--------------------")
JavaData = parse(JAVAPROG_CSV)
APCSAData = parse(APCSA_CSV)
#APCSAData.printStats()
JavaData.printChartStats()

