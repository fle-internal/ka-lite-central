from django.conf import settings

from kalite.dynamic_assets import DynamicSettingsBase, fields


class DynamicSettings(DynamicSettingsBase):
    is_config_package_nalanda = fields.BooleanField(default=False)


def modify_dynamic_settings(ds, request=None, user=None):

    user = user or request.user

    if user:
        # Some coach reports are only meaningful for Nalanda, so we hide them unless the user is part of the "Nalanda" org
        ds["ab_testing"].is_config_package_nalanda = user.is_authenticated() and any(["Nalanda" in org.name for org in user.organization_set.all()])