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
- {{ entry.book.display_details | safe }}
{% endfor -%}

{%- for month, month_entries in year_entries | selectattr('end_precision', 'lt', 2) | groupby('end_date.month') %}

## {{ month_entries[0].end_date.strftime("%B") }}{% if verbose %} {{ '{#' +  month_entries[0].end_date.strftime("%B-%Y").lower()  + '}' }}{% endif %}

{% for entry in month_entries %}
-   {{ entry.book.display_details | safe }}{% if verbose and ( entry.book.goodreads_id or entry.book.review_url ) %} [{% if entry.book.goodreads_id %}<a href="https://www.goodreads.com/book/show/{{ entry.book.goodreads_id }}" class="fab fa-goodreads"></a>{% endif %}
    {%- if entry.book.goodreads_id and entry.book.review_url %}, {% endif -%}
    {% if entry.book.review_url %}([review]({{ entry.book.review_url }})){% endif %}]{.small .text-muted}{% endif %}

{% endfor %}
{% endfor %}

{% endfor %}
{% endblock content %}
