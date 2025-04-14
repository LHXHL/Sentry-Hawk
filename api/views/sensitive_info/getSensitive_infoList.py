from django.http import JsonResponse
from django.views import View
from app.models import Wih_result, Asset_info, Projects
from django import forms
from api.views.login import clean_form
from api.serializers import Wih_resultSerializer
from django.core.paginator import Paginator

# 基础查询
class BaseWihResultForm(forms.Form):
    projectId = forms.CharField(required=False)
    type = forms.CharField(required=False)
    content = forms.CharField(required=False)
    target_id = forms.CharField(required=False)
    pageNum = forms.IntegerField(error_messages={'required': '请选择对应的页面'}, required=True)
    pageSize = forms.IntegerField(error_messages={'required': '请选择对应的页面大小'}, required=True)

    def clean_projectId(self):
        project_id = self.cleaned_data['projectId']
        if project_id:
            try:
                if project_id.startswith('[') and project_id.endswith(']'):
                    project_ids = [int(pid.strip()) for pid in project_id[1:-1].split(',')]
                    return project_ids[0] if len(project_ids) == 1 else project_ids
                return int(project_id)
            except (ValueError, IndexError):
                raise forms.ValidationError('项目ID格式错误')
        return project_id

class getSensitive_infoList(View):
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
        data = request.POST
        if not data and request.body:
            import json
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                res['msg'] = "无效的JSON数据"
                return JsonResponse(res)

        # 修改这里：使用 BaseWihResultForm 替代 WihResultForm
        form = BaseWihResultForm(data)
        
        if not form.is_valid():
            res['msg'] = clean_form(form)
            return JsonResponse(res)

        filter_kwargs = {}
        
        # 非管理员只能查看自己项目的敏感信息
        if not request.user.is_superuser:
            user_projects = Projects.objects.filter(project_user=request.user.nid).values_list('id', flat=True)
            filter_kwargs['target__asset_project__in'] = user_projects

        if form.cleaned_data['projectId']:
            project_id = form.cleaned_data['projectId']
            if not request.user.is_superuser:
                if isinstance(project_id, list):
                    if not all(pid in user_projects for pid in project_id):
                        return JsonResponse({
                            'code': 403,
                            'msg': '无权访问该项目的敏感信息',
                            'data': {}
                        })
                elif project_id not in user_projects:
                    return JsonResponse({
                        'code': 403,
                        'msg': '无权访问该项目的敏感信息',
                        'data': {}
                    })
            filter_kwargs['target__asset_project'] = project_id

        if form.cleaned_data['type']:
            filter_kwargs['type__icontains'] = form.cleaned_data['type']
        if form.cleaned_data['content']:
            filter_kwargs['content__icontains'] = form.cleaned_data['content']
        if form.cleaned_data['target_id']:
            # 验证用户是否有权限访问此目标
            target = Asset_info.objects.filter(asset_id=form.cleaned_data['target_id']).first()
            if target and not request.user.is_superuser:
                if target.asset_project_id not in user_projects:
                    return JsonResponse({
                        'code': 403,
                        'msg': '无权访问该目标的敏感信息',
                        'data': {}
                    })
            filter_kwargs['target_id'] = form.cleaned_data['target_id']

        # 简化查询逻辑，移除重复查询
        contact_list = Wih_result.objects.filter(**filter_kwargs).order_by('id')

        if filter_kwargs:
            contact_list = Wih_result.objects.filter(**filter_kwargs).order_by('id')
        else:
            contact_list = Wih_result.objects.all().order_by('id')

        page_size = form.cleaned_data['pageSize']
        paginator = Paginator(contact_list, page_size)  # Show 25 contacts per page.
        page_number = form.cleaned_data['pageNum']
        page_obj = paginator.get_page(page_number)
        wih_result_list = Wih_resultSerializer(instance=page_obj, many=True).data
        
        # 添加目标资产信息
        for item in wih_result_list:
            target_info = Asset_info.objects.filter(asset_id=item['target_id']).first()
            if target_info:
                item['target'] = target_info.asset
            else:
                item['target'] = None

        res['data']['list'] = wih_result_list
        res['data']['pageSize'] = page_obj.paginator.num_pages
        res['data']['pageNum'] = page_obj.number
        res['data']['total'] = page_obj.paginator.count
        res['code'] = 200
        return JsonResponse(res, safe=False, json_dumps_params={'ensure_ascii': False})
