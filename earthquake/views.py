from geodb.models import (
	# AfgFldzonea100KRiskLandcoverPop,
	AfgLndcrva,
	AfgAdmbndaAdm1,
	AfgAdmbndaAdm2,
	# AfgFldzonea100KRiskMitigatedAreas,
	# AfgAvsa,
	Forcastedvalue,
	AfgShedaLvl4,
	districtsummary,
	provincesummary,
	basinsummary,
	AfgPpla,
	tempCurrentSC,
	# earthquake_events,
	# earthquake_shakemap,
	# villagesummaryEQ,
	AfgPplp,
	# AfgSnowaAverageExtent,
	AfgCaptPpl,
	AfgAirdrmp,
	AfgHltfac,
	forecastedLastUpdate,
	AfgCaptGmscvr,
	# AfgEqtUnkPplEqHzd,
	# Glofasintegrated,
	AfgBasinLvl4GlofasPoint,
	AfgPpltDemographics,
	AfgLspAffpplp,
	# AfgMettClim1KmChelsaBioclim,
	# AfgMettClim1KmWorldclimBioclim2050Rpc26,
	# AfgMettClim1KmWorldclimBioclim2050Rpc45,
	# AfgMettClim1KmWorldclimBioclim2050Rpc85,
	# AfgMettClim1KmWorldclimBioclim2070Rpc26,
	# AfgMettClim1KmWorldclimBioclim2070Rpc45,
	# AfgMettClim1KmWorldclimBioclim2070Rpc85,
	# AfgMettClimperc1KmChelsaPrec,
	# AfgMettClimtemp1KmChelsaTempavg,
	# AfgMettClimtemp1KmChelsaTempmax,
	# AfgMettClimtemp1KmChelsaTempmin
	)
from .models import (
	earthquake_events,
	earthquake_shakemap,
	villagesummaryEQ,
	AfgEqtUnkPplEqHzd,
	)
from geodb.geo_calc import (
	getBaseline,
	getCommonUse,
	# getFloodForecastBySource,
	# getFloodForecastMatrix,
	getGeoJson,
	# getProvinceSummary_glofas,
	getProvinceSummary,
	# getRawBaseLine,
	# getRawFloodRisk,
	# getSettlementAtFloodRisk,
	getShortCutData,
	getTotalArea,
	getTotalBuildings,
	getTotalPop,
	getTotalSettlement,
	getRiskNumber,
	)
from geodb.views import (
	get_nc_file_from_ftp,
	getCommonVillageData,
	)
from django.contrib.gis.geos import Point
from django.contrib.gis.utils import LayerMapping
from django.core.serializers.json import DjangoJSONEncoder
from django.db import connection, connections
from django.shortcuts import render
from .usgs_comcat import getContents,getUTCTimeStamp
from geodb.views import GS_TMP_DIR, gdal_path, cleantmpfile, update_progress, getKeyCustom
from geonode.utils import include_section, none_to_zero, query_to_dicts, RawSQL_nogroupby, dict_ext
from graphos.renderers import flot, gchart
from graphos.sources.simple import SimpleDataSource
from itertools import cycle, izip
from matrix.models import matrix
from tastypie import fields
from tastypie.authorization import DjangoAuthorization
from tastypie.resources import ModelResource, Resource
from tastypie.serializers import Serializer
from tempfile import mktemp
from zipfile import ZipFile
from django.shortcuts import render_to_response
from django.template import RequestContext
import csv, os
import datetime, re
import json
import subprocess
import time, sys
import urllib
import urllib2

# ISDC
from django.utils.translation import ugettext as _
from geodb.enumerations import EARTHQUAKE_TYPES, EARTHQUAKE_TYPES_ORDER
from geonode.maps.views import _resolve_map, _PERMISSION_MSG_VIEW
from tastypie.cache import SimpleCache
from urlparse import urlparse
import shutil
import urllib3
from django.conf.urls import url
from tastypie.utils import trailing_slash
from tastypie.authentication import BasicAuthentication, SessionAuthentication, OAuthAuthentication

def get_dashboard_meta():
	return {
		'pages': [
			{
				'name': 'earthquake',
				'function': dashboard_earthquake, 
				'template': 'dash_earthquake.html',
				'menutitle': 'Earthquake',
			},
		],
		'menutitle': 'Earthquake',
	}

# def getQuickOverview(request, filterLock, flag, code, includes=[], excludes=[]):
# 	response = {}
# 	response.update(getEarthquake(request, filterLock, flag, code, excludes=['getListEQ']))
# 	return response

# moved from geodb.views

def getLatestEarthQuake():
	startdate = datetime.datetime.utcnow()
	startdate = startdate - datetime.timedelta(days=30)
	contents = getContents('origin',['stationlist.txt'],bounds=[60,77,29,45], magrange=[4,9], starttime=startdate, listURL=True, getAll=True)

	for content in contents:
		point = Point(x=content['geometry']['coordinates'][0], y=content['geometry']['coordinates'][1],srid=4326)
		dateofevent = getUTCTimeStamp(content['properties']['time'])
		recordExists = earthquake_events.objects.all().filter(event_code=content['properties']['code'])
		if recordExists.count() > 0:
			c = earthquake_events(pk=recordExists[0].pk,event_code=content['properties']['code'])
			c.wkb_geometry = point
			c.title = content['properties']['title']
			c.dateofevent = dateofevent
			c.magnitude = content['properties']['mag']
			c.shakemaptimestamp = recordExists[0].shakemaptimestamp
			c.depth = content['geometry']['coordinates'][2]
			c.save()
			print 'earthqueke id ' + content['properties']['code'] + ' modified'
		else:
			c = earthquake_events(event_code=content['properties']['code'])
			c.wkb_geometry = point
			c.title = content['properties']['title']
			c.dateofevent = dateofevent
			c.magnitude = content['properties']['mag']
			c.depth = content['geometry']['coordinates'][2]
			c.save()
			print 'earthqueke id ' + content['properties']['code'] + ' added'

