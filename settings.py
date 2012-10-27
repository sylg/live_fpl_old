import redis
import pusher


## PUSHER ##
pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()

#Pusher channel

#Pusher bind event

#Pusher event name

#Pusher setup



## REDIS ##


#Heroku

#redis_url =  os.getenv('OPENREDIS_URL', 'redis://localhost')
#r = redis.from_url(redis_url)

#Localhost

r = redis.StrictRedis(host='localhost', port=6379, db=0 )



