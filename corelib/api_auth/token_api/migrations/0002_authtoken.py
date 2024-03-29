# Generated by Django 3.2.2 on 2021-05-08 08:04

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('token_api', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='AuthToken',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False, verbose_name='ID')),
                ('username', models.CharField(default='', max_length=64, verbose_name='用户名称')),
                ('token', models.CharField(default='', max_length=64, verbose_name='用户TOKEN')),
                ('sign_date', models.DateTimeField(auto_now_add=True, verbose_name='注册日期')),
                ('expired_time', models.IntegerField(default=86400, verbose_name='有效期限')),
            ],
            options={
                'unique_together': {('username', 'token')},
            },
        ),
    ]
