{% block content %}
{% for year, year_entries in entries | groupby('end_date.year') | sort | reverse %}
{% if year > 1 %}
# Read in {{ year }}
{% else %}
# Read sometime
{% endif %}
{% for entry in year_entries | selectattr('end_precision', 'eq', 2) %}
{% if entry == year_entries[0] %}

{% endif %}
- {{ entry.book.first_author | safe }}, _{{ entry.book.display_title | safe }}_
{% endfor -%}

{%- for month, month_entries in year_entries | selectattr('end_precision', 'lt', 2) | groupby('end_date.month') %}

- **{{ month_entries[0].end_date.strftime("%B") }}**
{% for entry in month_entries %}
  - {{ entry.book.first_author | safe }}, _{{ entry.book.display_title | safe }}_
{% endfor %}
{% endfor %}

{% endfor %}
{% endblock content %}
