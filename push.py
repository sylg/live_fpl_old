import pusher
import redis
import os

redis_url =  os.getenv('OPENREDIS_URL', 'redis://localhost')
r = redis.from_url(redis_url)

#r = redis.StrictRedis(host='localhost', port=6379, db=0 )



pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()


messages = { 'A': 'just got an assist',
			  'GS': 'just scored a Goal',
			  'YC': 'just received a Yellow Card!',
			  'RC': 'has been sent off',
			  'PS': 'just saved a Penalty',
			  'PM': 'just missed a Penalty!',
			  'OG': 'just scored an OWN GOAL!',
			  'S': 'just made 3 saves, +1pt'
}

def push_data(name,keys,fixture_id):
	for key in keys:
		if key in messages and keys[key] != 0:
			msg = '<li><p><span rel="tooltip" title="total point: %s" class="player-name">%s </span>' % (r.hget(name+':fresh:'+str(fixture_id),'TP'), name) +messages[key]+ '</p></li>'
			if key == "S":
				if int(keys[key]) % 3 == 0:
					p['test_channel'].trigger('ticker', {'message': msg })
					r.lpush('pushed_data', msg)
			else:
				p['test_channel'].trigger('ticker', {'message': msg })
				r.lpush('pushed_data', msg)
	

def push_league(team_id):
	returned_data = {}
	for league in r.smembers('team:%s:leagues'%team_id):
		returned_data[league] = r.hgetall('league:%s:info'%league)
	p[team_id].trigger('league', {'message': returned_data })

# TODO
# - Gerer les Cleansheet