def getLatestShakemap(includeShakeMap=False):
	startdate = datetime.datetime.utcnow()
	startdate = startdate - datetime.timedelta(days=30)
	contents = getContents('shakemap',['shape.zip'],bounds=[60,77,29,45], magrange=[4,9], starttime=startdate, listURL=True, getAll=True)

	for content in contents:
		point = Point(x=content['geometry']['coordinates'][0], y=content['geometry']['coordinates'][1],srid=4326)
		dateofevent = getUTCTimeStamp(content['properties']['time'])
		shakemaptimestamp = content['shakemap_url'].split('/')[-3]
		recordExists = earthquake_events.objects.all().filter(event_code=content['properties']['code'])
		if recordExists.count() > 0:
			oldTimeStamp = recordExists[0].shakemaptimestamp
			c = earthquake_events(pk=recordExists[0].pk,event_code=content['properties']['code'])
			c.wkb_geometry = point
			c.title = content['properties']['title']
			c.dateofevent = dateofevent
			c.magnitude = content['properties']['mag']
			c.depth = content['geometry']['coordinates'][2]
			c.shakemaptimestamp = shakemaptimestamp
			c.save()

			filename = mktemp('.zip')

			c = urllib3.PoolManager()
			with c.request('GET', content['shakemap_url'], preload_content=False) as resp, open(filename, 'wb') as fhandle:
				shutil.copyfileobj(resp, fhandle)

			# name, hdrs = urllib.urlretrieve(content['shakemap_url'], filename)
			thefile=ZipFile(filename)
			for name in thefile.namelist():
				if name.split('.')[0]=='mi':
					outfile = open(os.path.join(GS_TMP_DIR,name), 'wb')
					outfile.write(thefile.read(name))
					outfile.close()
			thefile.close()

			# print str(oldTimeStamp) + ' - '+ str(shakemaptimestamp)

			if oldTimeStamp is None:
				oldTimeStamp = 0

			if includeShakeMap and long(oldTimeStamp) < long(shakemaptimestamp):
				mapping = {
					'wkb_geometry' : 'POLYGON',
					'grid_value':  'GRID_CODE',
				}

				# subprocess.call('%s -f "ESRI Shapefile" %s %s -overwrite -dialect sqlite -sql "select ST_union(ST_MakeValid(Geometry)),GRID_CODE from mi GROUP BY GRID_CODE"' %(os.path.join(gdal_path,'ogr2ogr'), os.path.join(GS_TMP_DIR,'mi_dissolved.shp'), os.path.join(GS_TMP_DIR,'mi.shp')),shell=True)
				subprocess.call('%s -f "ESRI Shapefile" %s %s -overwrite -dialect sqlite -sql "select ST_union(Geometry),GRID_CODE from mi GROUP BY GRID_CODE"' %(os.path.join(gdal_path,'ogr2ogr'), os.path.join(GS_TMP_DIR,'mi_dissolved.shp'), os.path.join(GS_TMP_DIR,'mi.shp')),shell=True)
				earthquake_shakemap.objects.filter(event_code=content['properties']['code']).delete()
				lm = LayerMapping(earthquake_shakemap, os.path.join(GS_TMP_DIR,'mi_dissolved.shp'), mapping)
				lm.save(verbose=True)
				earthquake_shakemap.objects.filter(event_code='').update(event_code=content['properties']['code'],shakemaptimestamp=shakemaptimestamp)

				updateEarthQuakeSummaryTable(event_code=content['properties']['code'])
			print 'earthqueke id ' + content['properties']['code'] + ' modified'
		else:
			c = earthquake_events(event_code=content['properties']['code'])
			c.wkb_geometry = point
			c.title = content['properties']['title']
			c.dateofevent = dateofevent
			c.magnitude = content['properties']['mag']
			c.depth = content['geometry']['coordinates'][2]
			c.shakemaptimestamp = shakemaptimestamp
			c.save()

			filename = mktemp('.zip')

			c = urllib3.PoolManager()
			with c.request('GET', content['shakemap_url'], preload_content=False) as resp, open(filename, 'wb') as fhandle:
				shutil.copyfileobj(resp, fhandle)

			# name, hdrs = urllib.urlretrieve(content['shakemap_url'], filename)
			thefile=ZipFile(filename)
			for name in thefile.namelist():
				if name.split('.')[0]=='mi':
					outfile = open(os.path.join(GS_TMP_DIR,name), 'wb')
					outfile.write(thefile.read(name))
					outfile.close()
			thefile.close()

			if includeShakeMap:
				mapping = {
					'wkb_geometry' : 'POLYGON',
					'grid_value':  'GRID_CODE',
				}
				# subprocess.call('%s -f "ESRI Shapefile" %s %s -overwrite -dialect sqlite -sql "select ST_union(ST_MakeValid(Geometry)),GRID_CODE from mi GROUP BY GRID_CODE"' %(os.path.join(gdal_path,'ogr2ogr'), os.path.join(GS_TMP_DIR,'mi_dissolved.shp'), os.path.join(GS_TMP_DIR,'mi.shp')),shell=True)
				subprocess.call('%s -f "ESRI Shapefile" %s %s -overwrite -dialect sqlite -sql "select ST_union(Geometry),GRID_CODE from mi GROUP BY GRID_CODE"' %(os.path.join(gdal_path,'ogr2ogr'), os.path.join(GS_TMP_DIR,'mi_dissolved.shp'), os.path.join(GS_TMP_DIR,'mi.shp')),shell=True)
				earthquake_shakemap.objects.filter(event_code=content['properties']['code']).delete()
				lm = LayerMapping(earthquake_shakemap, os.path.join(GS_TMP_DIR,'mi_dissolved.shp'), mapping)
				lm.save(verbose=True)
				earthquake_shakemap.objects.filter(event_code='').update(event_code=content['properties']['code'],shakemaptimestamp=shakemaptimestamp)

				updateEarthQuakeSummaryTable(event_code=content['properties']['code'])
			print 'earthqueke id ' + content['properties']['code'] + ' added'

	cleantmpfile('mi');

def updateEarthQuakeSummaryTable(event_code):
	# cursor = connections['geodb'].cursor()
	# cursor.execute("\
	#     select st_astext(a.wkb_geometry) as wkb_geometry, a.vuid, a.dist_code     \
	#     from afg_ppla a, earthquake_shakemap b   \
	#     where b.event_code = '"+event_code+"' and b.grid_value > 1 \
	#     and ST_Intersects(a.wkb_geometry,b.wkb_geometry)    \
	# ")
	# row = cursor.fetchall()
	# cursor.close()

	databaseFields = villagesummaryEQ._meta.get_all_field_names()
	databaseFields.remove('id')
	databaseFields.remove('district')
	databaseFields.remove('village')
	databaseFields.remove('event_code')

	print '----- Process baseline historical Statistics for EarthQuake------\n'

	cursor = connections['geodb'].cursor()

	resources = AfgAdmbndaAdm2.objects.all().order_by('dist_code')

	ppp = resources.count()
	xxx = 0
	update_progress(float(xxx/ppp), 'start', 0)

	for aoi in resources:
		start = time.time()
		# cursor.execute("\
		#     select a.vuid, b.grid_value, sum(   \
		#     case    \
		#         when ST_CoveredBy(a.wkb_geometry,b.wkb_geometry) then a.area_population \
		#         else st_area(st_intersection(a.wkb_geometry,b.wkb_geometry))/st_area(a.wkb_geometry)*a.area_population \
		#     end) as pop     \
		#     from afg_lndcrva a, earthquake_shakemap b   \
		#     where b.event_code = '"+event_code+"' and b.grid_value > 1  and a.dist_code="+str(aoi.dist_code)+"\
		#     and ST_Intersects(a.wkb_geometry,b.wkb_geometry)    \
		#     group by a.vuid, b.grid_value\
		# ")

		cursor.execute("\
			select a.vil_uid, b.grid_value, sum(a.vuid_population) as pop, sum(a.vuid_buildings) as buldings     \
			from afg_pplp a, earthquake_shakemap b   \
			where b.event_code = '"+event_code+"' and b.grid_value > 1  and a.dist_code="+str(aoi.dist_code)+"\
			and ST_Within(a.wkb_geometry,b.wkb_geometry)    \
			group by a.vil_uid, b.grid_value\
		")
		popData = cursor.fetchall()


		cursor.execute("\
			select a.vuid, a.dist_code, b.grid_value, count(*) as numbersettlements     \
			from afg_pplp a, earthquake_shakemap b   \
			where b.event_code = '"+event_code+"' and b.grid_value > 1  and a.dist_code="+str(aoi.dist_code)+" \
			and ST_Within(a.wkb_geometry,b.wkb_geometry)    \
			group by a.vuid, a.dist_code, b.grid_value\
		")
		settlementData = cursor.fetchall()
		# print popData


		riskNumber = {}


		for settlement in settlementData:

			if settlement[0] != None:


				settlementInPopData = [x for x in popData if x[0]==settlement[0]]

				temp = [x for x in settlementInPopData if x[1]==2]
				riskNumber['pop_shake_weak']= getKeyCustom(temp,2)
				riskNumber['buildings_shake_weak']= getKeyCustom(temp,3)
				temp = [x for x in settlementInPopData if x[1]==3]
				riskNumber['pop_shake_weak']= riskNumber['pop_shake_weak'] + getKeyCustom(temp,2)
				riskNumber['buildings_shake_weak']= riskNumber['buildings_shake_weak'] + getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==4]
				riskNumber['pop_shake_light']=getKeyCustom(temp,2)
				riskNumber['buildings_shake_light']=getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==5]
				riskNumber['pop_shake_moderate']=getKeyCustom(temp,2)
				riskNumber['buildings_shake_moderate']=getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==6]
				riskNumber['pop_shake_strong']=getKeyCustom(temp,2)
				riskNumber['buildings_shake_strong']=getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==7]
				riskNumber['pop_shake_verystrong']=getKeyCustom(temp,2)
				riskNumber['buildings_shake_verystrong']=getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==8]
				riskNumber['pop_shake_severe']=getKeyCustom(temp,2)
				riskNumber['buildings_shake_severe']=getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==9]
				riskNumber['pop_shake_violent']=getKeyCustom(temp,2)
				riskNumber['buildings_shake_violent']=getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==10]
				riskNumber['pop_shake_extreme']=getKeyCustom(temp,2)
				riskNumber['buildings_shake_extreme']=getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==11]
				riskNumber['pop_shake_extreme']=riskNumber['pop_shake_extreme']+getKeyCustom(temp,2)
				riskNumber['buildings_shake_extreme']=riskNumber['buildings_shake_extreme']+getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==12]
				riskNumber['pop_shake_extreme']=riskNumber['pop_shake_extreme']+getKeyCustom(temp,2)
				riskNumber['buildings_shake_extreme']=riskNumber['buildings_shake_extreme']+getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==13]
				riskNumber['pop_shake_extreme']=riskNumber['pop_shake_extreme']+getKeyCustom(temp,2)
				riskNumber['buildings_shake_extreme']=riskNumber['buildings_shake_extreme']+getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==14]
				riskNumber['pop_shake_extreme']=riskNumber['pop_shake_extreme']+getKeyCustom(temp,2)
				riskNumber['buildings_shake_extreme']=riskNumber['buildings_shake_extreme']+getKeyCustom(temp,3)

				temp = [x for x in settlementInPopData if x[1]==15]
				riskNumber['pop_shake_extreme']=riskNumber['pop_shake_extreme']+getKeyCustom(temp,2)
				riskNumber['buildings_shake_extreme']=riskNumber['buildings_shake_extreme']+getKeyCustom(temp,3)

				riskNumber['settlement_shake_weak']=0
				riskNumber['settlement_shake_light']=0
				riskNumber['settlement_shake_moderate']=0
				riskNumber['settlement_shake_strong']=0
				riskNumber['settlement_shake_verystrong']=0
				riskNumber['settlement_shake_severe']=0
				riskNumber['settlement_shake_violent']=0
				riskNumber['settlement_shake_extreme']=0

				if settlement[2] in [2,3]:
					riskNumber['settlement_shake_weak']=1
				elif settlement[2]==4:
					riskNumber['settlement_shake_light']=1
				elif settlement[2]==5:
					riskNumber['settlement_shake_moderate']=1
				elif settlement[2]==6:
					riskNumber['settlement_shake_strong']=1
				elif settlement[2]==7:
					riskNumber['settlement_shake_verystrong']=1
				elif settlement[2]==8:
					riskNumber['settlement_shake_severe']=1
				elif settlement[2]==9:
					riskNumber['settlement_shake_violent']=1
				elif settlement[2]>=10:
					riskNumber['settlement_shake_extreme']=1


				px = villagesummaryEQ.objects.filter(event_code=event_code,village=settlement[0],district=settlement[1])
				if px.count()>0:
					a = villagesummaryEQ(id=px[0].id,event_code=event_code,village=settlement[0],district=settlement[1])
				else:
					a = villagesummaryEQ(event_code=event_code,village=settlement[0],district=settlement[1])

				for i in databaseFields:
					setattr(a, i, riskNumber[i])

				a.save()
		loadingtime = time.time() - start
		xxx=xxx+1
		update_progress(float(float(xxx)/float(ppp)),  aoi.dist_code, loadingtime)
	cursor.close()
	return

