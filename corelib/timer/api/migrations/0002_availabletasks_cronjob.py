# Generated by Django 3.2 on 2021-04-29 08:57

from django.db import migrations, models
import django.utils.timezone
import jsonfield.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AvailableTasks',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('module_path', models.TextField(default='', verbose_name='任务函数路径')),
                ('usage_doc', models.TextField(default='', verbose_name='使用说明')),
            ],
        ),
        migrations.CreateModel(
            name='CronJob',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(default='', max_length=128, unique=True, verbose_name='任务名称')),
                ('description', models.TextField(default='', verbose_name='任务描述')),
                ('task', models.TextField(default='', verbose_name='任务函数')),
                ('args', jsonfield.fields.JSONField(default=[], verbose_name='位置参数')),
                ('kwargs', jsonfield.fields.JSONField(default={}, verbose_name='键值参数')),
                ('every', models.IntegerField(default=0, verbose_name='执行间隔')),
                ('crontab', models.TextField(default='', verbose_name='crontab配置')),
                ('at_time', models.DateTimeField(default=None, null=True, verbose_name='任务创建时间')),
                ('enabled', models.IntegerField(choices=[(0, '已停用'), (1, '已启用')], default=1, verbose_name='是否启用')),
                ('expired_count', models.IntegerField(default=0, verbose_name='失效次数设置')),
                ('last_run_start_at', models.DateTimeField(default=None, null=True, verbose_name='最后一次执行时间')),
                ('last_run_spend_time', models.FloatField(default=0, verbose_name='最后一次执行耗时')),
                ('last_run_result', models.CharField(choices=[('', '未知'), ('success', '成功'), ('failed', '失败')], default='', max_length=16, verbose_name='最后一次执行结果')),
                ('total_run_count', models.IntegerField(default=0, verbose_name='总共执行次数')),
                ('create_at', models.DateTimeField(default=django.utils.timezone.now, verbose_name='任务创建时间')),
            ],
            options={
                'ordering': ['-id'],
            },
        ),
    ]
