from django.db import models

class User(models.Model):
        name = models.CharField(max_length=100)
        password = models.CharField(max_length=100)
        email = models.EmailField()
        image = models.URLField()
        twitterid = models.CharField(max_length=100)
        facebookid = models.CharField(max_length=100, db_index=True)
	firstname = models.CharField(max_length=100)
	lastname = models.CharField(max_length=100)
	slogan = models.CharField(max_length=100)
	bio = models.TextField()
	following = models.ManyToManyField('self', symmetrical=False)
	accesstoken = models.CharField(max_length=1000, db_index=True)

        def __unicode__(self):
                return self.name

class Checkin(models.Model):
        user = models.ForeignKey(User, db_index=True)
        created = models.DateTimeField(auto_now_add=False)
        ticker = models.CharField(max_length=100, db_index=True)
        symbolName = models.CharField(max_length=255)
        symbolType = models.CharField(max_length=100)
        symbolExchange = models.CharField(max_length=100)
        comment = models.CharField(max_length=140)
        checkInType = models.IntegerField(db_index=True)
        twitter = models.BooleanField()
        facebook = models.BooleanField()

	def __unicode__(self):
		return "%s:%s:%s" % (self.created, self.user.name, self.ticker)