def getEarthquakeInfoVillages(request):
	template = './earthquakeInfo.html'
	village = request.GET["v"]

	context_dict = getCommonVillageData(village)

	# cursor = connections['geodb'].cursor()
	# cursor.execute("\
	#     select st_astext(a.wkb_geometry) as wkb_geometry, a.vuid, a.dist_code     \
	#     from afg_ppla a, earthquake_shakemap b   \
	#     where b.event_code = '"+event_code+"' and b.grid_value > 1 \
	#     and ST_Intersects(a.wkb_geometry,b.wkb_geometry)    \
	# ")
	# row = cursor.fetchall()
	# cursor.close()

	context_dict['sic_1']=''
	context_dict['sic_2']=''
	context_dict['sic_3']=''
	context_dict['sic_4']=''
	context_dict['sic_5']=''
	context_dict['sic_6']=''
	context_dict['sic_7']=''
	context_dict['sic_8']=''

	px = AfgEqtUnkPplEqHzd.objects.all().filter(vuid=village)
	for i in px:
		if i.seismic_intensity_cat == 'II':
		   context_dict['sic_1']='X'
		if i.seismic_intensity_cat == 'III':
		   context_dict['sic_1']='X'
		if i.seismic_intensity_cat == 'IV':
		   context_dict['sic_2']='X'
		if i.seismic_intensity_cat == 'V':
		   context_dict['sic_3']='X'
		if i.seismic_intensity_cat == 'VI':
		   context_dict['sic_4']='X'
		if i.seismic_intensity_cat == 'VII':
		   context_dict['sic_5']='X'
		if i.seismic_intensity_cat == 'VIII':
		   context_dict['sic_6']='X'
		if i.seismic_intensity_cat == 'IX':
		   context_dict['sic_7']='X'
		if i.seismic_intensity_cat == 'X+':
		   context_dict['sic_8']='X'

	px = earthquake_shakemap.objects.all().filter(wkb_geometry__intersects=context_dict['position']).exclude(grid_value=1).values('event_code','grid_value')

	event_code = []
	event_mag = {}

	data = []
	for i in px:
		event_code.append(i['event_code'])
		event_mag[i['event_code']]=i['grid_value']

	px = earthquake_events.objects.all().filter(event_code__in=event_code).order_by('-dateofevent')
	for i in px:
		data.append({'date':i.dateofevent.strftime("%Y-%m-%d %H:%M") ,'magnitude':i.magnitude,'sic':event_mag[i.event_code]})

	context_dict['eq_history']=data
	# data1 = []
	# data2 = []
	# data1.append(['agg_simplified_description','area_population'])
	# data2.append(['agg_simplified_description','area_sqm'])
	# for i in px:
	#     data1.append([i['agg_simplified_description'],i['totalpop']])
	#     data2.append([i['agg_simplified_description'],round(i['totalarea']/1000000,1)])

	# context_dict['landcover_pop_chart'] = gchart.PieChart(SimpleDataSource(data=data1), html_id="pie_chart1", options={'title': _("# of Population"), 'width': 250,'height': 250, 'pieSliceText': _('percentage'),'legend': {'position': 'top', 'maxLines':3}})
	# context_dict['landcover_area_chart'] = gchart.PieChart(SimpleDataSource(data=data2), html_id="pie_chart2", options={'title': _("# of Area (KM2)"), 'width': 250,'height': 250, 'pieSliceText': _('percentage'),'legend': {'position': 'top', 'maxLines':3}})

	context_dict.pop('position')
	return render_to_response(template,
								  RequestContext(request, context_dict))

def getEarthquakeInfoVillagesCommon(village):
	# template = './earthquakeInfo.html'
	# village = request.GET["v"]

	context_dict = getCommonVillageData(village)

	# cursor = connections['geodb'].cursor()
	# cursor.execute("\
	#     select st_astext(a.wkb_geometry) as wkb_geometry, a.vuid, a.dist_code     \
	#     from afg_ppla a, earthquake_shakemap b   \
	#     where b.event_code = '"+event_code+"' and b.grid_value > 1 \
	#     and ST_Intersects(a.wkb_geometry,b.wkb_geometry)    \
	# ")
	# row = cursor.fetchall()
	# cursor.close()

	context_dict['sic_1']=''
	context_dict['sic_2']=''
	context_dict['sic_3']=''
	context_dict['sic_4']=''
	context_dict['sic_5']=''
	context_dict['sic_6']=''
	context_dict['sic_7']=''
	context_dict['sic_8']=''

	px = AfgEqtUnkPplEqHzd.objects.all().filter(vuid=village)
	for i in px:
		if i.seismic_intensity_cat == 'II':
		   context_dict['sic_1']='X'
		if i.seismic_intensity_cat == 'III':
		   context_dict['sic_1']='X'
		if i.seismic_intensity_cat == 'IV':
		   context_dict['sic_2']='X'
		if i.seismic_intensity_cat == 'V':
		   context_dict['sic_3']='X'
		if i.seismic_intensity_cat == 'VI':
		   context_dict['sic_4']='X'
		if i.seismic_intensity_cat == 'VII':
		   context_dict['sic_5']='X'
		if i.seismic_intensity_cat == 'VIII':
		   context_dict['sic_6']='X'
		if i.seismic_intensity_cat == 'IX':
		   context_dict['sic_7']='X'
		if i.seismic_intensity_cat == 'X+':
		   context_dict['sic_8']='X'

	px = earthquake_shakemap.objects.all().filter(wkb_geometry__intersects=context_dict['position']).exclude(grid_value=1).values('event_code','grid_value')

	event_code = []
	event_mag = {}

	data = []
	for i in px:
		event_code.append(i['event_code'])
		event_mag[i['event_code']]=i['grid_value']

	px = earthquake_events.objects.all().filter(event_code__in=event_code).order_by('-dateofevent')
	for i in px:
		data.append({'date':i.dateofevent.strftime("%Y-%m-%d %H:%M") ,'magnitude':i.magnitude,'sic':event_mag[i.event_code]})

	context_dict['eq_history']=data
	# data1 = []
	# data2 = []
	# data1.append(['agg_simplified_description','area_population'])
	# data2.append(['agg_simplified_description','area_sqm'])
	# for i in px:
	#     data1.append([i['agg_simplified_description'],i['totalpop']])
	#     data2.append([i['agg_simplified_description'],round(i['totalarea']/1000000,1)])

	# context_dict['landcover_pop_chart'] = gchart.PieChart(SimpleDataSource(data=data1), html_id="pie_chart1", options={'title': _("# of Population"), 'width': 250,'height': 250, 'pieSliceText': _('percentage'),'legend': {'position': 'top', 'maxLines':3}})
	# context_dict['landcover_area_chart'] = gchart.PieChart(SimpleDataSource(data=data2), html_id="pie_chart2", options={'title': _("# of Area (KM2)"), 'width': 250,'height': 250, 'pieSliceText': _('percentage'),'legend': {'position': 'top', 'maxLines':3}})

	context_dict.pop('position')
	return context_dict

