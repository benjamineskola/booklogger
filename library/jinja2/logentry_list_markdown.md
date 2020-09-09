{%- block content -%}
{%- for entry in entries -%}
{%- if loop.changed(entry.end_date.year) %}
{%- if not loop.first %}
{% endif -%}
{%- if entry.end_date.year > 1 -%}
# Read in {{ entry.end_date.year }}

{% else -%}
# Read sometime

{% endif -%}
{%- endif -%}
- {{ entry.book | safe }}
{% endfor -%}
{%- endblock content -%}
