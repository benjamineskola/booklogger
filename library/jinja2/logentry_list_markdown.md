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
-   {% if verbose and entry.book.review_url %}[{{ entry.book.display_details | safe }}]({{ entry.book.review_url  }}){% else %}{{ entry.book.display_details | safe }}{% endif %}{% if verbose and entry.book.goodreads_id %} <a href="https://www.goodreads.com/book/show/{{ entry.book.goodreads_id }}" class="fab fa-goodreads"></a>{% endif %}

{% endfor %}
{% endfor %}

{% endfor %}
{% endblock content %}
