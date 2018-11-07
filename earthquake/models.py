from __future__ import unicode_literals

from django.contrib.gis.db import models
# from geodb.models import AfgShedaLvl4

class earthquake_events(models.Model):
    wkb_geometry = models.PointField(blank=True, null=True)
    event_code = models.CharField(max_length=25, blank=False)
    title = models.CharField(max_length=255, blank=False)
    dateofevent = models.DateTimeField(blank=False, null=False)
    magnitude = models.FloatField(blank=True, null=True)
    depth = models.FloatField(blank=True, null=True)
    shakemaptimestamp = models.BigIntegerField(blank=True, null=True)
    objects = models.GeoManager()
    class Meta:
        managed = True
        db_table = 'earthquake_events'

class earthquake_shakemap(models.Model):
    id = models.IntegerField(primary_key=True)
    wkb_geometry = models.MultiPolygonField(blank=True, null=True)
    event_code = models.CharField(max_length=25, blank=True)
    shakemaptimestamp = models.BigIntegerField(blank=True, null=True)
    grid_value = models.IntegerField(blank=True, null=True)
    objects = models.GeoManager()
    class Meta:
        managed = True
        db_table = 'earthquake_shakemap'             

class villagesummaryEQ(models.Model):
    id = models.IntegerField(primary_key=True)
    event_code = models.CharField(max_length=20)
    village = models.CharField(max_length=255)
    district = models.CharField(max_length=255)
    pop_shake_weak = models.FloatField(blank=True, null=True)
    pop_shake_light = models.FloatField(blank=True, null=True)
    pop_shake_moderate = models.FloatField(blank=True, null=True)
    pop_shake_strong = models.FloatField(blank=True, null=True)
    pop_shake_verystrong = models.FloatField(blank=True, null=True)
    pop_shake_severe = models.FloatField(blank=True, null=True)
    pop_shake_violent = models.FloatField(blank=True, null=True)
    pop_shake_extreme = models.FloatField(blank=True, null=True)
    settlement_shake_weak = models.FloatField(blank=True, null=True)
    settlement_shake_light = models.FloatField(blank=True, null=True)
    settlement_shake_moderate = models.FloatField(blank=True, null=True)
    settlement_shake_strong = models.FloatField(blank=True, null=True)
    settlement_shake_verystrong = models.FloatField(blank=True, null=True)
    settlement_shake_severe = models.FloatField(blank=True, null=True)
    settlement_shake_violent = models.FloatField(blank=True, null=True)
    settlement_shake_extreme = models.FloatField(blank=True, null=True)
    buildings_shake_weak = models.FloatField(blank=True, null=True)
    buildings_shake_light = models.FloatField(blank=True, null=True)
    buildings_shake_moderate = models.FloatField(blank=True, null=True)
    buildings_shake_strong = models.FloatField(blank=True, null=True)
    buildings_shake_verystrong = models.FloatField(blank=True, null=True)
    buildings_shake_severe = models.FloatField(blank=True, null=True)
    buildings_shake_violent = models.FloatField(blank=True, null=True)
    buildings_shake_extreme = models.FloatField(blank=True, null=True)
    class Meta:
        managed = True
        db_table = 'villagesummary_eq'

class AfgEqHzda(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    wkb_geometry = models.MultiPolygonField(blank=True, null=True)
    acc_val = models.FloatField(blank=True, null=True)
    valley = models.IntegerField(blank=True, null=True)
    seismic_intensity_and_description = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=255, blank=True)
    data = models.CharField(max_length=255, blank=True)
    population_at_risk = models.IntegerField(blank=True, null=True)
    shape_length = models.FloatField(blank=True, null=True)
    shape_area = models.FloatField(blank=True, null=True)
    seismic_intensity_cat = models.CharField(max_length=255, blank=True)
    objects = models.GeoManager()
    class Meta:
        managed = True
        db_table = 'afg_eq_hzda'

class AfgEqtUnkPplEqHzd(models.Model):
    ogc_fid = models.IntegerField(primary_key=True)
    dist_code = models.IntegerField(blank=True, null=True)
    acc_val = models.FloatField(blank=True, null=True)
    seismic_intensity_and_description = models.CharField(max_length=255, blank=True)
    source = models.CharField(max_length=255, blank=True)
    data = models.CharField(max_length=255, blank=True)
    seismic_intensity_cat = models.CharField(max_length=255, blank=True)
    vuid = models.CharField(max_length=255, blank=True)
    class Meta:
        managed = True
        db_table = 'afg_eqt_unk_ppl_eq_hzd'
