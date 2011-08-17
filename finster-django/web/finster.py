from django.http import HttpRequest, HttpResponse
from django.utils import simplejson
from facebook import GraphAPI, GraphAPIError
from models import User
import logging
import sys
import zmq
from datetime import datetime

class FinsterLogger(object):
	def __init__(self):
		self.socket = zmq.Context().socket(zmq.PUB)
		self.socket.connect("tcp://127.0.0.1:5556")
		self.socket.setsockopt(zmq.LINGER, 0)
	
	def log(self, message, request):
		data = {'message': message, 
			'userid': request.user.id, 
			'api_call': request.get_full_path(), 
			'entry_ts': str(datetime.now()) }
		self.socket.send(simplejson.dumps(data)) 

def fb_login_required(f):
        def wrap(request):
		logger = FinsterLogger()

                accesstoken = request.COOKIES.get('fb_accesstoken',None)
                if not accesstoken: accesstoken = request.GET.get('accesstoken',None)
		if not accesstoken: return HttpResponse('Access Token is empty!', status=403)

                try:
			request.user = User.objects.get(accesstoken__exact=accesstoken)
		except User.DoesNotExist:
			try:	
                        	graph = GraphAPI(accesstoken)
                        	fbUser = graph.get_object('me')

				try:
                        		request.user = User.objects.get(facebookid=fbUser['id'])
				except User.DoesNotExist:
                        		request.user = User(name=fbUser['name'],
                                    		    	email=fbUser['email'],
                                    		    	image="http://graph.facebook.com/%s/picture" % (fbUser['id'],),
                                    		    	facebookid=fbUser['id'],
                                    		    	firstname=fbUser['first_name'],
                                    		    	lastname=fbUser['last_name'])
                        		request.user.save()
					logger.log("Created User", request)
			except GraphAPIError as ge:
				print >> sys.stderr, 'Facebook error: %s', (ge, )
                		sys.stderr.flush()	
                		return HttpResponse('Not logged into Facebook: %s [%s]' % (ge,accesstoken), status=403)

		request.user.accesstoken = accesstoken
		request.user.save()

                req_start_time = datetime.now()

                response = f(request)
                
		response.set_cookie(key='fb_accesstoken', value=request.user.accesstoken, path='/api')

                logger.log("Request took %s" % (datetime.now() - req_start_time), request)
                return response

        wrap.__doc__=f.__doc__
        wrap.__name__=f.__name__
        return wrap

def put_wall_post(request,message):
	try:
		graph = GraphAPI(request.user.accesstoken)
		fb_response = graph.put_wall_post(message)
	except GraphAPIError as e:
		print >> sys.stderr, 'Facebook error: %s', (e, )
        	sys.stderr.flush()