# moved from geodb.geoapi

class EarthquakeStatisticResource(ModelResource):

	class Meta:
		# authorization = DjangoAuthorization()
		resource_name = 'statistic_earthquake'
		allowed_methods = ['post']
		detail_allowed_methods = ['post']
		cache = SimpleCache()
		object_class=None
		# always_return_data = True
 
	def getRisk(self, request):

		p = urlparse(request.META.get('HTTP_REFERER')).path.split('/')
		mapCode = p[3] if 'v2' in p else p[2]
		map_obj = _resolve_map(request, mapCode, 'base.view_resourcebase', _PERMISSION_MSG_VIEW)

		queryset = matrix(user=request.user,resourceid=map_obj,action='Interactive Calculation')
		queryset.save()

		boundaryFilter = json.loads(request.body)

		wkts = ['ST_GeomFromText(\'%s\',4326)'%(i) for i in boundaryFilter['spatialfilter']]
		bring = wkts[-1] if len(wkts) else None
		filterLock = 'ST_Union(ARRAY[%s])'%(','.join(wkts))

		response = getEarthquakeStatistic(request, filterLock, boundaryFilter.get('flag'), boundaryFilter.get('code'), eq_event=boundaryFilter.get('event_code'))

		return response

	def post_list(self, request, **kwargs):
		self.method_check(request, allowed=['post'])
		response = self.getRisk(request)
		return self.create_response(request, response)  

def getEarthQuakeExecuteExternal(filterLock, flag, code, event_code):   
	response = {} 
	cursor = connections['geodb'].cursor()
	cursor.execute("\
		select b.grid_value, sum(   \
		case    \
			when ST_CoveredBy(a.wkb_geometry,b.wkb_geometry) then a.area_population \
			else st_area(st_intersection(a.wkb_geometry,b.wkb_geometry))/st_area(a.wkb_geometry)*a.area_population \
		end) as pop     \
		from afg_lndcrva a, earthquake_shakemap b   \
		where b.event_code = '"+event_code+"' and b.grid_value > 1 and a.vuid = '"+str(code)+"'    \
		and ST_Intersects(a.wkb_geometry,b.wkb_geometry)    \
		group by b.grid_value\
	")
	# cursor.execute("\
	#     select b.grid_value, sum(   \
	#     case    \
	#         when ST_CoveredBy(a.wkb_geometry,b.wkb_geometry) then a.vuid_population_landscan \
	#         else st_area(st_intersection(a.wkb_geometry,b.wkb_geometry))/st_area(a.wkb_geometry)*a.vuid_population_landscan \
	#     end) as pop     \
	#     from afg_ppla a, earthquake_shakemap b   \
	#     where b.event_code = '"+event_code+"' and b.grid_value > 1 and a.vuid = '"+str(code)+"'    \
	#     and ST_Intersects(a.wkb_geometry,b.wkb_geometry)    \
	#     group by b.grid_value\
	# ")
	row = cursor.fetchall()

	temp = dict([(c[0], c[1]) for c in row])
	response['pop_shake_weak']=round(temp.get(2, 0),0) + round(temp.get(3, 0),0) 
	response['pop_shake_light']=round(temp.get(4, 0),0) 
	response['pop_shake_moderate']=round(temp.get(5, 0),0) 
	response['pop_shake_strong']=round(temp.get(6, 0),0) 
	response['pop_shake_verystrong']=round(temp.get(7, 0),0)
	response['pop_shake_severe']=round(temp.get(8, 0),0)  
	response['pop_shake_violent']=round(temp.get(9, 0),0) 
	response['pop_shake_extreme']=round(temp.get(10, 0),0)+round(temp.get(11, 0),0)+round(temp.get(12, 0),0)+round(temp.get(13, 0),0)+round(temp.get(14, 0),0)+round(temp.get(15, 0),0)

	cursor.execute("\
		select b.grid_value, count(*) as numbersettlements     \
		from afg_pplp a, earthquake_shakemap b   \
		where b.event_code = '"+event_code+"' and b.grid_value > 1 and a.vuid = '"+str(code)+"'    \
		and ST_Within(a.wkb_geometry,b.wkb_geometry)    \
		group by b.grid_value\
	")
	row = cursor.fetchall()

	temp = dict([(c[0], c[1]) for c in row])
	response['settlement_shake_weak']=round(temp.get(2, 0),0) + round(temp.get(3, 0),0) 
	response['settlement_shake_light']=round(temp.get(4, 0),0) 
	response['settlement_shake_moderate']=round(temp.get(5, 0),0) 
	response['settlement_shake_strong']=round(temp.get(6, 0),0) 
	response['settlement_shake_verystrong']=round(temp.get(7, 0),0)
	response['settlement_shake_severe']=round(temp.get(8, 0),0)  
	response['settlement_shake_violent']=round(temp.get(9, 0),0) 
	response['settlement_shake_extreme']=round(temp.get(10, 0),0)+round(temp.get(11, 0),0)+round(temp.get(12, 0),0)+round(temp.get(13, 0),0)+round(temp.get(14, 0),0)+round(temp.get(15, 0),0)
	
	cursor.close()
	return response

class EQEventsSerializer(Serializer):
	 def to_json(self, data, options=None):
		options = options or {}
		data = self.to_simple(data, options)
		data2 = self.to_simple({'objects':[]}, options)
		for i in data['objects']:
			i['sm_available'] = 'ShakeMap are Available'
			data2['objects'].append(i)

		return json.dumps(data2, cls=DjangoJSONEncoder, sort_keys=True)       

class getEQEvents(ModelResource):
	"""Provinces api"""
	detail_title = fields.CharField()
	date_custom = fields.CharField()
	evFlag = fields.IntegerField()
	smFlag = fields.IntegerField()
	sm_available = fields.CharField()
	def dehydrate_detail_title(self, bundle):
		return bundle.obj.title + ' on ' +  bundle.obj.dateofevent.strftime("%d-%m-%Y %H:%M:%S")
	def dehydrate_date_custom(self, bundle):
		return bundle.obj.dateofevent.strftime("%d-%m-%Y %H:%M:%S")
	# def dehydrate_evFlag(self, bundle):    
	#     pEV = earthquake_events.objects.extra(
	#         tables={'afg_admbnda_adm1'},
	#         where={"ST_Intersects(afg_admbnda_adm1.wkb_geometry,earthquake_events.wkb_geometry) and earthquake_events.event_code = '"+bundle.obj.event_code+"'"}
	#     )
	#     if pEV.count()>0:
	#         return 1
	#     else:
	#         return 0  
	# def dehydrate_smFlag(self, bundle):    
	#     pSM = earthquake_shakemap.objects.extra(
	#         tables={'afg_admbnda_adm1'},
	#         where={"ST_Intersects(afg_admbnda_adm1.wkb_geometry,earthquake_shakemap.wkb_geometry) and earthquake_shakemap.event_code = '"+bundle.obj.event_code+"'"}
	#     )
	#     if pSM.count()>0:
	#         return 1
	#     else:
	#         return 0                  
	class Meta:
		queryset = earthquake_events.objects.all().exclude(shakemaptimestamp__isnull=True).order_by('dateofevent')
		# queryset = earthquake_events.objects.extra(
		#     tables={'earthquake_shakemap'},
		#     where={'earthquake_events.event_code=earthquake_shakemap.event_code'
		#            # 'logsource_domain="example.com"',
		#            }
		# ).values('event_code','title','dateofevent','magnitude','depth', 'shakemaptimestamp','wkb_geometry')   
		resource_name = 'geteqevents'
		allowed_methods = ('get')
		filtering = { 
			"dateofevent" : ['gte', 'lte']
		} 
		serializer = EQEventsSerializer()   

# moved from geodb.geo_calc

