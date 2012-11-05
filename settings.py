import redis
import pusher
import os
from datetime import timedelta

## PUSHER ##
############
pusher.app_id = "28247"
pusher.key = "b2c9525770d59267a6a2"
pusher.secret = "12d6efe3c861e6ce372a"
p = pusher.Pusher()

#Ticker Channel

ticker_channel = 'prod_ticker'
# ticker_channel = 'dev_ticker'



## REDIS ##
###########

#Heroku

redis_url =  os.getenv('OPENREDIS_URL', 'redis://localhost')
r = redis.from_url(redis_url, db=0)
rp = redis.from_url(redis_url, db=1)

#Localhost

# redis_url = 'redis://localhost:6379/0'
# r = redis.StrictRedis(host='localhost', port=6379, db=0 )
# rp = redis.StrictRedis(host='localhost', port=6379, db=1 )


#Requests Headers

headers = {'User-agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'}


#Period Task timer

timer = crontab(minute='*', hour='10-22',day_of_week='saturday,sunday,monday,tuesday,wednesday,thursday')
#timer = timedelta(seconds=30)



