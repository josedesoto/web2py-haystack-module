# -*- coding: utf-8 -*-
from collections import OrderedDict
from gluon.html import URL


def paginate_solr(args, vars, max_items, json):
    limit = max_items
    def remove_duplicates(values):
        output = []
        seen = set()
        for value in values:
            # If value has not been encountered yet,
            # ... add it to both list and set.
            if value['id'] not in seen:
                output.append(value)
                seen.add(value['id'])
        return output

    r = OrderedDict()
    r['items'] = {
            'items_found': json.numFound,
            'data': remove_duplicates(json.docs),
        }

    vars['_offset'] = json.start + limit
    if vars['_offset'] < json.numFound:
        r['next'] = {'rel': 'next',
                     'href': URL(args=args, vars=vars, scheme=True)}

    if json.start >= limit:
        vars['_offset'] = json.start - limit
        r['previous'] = {'rel': 'previous',
                         'href': URL(args=args, vars=vars, scheme=True)}
    return r