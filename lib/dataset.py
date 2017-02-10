from openpyxl import load_workbook
import datetime
from datetime import timedelta
import re


class Dataset(object):

    def __init__(self, filename, date_format = '%Y-%d-%m', active_sheet = 'Sheet1', dates_column = 1, data_columns = [2]):
        self.date_format = date_format

        # Get excel sheet data
        wb = load_workbook(filename=filename, read_only=True)
        ws = wb[active_sheet]
        excel = [[col.value for col in row] for row in ws.rows]

        # Create dictionary array
        labels = ['date'] + [re.sub('[^0-9a-zA-Z]+', '_', excel[0][n - 1]) for n in range(0, len(data_columns))]

        data = []
        for row in excel:
            # Skip the first row
            if row != excel[0] and row [dates_column - 1] != None:
                entry = {}
                entry['date'] = self.format_date(row[dates_column - 1])
                for column in data_columns:
                    entry[re.sub('[^0-9a-zA-Z]+', '_', excel[0][column - 1])] = row[column - 1]

                data.append(entry)

        self.data = data

    def format_date(self, date):
        if isinstance(date, str):
            return datetime.strptime(date, self.format).date()
        if isinstance(date, datetime.datetime):
            return date.date()

    def get_data(self, tick, embargo = 0):
        date = tick.date - timedelta(days = embargo)
        for point1, point2 in zip(self.data, self.data[1:]):
            if datetime.strptime(str(point1['date']).split(' ')[0], self.date_format).date() < date < datetime.strptime(str(point2['date']).split(' ')[0], self.date_format).date():
                return point1

    def percent_change(self, tick, data_name, embargo = 0):
        date = tick.date - timedelta(days = embargo)
        for point1, point2, point3 in zip(self.data, self.data[1:], self.data[2:]):
            if point1['date'] > date > point2['date']:
                return ((point2[data_name] - point3[data_name]) / point3[data_name]) * 100

    def moving_average(self, tick, data_name, embargo = 0):
        date = tick.date - timedelta(days = embargo)
        for point1, point2, point3 in zip(self.data, self.data[1:], self.data[period + 1:]):
            if point1['date'] > date > point2['date']:
                return ((point2[data_name] - point3[data_name]) / point3[data_name]) * 100