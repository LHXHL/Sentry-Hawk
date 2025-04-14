from django.http import JsonResponse
from django.views import View
from app.models import UserInfo, GroupPath
import json
import os

class getAuthMenuList(View):
    def get(self, request):
        # 假设我们从请求中获取当前用户的身份
        user = request.user.username  # 例如，如果你使用的是Django的认证系统

        if user == 'admin':
            file_path = 'api/menu_static/admin_authMenuList.json'
        else:
            try:
                # 获取用户信息
                user_info = UserInfo.objects.get(username=user)
                if not user_info.user_group:
                    return JsonResponse({
                        'code': 403,
                        'msg': '用户未分配权限组',
                        'data': {},
                    })
                
                # 获取用户组对应的菜单
                group_path = GroupPath.objects.filter(group=user_info.user_group.id).first()
                if not group_path or not group_path.path:
                    return JsonResponse({
                        'code': 403,
                        'msg': '用户组未配置菜单权限',
                        'data': {},
                    })
                
                # 读取完整菜单配置
                try:
                    with open('api/menu_static/admin_authMenuList.json', 'r', encoding='utf-8') as file:
                        full_menu = json.load(file)
                        
                    # 过滤菜单
                    def filter_menu(menu_list, allowed_paths):
                        filtered = []
                        for item in menu_list:
                            if item['path'] in allowed_paths:
                                new_item = item.copy()
                                if 'children' in item:
                                    new_item['children'] = filter_menu(item['children'], allowed_paths)
                                filtered.append(new_item)
                            elif 'children' in item:
                                new_item = item.copy()
                                new_item['children'] = filter_menu(item['children'], allowed_paths)
                                if new_item['children']:
                                    filtered.append(new_item)
                        return filtered

                    filtered_menu = filter_menu(full_menu['data'], group_path.path)
                    
                    return JsonResponse({
                        'code': 200,
                        'msg': '成功',
                        'data': filtered_menu
                    })
                    
                except (FileNotFoundError, json.JSONDecodeError):
                    return JsonResponse({
                        'code': 500,
                        'msg': '菜单配置文件异常',
                        'data': {}
                    })
            except UserInfo.DoesNotExist:
                return JsonResponse({
                    'code': 401,
                    'msg': '用户不存在',
                    'data': {},
                })
            except Exception as e:
                return JsonResponse({
                    'code': 500,
                    'msg': f'获取权限失败：{str(e)}',
                    'data': {},
                })

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                menu_data = json.load(file)
                return JsonResponse(menu_data)  # 返回JsonResponse对象
        except FileNotFoundError:
            # 如果文件不存在，返回错误信息
            res = {
                'code': 500,
                'msg': '菜单文件未找到',
                'data': {},
            }
            return JsonResponse(res)
        except json.JSONDecodeError:
            # 如果JSON格式不正确，返回错误信息
            res = {
                'code': 500,
                'msg': '菜单文件格式错误',
                'data': {},
            }
            return JsonResponse(res)
