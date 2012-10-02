import pusher
import redis

r = redis.StrictRedis(host='localhost', port=6379, db=0)

pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()


def push_data(name,keys):
	for key in keys:
		if key == 'A':
			msg = '%s just scored 3pts with an Assist' % name
			p['test_channel'].trigger('chatmessage', {'message': msg })
		elif key == 'GS':
			if int(keys['GS']) > 1:
				msg = '%s just scored %s goals' %(name, keys['GS'])
				p['test_channel'].trigger('chatmessage', {'message': msg })
			else:
				msg = '%s just scored a Goal' % name
				p['test_channel'].trigger('chatmessage', {'message': msg })
		elif key == 'CS' and int(keys['CS']) == 0:
			msg = 'Clean sheet time for %s!' % name
			p['test_channel'].trigger('chatmessage', {'message': msg })
