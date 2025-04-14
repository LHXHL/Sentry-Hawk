from django.http import JsonResponse
from django.views import View
from app.models import Projects, Tags
from api.serializers import ProjectsSerializer, TagsSerializer

class getAssetOrganization(View):
    def get(self, request):
        res = {
            'code': 200,
            'data': [],
        }
        tags = Tags.objects.all().order_by('id')
        tags_data = TagsSerializer(instance=tags, many=True).data
        
        for tag in tags_data:
            tag_id = tag['id']
            # 根据用户权限过滤项目
            if request.user.is_superuser:
                Organization = Projects.objects.filter(tag=tag_id).order_by('id')
            else:
                Organization = Projects.objects.filter(
                    tag=tag_id,
                    project_user=request.user.nid
                ).order_by('id')
                
            AssetOrganization_info = ProjectsSerializer(instance=Organization, many=True).data
            if AssetOrganization_info:  # 只添加有权限查看的项目的标签
                tag['children'] = AssetOrganization_info
                res['data'].append(tag)
                
        return JsonResponse(res, safe=False, json_dumps_params={'ensure_ascii': False})
