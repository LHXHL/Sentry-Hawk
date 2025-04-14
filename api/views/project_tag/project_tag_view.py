from django.http import JsonResponse
from django.views import View
from app.models import Tags
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
import json

@method_decorator(csrf_exempt, name='dispatch')
class ProjectTagView(View):
    def get(self, request):
        """获取项目类型列表"""
        try:
            # 获取查询参数
            tag_id = request.GET.get('id')
            keyword = request.GET.get('keyword', '')
            
            if tag_id:
                # 获取单个标签详情
                tag = Tags.objects.filter(id=tag_id).values('id', 'name').first()
                if not tag:
                    return JsonResponse({
                        'code': 404,
                        'msg': '标签不存在',
                        'data': {}
                    })
                return JsonResponse({
                    'code': 200,
                    'msg': '获取标签成功',
                    'data': tag
                })
            
            # 构建查询条件
            query = Q()
            if keyword:
                query |= Q(name__icontains=keyword)
            
            tags = Tags.objects.filter(query).values('id', 'name')
            return JsonResponse({
                'code': 200,
                'msg': '获取项目类型成功',
                'data': list(tags)
            })
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': []
            })

    def post(self, request):
        """添加新的项目类型"""
        try:
            data = json.loads(request.body)
            name = data.get('name')
            
            if not name:
                return JsonResponse({
                    'code': 400,
                    'msg': '项目类型名称不能为空',
                    'data': {}
                })
            
            # 检查是否已存在
            if Tags.objects.filter(name=name).exists():
                tag = Tags.objects.filter(name=name).first()
                return JsonResponse({
                    'code': 200,
                    'msg': '项目类型已存在',
                    'data': {
                        'id': tag.id,
                        'name': tag.name
                    }
                })
            
            # 获取最大ID值
            max_id = Tags.objects.all().order_by('-id').first()
            next_id = (max_id.id + 1) if max_id else 1
            
            # 创建新类型
            new_tag = Tags.objects.create(
                id=next_id,
                name=name
            )
            
            return JsonResponse({
                'code': 200,
                'msg': '添加项目类型成功',
                'data': {
                    'id': new_tag.id,
                    'name': new_tag.name
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': {}
            })

    def put(self, request):
        """修改项目类型"""
        try:
            data = json.loads(request.body)
            tag_id = data.get('id')
            name = data.get('name')
            
            if not tag_id or not name:
                return JsonResponse({
                    'code': 400,
                    'msg': '参数错误',
                    'data': {}
                })
            
            # 检查标签是否存在
            tag = Tags.objects.filter(id=tag_id).first()
            if not tag:
                return JsonResponse({
                    'code': 404,
                    'msg': '标签不存在',
                    'data': {}
                })
            
            # 检查新名称是否与其他标签重复
            if Tags.objects.filter(name=name).exclude(id=tag_id).exists():
                return JsonResponse({
                    'code': 400,
                    'msg': '项目类型名称已存在',
                    'data': {}
                })
            
            # 更新标签
            tag.name = name
            tag.save()
            
            return JsonResponse({
                'code': 200,
                'msg': '修改项目类型成功',
                'data': {
                    'id': tag.id,
                    'name': tag.name
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': {}
            })

    def delete(self, request):
        """删除项目类型"""
        try:
            data = json.loads(request.body)
            tag_id = data.get('id')
            
            if not tag_id:
                return JsonResponse({
                    'code': 400,
                    'msg': '参数错误',
                    'data': {}
                })
            
            # 检查标签是否存在
            tag = Tags.objects.filter(id=tag_id).first()
            if not tag:
                return JsonResponse({
                    'code': 404,
                    'msg': '标签不存在',
                    'data': {}
                })
            
            # 删除标签
            tag.delete()
            
            return JsonResponse({
                'code': 200,
                'msg': '删除项目类型成功',
                'data': {}
            })
            
        except Exception as e:
            return JsonResponse({
                'code': 500,
                'msg': f'服务器错误: {str(e)}',
                'data': {}
            })