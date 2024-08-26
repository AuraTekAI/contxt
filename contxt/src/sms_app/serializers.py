
from sms_app.models import SMS

from rest_framework import serializers


class SmsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SMS
        fields = '__all__'
