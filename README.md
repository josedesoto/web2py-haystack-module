# web2py-haystack-module

La clase haystack basada en el plugin_haystack permite el acceso y manipulación de datos de Solr. Para sincronizar datos de la BBDD local con Solr, es tan simple como:
```
index = Haystack(db.auth_user, core="psycomy")
index.indexes('first_name', 'last_name')
```

Con esto la aplicación insertará, actualizará o borrará los datos sombre el core: psycomy Las lineas anteriores deben cargarse justo antes de hacer las operaciones de escritura sobre Solr.
Para realizar una búsqueda, sería:
```
index = Haystack(db.auth_user, core="psycomy")
json = index.search(compact=False, first_name='Ca*', last_name='*Gar')
```

Opciones:
* limit=20: Límite de los resultados devueltos.
* mode='AND' : Forma de combinar los campos para la búsqueda. Puede ser AND or OR.
* compact=True: Si es True, devuelve los IDs de los campos encontrados para posteriormente extraer la información de la BBDD. En el caso de False devuelve el JSON de la repuesta de Solr.
* sort='id asc': Campo por el que se quiere ordenar. Puede ser asc o desc.

En el caso de usar compact True. El acceso a la BBDD se puede hacer de la siguiente manera:
```
rows = db(index.search(first_name='CA*')).select()
```

o realizar combinaciones con otras consultas:
```
query = index.search(first_name='Ca*', last_name='*Gar')
print db(query)(db.auth_user.f_alias.endswith('r')).select() 
```

En el caso anterior es fácil cagar los datos en caso que realicen determinadas operaciones sobre la BBDD, pero ¿qué pasa si queremos cargar o reconstituir cada X tiempo el Core en Solr?
```
fields = [self.db.auth_user.id, self.db.auth_user.first_name, self.db.auth_user.last_name
query = (self.db.auth_user.id == self.db.t_common_profile.f_user_id)
core_fields={'id': 'id', 'first_name': 'first_name', 'last_name': 'last_name'}
index = Haystack(core="psycomy")
index.update(query, fields, self.db, **core_fields)
```

Lo de arriba, realizará la consulta query sobre la BBDD, seleccionará los campos: fields y cada campo los introducirá en Solr mapeándolos según core_fields

## Paginar con Solr
Para paginar en Solr es tan simple como hacer un return de:
```
from utils import paginate_solr
return paginate_solr(request.args, request.vars, self.MAXITEMS, json)
```

Donde json es el resultado de tu búsqueda son search. La salida sería:

![Alt text](./solr_json.png?raw=true "Solr json return")
