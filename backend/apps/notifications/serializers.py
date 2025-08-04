from rest_framework import serializers

from apps.notifications.constants import DeviceType, FCMTokenAction


class FCMTokenSerializer(serializers.Serializer):
    ''''
    Serializer for handling FCM device tokens and determining the required
    action based on provided tokens.

    Fields:
    - old_token: previous device token (optional)
    - new_token: new device token (optional)
    - action: action to perform (set by validation logic)
    - device_type: type of device ('android' or 'ios', optional)

    The validate method sets the action field:
    - 'update' if both old_token and new_token are provided
    - 'set' if only new_token is provided
    - 'deactivate' if only old_token is provided
    - Raises a validation error if neither token is provided

    After validation, returns a dictionary with 'action' and 'data' keys.
    '''
    old_token = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    new_token = serializers.CharField(
        required=False,
        allow_null=True,
        allow_blank=True
    )
    action = serializers.SerializerMethodField()
    device_type = serializers.ChoiceField(
        choices=DeviceType.CHOICES,
        required=False
    )

    def get_action(self, obj):
        '''Determines the action based on the provided tokens.'''
        old_token = obj.get('old_token')
        new_token = obj.get('new_token')
        if old_token and new_token:
            return FCMTokenAction.UPDATE
        elif new_token and not old_token:
            return FCMTokenAction.SET
        elif old_token and not new_token:
            return FCMTokenAction.DEACTIVATE
        return None

    def validate(self, data):
        '''
        Validates the input data and sets the action field.
        Raises a validation error if no tokens are provided.
        Returns a dictionary with provided tokens.
        '''
        action = self.get_action(data)
        if not action:
            raise serializers.ValidationError(
                "At least one token must be provided."
            )

        return { k: v for k, v in data.items() if k in (
            'old_token', 'new_token'
            ) and v
        }
        