import pusher
import redis

#redis_url =  'redis://' #os.getenv('REDISTOGO_URL', 'redis://localhost')
r = redis.StrictRedis(host='localhost', port=6379, db=0 ) #redis.from_url(redis_url)

pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()



messages = { 'A': '<li><a href="#"><span rel="tooltip" title="%s pts" style="color:red;">%s</span> just got an assist</a></li>',
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
			if key != 0:
				msg = messages[key] % (r.hget(name+':fresh:'+str(fixture_id),'TP'), name)
				p['test_channel'].trigger('chatmessage', {'message': msg })
				r.lpush('pushed_data', msg)


# TODO
# - Implement multiple goals by same players
# - Gerer les Cleansheet
