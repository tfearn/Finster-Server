from django.http import HttpResponse
from django.db import connection, transaction
from django.utils import simplejson
from django.db.models import Q
from models import Checkin, User
from finster import fb_login_required, put_wall_post, FinsterLogger, get_friends, send_email
from datetime import datetime, timedelta
import sys

CHECKINTYPE = { '1':'I Bought',
		'2':'I Sold',
		'3':'I am Bullish on',
		'4':'I am Bearish on',
		'5':'Good Rumour About',
		'6':'Bad Rumour About' }

@fb_login_required
def getcheckins(request):
	user = request.user
	start = int(request.GET.get('start', 0))
	limit = start + int(request.GET.get('limit', 100))
	checkInType = request.GET.get('type', None)
	ticker = request.GET.get('ticker', None)
	feed = request.GET.get('feed', 'you,friends').split(',')
	userid = int(request.GET.get('userid', user.id))

	checkins = Checkin.objects.all()
	
	if 'network' in feed:
		checkins = checkins.exclude(Q(user__in=user.following.all()) | Q(user=user))
	elif userid and 'user' in feed:
		checkins = checkins.filter(user=User.objects.get(pk=userid))
	elif 'you' in feed and 'friends' in feed:
		checkins = checkins.filter(Q(user__in=user.following.all()) | Q(user=user))
	elif 'you' in feed:
		checkins = checkins.filter(user=user)
	elif 'friends' in feed:
		checkins = checkins.filter(user__in=user.following.all())

	friends = User.objects.all().filter(id__in=user.following.all())

	if checkInType:
		checkins = checkins.filter(checkInType__exact=checkInType)
	
	if ticker and not ticker == 'all':
		checkins = checkins.filter(ticker__exact=ticker)
	
	checkins = checkins.order_by('-created')
	
	checkInList = { 'checkInList':[] }

	for checkin in checkins[start:limit]:
		if checkin.user.id == user.id:
			group = 'you'
		elif checkin.user in friends:
			group = 'friend'
		else:
			group = 'network'

		#num_checkins = Checkin.objects.filter(user=checkin.user).count()

		checkInNode = { 'id': checkin.id,
				'timestamp': checkin.created.strftime('%Y-%m-%d %H:%M:%S UTC'),
				'type': checkin.checkInType,
				'comment': checkin.comment,
				'user':{
					'id':checkin.user.id,
					'name':checkin.user.name,
					'group':group,
					'image':checkin.user.image,
                     			#'followers': User.objects.all().filter(following=checkin.user).count(),
                     			#'following': checkin.user.following.all().count(),
                     			#'checkins': num_checkins,
                     			#'badges': 0,
					'points': checkin.user.points, 
					},
				'ticker':{
					'symbol':checkin.ticker,
					'symbolName':checkin.symbolName,
					'type':checkin.symbolType,
					'exchange':checkin.symbolExchange
					}}
		checkInList['checkInList'].append(checkInNode)
	
	return HttpResponse(simplejson.dumps(checkInList), content_type='application/json')

@fb_login_required
def checkin(request):
	user = request.user
	ticker = request.GET['symbol']
	checkInType = request.GET['type']
	symbolName = request.GET.get('symbolName','')
	comment = request.GET.get('comment','')

	checkin = Checkin(user=user,
			  created=datetime.utcnow(),
			  checkInType=checkInType,
			  ticker=ticker,
			  comment=comment,
			  twitter=request.GET.get('sharetwitter',0),
			  facebook=request.GET.get('sharefacebook',0),
			  symbolName=symbolName,
			  symbolType=request.GET.get('symbolType', ''),
			  symbolExchange=request.GET.get('exchange', ''))
	checkin.save()

	# 2 points per checkin for now
	user.points = user.points + 2;
	user.save()

	if request.GET.get('sharefacebook', 0) and not user.id == 1:
		fbmsg = "%s %s" % (CHECKINTYPE[checkInType], ticker)
		if symbolName: fbmsg = "%s (%s)" % (fbmsg,symbolName)
		if comment: fbmsg = '%s "%s"' % (fbmsg,comment)
		put_wall_post(request,fbmsg)

	thirtydaysago = datetime.today() - timedelta(days=30)

	jsonresponse = { 'checkInsForTicker': Checkin.objects.filter(user=user).filter(ticker__iexact=ticker).filter(checkInType__iexact=checkInType).count(),
			 'otherCheckInsForTicker': Checkin.objects.exclude(user=user).filter(ticker__exact=ticker).filter(checkInType__iexact=checkInType).filter(created__gte=thirtydaysago).count(),
			 'otherTickerInterest': Checkin.objects.exclude(user=user).filter(ticker__exact=ticker).filter(created__gte=thirtydaysago).count(),
			 'pointsEarned': 2,
			 'totalPoints': user.points,
			 'badgeID': 0 }

	return HttpResponse(simplejson.dumps(jsonresponse), content_type='application/json')

