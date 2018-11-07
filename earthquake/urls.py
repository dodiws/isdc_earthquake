from .views import (
    EarthQuakeStatisticResource,
    getEQEvents,
)
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(EarthQuakeStatisticResource())
geoapi.register(getEQEvents())

urlpatterns_getoverviewmaps = patterns(
    'earthquake.views',
    url(r'^earthquakeinfo$', 'getEarthquakeInfoVillages', name='getEarthquakeInfoVillages'),
)

urlpatterns = [
    # api
    url(r'', include(geoapi.urls)),

    url(r'^getOverviewMaps/', include(urlpatterns_getoverviewmaps)),
]
