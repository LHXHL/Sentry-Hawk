from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views import View
from app.models import Projects, Tags, UserInfo
from django import forms
from api.views.login import clean_form

class BaseProjectForm(forms.Form):
    id = forms.IntegerField(error_messages={'required': '请输入要修改的项目'}, required=True)
    project_name = forms.CharField(error_messages={'required': '请输入要添加的单位'}, required=True)
    project_tag = forms.CharField(error_messages={'required': '请选择项目类型'}, required=True)
    project_user = forms.CharField(error_messages={'required': '请选择项目负责人'}, required=True)

# 资产查询数据清洗
class projectForm(BaseProjectForm):
    def clean_project_name(self):
        project_name = self.cleaned_data['project_name']
        project_id = self.cleaned_data.get('id')
        project_tag = self.data.get('project_tag')
        project_user = self.data.get('project_user')
        
        tag = Tags.objects.get(name=project_tag)
        print(tag.id)
        # 检查是否存在相同配置但ID不同的项目
        if Projects.objects.filter(
            name=project_name,
            tag=tag.id,
            project_user=project_user
        ).exclude(id=project_id).exists():
            raise forms.ValidationError('没有修改，请重新输入')
        return project_name

    def clean_project_tag(self):
        project_tag = self.cleaned_data['project_tag']
        if Tags.objects.filter(name=project_tag).exists():
            return project_tag
        else:
            Tags.objects.create(name=project_tag)
            return project_tag

# 资产添加视图
class editProject(View):
    def post(self, request):
        res = {
            'code': 500,
            'msg': "添加成功",
            'self': None,
        }
        data = request.data
        if not data.get('asset_type'):
            data['asset_type'] = ''
        form = projectForm(data)
        if not form.is_valid():
            res['self'],res['msg'] = clean_form(form)
            return JsonResponse(res)
        tag_instance = Tags.objects.get(name=form.cleaned_data['project_tag'])
        user = UserInfo.objects.get(nid=form.cleaned_data['project_user'])
        Projects.objects.filter(id=form.cleaned_data['id']).update(name=form.cleaned_data['project_name'], tag=tag_instance,project_user=user)
        res['self'] = form.cleaned_data
        res['msg'] = '修改成功'
        res['code'] = 200
        return JsonResponse(res, safe=False, json_dumps_params={'ensure_ascii': False})
