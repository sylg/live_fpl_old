import pusher
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)

pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()


messages = { 'A': '%s just got an assist',
			  'GS': '%s just scored a Goal',
			  'YC':'%s just received a Yellow Card!',
			  'RC':'%s has been sent off',
			  'PS':'%s just saved a Penalty',
			  'PM': '%s just missed a Penalty!',
			  'OG': '%s just scored an OWN GOAL!',
}

def push_data(name,keys):
	for key in keys:
		if key in messages:
			p['test_channel'].trigger('chatmessage', {'message': messages[key] % name })
			r.lpush('pushed_data', messages[key] % name)


# TODO
# - Implement multiple goals by same players
# - Gerer les Cleansheet
