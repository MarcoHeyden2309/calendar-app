from datetime import datetime, date, timedelta

# Enter the date you want to find the weekday for
year = 2022
month = 12
day = 20
SelectedDate = datetime.today()
# Create a datetime object from the date

date2 = SelectedDate

# Use the `strftime` method to print the weekday
# print(date2.strftime('%A'))


def getWeekdays(firstDay):
    weekdays = []
    for i in range(7):
        currentDay = firstDay + timedelta(days=(i))
        print(currentDay.strftime('%A'))
        weekdays.append([currentDay.strftime('%A'), currentDay])
    return weekdays


# print(getWeekdays(SelectedDate)[1][1].month)


def get_times(debut, intervalle):

    result = []
    addition = 1440/intervalle
    print(int(addition))
    i = 0
    for i in range(int(addition)):
        result.append(debut + timedelta(minutes=(i+1)*intervalle))

    return result


#print(get_times(SelectedDate, 30))

print(SelectedDate.date())
print(SelectedDate.time())
