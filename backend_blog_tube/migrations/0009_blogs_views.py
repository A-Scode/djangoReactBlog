# Generated by Django 3.2.7 on 2021-09-19 06:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('backend_blog_tube', '0008_auto_20210918_0714'),
    ]

    operations = [
        migrations.AddField(
            model_name='blogs',
            name='views',
            field=models.IntegerField(default=0),
        ),
    ]
