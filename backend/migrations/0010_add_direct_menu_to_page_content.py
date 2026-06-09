from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('backend', '0009_contact_logo'),
    ]

    operations = [
        # ── PageSection: make submenu nullable, add menu FK ──────────────────
        migrations.AlterField(
            model_name='pagesection',
            name='submenu',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='sections',
                to='backend.submenu',
            ),
        ),
        migrations.AddField(
            model_name='pagesection',
            name='menu',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='page_sections',
                to='backend.menu',
            ),
        ),

        # ── PagePhoto: make submenu nullable, add menu FK ────────────────────
        migrations.AlterField(
            model_name='pagephoto',
            name='submenu',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='photos',
                to='backend.submenu',
            ),
        ),
        migrations.AddField(
            model_name='pagephoto',
            name='menu',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='page_photos',
                to='backend.menu',
            ),
        ),

        # ── PageRichText: make submenu nullable, add menu FK ─────────────────
        migrations.AlterField(
            model_name='pagerichtext',
            name='submenu',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='rich_texts',
                to='backend.submenu',
            ),
        ),
        migrations.AddField(
            model_name='pagerichtext',
            name='menu',
            field=models.ForeignKey(
                blank=True, null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='page_rich_texts',
                to='backend.menu',
            ),
        ),
    ]
