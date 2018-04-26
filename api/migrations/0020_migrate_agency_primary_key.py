# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def fill_agency_id(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Agency = apps.get_model('api', 'agency')
    for n, obj in enumerate(Agency.objects.using(db_alias).all()):
        obj.id = n
        obj.save()


def fill_fake_fk(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Agency = apps.get_model('api', 'agency')
    for n, obj in enumerate(Agency.objects.using(db_alias).all()):
        obj.orbiter_list.all().update(fake_fk=n)
        obj.launcher_list.all().update(fake_fk=n)
        obj.save()


def fix_relations(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    LauncherDetail = apps.get_model('api', 'launcherdetail')
    Agency = apps.get_model('api', 'agency')
    for obj in LauncherDetail.objects.using(db_alias).all():
        if obj.fake_fk:
            agency = Agency.objects.using(db_alias).get(id=obj.fake_fk)
            obj.launch_agency = agency
            obj.save()
    Orbiter = apps.get_model('api', 'orbiter')
    for obj in Orbiter.objects.using(db_alias).all():
        if obj.fake_fk:
            agency = Agency.objects.using(db_alias).get(id=obj.fake_fk)
            obj.launch_agency = agency
            obj.save()


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_auto_20180425_1949'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='id',
            field=models.AutoField(null=True),
        ),
        migrations.AddField(
            model_name='LauncherDetail',
            name='fake_fk',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.AddField(
            model_name='Orbiter',
            name='fake_fk',
            field=models.IntegerField(null=True, blank=True),
        ),
        migrations.RunPython(fill_fake_fk, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='LauncherDetail',
            name='launch_agency',
        ),
        migrations.RemoveField(
            model_name='Orbiter',
            name='launch_agency',
        ),
        migrations.RunPython(fill_agency_id, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='agency',
            name='agency',
            field=models.CharField(max_length=200, primary_key=False),
        ),
        migrations.AddField(
            model_name='LauncherDetail',
            name='launch_agency',
            field=models.ForeignKey(null=True, related_name='launcher_list', blank=True, to='api.Agency'),
        ),
        migrations.AddField(
            model_name='Orbiter',
            name='launch_agency',
            field=models.ForeignKey(null=True, related_name='orbiter_list', blank=True, to='api.Agency'),
        ),
        migrations.RunPython(fix_relations, migrations.RunPython.noop),
        migrations.RemoveField(
            model_name='LauncherDetail',
            name='fake_fk',
        ),
        migrations.RemoveField(
            model_name='Orbiter',
            name='fake_fk',
        ),
    ]