def getEarthquake(request, filterLock, flag, code, includes=[], excludes=[], eq_event='', response=dict_ext()):

	# response = dict_ext()
	# eq_event = ''
	# if 'eq_event' in request.GET:
	# 	eq_event = request.GET['eq_event']

	# if include_section('', includes, excludes):
		# response = getCommonUse(request, flag, code)
		# targetBase = AfgLndcrva.objects.all()

	response['baseline'] = response.pathget('cache','getBaseline','baseline') or getBaseline(request, filterLock, flag, code, includes=['pop_lc','building_lc'])
		# if flag not in ['entireAfg','currentProvince']:
		#     response['Population']=getTotalPop(filterLock, flag, code, targetBase)
		#     response['Area']=getTotalArea(filterLock, flag, code, targetBase)
		#     response['Buildings']=getTotalBuildings(filterLock, flag, code, targetBase)
		#     response['settlement']=getTotalSettlement(filterLock, flag, code, targetBase)
		# else :
		#     tempData = getShortCutData(flag,code)
		#     response['Population']= tempData['Population']
		#     response['Area']= tempData['Area']
		#     response['Buildings']= tempData['total_buildings']
		#     response['settlement']= tempData['settlements']

	if include_section('eq_list', includes, excludes):

		url = 'http://asdc.immap.org/geoapi/geteqevents/?dateofevent__gte=2015-09-08&_dc=1473243793279'
		req = urllib2.Request(url)
		req.add_unredirected_header('User-Agent', 'Custom User-Agent')
		fh = urllib2.urlopen(req)
		data = fh.read()
		fh.close()
		jdict = json.loads(data)

		# response['eq_list'] = []
		# pertama = True

		# response['EQ_title'] = ''
		# response['eq_link'] = ''

		# for x in reversed(jdict['objects']):
		# 	if eq_event != '':
		# 		if x['event_code'] == eq_event:
		# 			x['selected']=True
		# 			response['EQ_title'] = x['detail_title']
		# 		else:
		# 			x['selected']=False
		# 		response['eq_link'] = '&eq_event='+eq_event
		# 	else:
		# 		if pertama:
		# 			x['selected']=True
		# 			pertama = False
		# 			eq_event = x['event_code']
		# 			response['EQ_title'] = x['detail_title']
		# 			response['eq_link'] = '&eq_event='+eq_event
		# 		else:
		# 			x['selected']=False

		response['eq_list'] = list(reversed(jdict['objects']))
		response['eq_link'] = '&eq_event='+eq_event
		for x in response['eq_list']:
			x['selected'] = bool(x['event_code'] == eq_event)
			if x['selected']:
				response['EQ_title'] = x['detail_title']

	if include_section('getEQData', includes, excludes):
		response['rawearthquake'] = getEQData(filterLock, flag, code, eq_event)

		# for i in rawEarthquake:
		#     response[i]=rawEarthquake[i]

		for i,j in {'pop':'pop','building':'buildings','settlement':'settlement'}.items():
			for k in EARTHQUAKE_TYPES:
				response.path(i+'_shake')[k] = min(response['rawearthquake'].get(j+'_shake_'+k) or 0, response['baseline'][i+'_total'])
			response[i+'_shake_total'] = min(sum(response[i+'_shake'].values()), response['baseline'][i+'_total'])
		
		# if 'pop_shake_weak' in response:
		#     response['pop_shake_weak'] if response['pop_shake_weak']<response['Population'] else response['Population']
		# if 'pop_shake_light' in response:
		#     response['pop_shake_light'] if response['pop_shake_light']<response['Population'] else response['Population']
		# if 'pop_shake_moderate' in response:
		#     response['pop_shake_moderate'] if response['pop_shake_moderate']<response['Population'] else response['Population']
		# if 'pop_shake_strong' in response:
		#     response['pop_shake_strong'] if response['pop_shake_strong']<response['Population'] else response['Population']
		# if 'pop_shake_verystrong' in response:
		#     response['pop_shake_verystrong'] if response['pop_shake_verystrong']<response['Population'] else response['Population']
		# if 'pop_shake_severe' in response:
		#     response['pop_shake_severe'] if response['pop_shake_severe']<response['Population'] else response['Population']
		# if 'pop_shake_violent' in response:
		#     response['pop_shake_violent'] if response['pop_shake_violent']<response['Population'] else response['Population']
		# if 'pop_shake_extreme' in response:
		#     response['pop_shake_extreme'] if response['pop_shake_extreme']<response['Population'] else response['Population']

		# if 'buildings_shake_weak' in response:
		#     response['buildings_shake_weak'] if response['buildings_shake_weak']<response['Buildings'] else response['Buildings']
		# if 'buildings_shake_light' in response:
		#     response['buildings_shake_light'] if response['buildings_shake_light']<response['Buildings'] else response['Buildings']
		# if 'buildings_shake_moderate' in response:
		#     response['buildings_shake_moderate'] if response['buildings_shake_moderate']<response['Buildings'] else response['Buildings']
		# if 'buildings_shake_strong' in response:
		#     response['buildings_shake_strong'] if response['buildings_shake_strong']<response['Buildings'] else response['Buildings']
		# if 'buildings_shake_verystrong' in response:
		#     response['buildings_shake_verystrong'] if response['buildings_shake_verystrong']<response['Buildings'] else response['Buildings']
		# if 'buildings_shake_severe' in response:
		#     response['buildings_shake_severe'] if response['buildings_shake_severe']<response['Buildings'] else response['Buildings']
		# if 'buildings_shake_violent' in response:
		#     response['buildings_shake_violent'] if response['buildings_shake_violent']<response['Buildings'] else response['Buildings']
		# if 'buildings_shake_extreme' in response:
		#     response['buildings_shake_extreme'] if response['buildings_shake_extreme']<response['Buildings'] else response['Buildings']

		# if 'settlement_shake_weak' in response:
		#     response['settlement_shake_weak'] if response['settlement_shake_weak']<response['settlement'] else response['settlement']
		# if 'settlement_shake_light' in response:
		#     response['settlement_shake_light'] if response['settlement_shake_light']<response['settlement'] else response['settlement']
		# if 'settlement_shake_moderate' in response:
		#     response['settlement_shake_moderate'] if response['settlement_shake_moderate']<response['settlement'] else response['settlement']
		# if 'settlement_shake_strong' in response:
		#     response['settlement_shake_strong'] if response['settlement_shake_strong']<response['settlement'] else response['settlement']
		# if 'settlement_shake_verystrong' in response:
		#     response['settlement_shake_verystrong'] if response['settlement_shake_verystrong']<response['settlement'] else response['settlement']
		# if 'settlement_shake_severe' in response:
		#     response['settlement_shake_severe'] if response['settlement_shake_severe']<response['settlement'] else response['settlement']
		# if 'settlement_shake_violent' in response:
		#     response['settlement_shake_violent'] if response['settlement_shake_violent']<response['settlement'] else response['settlement']
		# if 'settlement_shake_extreme' in response:
		#     response['settlement_shake_extreme'] if response['settlement_shake_extreme']<response['settlement'] else response['settlement']

		# dataEQ = []
		# dataEQ.append(['intensity','population'])
		# dataEQ.append(['II-III : Weak',response['pop_shake_weak'] if 'pop_shake_weak' in response else 0])
		# dataEQ.append(['IV : Light',response['pop_shake_light'] if 'pop_shake_light' in response else 0])
		# dataEQ.append(['V : Moderate',response['pop_shake_moderate'] if 'pop_shake_moderate' in response else 0])
		# dataEQ.append(['VI : Strong',response['pop_shake_strong'] if 'pop_shake_strong' in response else 0])
		# dataEQ.append(['VII : Very-strong',response['pop_shake_verystrong'] if 'pop_shake_verystrong' in response else 0])
		# dataEQ.append(['VIII : Severe',response['pop_shake_severe'] if 'pop_shake_severe' in response else 0])
		# dataEQ.append(['IX : Violent',response['pop_shake_violent'] if 'pop_shake_violent' in response else 0])
		# dataEQ.append(['X+ : Extreme',response['pop_shake_extreme'] if 'pop_shake_extreme' in response else 0])
		# response['EQ_chart'] = gchart.PieChart(SimpleDataSource(data=dataEQ), html_id="pie_chart1", options={'title': response['EQ_title'], 'width': 450,'height': 300, 'pieSliceTextStyle': {'color': 'black'}, 'pieSliceText': 'percentage','legend': {'position':'right', 'maxLines':4}, 'slices':{0:{'color':'#c4ceff'},1:{'color':'#7cfddf'},2:{'color':'#b1ff55'},3:{'color':'#fcf109'},4:{'color':'#ffb700'},5:{'color':'#fd6500'},6:{'color':'#ff1f00'},7:{'color':'#d20003'}} })

		# response['total_eq_pop'] = response['pop_shake_weak']+response['pop_shake_light']+response['pop_shake_moderate']+response['pop_shake_strong']+response['pop_shake_verystrong']+response['pop_shake_severe']+response['pop_shake_violent']+response['pop_shake_extreme']
		# response['total_eq_settlements'] = response['settlement_shake_weak']+response['settlement_shake_light']+response['settlement_shake_moderate']+response['settlement_shake_strong']+response['settlement_shake_verystrong']+response['settlement_shake_severe']+response['settlement_shake_violent']+response['settlement_shake_extreme']
		# response['total_eq_buildings'] = response['buildings_shake_weak']+response['buildings_shake_light']+response['buildings_shake_moderate']+response['buildings_shake_strong']+response['buildings_shake_verystrong']+response['buildings_shake_severe']+response['buildings_shake_violent']+response['buildings_shake_extreme']

		# response['total_eq_pop'] = response['total_eq_pop'] if response['total_eq_pop'] < response['Population'] else response['Population']
		# response['total_eq_settlements'] = response['total_eq_settlements'] if response['total_eq_settlements'] < response['settlement'] else response['settlement']
		# response['total_eq_buildings'] = response['total_eq_buildings'] if response['total_eq_buildings'] < response['Buildings'] else response['Buildings']

	if include_section('getListEQ', includes, excludes):
		response['lc_child'] = getListEQ(filterLock, flag, code, eq_event)

	if include_section('GeoJson', includes, excludes):
		response['GeoJson'] = getGeoJson(request, flag, code)

	return response

