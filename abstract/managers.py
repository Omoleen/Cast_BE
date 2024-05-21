from rest_framework import serializers


class SimpleManager(serializers.Serializer):
    def validate(self, attrs):
        attrs = super().validate(attrs)

        attrs = self._validate_fields(attrs)

        attrs = self._validate_db(attrs)

        attrs = self._transform_data(attrs)

        return attrs

    def _transform_data(self, attrs):
        return attrs

    def _validate_fields(self, attrs):
        return attrs

    def _validate_db(self, attrs):
        return attrs

    def _misc(self, data):
        self._notify_user(data)

    def create(self, validated_data):

        obj = self._create(validated_data)

        data = validated_data
        self.obj = obj
        data["obj"] = obj
        self._misc(data)

        return obj

    def _create(self, validated_data):
        return super().create(validated_data)

    def update(self, instance, validated_data):

        obj = self._update(instance, validated_data)

        data = validated_data
        self.obj = obj
        data["obj"] = obj
        self._misc(data)

        return obj

    def _update(self, instance, validated_data):
        return super().update(instance, validated_data)

    def _notify_user(self, data):
        pass

    def to_representation(self, instance):
        if isinstance(self._to_representation(instance), str):
            message = self._to_representation(instance)
            data = {}
        else:
            data = self._to_representation(instance)
            message = ""
        return dict(data=data, message=message)

    def _to_representation(self, instance):
        return super().to_representation(instance)


class SimpleModelManager(SimpleManager, serializers.ModelSerializer):
    ...
