from collections import namedtuple
import datetime

import numpy


numpy.seterr(invalid='ignore')

class Tick(namedtuple('Tick',
                      ['series', 'index', 'date', 'open', 'high', 'low',
                       'close', 'volume', 'adj'])):
    """ Tick i.e. stock price etc. on a given day

    Contains a reference to the time series it belongs to (Stock.data) and its
    index in the list in order to compute metrics.

    >>> Tick([], 0, datetime.date(2012, 5, 25), 1.0, 1.0, 1.0,
    ...              1.0, 1, 1.0)
    Tick(series=[...], index=0, date=2012-05-25 open=1.0, high=1.0, low=1.0, close=1.0, volume=1, adj=1.0)
    """

    __slots__ = ()

    def __repr__(self):
        return 'Tick(series=[...], index={0.index}, date={0.date} \
open={0.open}, high={0.high}, low={0.low}, close={0.close}, \
volume={0.volume}, adj={0.adj})'.format(self)

    def std(self, n):
        index = self.index + 1
        return numpy.std([tick.close for tick in self.series[index-n:index]])

    def ma(self, n):
        index = self.index + 1
        return numpy.mean([tick.close for tick in self.series[index-n:index]])

    def upper_bb(self, n, k):
        return self.ma(n) + k * self.std(n)

    def lower_bb(self, n, k):
        return self.ma(n) - k * self.std(n)

    def streak_indicator(self, streak_length, horizon, direction, memory = 0):
        up = 0
        down = 0

        if memory == 0:
            first = 0
        else:
            if self.index - memory < 0:
                first = 0
            else:
                first = self.index - memory

        last = self.index

        if last - first < streak_length:
            return None, None, None

        ticks = [self.series[n] for n in range(first, last)][0::horizon]

        streak = 0 
        for yesterday, today, tomorrow in zip(ticks, ticks[1:], ticks[2:]):
            if direction == 'up':
                if yesterday.close < today.close:
                    streak += 1
                else:
                    streak = 0

            if direction == 'down':
                if yesterday.close > today.close:
                    streak += 1
                else:
                    streak = 0

            if streak == streak_length:
                if tomorrow.close > today.close:
                    up += 1
                else:
                    down += 1

        confidence = float(up + down)/float(last - first)

        return up, down, confidence

    def data_indicator(self, dataset, target, margin, offset = 1):
        def closest_date(current, target):
            target = datetime.datetime.strptime(target, '%Y-%d-%m').date()
            today = current.date
            yesterday = current.series[current.index - 1].date

            if today == target: 
                return True

            if yesterday < target and today > target: 
                return True

            return False

        dataset[0]['price_change'] = None

        up = 0
        down = 0
        avg_change = 0

        for n in range(0, len(dataset) - 1):
            date1 = dataset[n]['date'] 
            date2 = dataset[n + 1]['date']
            
            tick1 = [tick for tick in self.series if closest_date(tick, date1)]
            tick2 = [tick for tick in self.series if closest_date(tick, date2)]

            if len(tick1) > 0 and len(tick2) > 0:
                dataset[n + 1]['price_change'] = float(tick2[0].close - tick1[0].close)/float(tick2[0].close)
            else:
                dataset[n + 1]['price_change'] = None 

        for n in range(1, len(dataset) - 1):
            if target - margin < dataset[n]['x'] < target + margin:
                if dataset[n + offset]['price_change'] > 0:
                    up += 1
                if dataset[n + offset]['price_change'] < 0:
                    down += 1

                if dataset[n + offset]['price_change'] is not None:
                    avg_change += dataset[n + 1]['price_change']

        pause = raw_input()

        confidence = float(up + down)/float(len([data for data in dataset if data['price_change'] is not None]))

        return up, down, avg_change, confidence