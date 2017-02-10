class Patent(object):

	def __init__(self, patent_high, patent_low, patents):
		self.patent_high = patent_high
		self.patent_low = patent_low

		self.patents = patents

	def __call__(self, tick):
		percent_change = self.patents.percent_change(tick, 'Utility_Patents_Issued', 365)
	
		if percent_change == None:
			return 'close'

		if percent_change > self.patent_high:
			return 'buy'
		if percent_change < self.patent_low:
			return 'sell'