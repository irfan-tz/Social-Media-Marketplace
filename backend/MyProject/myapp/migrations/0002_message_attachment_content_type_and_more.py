# Generated by Django 5.1.5 on 2025-03-31 10:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('myapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='message',
            name='attachment_content_type',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='message',
            name='original_filename',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