@fb_login_required
def loginwithfb(request):
	"""
	Validates the facebook access token (as a cookie or GET parameter) and creates the user
	in the database if necessary.

	Notice, this function is not necessary because the @fb_login_required decorator
	will perform this function for any call so decorated
	"""
	return HttpResponse(request.user.name)

@fb_login_required
def follow(request):
	user = request.user
	following = User.objects.get(pk=int(request.GET.get('userid',0)))
	user.following.add(following)		
	send_email(following.email,following.name, user.name)
	return HttpResponse("follow")

@fb_login_required
def unfollow(request):
	user = request.user
        following = User.objects.get(pk=int(request.GET.get('userid',0)))
        user.following.remove(following)
	return HttpResponse("unfollow")

@fb_login_required
def finduser(request):
	searchfor = request.GET.get('search', '')
	users = User.objects.filter(name__icontains=searchfor).exclude(id=request.user.id)
	
	jsonresp = {'searchresults':[]}
	
	for user in users:
		group = 'network'
        	if user.id == request.user.id:
                	group = 'you'
        	elif user in request.user.following.all():
                	group = 'friend'

		userNode = {'user':{
        	     	    	'id': user.id,
                     		'name': user.name,
				'group': group,
                     		'slogan': user.slogan,
                     		'bio': user.bio,
                     		'image': user.image,
                     		'followers': User.objects.all().filter(following=user).count(),
                     		'following': user.following.all().count(),
                     		'checkins': Checkin.objects.filter(user=user).count(),
                     		'points': user.points,
                     		'badges': 0 }}

		jsonresp['searchresults'].append(userNode)

        return HttpResponse(simplejson.dumps(jsonresp), content_type='application/json')	

@fb_login_required
def getuser(request):
	userid = int(request.GET.get('userid', 0))
	if userid:
		user = User.objects.get(pk=userid)
 	else:
		user = request.user

	group = 'network'
	if user.id == request.user.id:
        	group = 'you'
        elif user in request.user.following.all():
                group = 'friend'

	jsonresp = { 'id': user.id,
		     'name': user.name,
		     'group': group,
		     'slogan': user.slogan,
		     'bio': user.bio,
		     'image': user.image,
		     'followers': User.objects.all().filter(following=user).count(),
		     'following': user.following.all().count(),
		     'checkins': Checkin.objects.filter(user=user).count(),
		     'points': user.points,
		     'badges': 0, }

	return HttpResponse(simplejson.dumps(jsonresp), content_type='application/json')

@fb_login_required
def getleaderboard(request):
	leaders = User.objects.filter(Q(id__in=request.user.following.all()) | Q(id=request.user.id)).order_by('-points')
	jsonresp = { 'leaderboard': [] }
        for leader in leaders:
        	userNode = {'user':{
                             'id': leader.id,
                             'name': leader.name,
                             'image': leader.image,
                             'followers': 0, #User.objects.all().filter(following=leader).count(),
                             'following': 0, #leader.following.all().count(),
                             'checkins': 0, #Checkin.objects.filter(user=leader).count(),
                             'points': leader.points,
                             'badges': 0 }}

                jsonresp['leaderboard'].append(userNode)

	return HttpResponse(simplejson.dumps(jsonresp), content_type='application/json')

@fb_login_required
def getuserfollowing(request):
	userid = int(request.GET.get('userid', 0))
        if userid:
                user = User.objects.get(pk=userid)
        else:
                user = request.user
         
        followingList = { 'following':[] }
        for following_user in user.following.all():
                if following_user.id == request.user.id:
                        group = 'you'
                else:
                        group = 'friend'

                followingNode = { 
                                'user':{
                                        'id':following_user.id,
                                        'name':following_user.name,
                                        'group':group,
                                        'image':following_user.image,
                                        'followers': User.objects.all().filter(following=following_user).count(),
                                        'following': following_user.following.all().count(),
                                        'checkins': Checkin.objects.filter(user=following_user).count(),
					'points': following_user.points,
                                        'badges': 0                                        
					}
                                 }
                followingList['following'].append(followingNode)
	
	return HttpResponse(simplejson.dumps(followingList), content_type='application/json')

