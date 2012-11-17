from settings import *

messages = { 'A': ' just got an assist.',
			  'GS': ' just scored a Goal!',
			  'YC': ' just received a Yellow Card!',
			  'RC': ' has been sent off.',
			  'PS': ' just saved a Penalty!',
			  'PM': ' just missed a Penalty!',
			  'OG': ' just scored an OWN GOAL!',
			  'S': ' just made 3 saves, +1pt.',
}

def push_data(pid,keys,current_mp):
	print "Pushing data: %s"%keys
	old_stats = rp.hgetall('%s:old'%pid)
	old_tp = old_stats['TP']
	if 'TP' in keys and keys['TP'] != old_tp:
		for key in keys:
			if key in messages and keys[key] != 0:
				msg = '<li class="pushmsg"><p>['+current_mp+'\'] <span rel="tooltip" title="total point: %s" class="player-name" pid ="%s">%s</span>' %(rp.hget('%s:fresh'%pid, 'TP'),pid, keys['playername']) +messages[key]+ '</p></li>'
				if key == "S" and int(keys[key]) % 3 == 0:
					p[ticker_channel].trigger('ticker', {'message': msg })
					r.lpush('pushed_data', msg)
				elif key =='B':
					print "bonus point"
					msg = '<li class="pushmsg"><p><span rel="tooltip" title="total point: %s" class="player-name" pid ="%s">%s</span>' %(rp.hget('%s:fresh'%pid, 'TP'),pid, keys['playername']) +' received %s Bonus point(s).'%keys[key] + '</p></li>'
					p[ticker_channel].trigger('ticker', {'message': msg })
				else:
					p[ticker_channel].trigger('ticker', {'message': msg })
					r.lpush('pushed_data', msg)

def push_league(team_id):
	returned_data = {}
	for league in r.hgetall('team:%s:leagues'%team_id):
		returned_data[league] = r.hgetall('league:%s:info'%league)
	p[team_id].trigger('league', {'message': returned_data })



def player_change(pdict, fixture_id, old_mp, current_mp):
	print "received this dict to check for player sub (fixture id = %s,old = %s, current = %s)"%(fixture_id, old_mp, current_mp)
	print pdict
	for player in pdict:
		msg_in = '<li class="pushmsg"><p><span rel="tooltip" title="total point: %s" class="player-name" pid ="%s">%s</span>' %(rp.hget('%s:fresh'%player, 'TP'),player, rdb.hget(player,'web_name'))+' has come onto the pitch.</p></li>'
		if int(pdict[player]['MP']) == 1:
			push = 0
			for pid in rp.lrange('lineups:%s'%fixture_id, 0, -1):
				if int(rp.hget('%s:fresh'%pid,'MP')) == int(old_mp) and pid not in rp.lrange('subs:%s'%fixture_id,0,-1):
					msg_out = '<li class="pushmsg"><p><span rel="tooltip" title="total point: %s" class="player-name" pid ="%s">%s</span>' %(rp.hget('%s:fresh'%pid, 'TP'),pid, rdb.hget(player,'web_name'))+' has been subbed off.</p></li>'
					print "pushing subs OUT %s"%rdb.hget(pid,'web_name')
					p[ticker_channel].trigger('ticker', {'message': msg_out })
					push = 1
					rp.lpush('subs:%s'%fixture_id, pid)
			if push == 1:
				print "pushing subs IN %s"%pdict[player]['playername']
				p[ticker_channel].trigger('ticker', {'message': msg_in })








# TODO
# - Gerer les Cleansheet