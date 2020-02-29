from django.db import models

# Create your models here.

class LineUser(models.Model):
    """ユーザ情報"""
    user_id = models.CharField('ユーザID', unique=True, max_length=255)
    display_name = models.CharField('表示名', max_length=255)
    age = models.IntegerField('年齢', null=False, default=-1)
    occupation = models.IntegerField('職業', null=False, default=-1)
    is_rock = models.IntegerField('施錠状態', null=False, default=-1)
    latitude = models.FloatField('変換前の緯度', null=False, default=-1.0)
    longitude = models.FloatField('変換前の経度', null=False, default=-1.0)
    conLatitude = models.FloatField('変換後の緯度', null=False, default=-1.0)
    conLongitude = models.FloatField('変換後の経度', null=False, default=-1.0)
    pattern = models.IntegerField('メッセージパターン', null=False, default=-1)
    def __str__(self):
        return self.user_id + ':' + self.display_name

class Record(models.Model):
    """レコード情報"""
    user_id = models.CharField('ユーザID', max_length=255)
    display_name = models.CharField('表示名', max_length=255)
    age = models.IntegerField('年齢', null=False, default=-1)
    occupation = models.IntegerField('職業', null=False, default=-1)
    is_rock = models.IntegerField('施錠状態', null=False, default=-1)
    latitude = models.FloatField('変換前の緯度', null=False, default=-1.0)
    longitude = models.FloatField('変換前の経度', null=False, default=-1.0)
    conLatitude = models.FloatField('変換後の緯度', null=False, default=-1.0)
    conLongitude = models.FloatField('変換後の経度', null=False, default=-1.0)
    month = models.IntegerField('月', null=False, default=-1)
    time = models.IntegerField('時間', null=False, default=-1)
    score = models.FloatField('安全スコア', null=False, default=-1.0)
    def __str__(self):
        return self.display_name + 'の' + str(self.month) + '月' + str(self.time) + '時のレコード情報'