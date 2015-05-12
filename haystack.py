"""
extend from plugin_haystack.py by Massimo Di Pierro
It allows full text search using database Solr.


Usage:
index = Haystack(db.thing)                        # table to be indexed
index.indexes('name','description')               # fields to be indexed
db.thing.insert(name='Char',description='A char') # automatically indexed
db(db.thing.id).update(description='The chair')   # automatically re-indexed
db(db.thing).delete()                             # automatically re-indexed
query = index.search(name='chair',description='the')
print db(query).select()

Info about parameters in Solr: https://cwiki.apache.org/confluence/display/solr/Common+Query+Parameters

"""

import logging
from gluon import current
request = current.request

logger = logging.getLogger("web2py.app." + request.application)
logger.setLevel(logging.DEBUG) # INFO, DEBUG, WARNNING, ERROR, CRITICAL


try:
    from solrcloudpy import SolrConnection, SearchOptions
except ImportError:
    logger.warning("Cannot find SolrConnection")
    raise ImportError("Cannot find SolrConnection")


class SolrBackend(object):
    def __init__(self, table, core="collection1"):
        self.table = table
        self.core = core
        self.url = 'localhost:8983'
        try:
            self.interface = SolrConnection(self.url)[self.core]
        except Exception as e:
            logger.warning("Cannot connect to Solr: %s" % e)
            raise RuntimeError("Cannot connect to Solr: %s" % e)

    def get_ids(self, queryset):
        return [r.id for r in queryset.select(self.table._id)]

    def indexes(self, *fieldnames):
        self.fieldnames = fieldnames

    def after_insert(self, fields, id):
        document = [{'id': id}]
        for name in self.fieldnames:
            if name in fields:
                document[0][name] = unicode(fields[name])
        self.interface.add(document)
        self.interface.commit()
        return True

    def after_update(self, queryset, fields):
        """ caveat, this should work but only if ALL indexed fields are updated at once """
        ids = self.get_ids(queryset)
        documents = []
        for id in ids:
            self.interface.delete(id)
            document = {'id':id}
            for name in self.fieldnames:
                if name in fields:
                    document[name] = unicode(fields[name])
            documents.append(document)
        self.interface.add(documents)
        self.interface.commit()
        return True

    def update(self, query, fields, db, **core_fields):
        '''
        Usage:

        '''
        rows = db(query).select(*fields)
        documents = []
        for row in rows:
            document={}
            for key in row.keys():
                for core_field in core_fields:
                    if core_field in row[key]:
                        document[core_fields[core_field]] = unicode(row[key][core_field])
                        if core_field == 'id':
                            self.interface.delete(row[key][core_field])
            documents.append(document)
        self.interface.add(documents)
        self.interface.commit()
        return True

    def before_delete(self, queryset):
        self.ids = self.get_ids(queryset)
        return False

    def after_delete(self):
        for id in self.ids:
            self.interface.delete(id=id)
        self.interface.commit()
        return True

    def meta_search(self, limit, offset, mode, compact, sort, **fieldkeys):
        query = ''
        items = len(fieldkeys)
        count = 0
        # Convert to solrcloudpy search
        for fieldkey in fieldkeys:
            query += " %s:%s " % (fieldkey, fieldkeys[fieldkey])
            count += 1
            if items > 1 and count < items:
                query += mode

        se = SearchOptions()
        se.commonparams.q(query).rows(limit).sort(sort).start(offset)
        print se
        response = self.interface.search(se)
        if compact:
            return [r['id'] for r in response.result['response'].docs]
        return response.result['response']


class Haystack(object):
    def __init__(self, table=None, backend=SolrBackend, **attr):
        self.table = table
        self.backend = backend(table, **attr)

    def indexes(self, *fieldnames):
        invalid = [f for f in fieldnames if not f in self.table.fields() or
                   not self.table[f].type in ('string', 'text')]

        if invalid:
            raise RuntimeError("Unable to index fields: %s" % ', '.join(invalid))
        self.backend.indexes(*fieldnames)
        self.table._after_insert.append(
            lambda fields, id: self.backend.after_insert(fields, id))
        self.table._after_update.append(
            lambda queryset, fields: self.backend.after_update(queryset, fields))

        # Get all the Ids will be deleted
        self.table._before_delete.append(
            lambda queryset: self.backend.before_delete(queryset))
        self.table._after_delete.append(
            lambda queryset: self.backend.after_delete(queryset))

    def search(self, limit=20, offset=0, mode='AND', compact=True, sort='id asc', **fieldkeys):
        if compact:
            ids = self.backend.meta_search(limit, offset, mode, compact, sort, **fieldkeys)
            return self.table._id.belongs(ids)
        return self.backend.meta_search(limit, offset, mode, compact, sort, **fieldkeys)

    def update(self, query, fields, db, **arguments):
        return self.backend.update(query, fields, db, **arguments)