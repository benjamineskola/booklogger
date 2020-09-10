{%- block content -%}
{%- for entry in entries -%}
{%- if loop.changed(entry.end_date.strftime("%B %Y")) %}
{%- if loop.first or loop.previtem.end_date.year != entry.end_date.year -%}
{%- if entry.end_date.year > 1 -%}
# Read in {{ entry.end_date.year }}
{%- else -%}
# Read sometime
{%- endif -%}
{%- endif %}

- **{{ entry.end_date.strftime("%B") }}**
{%- endif %}
  - {{ entry.book.first_author | safe }}, _{{ entry.book.display_title | safe }}_
{%- if not loop.last and loop.nextitem.end_date.year != entry.end_date.year %}

{% endif -%}
{%- endfor %}
{%- endblock content -%}
