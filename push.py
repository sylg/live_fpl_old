import pusher
import redis
import os

redis_url =  os.getenv('REDISTOGO_URL', 'redis://localhost')
r = redis.from_url(redis_url) #redis.StrictRedis(host='localhost', port=6379, db=0 )

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
}

def push_data(name,keys,fixture_id):
	if r.get('livefpl_status') != 'live':
		r.set('livefpl_status','live')
	for key in keys:
		if key in messages:
			if key != 0:
				msg = '<li><a href="#"><span rel="tooltip" title="total point: %s" class="player-name">%s</span>' % (r.hget(name+':fresh:'+str(fixture_id),'TP'), name) +messages[key]+ '</a></li>'
				p['test_channel'].trigger('chatmessage', {'message': msg })
				r.lpush('pushed_data', msg)


# TODO
# - Implement multiple goals by same players
# - Gerer les Cleansheet

