from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('creme_core', '0111_v2_4__rtype_forbidden_properties'),
    ]

    operations = [
        migrations.AddField(
            model_name='worldsettings',
            name='password_change_enabled',
            field=models.BooleanField(
                default=True,
                verbose_name='Allow all users to change their own password?',
            ),
        ),
        migrations.AddField(
            model_name='worldsettings',
            name='password_reset_enabled',
            field=models.BooleanField(
                default=True,
                verbose_name='Enable the «Lost password» feature?',
                help_text=(
                    'This feature allows users to reset their password if they forgot it. '
                    'The login page proposes to receive an e-mail to start the reset process.'
                ),
            ),
        ),
    ]
