from django.http import JsonResponse
from app.models import UserInfo, GroupPath
from functools import wraps

def check_permission(func):
    @wraps(func)
    def wrapper(self, request, *args, **kwargs):
        # 获取当前用户ID
        user_id = request.user.nid
        if not user_id:
            return JsonResponse({
                'code': 401,
               'msg': '用户未登录',
                'data': None
            })
        
        try:
            user = UserInfo.objects.get(nid=user_id)
            # 超级管理员直接放行
            if user.is_superuser:
                return func(self, request, *args, **kwargs)
            
            # 获取当前请求路径
            current_path = request.path
            
            # 获取用户所在组的权限路径
            user_groups = user.groups.all()
            allowed_paths = []
            for group in user_groups:
                group_path = GroupPath.objects.filter(group=group).first()
                if group_path and group_path.path:
                    allowed_paths.extend(group_path.path)
            
            # 检查权限
            if not allowed_paths or current_path not in allowed_paths:
                return JsonResponse({
                    'code': 403,
                    'msg': '权限不足',
                    'data': None
                })
            
            return func(self, request, *args, **kwargs)
            
        except UserInfo.DoesNotExist:
            return JsonResponse({
                'code': 401,
                'msg': '用户不存在',
                'data': None
            })
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'权限验证失败：{str(e)}',
                'data': None
            })
    
    return wrapper