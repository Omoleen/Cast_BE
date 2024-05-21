from rest_framework import generics, serializers, status
from rest_framework.response import Response


class SimpleCreateGenericView(generics.GenericAPIView):
    serializer_class = serializers.Serializer

    def post(self, request, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context=dict(request=request)
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SimplePostGenericView(generics.GenericAPIView):
    serializer_class = serializers.Serializer

    def post(self, request, **kwargs):
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            data=request.data, context=dict(request=request, **self.kwargs)
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SimpleUpdateGenericView(generics.GenericAPIView):
    serializer_class = serializers.Serializer
    lookup_field = "id"

    def patch(self, request, **kwargs):
        obj = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            obj,
            data=request.data,
            context=dict(request=request, **self.kwargs),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SimplePartialUpdateGenericView(generics.GenericAPIView):
    serializer_class = serializers.Serializer
    lookup_field = "id"

    def patch(self, request, **kwargs):
        obj = self.get_object()
        serializer_class = self.get_serializer_class()
        serializer = serializer_class(
            obj,
            data=request.data,
            partial=True,
            context=dict(request=request, **self.kwargs),
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SimpleGetDetailGenericView(generics.GenericAPIView):
    lookup_field = "id"

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer_class = self.get_serializer_class()
        return Response(
            serializer_class(obj, context=dict(request=request, **self.kwargs)).data,
            status=status.HTTP_200_OK,
        )


class SimpleGetListGenericView(generics.GenericAPIView):
    def get(self, request, *args, **kwargs):
        objs = self.get_queryset()
        serializer_class = self.get_serializer_class()
        return Response(
            serializer_class(
                objs, many=True, context=dict(request=request, **self.kwargs)
            ).data,
            status=status.HTTP_200_OK,
        )


class SimpleDeleteOneGenericView(generics.GenericAPIView):
    lookup_field = "id"

    def delete(self, request, *args, **kwargs):
        obj = self.get_object()
        obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class SimpleCreateUpdateGenericView(
    SimpleCreateGenericView, SimplePartialUpdateGenericView
):
    ...


class SimpleGetDetailDeleteGenericView(
    SimpleGetDetailGenericView, SimpleDeleteOneGenericView
):
    ...
