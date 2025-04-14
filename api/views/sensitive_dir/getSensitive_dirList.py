from django.http import JsonResponse
from django.views import View
from app.models import Sensitive_dir, Asset_info, Projects
from django import forms
from api.views.login import clean_form
from api.serializers import Sensitive_dirSerializer
from django.core.paginator import Paginator


# 基础漏洞查询
class BaseSensitive_dirForm(forms.Form):
    projectId = forms.CharField(required=False)
    info = forms.CharField(required=False)
    target_id = forms.CharField(required=False)
    pageNum = forms.IntegerField(error_messages={'required': '请选择对应的页面'}, required=True)
    pageSize = forms.IntegerField(error_messages={'required': '请选择对应的页面大小'}, required=True)

    def clean_projectId(self):
        project_id = self.cleaned_data['projectId']
        if project_id:
            try:
                # Handle both single ID and list of IDs
                if project_id.startswith('[') and project_id.endswith(']'):
                    # Convert string representation of list to actual list of integers
                    project_ids = [int(pid.strip()) for pid in project_id[1:-1].split(',')]
                    return project_ids[0] if len(project_ids) == 1 else project_ids
                return int(project_id)
            except (ValueError, IndexError):
                raise forms.ValidationError('Invalid project ID format')
        return project_id


# 漏洞查询数据清洗
class Sensitive_dirForm(BaseSensitive_dirForm):
    pass


# 漏洞查询视图
class getSensitive_dirList(View):
    def post(self, request):
        res = {
            'code': 500,
            'data': {
                'list': [],
                'pageSize': '',
                'pageNum': '',
                'total': ''
            },
        }
        # 处理请求数据
        data = request.POST
        if not data and request.body:
            import json
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                res['msg'] = "无效的JSON数据"
                return JsonResponse(res)

        form = Sensitive_dirForm(data)
        if not form.is_valid():
            res['msg'] = clean_form(form)
            return JsonResponse(res)

        filter_kwargs = {}
        
        # 非管理员只能查看自己项目的敏感目录
        if not request.user.is_superuser:
            user_projects = Projects.objects.filter(project_user=request.user.nid).values_list('id', flat=True)
            filter_kwargs['project__in'] = user_projects

        if form.cleaned_data['projectId']:
            project_id = form.cleaned_data['projectId']
            # 验证用户是否有权限访问此项目
            if not request.user.is_superuser:
                if isinstance(project_id, list):
                    if not all(pid in user_projects for pid in project_id):
                        return JsonResponse({
                            'code': 403,
                            'msg': '无权访问该项目的敏感目录信息',
                            'data': {}
                        })
                elif project_id not in user_projects:
                    return JsonResponse({
                        'code': 403,
                        'msg': '无权访问该项目的敏感目录信息',
                        'data': {}
                    })
            filter_kwargs['project'] = project_id
            
        if form.cleaned_data['info']:
            filter_kwargs['info__icontains'] = form.cleaned_data['info']
            
        if form.cleaned_data['target_id']:
            # 验证用户是否有权限访问此目标
            target = Asset_info.objects.filter(asset_id=form.cleaned_data['target_id']).first()
            if target and not request.user.is_superuser:
                if target.asset_project_id not in user_projects:
                    return JsonResponse({
                        'code': 403,
                        'msg': '无权访问该目标的敏感目录信息',
                        'data': {}
                    })
            filter_kwargs['target_id'] = form.cleaned_data['target_id']

        contact_list = Sensitive_dir.objects.filter(**filter_kwargs).order_by('id')

        page_size = form.cleaned_data['pageSize']
        paginator = Paginator(contact_list, page_size)
        page_number = form.cleaned_data['pageNum']
        page_obj = paginator.get_page(page_number)
        sensitive_dir_list = Sensitive_dirSerializer(instance=page_obj, many=True).data
        res['data']['list'] = sensitive_dir_list
        res['data']['pageSize'] = page_obj.paginator.num_pages
        res['data']['pageNum'] = page_obj.number
        res['data']['total'] = page_obj.paginator.count
        res['code'] = 200
        return JsonResponse(res, safe=False, json_dumps_params={'ensure_ascii': False})
