# Generated by Django 3.0.2 on 2020-02-05 11:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('library', '0021_date_to_datetime_20200204_1637'),
    ]

    operations = [
        migrations.AlterField(
            model_name='book',
            name='edition_language',
            field=models.CharField(blank=True, choices=[('mk', 'Macedonian'), ('he', 'Hebrew'), ('th', 'Thai'), ('ar', 'Arabic'), ('sk', 'Slovak'), ('os', 'Ossetic'), ('ga', 'Irish'), ('ro', 'Romanian'), ('el', 'Greek'), ('br', 'Breton'), ('kk', 'Kazakh'), ('it', 'Italian'), ('uk', 'Ukrainian'), ('ta', 'Tamil'), ('az', 'Azerbaijani'), ('id', 'Indonesian'), ('et', 'Estonian'), ('my', 'Burmese'), ('ru', 'Russian'), ('ne', 'Nepali'), ('gd', 'Scottish Gaelic'), ('sq', 'Albanian'), ('fi', 'Finnish'), ('lv', 'Latvian'), ('sw', 'Swahili'), ('mr', 'Marathi'), ('de', 'German'), ('ka', 'Georgian'), ('ko', 'Korean'), ('gl', 'Galician'), ('eu', 'Basque'), ('fy', 'Frisian'), ('tr', 'Turkish'), ('io', 'Ido'), ('mn', 'Mongolian'), ('nb', 'Norwegian Bokmål'), ('be', 'Belarusian'), ('cy', 'Welsh'), ('ja', 'Japanese'), ('hu', 'Hungarian'), ('pt', 'Portuguese'), ('ia', 'Interlingua'), ('te', 'Telugu'), ('vi', 'Vietnamese'), ('nl', 'Dutch'), ('lb', 'Luxembourgish'), ('ml', 'Malayalam'), ('hy', 'Armenian'), ('is', 'Icelandic'), ('af', 'Afrikaans'), ('bs', 'Bosnian'), ('fa', 'Persian'), ('uz', 'Uzbek'), ('ca', 'Catalan'), ('lt', 'Lithuanian'), ('en', 'English'), ('ur', 'Urdu'), ('bn', 'Bengali'), ('cs', 'Czech'), ('da', 'Danish'), ('km', 'Khmer'), ('nn', 'Norwegian Nynorsk'), ('pa', 'Punjabi'), ('pl', 'Polish'), ('hr', 'Croatian'), ('kn', 'Kannada'), ('sl', 'Slovenian'), ('hi', 'Hindi'), ('sr', 'Serbian'), ('fr', 'French'), ('es', 'Spanish'), ('tt', 'Tatar'), ('bg', 'Bulgarian'), ('sv', 'Swedish'), ('eo', 'Esperanto')], max_length=2),
        ),
        migrations.AlterField(
            model_name='book',
            name='language',
            field=models.CharField(choices=[('mk', 'Macedonian'), ('he', 'Hebrew'), ('th', 'Thai'), ('ar', 'Arabic'), ('sk', 'Slovak'), ('os', 'Ossetic'), ('ga', 'Irish'), ('ro', 'Romanian'), ('el', 'Greek'), ('br', 'Breton'), ('kk', 'Kazakh'), ('it', 'Italian'), ('uk', 'Ukrainian'), ('ta', 'Tamil'), ('az', 'Azerbaijani'), ('id', 'Indonesian'), ('et', 'Estonian'), ('my', 'Burmese'), ('ru', 'Russian'), ('ne', 'Nepali'), ('gd', 'Scottish Gaelic'), ('sq', 'Albanian'), ('fi', 'Finnish'), ('lv', 'Latvian'), ('sw', 'Swahili'), ('mr', 'Marathi'), ('de', 'German'), ('ka', 'Georgian'), ('ko', 'Korean'), ('gl', 'Galician'), ('eu', 'Basque'), ('fy', 'Frisian'), ('tr', 'Turkish'), ('io', 'Ido'), ('mn', 'Mongolian'), ('nb', 'Norwegian Bokmål'), ('be', 'Belarusian'), ('cy', 'Welsh'), ('ja', 'Japanese'), ('hu', 'Hungarian'), ('pt', 'Portuguese'), ('ia', 'Interlingua'), ('te', 'Telugu'), ('vi', 'Vietnamese'), ('nl', 'Dutch'), ('lb', 'Luxembourgish'), ('ml', 'Malayalam'), ('hy', 'Armenian'), ('is', 'Icelandic'), ('af', 'Afrikaans'), ('bs', 'Bosnian'), ('fa', 'Persian'), ('uz', 'Uzbek'), ('ca', 'Catalan'), ('lt', 'Lithuanian'), ('en', 'English'), ('ur', 'Urdu'), ('bn', 'Bengali'), ('cs', 'Czech'), ('da', 'Danish'), ('km', 'Khmer'), ('nn', 'Norwegian Nynorsk'), ('pa', 'Punjabi'), ('pl', 'Polish'), ('hr', 'Croatian'), ('kn', 'Kannada'), ('sl', 'Slovenian'), ('hi', 'Hindi'), ('sr', 'Serbian'), ('fr', 'French'), ('es', 'Spanish'), ('tt', 'Tatar'), ('bg', 'Bulgarian'), ('sv', 'Swedish'), ('eo', 'Esperanto')], default='en', max_length=2),
        ),
    ]