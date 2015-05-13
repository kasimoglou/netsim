#
# JSON Reader 
#
# A class for parsing json into model objects
# 

from models.mf import RelKind, python_type, annotation_class, Attribute




##################################################################
#
# Some attribute annotations.  See nsd.py for an example
#
##################################################################

# Declare an attribute to have another name in json
json_name = annotation_class('json_name', ('name'))

# Declare a required attribute to map
required = annotation_class('required',())()

# Declare an ignored attribute. Even if it can be
# mapped in json, it is left alone!
ignore = annotation_class('ignore', ())()


#
# relationship annotation
#

# Create (if needed) an object for this relationship and 
# descend into the json object.
# Json objects correspond to ref and json arrays to 
# ref_list or refs.
#
# Example:
#
#class Foo:
#    a = ref(...)
#    descend(a)
#
#    b = ref_list(...)
#    descend(b)
#
#json = {
#    ...
#    "a "= { 
#        ...
#    },
#
#    "b" = [ 
#        { ... },
#        { ... }
#    ],
#}

descend = annotation_class('descend',())()


#
#  
#


class TransformValueError(ValueError):
    '''
    Error transforming a value from json.
    '''
    def __init__(self, attr, value):
        super().__init__(attr,value)
        self.attr = attr
        self.value = value

class RequiredMissingError(NameError):
    '''
    A required attribute of relationship is missing
    '''
    def __init__(self, element):
        super().__init__(element)
        self.element = element

class DescendError(TypeError):
    '''
    Error descending to a json subobject.
    '''
    def __init__(self, rel):
        self.rel=rel


class JSONReader:
    '''
    Instances of this class can be used to provide for translation
    of a json object into a hierarchy of model objects.
    '''

    def __init__(self, log):
        self.log = log

    def transform_value(self, attr, value):
        """Transform a value so that it is assignment-compatible the given mf.Attribute.
        """
        assert isinstance(attr, Attribute)
        
        if isinstance(value, attr.type):
            return value 
        if attr.nullable and value is None:
            return value
        
        try:
            # try a default python conversion
            tval = attr.type(value)
            return tval
        except Exception as e:
            raise TransformValueError(attr,value) from e


    def populate_modeled_instance(self, model, json):
        """
        Given a model object and a json dict, fill in the attributes of model
        from the json dict.
        
        This method will cast certain types to others, using transform_value.
        """

        metamodel = model.__model_class__
        json_fields = set(json.keys())

        self.log.debug('Mapping for %s', metamodel.name)
        
        # Map the model attributes         
        for attr in metamodel.attributes:
            # Respect 'ignore' annotation
            if ignore.has(attr):
                continue

            # here we respect name mapping by a 'json_name' annotation
            json_field = json_name.get_item(attr, default=attr.name)
            map_msg = "%s (json=%s)" % (attr.name, json_field) \
                if attr.name != json_field else json_field

            # look up attribute in json object
            if json_field in json:
                json_fields.remove(json_field)
                tval = self.transform_value(attr, json[json_field])
                setattr(model, attr.name, tval)                

                self.log.debug('   Mapped attribute %s = %s', map_msg, tval)
            else:
                if required.has(attr):
                    raise RequiredMissingError(attr)
                self.log.debug('   Skipped attribute %s', map_msg)

        # Map the relationships
        for rel in metamodel.relationships:
            # only process those relationships annotated as 'descend'
            if not descend.has(rel): continue

            # here we respect name mapping by a 'json_name' annotation
            json_field = json_name.get_item(rel, default=rel.name)
            map_msg = "%s (json=%s)" % (rel.name, json_field) \
                if rel.name != json_field else json_field

            # look up name in json object
            if json_field in json:
                json_value = json[json_field]

                if isinstance(json_value, list)==(rel.kind is RelKind.ONE):
                    raise DescendError(rel)

                # ok, now create subobject(s) (must be default constructibe)
                submodel_class = python_type.get_item(rel.target)
                # a small trick: to handle both a json subobject and a sublist
                # in the same way, make the object into a list of one item!
                if not isinstance(json_value, list):
                    subitems = [json_value]
                else:
                    subitems = json_value

                # loop over subitems
                for subitem in subitems:               
                    subobj = submodel_class()
                    self.populate_modeled_instance(subobj, subitem)
                    # establish the association
                    getattr(model.__class__, rel.name).associate(model, subobj)

                # all done, mark field as processed
                json_fields.remove(json_field)
                self.log.debug('   Mapped subobject %s ', map_msg)

            else:
                if required.has(rel):
                    raise RequiredMissingError(rel)
                self.log.debug('   Skipped subobject %s', map_msg)


        for f in json_fields:
            self.log.debug('   Ignored json field %s', f)


        self.log.debug('Done mapping for %s', metamodel.name)