@fb_login_required
def getuserfollowers(request):
        userid = int(request.GET.get('userid', 0))
        if userid:
                user = User.objects.get(pk=userid)
        else:
                user = request.user

        followerList = { 'follower':[] }
        for follower_user in User.objects.all().filter(following=user):
                if follower_user.id == request.user.id:
                        group = 'you'
                else:
                        group = 'friend'

                followerNode = {
                                'user':{
                                        'id':follower_user.id,
                                        'name':follower_user.name,
                                        'group':group,
                                        'image':follower_user.image,
                                        'followers': User.objects.all().filter(following=follower_user).count(),
                                        'following': follower_user.following.all().count(),
                                        'checkins': Checkin.objects.filter(user=follower_user).count(),
                                        'points': follower_user.points,
					'badges': 0
                                        }
                                 }
                followerList['follower'].append(followerNode)

        return HttpResponse(simplejson.dumps(followerList), content_type='application/json')

@fb_login_required
def isfollowinguser(request):
	if request.user.following.filter(pk=int(request.GET.get('userid',0))).count() > 0:
		res = { 'isfollowinguser':1 }
	else:
		res = { 'isfollowinguser':0 }

	return HttpResponse(simplejson.dumps(res), content_type='application/json')

@fb_login_required
def gettrending(request):
	#checkInType = request.GET.get('type', None)
        
	cursor = connection.cursor()
    	cursor.execute("select ticker, symbolName, symbolType, symbolExchange, count(id) as checkins, sum(case when checkInType in (1,3,5) then 1 else 0 end) as positive, sum(case when checkInType in (2,4,6) then 1 else 0 end) as negative from web_checkin group by ticker, symbolName, symbolType, symbolExchange order by checkins desc, checkInType limit 0, 20")
    	rows = cursor.fetchall()
	
	res = { 'trendingList': [] }
	for row in rows:
		trending = { 'trend':{
					'ticker':{
						'symbol':row[0],
						'symbolName': row[1],
						'type': row[2],
						'exchange': row[3],
					},
					'checkins':int(row[4]),
					'positive':int(row[5]),
					'negative':int(row[6]),
			   }}

		res['trendingList'].append(trending)

	return HttpResponse(simplejson.dumps(res), content_type='application/json')

@fb_login_required
def getuserlastcheckins(request):
        userid = int(request.GET.get('userid', 0))
        if userid:
                user = User.objects.get(pk=userid)
        else:
                user = request.user

	cursor = connection.cursor()
        cursor.execute('select max(id) as id from web_checkin where user_id = %d group by ticker limit 50' % (user.id,))
        ids = [row[0] for row in cursor.fetchall()]

	checkins = Checkin.objects.filter(id__in=ids).order_by('-created')

	checkInList = { 'checkInList':[] }
        for checkin in checkins:
                if checkin.user.id == request.user.id:
                        group = 'you'
                elif checkin.user.id in request.user.following.all():
                        group = 'friend'
                else:
                        group = 'network'

                checkInNode = { 'id': checkin.id,
                                'timestamp': checkin.created.strftime('%Y-%m-%d %H:%M:%S UTC'),
                                'type': checkin.checkInType,
                                'comment': checkin.comment,
                                'user':{
                                        'id':checkin.user.id,
                                        'name':checkin.user.name,
                                        'group':group,
                                        'image':checkin.user.image,
                                        'points': checkin.user.points,
                                        },
                                'ticker':{
                                        'symbol':checkin.ticker,
                                        'symbolName':checkin.symbolName,
                                        'type':checkin.symbolType,
                                        'exchange':checkin.symbolExchange
                                        }}
                checkInList['checkInList'].append(checkInNode)

	return HttpResponse(simplejson.dumps(checkInList), content_type='application/json')	

@fb_login_required
def getfriends(request):
	res = { 'friends': [] } 
	res['friends'] = get_friends(request)
	return HttpResponse(simplejson.dumps(res), content_type='application/json')