def getListEQ(filterLock, flag, code, eq_event):
	response = []
	data = getProvinceSummary(filterLock, flag, code)
	for i in data:
		data ={}
		data['code'] = i['code']
		data['na_en'] = i['na_en']
		data['Population'] = i['Population']
		data['Area'] = i['Area']

		rawEarthquake = getEQData(filterLock, 'currentProvince', i['code'], eq_event)
		for x in rawEarthquake:
			data[x]=rawEarthquake[x]

		response.append(data)
	return response

def getEQData(filterLock, flag, code, event_code):
	p = earthquake_shakemap.objects.all().filter(event_code=event_code)
	if p.count() == 0:
		return {
			'pop_shake_weak':0,
			'pop_shake_light':0,
			'pop_shake_moderate':0,
			'pop_shake_strong':0,
			'pop_shake_verystrong':0,
			'pop_shake_severe':0,
			'pop_shake_violent':0,
			'pop_shake_extreme':0,
			'settlement_shake_weak':0,
			'settlement_shake_light':0,
			'settlement_shake_moderate':0,
			'settlement_shake_strong':0,
			'settlement_shake_verystrong':0,
			'settlement_shake_severe':0,
			'settlement_shake_violent':0,
			'settlement_shake_extreme':0,
			'buildings_shake_weak':0,
			'buildings_shake_light':0,
			'buildings_shake_moderate':0,
			'buildings_shake_strong':0,
			'buildings_shake_verystrong':0,
			'buildings_shake_severe':0,
			'buildings_shake_violent':0,
			'buildings_shake_extreme':0
		}

	if flag=='drawArea':
		cursor = connections['geodb'].cursor()
		cursor.execute("\
			select coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.pop_shake_weak \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.pop_shake_weak \
				end \
			)),0) as pop_shake_weak,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.pop_shake_light \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.pop_shake_light \
				end \
			)),0) as pop_shake_light,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.pop_shake_moderate \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.pop_shake_moderate \
				end \
			)),0) as pop_shake_moderate,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.pop_shake_strong \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.pop_shake_strong \
				end \
			)),0) as pop_shake_strong,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.pop_shake_verystrong \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.pop_shake_verystrong \
				end \
			)),0) as pop_shake_verystrong,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.pop_shake_severe \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.pop_shake_severe \
				end \
			)),0) as pop_shake_severe,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.pop_shake_violent \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.pop_shake_violent \
				end \
			)),0) as pop_shake_violent,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.pop_shake_extreme \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.pop_shake_extreme \
				end \
			)),0) as pop_shake_extreme,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.settlement_shake_weak \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.settlement_shake_weak \
				end \
			)),0) as settlement_shake_weak,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.settlement_shake_light \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.settlement_shake_light \
				end \
			)),0) as settlement_shake_light,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.settlement_shake_moderate \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.settlement_shake_moderate \
				end \
			)),0) as settlement_shake_moderate,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.settlement_shake_strong \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.settlement_shake_strong \
				end \
			)),0) as settlement_shake_strong,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.settlement_shake_verystrong \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.settlement_shake_verystrong \
				end \
			)),0) as settlement_shake_verystrong,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.settlement_shake_severe \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.settlement_shake_severe \
				end \
			)),0) as settlement_shake_severe,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.settlement_shake_violent \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.settlement_shake_violent \
				end \
			)),0) as settlement_shake_violent,     \
			coalesce(round(sum(   \
				case    \
					when ST_CoveredBy(a.wkb_geometry,"+filterLock+") then b.settlement_shake_extreme \
					else st_area(st_intersection(a.wkb_geometry,"+filterLock+"))/st_area(a.wkb_geometry)*b.settlement_shake_extreme \
				end \
			)),0) as settlement_shake_extreme,     \
			coalesce(round(sum(b.buildings_shake_weak)),0) as buildings_shake_weak,     \
			coalesce(round(sum(b.buildings_shake_light)),0) as buildings_shake_light,     \
			coalesce(round(sum(b.buildings_shake_moderate)),0) as buildings_shake_moderate,     \
			coalesce(round(sum(b.buildings_shake_strong)),0) as buildings_shake_strong,     \
			coalesce(round(sum(b.buildings_shake_verystrong)),0) as buildings_shake_verystrong,     \
			coalesce(round(sum(b.buildings_shake_severe)),0) as buildings_shake_severe,     \
			coalesce(round(sum(b.buildings_shake_violent)),0) as buildings_shake_violent,     \
			coalesce(round(sum(b.buildings_shake_extreme)),0) as buildings_shake_extreme \
			from afg_ppla a, villagesummary_eq b   \
			where  a.vuid = b.village and b.event_code = '"+event_code+"'  \
			and ST_Intersects(a.wkb_geometry,"+filterLock+")    \
		")
		col_names = [desc[0] for desc in cursor.description]

		row = cursor.fetchone()
		row_dict = dict(izip(col_names, row))

		cursor.close()
		counts={}
		counts[0] = row_dict

	elif flag=='entireAfg':
		counts = list(villagesummaryEQ.objects.all().extra(
			select={
				'pop_shake_weak' : 'coalesce(SUM(pop_shake_weak),0)',
				'pop_shake_light' : 'coalesce(SUM(pop_shake_light),0)',
				'pop_shake_moderate' : 'coalesce(SUM(pop_shake_moderate),0)',
				'pop_shake_strong' : 'coalesce(SUM(pop_shake_strong),0)',
				'pop_shake_verystrong' : 'coalesce(SUM(pop_shake_verystrong),0)',
				'pop_shake_severe' : 'coalesce(SUM(pop_shake_severe),0)',
				'pop_shake_violent' : 'coalesce(SUM(pop_shake_violent),0)',
				'pop_shake_extreme' : 'coalesce(SUM(pop_shake_extreme),0)',

				'settlement_shake_weak' : 'coalesce(SUM(settlement_shake_weak),0)',
				'settlement_shake_light' : 'coalesce(SUM(settlement_shake_light),0)',
				'settlement_shake_moderate' : 'coalesce(SUM(settlement_shake_moderate),0)',
				'settlement_shake_strong' : 'coalesce(SUM(settlement_shake_strong),0)',
				'settlement_shake_verystrong' : 'coalesce(SUM(settlement_shake_verystrong),0)',
				'settlement_shake_severe' : 'coalesce(SUM(settlement_shake_severe),0)',
				'settlement_shake_violent' : 'coalesce(SUM(settlement_shake_violent),0)',
				'settlement_shake_extreme' : 'coalesce(SUM(settlement_shake_extreme),0)',

				'buildings_shake_weak' : 'coalesce(SUM(buildings_shake_weak),0)',
				'buildings_shake_light' : 'coalesce(SUM(buildings_shake_light),0)',
				'buildings_shake_moderate' : 'coalesce(SUM(buildings_shake_moderate),0)',
				'buildings_shake_strong' : 'coalesce(SUM(buildings_shake_strong),0)',
				'buildings_shake_verystrong' : 'coalesce(SUM(buildings_shake_verystrong),0)',
				'buildings_shake_severe' : 'coalesce(SUM(buildings_shake_severe),0)',
				'buildings_shake_violent' : 'coalesce(SUM(buildings_shake_violent),0)',
				'buildings_shake_extreme' : 'coalesce(SUM(buildings_shake_extreme),0)'
			},
			where = {
				"event_code = '"+event_code+"'"
			}).values(
				'pop_shake_weak',
				'pop_shake_light',
				'pop_shake_moderate',
				'pop_shake_strong',
				'pop_shake_verystrong',
				'pop_shake_severe',
				'pop_shake_violent',
				'pop_shake_extreme',
				'settlement_shake_weak',
				'settlement_shake_light',
				'settlement_shake_moderate',
				'settlement_shake_strong',
				'settlement_shake_verystrong',
				'settlement_shake_severe',
				'settlement_shake_violent',
				'settlement_shake_extreme',
				'buildings_shake_weak',
				'buildings_shake_light',
				'buildings_shake_moderate',
				'buildings_shake_strong',
				'buildings_shake_verystrong',
				'buildings_shake_severe',
				'buildings_shake_violent',
				'buildings_shake_extreme'
			))
	elif flag =='currentProvince':
		if len(str(code)) > 2:
			ff0001 =  "district  = '"+str(code)+"'"
		else :
			ff0001 =  "left(cast(district as text), "+str(len(str(code)))+") = '"+str(code)+"' and length(cast(district as text))="+ str(len(str(code))+2)
		counts = list(villagesummaryEQ.objects.all().extra(
			select={
				'pop_shake_weak' : 'coalesce(SUM(pop_shake_weak),0)',
				'pop_shake_light' : 'coalesce(SUM(pop_shake_light),0)',
				'pop_shake_moderate' : 'coalesce(SUM(pop_shake_moderate),0)',
				'pop_shake_strong' : 'coalesce(SUM(pop_shake_strong),0)',
				'pop_shake_verystrong' : 'coalesce(SUM(pop_shake_verystrong),0)',
				'pop_shake_severe' : 'coalesce(SUM(pop_shake_severe),0)',
				'pop_shake_violent' : 'coalesce(SUM(pop_shake_violent),0)',
				'pop_shake_extreme' : 'coalesce(SUM(pop_shake_extreme),0)',

				'settlement_shake_weak' : 'coalesce(SUM(settlement_shake_weak),0)',
				'settlement_shake_light' : 'coalesce(SUM(settlement_shake_light),0)',
				'settlement_shake_moderate' : 'coalesce(SUM(settlement_shake_moderate),0)',
				'settlement_shake_strong' : 'coalesce(SUM(settlement_shake_strong),0)',
				'settlement_shake_verystrong' : 'coalesce(SUM(settlement_shake_verystrong),0)',
				'settlement_shake_severe' : 'coalesce(SUM(settlement_shake_severe),0)',
				'settlement_shake_violent' : 'coalesce(SUM(settlement_shake_violent),0)',
				'settlement_shake_extreme' : 'coalesce(SUM(settlement_shake_extreme),0)',

				'buildings_shake_weak' : 'coalesce(SUM(buildings_shake_weak),0)',
				'buildings_shake_light' : 'coalesce(SUM(buildings_shake_light),0)',
				'buildings_shake_moderate' : 'coalesce(SUM(buildings_shake_moderate),0)',
				'buildings_shake_strong' : 'coalesce(SUM(buildings_shake_strong),0)',
				'buildings_shake_verystrong' : 'coalesce(SUM(buildings_shake_verystrong),0)',
				'buildings_shake_severe' : 'coalesce(SUM(buildings_shake_severe),0)',
				'buildings_shake_violent' : 'coalesce(SUM(buildings_shake_violent),0)',
				'buildings_shake_extreme' : 'coalesce(SUM(buildings_shake_extreme),0)'
			},
			where = {
				"event_code = '"+event_code+"' and "+ff0001
			}).values(
				'pop_shake_weak',
				'pop_shake_light',
				'pop_shake_moderate',
				'pop_shake_strong',
				'pop_shake_verystrong',
				'pop_shake_severe',
				'pop_shake_violent',
				'pop_shake_extreme',
				'settlement_shake_weak',
				'settlement_shake_light',
				'settlement_shake_moderate',
				'settlement_shake_strong',
				'settlement_shake_verystrong',
				'settlement_shake_severe',
				'settlement_shake_violent',
				'settlement_shake_extreme',
				'buildings_shake_weak',
				'buildings_shake_light',
				'buildings_shake_moderate',
				'buildings_shake_strong',
				'buildings_shake_verystrong',
				'buildings_shake_severe',
				'buildings_shake_violent',
				'buildings_shake_extreme'
			))
	else:
		cursor = connections['geodb'].cursor()
		cursor.execute("\
			select coalesce(round(sum(b.pop_shake_weak)),0) as pop_shake_weak,     \
			coalesce(round(sum(b.pop_shake_light)),0) as pop_shake_light,     \
			coalesce(round(sum(b.pop_shake_moderate)),0) as pop_shake_moderate,     \
			coalesce(round(sum(b.pop_shake_strong)),0) as pop_shake_strong,     \
			coalesce(round(sum(b.pop_shake_verystrong)),0) as pop_shake_verystrong,     \
			coalesce(round(sum(b.pop_shake_severe)),0) as pop_shake_severe,     \
			coalesce(round(sum(b.pop_shake_violent)),0) as pop_shake_violent,     \
			coalesce(round(sum(b.pop_shake_extreme)),0) as pop_shake_extreme,     \
			coalesce(round(sum(b.settlement_shake_weak)),0) as settlement_shake_weak,     \
			coalesce(round(sum(b.settlement_shake_light)),0) as settlement_shake_light,     \
			coalesce(round(sum(b.settlement_shake_moderate)),0) as settlement_shake_moderate,     \
			coalesce(round(sum(b.settlement_shake_strong)),0) as settlement_shake_strong,     \
			coalesce(round(sum(b.settlement_shake_verystrong)),0) as settlement_shake_verystrong,     \
			coalesce(round(sum(b.settlement_shake_severe)),0) as settlement_shake_severe,     \
			coalesce(round(sum(b.settlement_shake_violent)),0) as settlement_shake_violent,     \
			coalesce(round(sum(b.settlement_shake_extreme)),0) as settlement_shake_extreme,     \
			coalesce(round(sum(b.buildings_shake_weak)),0) as buildings_shake_weak,     \
			coalesce(round(sum(b.buildings_shake_light)),0) as buildings_shake_light,     \
			coalesce(round(sum(b.buildings_shake_moderate)),0) as buildings_shake_moderate,     \
			coalesce(round(sum(b.buildings_shake_strong)),0) as buildings_shake_strong,     \
			coalesce(round(sum(b.buildings_shake_verystrong)),0) as buildings_shake_verystrong,     \
			coalesce(round(sum(b.buildings_shake_severe)),0) as buildings_shake_severe,     \
			coalesce(round(sum(b.buildings_shake_violent)),0) as buildings_shake_violent,     \
			coalesce(round(sum(b.buildings_shake_extreme)),0) as buildings_shake_extreme    \
			from afg_ppla a, villagesummary_eq b   \
			where  a.vuid = b.village and b.event_code = '"+event_code+"'  \
			and ST_Within(a.wkb_geometry,"+filterLock+")    \
		")
		col_names = [desc[0] for desc in cursor.description]

		row = cursor.fetchone()
		row_dict = dict(izip(col_names, row))

		cursor.close()
		counts={}
		counts[0] = row_dict

	return counts[0]

