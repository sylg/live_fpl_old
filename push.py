from settings import *

messages = { 'A': 'just got an assist',
			  'GS': 'just scored a Goal',
			  'YC': 'just received a Yellow Card!',
			  'RC': 'has been sent off',
			  'PS': 'just saved a Penalty',
			  'PM': 'just missed a Penalty!',
			  'OG': 'just scored an OWN GOAL!',
			  'S': 'just made 3 saves, +1pt',
}

def push_data(name,keys,fixture_id):
	print "For player: %s in fixture: %s"%(name, fixture_id)
	print "Pushing data: %s"%keys
	old_stats = rp.hgetall('%s:old:%s'%(name,fixture_id))
	old_tp = old_stats['TP']
	if 'TP' in keys and keys['TP'] != old_tp:
		for key in keys:
			if key in messages and keys[key] != 0:
				msg = '<li class="pushmsg"><p><span rel="tooltip" title="total point: %s" class="player-name">%s</span>' % (rp.hget(name+':fresh:%s'%fixture_id, 'TP'), name) +" "+messages[key]+ '</p></li>'
				if key == "S":
					if int(keys[key]) % 3 == 0:
						p[ticker_channel].trigger('ticker', {'message': msg })
						r.lpush('pushed_data', msg)
				elif key =='B':
					print "bonus point"
					msg = '<li class="pushmsg"><p><span rel="tooltip" title="total point: %s" class="player-name">%s</span>' % (rp.hget(name+':fresh:%s'%fixture_id, 'TP'), name) +' Received %s Bonus point(s)'%keys[key] + '</p></li>'
					p[ticker_channel].trigger('ticker', {'message': msg })
				else:
					p[ticker_channel].trigger('ticker', {'message': msg })
					r.lpush('pushed_data', msg)

def push_league(team_id):
	returned_data = {}
	for league in r.hgetall('team:%s:leagues'%team_id):
		returned_data[league] = r.hgetall('league:%s:info'%league)
	p[team_id].trigger('league', {'message': returned_data })

# TODO
# - Gerer les Cleansheet
