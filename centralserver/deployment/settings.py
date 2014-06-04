########################
# Django dependencies
########################

INSTALLED_APPS = (
    'securesync',  # DeviceZone model for queries
    'kalite.facility',  # Facility model for queries
    'kalite.control_panel',  # Links from deployments CMS into control_panel
    'centralserver.central',  # Organization model
)
