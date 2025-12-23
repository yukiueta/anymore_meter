from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from .models import User
from .serializers import UserSerializer


class PaginationMixin:
    def paginate(self, queryset, request):
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))
        
        total = queryset.count()
        total_pages = (total + per_page - 1) // per_page
        
        start = (page - 1) * per_page
        end = start + per_page
        items = queryset[start:end]
        
        return {
            'items': items,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages
            }
        }


class UserListView(APIView, PaginationMixin):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all().order_by('-id')
        result = self.paginate(users, request)
        serializer = UserSerializer(result['items'], many=True)
        return Response({
            'items': serializer.data,
            'pagination': result['pagination']
        })


class UserCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = User.objects.create_user(
            username=request.data.get('username'),
            email=request.data.get('email'),
            password=request.data.get('password'),
            permission=request.data.get('permission', 'staff'),
        )
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        user.username = request.data.get('username', user.username)
        user.email = request.data.get('email', user.email)
        user.permission = request.data.get('permission', user.permission)
        user.is_active = request.data.get('is_active', user.is_active)
        user.save()
        serializer = UserSerializer(user)
        return Response(serializer.data)

class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)