def dashboard_earthquake(request, filterLock, flag, code, includes=[], excludes=[], eq_event='', response=dict_ext()):

	eq_event = eq_event or request.GET.get('eq_event') or ''
	# response = dict_ext()

	if include_section('getCommonUse', includes, excludes):
		response.update(getCommonUse(request, flag, code))

	response['source'] = earthquake = response.pathget('cache','getEarthquake') or getEarthquake(request, filterLock, flag, code, includes=includes, excludes=excludes, eq_event=eq_event)
	baseline = earthquake['baseline']
	panels = response.path('panels')
	charts = panels.path('charts')
	tables = panels.path('tables')
	response.update(earthquake.within('eq_list'))

	titles = {'pop':_('Population Affected by Earthquake'), 'settlement':_('Settlements Affected by Earthquake'), 'building':_('Building Affected by Earthquake')}
	for k in titles:
		with charts.path(k+'_affected_by_earthquake') as chart:
			chart['title'] = titles[k]
			chart['total'] = baseline[k+'_total']
			chart['affected'] = earthquake[k+'_shake_total']
			chart['child'] = [
				[_('Affected'), chart['affected']], 
				[_('Not Affected'), chart['total']-chart['affected']],
			]

	titles = {'pop':_('Mercalli Intensity Scale Population'), 'settlement':_('Mercalli Intensity Scale Settlements'), 'building':_('Mercalli Intensity Scale Building')}
	for k in titles:
		with charts.path('mercalli_intensity_scale_'+k) as chart:
			chart['title'] = titles[k]
			chart['child'] = [[EARTHQUAKE_TYPES[i],earthquake[k+'_shake'][i]] for i in EARTHQUAKE_TYPES_ORDER]

	if include_section('tables', includes, excludes):
		titles = {'pop_settlement':_('Overview of Earthquake Affecting Population and Settlements')}
		subkeys = {'pop_settlement':['pop','settlement']}
		for k in titles:
			with tables.path(k) as table:
				table['title'] = titles[k]
				table['parentdata'] = [response['parent_label']]+[earthquake[l+'_shake'][j] for j in EARTHQUAKE_TYPES_ORDER for l in subkeys[k]]
				table['child'] = [{
					'code':i['code'],
					'value':[i['na_en']]+[i.get('%s_shake_%s'%(l,j)) or 0 for j in EARTHQUAKE_TYPES_ORDER for l in subkeys[k]],
				} for i in earthquake['lc_child']]

	if include_section('GeoJson', includes, excludes):
		response['GeoJson'] = geojsonadd_earthquake(response)

	return response

