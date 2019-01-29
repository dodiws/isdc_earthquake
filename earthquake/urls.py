from earthquake.views import EarthquakeStatisticResource, EarthquakeInfoVillages, getEQEvents
from django.conf.urls import include, patterns, url
from tastypie.api import Api

geoapi = Api(api_name='geoapi')

geoapi.register(EarthquakeStatisticResource())
geoapi.register(getEQEvents())

# this var will be imported by geonode.urls and registered by getoverviewmaps api
GETOVERVIEWMAPS_APIOBJ = [
    EarthquakeInfoVillages(),
]

urlpatterns = [
    url(r'', include(geoapi.urls)),
    url(r'^getOverviewMaps/', include(patterns(
        'earthquake.views',
        url(r'^earthquakeinfo$', 'getEarthquakeInfoVillages', name='getEarthquakeInfoVillages'),
    ))),
]
