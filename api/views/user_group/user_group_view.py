from django.http import JsonResponse
from django.views import View
from app.models import GroupPath, UserInfo
from django.contrib.auth.models import Group, Permission
from django.db.models import Q
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import Group
from api.utils.auth import check_permission

@method_decorator(csrf_exempt, name='dispatch')
class UserGroupView(View):
    """
    用户组管理视图
    提供用户组的增删改查功能
    """
    
    @check_permission
    def get(self, request):
        """获取用户组列表或详情"""
        try:
            # 获取当前用户
            # user_id = request.session.get('user_id')
            # if not user_id:
            #     return JsonResponse({
            #         'code': 401,
            #         'msg': '用户未登录',
            #         'data': {}
            #     })
            
            # # 检查用户权限
            # current_user = UserInfo.objects.get(nid=user_id)
            # if not current_user.is_superuser:
            #     return JsonResponse({
            #         'code': 403,
            #         'msg': '权限不足',
            #         'data': {}
            #     })
            
            # 获取查询参数
            group_id = request.GET.get('id')
            
            if group_id:
                # 获取指定ID的用户组
                try:
                    group = Group.objects.get(id=group_id)
                    # 获取用户组关联的菜单
                    menus = []
                    # 如果有关联菜单的逻辑，需要在这里实现
                    
                    # 获取用户组关联的用户
                    users = UserInfo.objects.filter(groups=group).values('nid', 'username', 'nick_name')
                    group_path = GroupPath.objects.filter(group=group)
                    # 获取用户组的权限
                    permissions = GroupPath.object().values('id', 'path', 'group_id')
                    menus = group_path.path
                    # 构建返回数据
                    group_data = {
                        'id': group.id,
                        'group_name': group.name,
                        'permissions': list(permissions),
                        'users': list(users),
                        'menus': menus
                    }
                    return JsonResponse({
                        'code': 200,
                        'msg': '获取用户组成功',
                        'data': group_data
                    })
                except Group.DoesNotExist:
                    return JsonResponse({
                        'code': 404,
                        'msg': '用户组不存在',
                        'data': {}
                    })
            else:
                # 获取分页参数
                page = int(request.GET.get('page', 1))
                limit = int(request.GET.get('limit', 10))
                
                # 获取搜索参数
                keyword = request.GET.get('keyword', '')
                
                # 构建查询条件
                query = Q()
                if keyword:
                    query |= Q(name__icontains=keyword)
                
                # 查询用户组列表
                groups = Group.objects.filter(query).order_by('id')
                
                # 计算总数
                total = groups.count()
                
                # 分页
                start = (page - 1) * limit
                end = page * limit
                groups = groups[start:end]
                
                # 构建返回数据
                group_list = []
                for group in groups:
                    # 获取该组的菜单路径
                    group_path = GroupPath.objects.filter(group=group).first()
                    menus = group_path.path if group_path else []
                    
                    group_list.append({
                        'id': group.id,
                        'group_name': group.name,
                        'permission_count': group.permissions.count(),
                        'user_count': UserInfo.objects.filter(groups=group).count(),
                        'menus': menus
                    })
                
                return JsonResponse({
                    'code': 200,
                    'msg': '获取用户组列表成功',
                    'data': {
                        'list': group_list,
                        'total': total
                    }
                })
                
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': {}
            })
    
    @check_permission
    def post(self, request):
        """创建或更新权限组路径"""
        try:
            data = json.loads(request.body)
            group_name = data.get('group_name')
            group_menu = data.get('group_menu')

            if not group_name or not group_menu:
                return JsonResponse({
                    'code': 400,
                    'msg': '参数错误',
                    'data': None
                })

            # 获取或创建权限组
            group, created = Group.objects.get_or_create(name=group_name)
            
            # 更新或创建权限组路径
            group_path, created = GroupPath.objects.update_or_create(
                group=group,
                defaults={'path': group_menu}
            )

            return JsonResponse({
                'code': 200,
                'msg': '保存成功',
                'data': {
                    'group_id': group.id,
                    'group_name': group.name,
                    'path': group_path.path
                }
            })
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'保存失败：{str(e)}',
                'data': None
            })
    
    @check_permission
    def put(self, request):
        """编辑用户组"""
        try:
            data = json.loads(request.body)
            group_id = data.get('id')
            group_name = data.get('group_name')
            group_menu = data.get('group_menu')
            
            if not group_id or not group_name or not group_menu:
                return JsonResponse({
                    'code': 400,
                    'msg': '参数错误',
                    'data': None
                })
            
            # 获取用户组
            try:
                group = Group.objects.get(id=group_id)
            except Group.DoesNotExist:
                return JsonResponse({
                    'code': 404,
                    'msg': '用户组不存在',
                    'data': None
                })
            
            # 检查名称是否已存在（排除自身）
            if group_name != group.name and Group.objects.filter(name=group_name).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': '用户组名称已存在',
                    'data': None
                })
            
            # 更新用户组信息
            group.name = group_name
            group.save()
            
            # 更新菜单权限
            group_path, created = GroupPath.objects.update_or_create(
                group=group,
                defaults={'path': group_menu}
            )
            
            return JsonResponse({
                'code': 200,
                'msg': '更新成功',
                'data': {
                    'group_id': group.id,
                    'group_name': group.name,
                    'path': group_path.path
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'更新失败：{str(e)}',
                'data': None
            })
    @check_permission
    def delete(self, request):
        """删除用户组"""
        try:
            ids = request.GET.getlist('id[]')
            group_ids = list(map(int, ids))

            if not group_ids:
                return JsonResponse({
                    'code': 400,
                    'msg': '用户组ID不能为空',
                    'data': None
                })
            
            # 批量删除用户组
            deleted_groups = Group.objects.filter(id__in=group_ids)
            deleted_count = deleted_groups.count()
            
            # 删除关联的菜单路径
            GroupPath.objects.filter(group__in=deleted_groups).delete()
            # 删除用户组
            deleted_groups.delete()
            
            return JsonResponse({
                'code': 200,
                'msg': f'成功删除{deleted_count}个用户组',
                'data': None
            })
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'删除失败：{str(e)}',
                'data': None
            })