from annoying.functions import get_object_or_None
from tastypie.exceptions import NotFound
from tastypie.resources import ModelResource

from models import Organization
from kalite.shared.api_auth.auth import ObjectAdminAuthorization, UserObjectsOnlyAuthorization
from securesync.models import Zone

class ZoneResource(ModelResource):
    class Meta:
        queryset = Zone.objects.all()
        resource_name = 'zone'
        authorization = ObjectAdminAuthorization()

    def obj_get_list(self, bundle, **kwargs):
        # Filter by zone objects by org ID
        org_id = bundle.request.GET.get('org_id')
        if org_id:
            org_obj = get_object_or_None(Organization, id=org_id)
            if not org_obj:
                raise NotFound("Organization not found")
            else:
                zone_list = org_obj.get_zones()
        else:
            zone_list = Zone.objects.all()

        # call super to trigger auth
        return super(ZoneResource, self).authorized_read_list(zone_list, bundle)