# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.contrib.gis.db.models.fields


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AfgEqHzda',
            fields=[
                ('ogc_fid', models.IntegerField(serialize=False, primary_key=True)),
                ('wkb_geometry', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('acc_val', models.FloatField(null=True, blank=True)),
                ('valley', models.IntegerField(null=True, blank=True)),
                ('seismic_intensity_and_description', models.CharField(max_length=255, blank=True)),
                ('source', models.CharField(max_length=255, blank=True)),
                ('data', models.CharField(max_length=255, blank=True)),
                ('population_at_risk', models.IntegerField(null=True, blank=True)),
                ('shape_length', models.FloatField(null=True, blank=True)),
                ('shape_area', models.FloatField(null=True, blank=True)),
                ('seismic_intensity_cat', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'db_table': 'afg_eq_hzda',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='AfgEqtUnkPplEqHzd',
            fields=[
                ('ogc_fid', models.IntegerField(serialize=False, primary_key=True)),
                ('dist_code', models.IntegerField(null=True, blank=True)),
                ('acc_val', models.FloatField(null=True, blank=True)),
                ('seismic_intensity_and_description', models.CharField(max_length=255, blank=True)),
                ('source', models.CharField(max_length=255, blank=True)),
                ('data', models.CharField(max_length=255, blank=True)),
                ('seismic_intensity_cat', models.CharField(max_length=255, blank=True)),
                ('vuid', models.CharField(max_length=255, blank=True)),
            ],
            options={
                'db_table': 'afg_eqt_unk_ppl_eq_hzd',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='earthquake_events',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wkb_geometry', django.contrib.gis.db.models.fields.PointField(srid=4326, null=True, blank=True)),
                ('event_code', models.CharField(max_length=25)),
                ('title', models.CharField(max_length=255)),
                ('dateofevent', models.DateTimeField()),
                ('magnitude', models.FloatField(null=True, blank=True)),
                ('depth', models.FloatField(null=True, blank=True)),
                ('shakemaptimestamp', models.BigIntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'earthquake_events',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='earthquake_shakemap',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('wkb_geometry', django.contrib.gis.db.models.fields.MultiPolygonField(srid=4326, null=True, blank=True)),
                ('event_code', models.CharField(max_length=25, blank=True)),
                ('shakemaptimestamp', models.BigIntegerField(null=True, blank=True)),
                ('grid_value', models.IntegerField(null=True, blank=True)),
            ],
            options={
                'db_table': 'earthquake_shakemap',
                'managed': True,
            },
        ),
        migrations.CreateModel(
            name='villagesummaryEQ',
            fields=[
                ('id', models.IntegerField(serialize=False, primary_key=True)),
                ('event_code', models.CharField(max_length=20)),
                ('village', models.CharField(max_length=255)),
                ('district', models.CharField(max_length=255)),
                ('pop_shake_weak', models.FloatField(null=True, blank=True)),
                ('pop_shake_light', models.FloatField(null=True, blank=True)),
                ('pop_shake_moderate', models.FloatField(null=True, blank=True)),
                ('pop_shake_strong', models.FloatField(null=True, blank=True)),
                ('pop_shake_verystrong', models.FloatField(null=True, blank=True)),
                ('pop_shake_severe', models.FloatField(null=True, blank=True)),
                ('pop_shake_violent', models.FloatField(null=True, blank=True)),
                ('pop_shake_extreme', models.FloatField(null=True, blank=True)),
                ('settlement_shake_weak', models.FloatField(null=True, blank=True)),
                ('settlement_shake_light', models.FloatField(null=True, blank=True)),
                ('settlement_shake_moderate', models.FloatField(null=True, blank=True)),
                ('settlement_shake_strong', models.FloatField(null=True, blank=True)),
                ('settlement_shake_verystrong', models.FloatField(null=True, blank=True)),
                ('settlement_shake_severe', models.FloatField(null=True, blank=True)),
                ('settlement_shake_violent', models.FloatField(null=True, blank=True)),
                ('settlement_shake_extreme', models.FloatField(null=True, blank=True)),
                ('buildings_shake_weak', models.FloatField(null=True, blank=True)),
                ('buildings_shake_light', models.FloatField(null=True, blank=True)),
                ('buildings_shake_moderate', models.FloatField(null=True, blank=True)),
                ('buildings_shake_strong', models.FloatField(null=True, blank=True)),
                ('buildings_shake_verystrong', models.FloatField(null=True, blank=True)),
                ('buildings_shake_severe', models.FloatField(null=True, blank=True)),
                ('buildings_shake_violent', models.FloatField(null=True, blank=True)),
                ('buildings_shake_extreme', models.FloatField(null=True, blank=True)),
            ],
            options={
                'db_table': 'villagesummary_eq',
                'managed': True,
            },
        ),
    ]
