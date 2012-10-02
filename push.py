import pusher
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)

pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()


messages = { 'A': '%s(%s pts) just got an assist',
			  'GS': '%s(%s pts) just scored a Goal',
			  'YC': '%s(%s pts) just received a Yellow Card!',
			  'RC': '%s(%s pts) has been sent off',
			  'PS': '%s(%s pts) just saved a Penalty',
			  'PM': '%s(%s pts) just missed a Penalty!',
			  'OG': '%s(%s pts) just scored an OWN GOAL!',
}

def push_data(name,keys,fixture_id):
	for key in keys:
		if key in messages:
			msg = messages[key] % (name, r.hget(name+':fresh:'+str(fixture_id),'TP'))
			p['test_channel'].trigger('chatmessage', {'message': msg })
			r.lpush('pushed_data', msg)


# TODO
# - Implement multiple goals by same players
# - Gerer les Cleansheet
