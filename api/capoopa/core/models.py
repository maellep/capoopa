from django.db import models
from django.contrib.auth.models import User

# Create your models here. django.hote
	
class Challenge(models.Model):
	title = models.CharField(max_length=200)
	description = models.TextField()
	author = models.ForeignKey(User)
	#beginning = models.IntegerField(max_length=200)
	#end = models.IntegerField(max_length=200)
	#category = models.CharField(max_length=200) # cree un dico de differentes valus pour les enums
	#nbAbuse = models.IntegerField(max_length=200) 
	#nbAnswer = models.IntegerField(max_length=200)
	#type = models.CharField(max_length=200)
	
class Answer(models.Model):
	userID = models.ForeignKey(User)
	challengeID = models.ForeignKey(Challenge)
	status = models.CharField(max_length=200)
	#media = models.IntegerField(max_length=200)
	#nbAbuse = models.IntegerField(max_length=200) 
