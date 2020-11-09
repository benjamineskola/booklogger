{% block content %}
{% for year, year_entries in entries | groupby('end_date.year') | sort | reverse %}
{% if year > 1 %}
# Read in {{ year }}
{% else %}
# Read sometime
{% endif %}
{% for month, month_entries in year_entries | groupby('end_date.month') %}

- **{{ month_entries[0].end_date.strftime("%B") }}**
{% for entry in month_entries %}
  - {{ entry.book.first_author | safe }}, _{{ entry.book.display_title | safe }}_
{% endfor %}
{% endfor %}

{% endfor %}
{% endblock content %}
