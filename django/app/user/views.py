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
        return {
            'items': queryset[start:end],
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
        if not request.user.is_admin:
            return Response({'error': 'admin required'}, status=status.HTTP_403_FORBIDDEN)
        
        users = User.objects.order_by('-id')
        
        if request.GET.get('permission'):
            users = users.filter(permission=request.GET['permission'])
        if request.GET.get('search'):
            users = users.filter(email__icontains=request.GET['search'])
        
        result = self.paginate(users, request)
        return Response({
            'items': UserSerializer(result['items'], many=True).data,
            'pagination': result['pagination']
        })


class UserCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not request.user.is_admin:
            return Response({'error': 'admin required'}, status=status.HTTP_403_FORBIDDEN)
        
        user = User.objects.create_user(
            username=request.data.get('username'),
            email=request.data.get('email'),
            password=request.data.get('password'),
            permission=request.data.get('permission', 'operator'),
        )
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        if not request.user.is_admin:
            return Response({'error': 'admin required'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(UserSerializer(user).data)


class UserUpdateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_admin:
            return Response({'error': 'admin required'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        user.username = request.data.get('username', user.username)
        user.email = request.data.get('email', user.email)
        user.permission = request.data.get('permission', user.permission)
        user.is_active = request.data.get('is_active', user.is_active)
        user.save()
        return Response(UserSerializer(user).data)


class UserDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        if not request.user.is_admin:
            return Response({'error': 'admin required'}, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'not found'}, status=status.HTTP_404_NOT_FOUND)

        if user.id == request.user.id:
            return Response({'error': 'cannot delete yourself'}, status=status.HTTP_400_BAD_REQUEST)

        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class UserMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class UserChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        
        if not request.user.check_password(current_password):
            return Response({'error': 'invalid current password'}, status=status.HTTP_400_BAD_REQUEST)
        
        if len(new_password) < 8:
            return Response({'error': 'password must be at least 8 characters'}, status=status.HTTP_400_BAD_REQUEST)
        
        request.user.set_password(new_password)
        request.user.save()
        return Response({'status': 'password changed'})