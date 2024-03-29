# Generated by Django 3.2.2 on 2021-05-08 08:04

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('async_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AsyncTask',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('uuid', models.CharField(default='', max_length=128, unique=True, verbose_name='UUID')),
                ('name', models.CharField(default='', max_length=128, verbose_name='任务名称')),
                ('status', models.IntegerField(choices=[(0, '等待执行'), (1, '正在执行'), (2, '执行完毕')], default=0, verbose_name='执行状态')),
                ('result', models.BooleanField(default=True, verbose_name='执行结果')),
                ('result_data', jsonfield.fields.JSONField(default={}, verbose_name='执行返回数据')),
                ('create_time', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('finish_time', models.DateTimeField(null=True, verbose_name='完成时间')),
            ],
        ),
    ]
