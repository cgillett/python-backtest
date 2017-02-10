from collections import namedtuple, Counter

from matplotlib.pyplot import plot, subplot2grid, ylim, yticks, savefig, clf, \
	fill_between

from lib import Stock, Dataset
import numpy
import datetime
import math

Trade = namedtuple('Trade', ['order', 'tick'])
Data = namedtuple('Data', ['x', 'tick'])

class BackTest(object):
	""" Callable object running back tests for a strategy over a stock

	>>> backtest = BackTest()

	If goog is a Stock and bollinger a strategy (cf. strategy/__init__.py)

	>>> backtest(goog, bollinger) #doctest: +SKIP
	BackTest(trades=[99], position=short, gross=1253.63, net=662.1)

	Current position is short, gross PNL is 1253.63, net PNL taking into account
	the closing of the position and the trading costs if applicable is 662.1.

	Trading costs are 0 by default. To change that set the cost attribute of
	the backtest object to a function taking a trade as an argument and returning
	the cost.

	>>> backtest.cost = lambda trade: 0.5 * trade / 100
	>>> backtest #doctest: +SKIP
	BackTest(trades=[99], position=short, gross=1253.63, net=435.78005)
	"""

	def __init__(self):
		self.cost = lambda trade: 0
		self.stock = None
		self.strategy = None
		self.trades = []
		self.historical = []

	def __call__(self, stock, strategy):
		self.stock = stock
		self.strategy = strategy
		self.trades = []
		self.historical = []
		for t in stock:
			order = strategy(t)
			
			if order == 'buy' and self.position != 'long':
				self.trades.append(Trade('buy', t))
			elif order == 'sell' and self.position != 'short':
				self.trades.append(Trade('sell', t))

			elif order == 'close':
				if self.position == 'long':
					self.trades.append(Trade('sell', t))
				if self.position == 'short':
					self.trades.append(Trade('buy', t))

			# Calculate portfolio value for the day
			self.historical.append(Data(self._net(t.index), t))
		return self

	def __repr__(self):
		return 'BackTest(trades=[{1}], returns={0.returns}, gross={0.gross}, \
net={0.net})'.format(self, len(self.trades))

	@property
	def position(self):
		""" position at the end of the backtest period """
		return self._position(len(self.stock) - 1)

	def _position(self, tick_index, numeric_flag=False):
		""" position at tick_index 1/0/-1 if numeric_flag """
		position_ = {1: 'long', 0: None, -1: 'short'}
		counter = Counter(trade.order for trade in self.trades
						if trade.tick.index <= tick_index)
		numeric = counter['buy'] - counter['sell']
		if numeric_flag:
			return numeric
		return position_[counter['buy'] - counter['sell']]
		
	@property
	def trade_cost(self):
		""" trade cost for the backtest period """
		return self._trade_cost(len(self.stock) - 1)

	def _trade_cost(self, tick_index):
		""" trade cost from start to tick_index """
		return sum(self.cost(abs(trade.tick.close)) for trade in self.trades
				   if trade.tick.index <= tick_index)

	@property
	def gross(self):
		""" gross pnl for the backtest period """
		return self._gross(len(self.stock) - 1)

	def _gross(self, tick_index):
		""" gross pnl from start to tick_index """
		sign = lambda trade: 1 if trade.order == 'sell' else -1
		return sum(sign(trade) * trade.tick.close for trade in self.trades
				   if trade.tick.index <= tick_index)

	@property
	def net(self):
		""" net pnl for the backtest period """
		return self._net(len(self.stock) - 1)

	def _net(self, tick_index):
		""" net pnl from start to tick_index """
		result = 0
		if self._position(tick_index) == 'long':
			result += self.stock[tick_index].close
		elif self._position(tick_index) == 'short':
			result -= self.stock[tick_index].close
		result += self._gross(tick_index)
		result -= self._trade_cost(tick_index)
		return result

	@property
	def returns(self):
		""" position at the end of the backtest period """
		return self._returns(len(self.stock) - 1)

	def _returns(self, tick_index):
		start = self.stock[0].close
		end = start + self._net(tick_index) # Net is the amount of extra money made so we add it to the starting price

		return round(((end - start) / start) * 100, 2)

	@property
	def volatility(self):
		""" position at the end of the backtest period """
		historical = [100.0 * (today.x - yesterday.x) / yesterday.x for today, yesterday in zip(self.historical[1:], self.historical) if yesterday.x != 0]
		return numpy.std(historical)

	@property
	def average_annual_return(self):
		""" position at the end of the backtest period """
		return self._average_annual_return(len(self.stock) - 1)

	def _average_annual_return(self, tick_index):
		start = self.stock[0].close
		end = start + self._net(tick_index)

		start_date = self.stock[0].date
		end_date = self.stock[tick_index].date
		years = end_date - start_date
		years = years.days / 365

		if years == 0:
			years = 1

		a = float(end) / float(start)
		b = 1.0 / float(years)

		return ((a ** b) - 1) * 100		

	def trade_winrate(self, verbose = False):
		winners = []
		losers = []

		for trade1, trade2 in zip(self.trades, self.trades[1:]):
			net = trade2.tick.close - trade1.tick.close
			if net > 0:
				if self._position(trade1.tick.index) == 'long':
					winners.append(net)
				if self._position(trade1.tick.index) == 'short':
					losers.append(net)
			if net <= 0:
				if self._position(trade1.tick.index) == 'short':
					winners.append(net)
				if self._position(trade1.tick.index) == 'long':
					losers.append(net)

		win_pct = float(len(winners)) / float(len(self.trades))

		if verbose == True:
			print 'Win Rate: ' + str(win_pct)
			print 'Average Trade Return: ' + str((sum(winners) + sum(losers)) / len(self.trades))
		else:
			return win_pct * 100

	def winrate(self, n):
		historical_tmp = self.historical[0::n]
		pct_change_portfolio = [Data(today.x - yesterday.x, today.tick) for today, yesterday in zip(historical_tmp[1:], historical_tmp) if yesterday.x != 0]

		winners = [day for day in pct_change_portfolio if day.x >= 0]
		losers = [day for day in pct_change_portfolio if day.x < 0]

		win_pct = float(len(winners)) / float(len(pct_change_portfolio))
		return win_pct * 100

	@property
	def daily(self): return self.winrate(1)

	@property
	def weekly(self): return self.winrate(7)

	@property
	def monthly(self): return self.winrate(30)

	@property
	def quarterly(self): return self.winrate(65)

	@property
	def yearly(self): return self.winrate(365)

	@property
	def beta(self):
		# Get daily percent change for portfolio value
		pct_change_portfolio = [100.0 * (today.x - yesterday.x) / yesterday.x for today, yesterday in zip(self.historical[1:], self.historical) if yesterday.x != 0]

		# Get daily percent change for S&P 500
		pct_change_spy = [100.0 * (today.close - yesterday.close) / yesterday.close for today, yesterday in zip(Stock('SPY')[1:], Stock('SPY'))]

		# Make sure our arrays are the same length
		if len(pct_change_portfolio) != len(pct_change_spy):
			pct_change_spy = pct_change_spy[:len(pct_change_portfolio)]

		# Perform calculations
		covariance = numpy.cov(pct_change_portfolio, pct_change_spy)[0][1]
		variance = numpy.var(pct_change_spy)

		return round(covariance / variance, 3)

	def plot(self):
		date = [tick.date for tick in self.stock]
		returns = [self._returns(tick.index) for tick in self.stock]
		position = [self._position(tick.index, True) for tick in self.stock]
		plot_net = subplot2grid((3, 1), (0, 0), rowspan=2)
		plot(date, returns)
		plot_position = subplot2grid((3, 1), (2, 0), sharex=plot_net)
		ylim(-1.5, 1.5)
		yticks((-1, 0, 1), ('short', '...', 'long'))
		fill_between(date, position)
		savefig('png/{0}_{1}.png'.format(self.stock.symbol,
									 self.strategy.__class__.__name__))
		clf()