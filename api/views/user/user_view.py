from django.http import JsonResponse
from django.views import View
from app.models import UserInfo,Group
from django.db.models import Q
import json
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.hashers import make_password
import re
from django.contrib.auth.models import Group

@method_decorator(csrf_exempt, name='dispatch')
class UserView(View):
    """
    用户管理视图
    提供用户的增删改查功能
    """
    
    def get(self, request):
        """获取用户列表或详情"""
        try:
            # 获取当前用户
            #user_id = request.session.get('user_id')
            #if not user_id:
            #    return JsonResponse({
            #        'code': 401,
            #        'msg': '用户未登录',
            #        'data': {}
            #    })
            
            # 获取查询参数
            user_id_param = request.GET.get('id')
            
            if user_id_param:
                # 获取指定ID的用户
                try:
                    user = UserInfo.objects.get(nid=user_id_param)
                    user_data = {
                        'id': user.nid,
                        'username': user.username,
                        'user_group': user.user_group,
                        'email': user.email,
                        'phone_num': user.phone_num,
                        'is_active': user.is_active,
                        'is_superuser': user.is_superuser,
                        'last_login': user.last_login,
                        'date_joined': user.date_joined,
                        'ip': user.ip,
                        'addr': user.addr
                    }
                    return JsonResponse({
                        'code': 200,
                        'msg': '获取用户成功',
                        'data': user_data
                    })
                except UserInfo.DoesNotExist:
                    return JsonResponse({
                        'code': 404,
                        'msg': '用户不存在',
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
                    query |= Q(username__icontains=keyword)
                    query |= Q(user_group__icontains=keyword)
                    query |= Q(email__icontains=keyword)
                
                # 查询用户列表
                # users = UserInfo.objects.prefetch_related('groups').all()
                users = UserInfo.objects.prefetch_related('groups').filter(query).order_by('-date_joined')
                
                # 计算总数
                total = users.count()
                
                # 分页
                start = (page - 1) * limit
                end = page * limit
                users = users[start:end]
                
                
                
                # 构建返回数据
                user_list = []
                for user in users:
                    group_names = [group.name for group in user.groups.all()]
                    user_group = group_names[0] if len(group_names) > 0 else ""
                    # print("user", group_names)
                    user_list.append({
                        'id': user.nid,
                        'username': user.username,
                        'user_group': user_group,
                        'email': user.email,
                        'phone_num': user.phone_num,
                        'is_active': user.is_active,
                        # 'is_superuser': user.is_superuser,
                        #'last_login': user.last_login,
                        #'date_joined': user.date_joined
                    })
                
                return JsonResponse({
                    'code': 200,
                    'msg': '获取用户列表成功',
                    'data': {
                        'list': user_list,
                        'total': total
                    }
                })
                
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': {}
            })
    
    def post(self, request):
        """添加用户"""
        try:
            # 获取当前用户
            # user_id = request.session.get('user_id')
            #if not user_id:
            #    return JsonResponse({
            #        'code': 401,
            #        'msg': '用户未登录',
            #        'data': {}
            #    })
            
            # 检查用户权限
            #current_user = UserInfo.objects.get(nid=user_id)
            #if not current_user.is_superuser:
            #    return JsonResponse({
            #        'code': 403,
            #        'msg': '权限不足',
            #        'data': {}
            #    })
            
            # 解析请求数据
            data = json.loads(request.body)
            username = data.get('username')
            password = data.get('password')
            user_group = data.get('user_group')
            email = data.get('email')
            phone_num = data.get('phone_num')
            is_active = data.get('is_active', True)
            is_superuser = data.get('is_superuser', False)
            
            # 验证必填字段
            if not username or not password:
                return JsonResponse({
                    'code': 400,
                    'msg': '用户名和密码不能为空',
                    'data': {}
                })
            
            # 验证用户名格式
            if not re.match(r'^[a-zA-Z0-9_]{4,16}$', username):
                return JsonResponse({
                    'code': 400,
                    'msg': '用户名只能包含字母、数字和下划线，长度为4-16位',
                    'data': {}
                })
            
            # 验证密码强度
            if len(password) < 8:
                return JsonResponse({
                    'code': 400,
                    'msg': '密码长度不能少于8位',
                    'data': {}
                })
            
            # 验证邮箱格式
            if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return JsonResponse({
                    'code': 400,
                    'msg': '邮箱格式不正确',
                    'data': {}
                })
            
            # 验证手机号格式
            if phone_num and not re.match(r'^1[3-9]\d{9}$', str(phone_num)):
                return JsonResponse({
                    'code': 400,
                    'msg': '手机号格式不正确',
                    'data': {}
                })
            
            # 检查用户名是否已存在
            if UserInfo.objects.filter(username=username).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': '用户名已存在',
                    'data': {}
                })
            
            # 检查邮箱是否已存在
            if email and UserInfo.objects.filter(email=email).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': '邮箱已存在',
                    'data': {}
                })
            
            # 检查手机号是否已存在
            if phone_num and UserInfo.objects.filter(phone_num=phone_num).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': '手机号已存在',
                    'data': {}
                })
            
            # 创建用户
            
            group, created = Group.objects.get_or_create(name=user_group)
            user = UserInfo.objects.create_user(username=username, password=password, email=email,phone_num=phone_num, is_active=is_active, is_superuser=is_superuser,user_group=group)
            user.groups.add(group)
            user.save()
            return JsonResponse({
                'code': 200,
                'msg': '添加用户成功',
                'data': {'id': user.nid}
            })
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': {}
            })
    
    def put(self, request):
        """编辑用户"""
        try:
            # 解析请求数据
            data = json.loads(request.body)
            user_id_param = data.get('id')
            user_group = data.get('user_group')
            email = data.get('email')
            phone_num = data.get('phone_num')
            is_active = data.get('is_active')
            is_superuser = data.get('is_superuser')
            password = data.get('password')
            
            # 验证必填字段
            if not user_id_param:
                return JsonResponse({
                    'code': 400,
                    'msg': '用户ID不能为空',
                    'data': {}
                })
            
            # 获取用户
            try:
                user = UserInfo.objects.get(nid=user_id_param)
            except UserInfo.DoesNotExist:
                return JsonResponse({
                    'code': 404,
                    'msg': '用户不存在',
                    'data': {}
                })
            
            # 验证邮箱格式
            if email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
                return JsonResponse({
                    'code': 400,
                    'msg': '邮箱格式不正确',
                    'data': {}
                })
            
            # 验证手机号格式
            if phone_num and not re.match(r'^1[3-9]\d{9}$', str(phone_num)):
                return JsonResponse({
                    'code': 400,
                    'msg': '手机号格式不正确',
                    'data': {}
                })
            
            # 检查邮箱是否已存在（排除自身）
            if email and email != user.email and UserInfo.objects.filter(email=email).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': '邮箱已存在',
                    'data': {}
                })
            
            # 检查手机号是否已存在（排除自身）
            if phone_num and str(phone_num) != str(user.phone_num) and UserInfo.objects.filter(phone_num=phone_num).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': '手机号已存在',
                    'data': {}
                })
            


            # 更新用户信息
            if user_group is not None:
                user.user_group = Group.objects.get(name=user_group)
            if email is not None:
                user.email = email
            if phone_num is not None:
                user.phone_num = phone_num
            if is_active is not None:
                user.is_active = is_active
            if is_superuser is not None:
                user.is_superuser = is_superuser
            
            # 更新用户组
            if user_group:
                user.groups.clear()
                group, created = Group.objects.get_or_create(name=user_group)
                user.groups.add(group)

            # 如果提供了新密码，则更新密码
            if password:
                if len(password) < 8:
                    return JsonResponse({
                        'code': 400,
                        'msg': '密码长度不能少于8位',
                        'data': {}
                    })
                user.password = make_password(password)
            print("user", user.user_group)
            user.save()
            
            return JsonResponse({
                'code': 200,
                'msg': '更新用户成功',
                'data': {}
            })
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': {}
            })
    
    def delete(self, request):
        """删除用户"""
        try:
            ids = request.GET.getlist('id[]')
            user_ids = list(map(int, ids))

            if not user_ids:
                return JsonResponse({
                    'code': 400,
                    'msg': '用户ID不能为空',
                    'data': {}
                })
            
            # # 防止删除自己
            # if user_id in user_ids:
            #     return JsonResponse({
            #         'code': 400,
            #         'msg': '不能删除当前登录用户',
            #         'data': {}
            #     })
            
            # 批量删除用户
            deleted_users = UserInfo.objects.filter(nid__in=user_ids)
            deleted_count = deleted_users.count()
            deleted_users.delete()
            
            return JsonResponse({
                'code': 200,
                'msg': f'成功删除{deleted_count}个用户',
                'data': {}
            })
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': {}
            })
