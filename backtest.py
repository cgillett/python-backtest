import code

from lib import Stock, BackTest, Dataset
from strategy import Patent, AQR, Hold, Valuation, Monkey, Cheat, Experiment, Technical

def help():
    print open('README.rst').read()

def example():
	print "patent_dataset = Dataset('datasets/patents.xlsx', '%Y-%d-%m')"
	patent_dataset = Dataset('datasets/patents.xlsx', '%Y-%d-%m')
	
	print "strategy = Patent(-2, -2, patent_dataset)"
	strategy = Patent(-2, -2, patent_dataset)
	
	print "spy = Stock('SPY')"
	spy = Stock('SPY')

	print "backtest(spy, strategy)"
	print backtest(spy, strategy)

banner = """Back Testing Trading Strategy Console
type help() for assistance."""

backtest = BackTest()
code.interact(banner=banner, local=locals())