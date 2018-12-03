from earthquake.views import EarthquakeStatisticResource
from earthquake.views import getEQEvents
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(EarthquakeStatisticResource())
geoapi.register(getEQEvents())

urlpatterns_getoverviewmaps = patterns(
    'earthquake.views',
    url(r'^earthquakeinfo$', 'getEarthquakeInfoVillages', name='getEarthquakeInfoVillages'),
)

urlpatterns = [
    url(r'', include(geoapi.urls)),
    url(r'^getOverviewMaps/', include(urlpatterns_getoverviewmaps)),
]
