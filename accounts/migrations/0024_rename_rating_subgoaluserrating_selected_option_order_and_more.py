# Generated by Django 5.1.7 on 2025-04-22 19:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0023_remove_subgoal_option1_remove_subgoal_option2_and_more'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subgoaluserrating',
            old_name='rating',
            new_name='selected_option_order',
        ),
        migrations.AddField(
            model_name='subgoaluserrating',
            name='selected_option',
            field=models.CharField(default=0, max_length=150),
            preserve_default=False,
        ),
    ]