def geojsonadd_earthquake(response):

	earthquake = response['source']
	baseline = response['source']['baseline']
	boundary = response['source']['GeoJson']
	earthquake['lc_child_dict'] = {v['code']:v for v in earthquake['lc_child']}
	convertkeys = {'pop':'pop', 'settlement':'settlement', 'building':'buildings'}

	for i,l in enumerate(boundary.get('features',[])):
		boundary['features'][i]['properties'] = prop = dict_ext(boundary['features'][i]['properties'])

		# Checking if it's in a district
		if response['areatype'] == 'district':
			response['set_jenk_divider'] = 1
			prop.update({'%s_shake_%s'%(l,j):earthquake[l+'_shake'][j] or 0 for j in EARTHQUAKE_TYPES_ORDER for l in convertkeys})

		else:
			response['set_jenk_divider'] = 7
			if (prop['code'] in earthquake['lc_child_dict']):
				child = earthquake.path('lc_child_dict')[prop['code']] 
				prop.update({'%s_shake_%s'%(l,j):child.get('%s_shake_%s'%(l,j)) or 0 for j in EARTHQUAKE_TYPES_ORDER for l in convertkeys})

	return boundary

def getEarthquakeStatistic(request,filterLock, flag, code, eq_event=''):

	response_dashboard_earthquake = dashboard_earthquake(request, filterLock, flag, code, excludes=['GeoJson'], eq_event=eq_event)
	panels = response_dashboard_earthquake.pathget('panels')
	response = response_dashboard_earthquake.within('eq_list')
	panels_list = response.path('panels_list')

	panels_list['charts'] = [v for k,v in panels['charts'].items() if k in ['pop_affected_by_earthquake','settlement_affected_by_earthquake','building_affected_by_earthquake','mercalli_intensity_scale_pop','mercalli_intensity_scale_settlement','mercalli_intensity_scale_building']]
	panels_list['tables'] = [{
		'title':v['title'],
		'child':[v['parentdata']] + [i['value'] for i in v['child']]
	} for k,v in panels['tables'].items() if k in ['pop_settlement']]

	return response

class EarthquakeInfoVillages(Resource):

	class Meta:
		resource_name = 'earthquake'
		authentication = SessionAuthentication()

	def prepend_urls(self):
		name = self._meta.resource_name
		return [
			url(r"^%s%s$" % (name, trailing_slash()), self.wrap_view('getdata'), name='get_%s'%(name)),
		]

	def getdata(self, request, **kwargs):
		self.method_check(request, allowed=['get'])
		self.is_authenticated(request)
		self.throttle_check(request)

		data = getEarthquakeInfoVillagesCommon(request.GET.get('vuid'))
		response = {
			'panels_list':{
				'tables':[
					{
						'key':'base_info',
						'child':[
							[_('Settlement'),data.get('name_en')],
							[_('District'),data.get('dist_na_en')],
							[_('Province'),data.get('prov_na_en')],
							[_('Area'),data.get('area_sqm')],
							[_('Total Population'),data.get('area_population')],
						],
					},
					{
						'key':'earthquake_hazard_risk',
						'title':_('Earthquake Hazard Risk')+'*',
						'child':[
							["II-III Weak",data.get('sic_1','')],
							["IV Light",data.get('sic_2','')],
							["V Moderate",data.get('sic_3','')],
							["VI Strong",data.get('sic_4','')],
							["VII Very Strong",data.get('sic_5','')],
							["VIII Severe",data.get('sic_6','')],
							["IX Violent",data.get('sic_7','')],
							["X+ Extreme",data.get('sic_8','')],							
						],
						'footnotes':[
							'*'+_('Seismic intensity and description of potential damage (USGS, 2007)'),
							_('Peak Horizontal Acceleration with 2 Percent Probability of Exceedance in 50 years')+'**',
						]
					},
					{
						'key':'latest_20_earthquakes',
						'title':_('Latest 20 earthquakes')+'*',
						'child':[{
							'date':item.get('date'),
							'child':[
								["II-III Weak",'X' if (int(item.get('sic',0)) in [2,3]) else ''],
								["IV Light",'X' if int(item.get('sic',0)==4) else ''],
								["V Moderate",'X' if int(item.get('sic',0)==5) else ''],
								["VI Strong",'X' if int(item.get('sic',0)==6) else ''],
								["VII Very Strong",'X' if int(item.get('sic',0)==7) else ''],
								["VIII Severe",'X' if int(item.get('sic',0)==8) else ''],
								["IX Violent",'X' if int(item.get('sic',0)==9) else ''],
								["X+ Extreme",'X' if int(item.get('sic',0)>=10) else ''],							
							],
						} for item in data.get('eq_history',[])],
					},
					{
						'key':'description',
						'title':_('Description'),
						'columntitles':[
							_('Intensity'),
							_('Shaking'),
							_('Description/Damage'),
						],
						'child':[
							[_('I'),_('Not felt'),_('Not felt except by a very few under especially favorable conditions.'),],
							[_('II'),_('Weak'),_('Felt only by a few persons at rest,especially on upper floors of buildings.'),],
							[_('III'),_('Weak'),_('Felt quite noticeably by persons indoors, especially on upper floors of buildings. Many people do not recognize it as an earthquake. Standing motor cars may rock slightly. Vibrations similar to the passing of a truck. Duration estimated.'),],
							[_('IV'),_('Light'),_('Felt indoors by many, outdoors by few during the day. At night, some awakened. Dishes, windows, doors disturbed; walls make cracking sound. Sensation like heavy truck striking building. Standing motor cars rocked noticeably.'),],
							[_('V'),_('Moderate'),_('Felt by nearly everyone; many awakened. Some dishes, windows broken. Unstable objects overturned. Pendulum clocks may stop.'),],
							[_('VI'),_('Strong'),_('Felt by all, many frightened. Some heavy furniture moved; a few instances of fallen plaster. Damage slight.'),],
							[_('VII'),_('Very strong'),_('Damage negligible in buildings of good design and construction; slight to moderate in well-built ordinary structures; considerable damage in poorly built or badly designed structures; some chimneys broken.'),],
							[_('VIII'),_('Severe'),_('Damage slight in specially designed structures; considerable damage in ordinary substantial buildings with partial collapse. Damage great in poorly built structures. Fall of chimneys, factory stacks, columns, monuments, walls. Heavy furniture overturned.'),],
							[_('IX'),_('Violent'),_('Damage considerable in specially designed structures; well-designed frame structures thrown out of plumb. Damage great in substantial buildings, with partial collapse. Buildings shifted off foundations.'),],
							[_('X+'),_('Extreme'),_('Some well-built wooden structures destroyed; most masonry and frame structures destroyed with foundations. Rails bent.'),],
						],
						'footnotes':[
							'**'+_('A 2 percent probability of exceedance in 50 years corresponds to a ground-motion return time of approximately 2500 years, or approximately a 10% probability of of exceedance in 250 years. . The seismic intensity data and classes originate from the USGS Earthquake Hazard Map for Afghanistan (2007), by By Oliver S. Boyd, Charles S. Mueller, and Kenneth S. Rukstales'),
						]
					},
				],
			},
		}

		return self.create_response(request, response)

def getQuickOverview(request, filterLock, flag, code, response=dict_ext()):
	
	eq_event = request.GET.get('eq_event') or ''

	response.path('cache')['getEarthquake'] = response.pathget('cache','getEarthquake') or getEarthquake(request, filterLock, flag, code, includes=['eq_list','getEQData'], eq_event=eq_event, response=response.within('cache'))
	dashboard_earthquake_response = dashboard_earthquake(request, filterLock, flag, code, includes=[''], response=response.within('cache','parent_label'))
	
	return {
		'templates':{
			'panels':'dash_qoview_earthquake.html',
		},
		'data':dict_ext(dashboard_earthquake_response).within('panels','eq_list','add_link'),
	}
	