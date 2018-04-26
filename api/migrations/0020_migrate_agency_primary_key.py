# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


# Iterate through Agencies and their related launchers and orbiters and assign the temporary ID.
def fill_fake_keys(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Agency = apps.get_model('api', 'agency')
    print "Filling fake fks and pks"
    for n, obj in enumerate(Agency.objects.using(db_alias).all()):
        # Dont try to use 0 - things break
        n = n + 1
        obj.fake_id = n
        obj.orbiter_list.all().update(fake_fk=n)
        obj.launcher_list.all().update(fake_fk=n)
        obj.save()
    print "Completed - fake fks"


# Migrate temp ID's to override PK
def fill_agency_id(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    Agency = apps.get_model('api', 'agency')
    print "Filling new Agency ID"
    for obj in Agency.objects.using(db_alias).all():
        obj.id = obj.fake_id
        obj.save()
    print "Completed - IDs"


# Iterate through launchers and orbiters - look for those that have temp ids and assign fk's back.
def fix_relations(apps, schema_editor):
    db_alias = schema_editor.connection.alias
    LauncherDetail = apps.get_model('api', 'launcherdetail')
    Agency = apps.get_model('api', 'agency')
    for obj in LauncherDetail.objects.using(db_alias).all():
        if obj.fake_fk:
            agency = Agency.objects.using(db_alias).get(fake_id=obj.fake_fk)
            obj.launch_agency = agency
            obj.save()
    Orbiter = apps.get_model('api', 'orbiter')
    for obj in Orbiter.objects.using(db_alias).all():
        if obj.fake_fk:
            agency = Agency.objects.using(db_alias).get(fake_id=obj.fake_fk)
            obj.launch_agency = agency
            obj.save()
    print "Completed - relations"


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_auto_20180425_1949'),
    ]

    operations = [

        # Start by creating temporary ID fields to persist relationships for all related objects.
        migrations.AddField(
            model_name='agency',
            name='fake_id',
            field=models.IntegerField(null=True),
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
        migrations.RunPython(fill_fake_keys, migrations.RunPython.noop),

        # Remove relationship fields
        migrations.RemoveField(
            model_name='LauncherDetail',
            name='launch_agency',
        ),
        migrations.RemoveField(
            model_name='Orbiter',
            name='launch_agency',
        ),

        # Create new PK field, remove PK from CharField and then make new ID PK
        migrations.AddField(
            model_name='agency',
            name='id',
            field=models.AutoField(null=True),
        ),
        migrations.AlterField(
            model_name='agency',
            name='agency',
            field=models.CharField(max_length=200, primary_key=False),
        ),
        migrations.AlterField(
            model_name='agency',
            name='id',
            field=models.AutoField(null=True, primary_key=True),
        ),

        # Rebuild relationships using temp IDs
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

        # Remove Temp ID's
        migrations.RemoveField(
            model_name='LauncherDetail',
            name='fake_fk',
        ),
        migrations.RemoveField(
            model_name='Orbiter',
            name='fake_fk',
        ),
        migrations.RemoveField(
            model_name='Agency',
            name='fake_id',
        ),
    ]
