{% macro select_clean_flattened_dict_columns(relation, table_alias='b') %}
    {% if execute %}
        {% set cols = adapter.get_columns_in_relation(relation) %}
        {% set expressions = [] %}
        {% for col in cols %}
            {% set col_name = col.name %}
            {% if '__' in col_name %}
                {% set expr = "nullif(trim(cast(" ~ table_alias ~ ".\"" ~ col_name ~ "\" as text)), '') as \"" ~ col_name ~ "_clean\"" %}
                {% do expressions.append(expr) %}
            {% endif %}
        {% endfor %}
        {{ return(expressions | join(',\n    ')) }}
    {% else %}
        {{ return('') }}
    {% endif %}
{% endmacro %}
