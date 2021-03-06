from tastypie.resources import ModelResource
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.conf.urls import *
from django.core.files import File
from django.core.files.base import ContentFile
from core.models import Challenge
from core.models import Answer
from core.models import User
from core.models import Vote
from core.models import Group
from tastypie.authorization import Authorization
from tastypie import fields
from tastypie.utils import trailing_slash


from tastypie.resources import ALL, ALL_WITH_RELATIONS

from tastypie.serializers import Serializer
import time
import base64
import os


class UserResource(ModelResource):

	class Meta:
		queryset = User.objects.all()
		resource_name = 'user'
		allowed_methods = ['get','post']
		serializer = Serializer(formats=['xml', 'json'])

		authorization= Authorization()
		always_return_data = True

		filtering = {
			'email': ALL_WITH_RELATIONS
		}

	def prepend_urls(self):
		return [
			url(r'^(?P<resource_name>%s)/search%s$' %(self._meta.resource_name, trailing_slash()),self.wrap_view('search'), name='api_search'),
			url(r'^(?P<resource_name>%s)/addFriend%s$' %(self._meta.resource_name, trailing_slash()),self.wrap_view('addFriend'), name='api_addFriend'),
			url(r'^(?P<resource_name>%s)/getGroups%s$' %(self._meta.resource_name, trailing_slash()),self.wrap_view('getGroups'), name='api_getGroups'),
			]

	def search(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		data = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
		nickname = data.get('nickname', '')
		user = [st.__dict__ for st in User.objects.filter(nickname=nickname)]
		return self.create_response(request, {
					'objects': [st.__dict__ for st in User.objects.filter(nickname=nickname)]
					})

	def addFriend(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		data = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
		userID = data.get('userID')
		friendID = data.get('friendID')
		my_user = User.objects.get(id=userID)
		my_user.friends.add(User.objects.get(id=friendID))
		my_user.save()
		return self.create_response(request, {
					'success': True
					})

	def getGroups(self, request, **kwargs):
		self.method_check(request, allowed=['get'])
		userID = request.GET['userID']
		user = User.objects.get(id=userID)
		sqsGroup = Group.objects.filter(owner=user)
		if sqsGroup:
			return self.create_response(request, {
				'success': True,
				'groups': [group.__dict__ for group in sqsGroup]
				})
		else:
			return self.create_response(request, {
				'success': False,
				'groups': []
				})

	def dehydrate(self, bundle):
	 	userID = bundle.obj
		bundle.data['nbCompleted'] = Answer.objects.filter(userID=userID, status="completed").count()
		bundle.data['nbFailed'] = Answer.objects.filter(userID=userID, status="failed").count()
		bundle.data['friends'] = [friend.__dict__ for friend in bundle.obj.friends.all()]
		return bundle



class GroupResource(ModelResource):
	owner = fields.ToOneField(UserResource, attribute='owner' , related_name='owner', full=True)
	members = fields.ToManyField(UserResource, attribute=lambda bundle: User.objects.all())

	class Meta:
		queryset = Group.objects.all()
		resource_name = 'group'
		allowed_methods = ['get','post']
		serializer = Serializer(formats=['xml', 'json'])
		authorization= Authorization()
		always_return_data = True
		filtering = {
			'owner': ALL_WITH_RELATIONS
		}

	def createGroup(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		data = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
		owner = User.objects.get(id=data.get('owner'))
		title = data.get('title')
		members = data.get('members')
		group = Group(title=title, owner=owner)
		group.save()
		for member in members:
			member = User.objects.get(id=member)
			group.members.add(member)
		group.save()

		return self.create_response(request, {
					'success': True
					})

	def prepend_urls(self):
		return [
	  url(r"^(?P<resource_name>%s)/createGroup%s$" %(self._meta.resource_name, trailing_slash()),self.wrap_view('createGroup'), name="api_createGroup")
	 ]

	def build_filters(self, filters=None):
		if filters is None:
			filters = {}
		orm_filters = super(GroupResource, self).build_filters(filters)
		if 'owner' in filters:
		  orm_filters['owner__exact'] = filters['owner']
		return orm_filters

	def dehydrate(self, bundle):
		bundle.data['members'] = [members.__dict__ for members in bundle.obj.members.all()]
		return bundle



class ChallengeResource(ModelResource):
	author = fields.ToOneField(UserResource, attribute='author' , related_name='author', full=True)

	class Meta:
		queryset = Challenge.objects.all()
		resource_name = 'challenge'
		allowed_methods = ['get','post','delete']
		serializer = Serializer(formats=['xml', 'json'])
		authorization= Authorization()
		always_return_data = True

	def prepend_urls(self):
		return [
	  url(r"^(?P<resource_name>%s)/getChallenges%s$" %(self._meta.resource_name, trailing_slash()),self.wrap_view('getChallenges'), name="api_getChallenges"),
	  url(r"^(?P<resource_name>%s)/createChallenge%s$" %(self._meta.resource_name, trailing_slash()),self.wrap_view('createChallenge'), name="api_createChallenge")
	 ]

	def dehydrate(self, bundle):
		if bundle.obj.group:
			bundle.data['group'] = bundle.obj.group.__dict__
		return bundle

	def createChallenge(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		data = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
		title = data.get('title')
		description = data.get('description')
		author = User.objects.get(id=data.get('authorID'))
		beginning = data.get('beginning')
		duration = data.get('duration')
		category = data.get('category')
		nbAbuse = data.get('nbAbuse')
		type = data.get('type')
		private = data.get('private')
		if data.get('groupID'):
			group = Group.objects.get(id=data.get('groupID'))
		else:
			group = None
		challenge = Challenge(title=title, description=description, author=author, beginning=beginning, duration=duration, category=category, nbAbuse=nbAbuse, type=type, private=private, group=group)
		challenge.save()
		return self.create_response(request, {
					'challengeID': challenge.id,
					'success': True
					})

	def getChallenges(self, request, **kwargs):
		self.method_check(request, allowed=['get'])
		userID = request.GET['userID']
		user = User.objects.get(id=userID)
		sqsAnswer = Answer.objects.filter(userID=user)
		if sqsAnswer:
			sqsAnswer = [ans for ans in sqsAnswer]
			sqsChallenge = Challenge.objects.exclude(id__in=[ans.challengeID.id for ans in sqsAnswer])
			if sqsChallenge:
				return self.create_response(request, {
					'success': True,
					'objects': [challenge.__dict__ for challenge in sqsChallenge]
					})
			else:
				return self.create_response(request, {
					'success': False,
					'objects': []
					})

		else:
			sqsChallenge = Challenge.objects.all()
			if sqsChallenge:
				return self.create_response(request, {
					'success': True,
					'objects': [challenge.__dict__ for challenge in sqsChallenge]
					})
			else:
				return self.create_response(request, {
					'success': False,
					'objects': []
					})


class AnswerResource(ModelResource):
	userID = fields.OneToOneField(UserResource, attribute='userID' , related_name='userID', full=True, null=True)
	challengeID = fields.OneToOneField(ChallengeResource, attribute='challengeID' , related_name='challengeID', full=True, null=True)
	class Meta:
		queryset = Answer.objects.all()
		resource_name = 'answer'
		allowed_methods = ['get','post','delete']
		serializer = Serializer(formats=['xml', 'json'])
		authorization= Authorization()
		always_return_data = True
		filtering = {
			'userID': ALL
		}

	def prepend_urls(self):
		return [
	  url(r"^(?P<resource_name>%s)/getRandomAnswer%s$" %(self._meta.resource_name, trailing_slash()),self.wrap_view('getRandomAnswer'), name="api_getRandomAnswer"),
	  url(r"^(?P<resource_name>%s)/addImage%s$" %(self._meta.resource_name, trailing_slash()),self.wrap_view('addImage'), name="api_addImage"),
	  url(r"^(?P<resource_name>%s)/getImage%s$" %(self._meta.resource_name, trailing_slash()),self.wrap_view('getImage'), name="api_getImage"),
	 ]

	def dehydrate(self, bundle):
		serializers = Serializer(formats=['xml', 'json'])
		vote = [st.__dict__ for st in Vote.objects.filter(answerID=bundle.obj)] #serializers.serialize('json', Answer.objects.filter(userID=bundle.obj))
		bundle.data['vote'] = vote
		return bundle

	
	def build_filters(self, filters=None):
		if filters is None:
			filters = {}
		orm_filters = super(AnswerResource, self).build_filters(filters)
		if 'userID' in filters:
		  orm_filters['userID__exact'] = filters['userID']
		return orm_filters

	def getRandomAnswer(self, request, **kwargs):
		self.method_check(request, allowed=['get'])
		userID = request.GET['userID']
		user = User.objects.get(id=userID)
		sqsAnswer = Answer.objects.exclude(userID=user).order_by('?')[:1]
		if sqsAnswer:
			return self.create_response(request, {
				'success': True,
				'objects': [answer.__dict__ for answer in sqsAnswer]
				})

	def getImage(self, request, **kwargs):
		self.method_check(request, allowed=['get'])
		answer = Answer.objects.get(id=1)
		return self.create_response(request, {
				'name': answer.image.name,
				'url': answer.image.url,
				'path': answer.image.path
				})

	def addImage(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		print 11
		data = self.deserialize(request, request.raw_post_data, format=request.META.get('CONTENT_TYPE', 'application/json'))
		print 22
		image64 = data.get('image')
		print 33
		answer = Answer.objects.get(id=data.get('answerID'))
		print 44
		fh = open("temporaire.jpg", "wb")
		print 111
		fh.write(image64.decode('base64')) # decode et creation de l'img
		print 222
		fh.close()
		print 333
		if fh.closed:
			print 444
			fh = open("temporaire.jpg", "r") #ouverture en lecture
			print 555
			content_file = ContentFile(fh.read()) #ecriture du contenu du fichier
			print 666
			answer.image.save('answer.jpg', content_file)
			print 777
			answer.status = 'over'
			print 888
			answer.save()
			print 999
			fh.close()
			print 000
		if fh.closed:
			os.remove(unicode(fh.name))
			del fh
		return self.create_response(request, {
					'success': True
					})


class VoteResource(ModelResource):
	answerID = fields.ToOneField(AnswerResource, attribute='answerID' , related_name='answerID', full=True, null=True)
	class Meta:
		queryset = Vote.objects.all()
		resource_name = 'vote'
		allowed_methods = ['get','post']
		serializer = Serializer(formats=['xml', 'json'])
		authorization= Authorization()
		always_return_data = True