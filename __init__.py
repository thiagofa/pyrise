import httplib2
import re
import sys
import datetime
from xml.etree import ElementTree

VERSION = '0.1'

class Highrise:
    """Class designed to handle all interactions with the Highrise API."""
    
    _http = httplib2.Http()
    _server = None

    @classmethod
    def auth(cls, token):
        """Define the settings used to connect to Highrise"""
        
        # add the credentials to the HTTP connection
        cls._http.add_credentials(token, 'X')
    
    @classmethod
    def set_server(cls, server):
        """Define the server to be used for API requests"""
        
        if server[:4] == 'http':
            cls._server = server.strip('/') 
        else:
            cls._server = "https://%s.highrisehq.com" % server
    
    @classmethod
    def request(cls, path, method='GET', xml=None):
        """Process an arbitrary request to Highrise.
        
        Ordinarily, you shouldn't have to call this method directly,
        but it's available to send arbitrary requests if needed."""
        
        # build the base request URL
        url = '%s/%s' % (cls._server, path.strip('/'))
        
        # create the curl command
        if method in ('GET', 'DELETE'):
            request, content = cls._http.request(url, method=method)
        else:
            request, content = cls._http.request(url, method=method, body=xml, headers={'content-type': 'application/xml'})
        
        # raise appropriate exceptions if there is an error
        status = int(request['status'])
        if status >= 400:
            if status == 400:
                raise BadRequest
            elif status == 401:
                raise AuthorizationRequired, content
            elif status == 403:
                raise Forbidden, content
            elif status == 404:
                raise NotFound, content
            elif status == 422:
                raise GatewayFailure, content
            elif status == 502:
                raise GatewayConnectionError, content
            elif status == 507:
                raise InsufficientStorage, content
            else:
                raise UnexpectedResponse, content
    
        # if this was a PUT or DELETE request, return status (hopefully success)
        if method in ('PUT', 'DELETE'):
            return status
        
        # for GET and POST requests, return the XML response
        try:
            return ElementTree.fromstring(content)
        except:
            raise UnexpectedResponse, "The server sent back something that wasn't valid XML."

    @classmethod
    def key_to_class(cls, key):
        """Utility method to convert a hyphenated key (like what is used
        in Highrise XML responses) to a Python class name"""

        klass = key.capitalize()
        while '-' in klass:
            ix = klass.index('-')
            next = klass[ix + 1].upper()
            klass = klass[0:ix] + next + klass[ix + 2:]

        return klass

    @classmethod
    def class_to_key(cls, key):
        """Utility method to convert a Python class name to a hyphenated
        key (like what is used in Highrise XML responses)"""

        match = re.search(r'([A-Z])', key)
        while match:
            char = match.groups()[0]
            key = key.replace(char, '-' + char.lower())
            match = re.search(r'([A-Z])', key)

        return key[1:]


class HighriseObject(object):
    """Base class for all Highrise data objects"""
    
    @classmethod
    def from_xml(cls, xml, parent=None):
        """Create a new object from XML data"""
        
        # instiantiate the object
        self = cls()
        
        for child in xml.getchildren():
            
            # convert the key to underscore notation for Python
            key = child.tag.replace('-', '_')
        
            # if there is no data, just set the default
            if child.text == None:
                self.__dict__[key] = self.fields[key].default
                continue

            # handle the contact-data key differently
            if key == 'contact_data':
                klass = getattr(sys.modules[__name__], 'ContactData')
                self.contact_data = klass.from_xml(child, parent=self)
                continue

            # if this an element with children, it's an object relationship
            if len(child.getchildren()) > 0:
                items = []
                for item in child.getchildren():
                    klass = getattr(sys.modules[__name__], Highrise.key_to_class(item.tag))
                    items.append(klass.from_xml(item, parent=self))
                self.__dict__[child.tag.replace('-', '_')] = items
                continue
                
            # get and convert attribute value based on type
            data_type = child.get('type')
            if data_type == 'integer':
                value = int(child.text)
            elif data_type == 'datetime':
                value = datetime.datetime.strptime(child.text, '%Y-%m-%dT%H:%M:%SZ')
            else:
                value = unicode(child.text)

            # add value to object dictionary
            self.__dict__[key] = value
                
        return self

    @classmethod
    def _list(cls, path, tag):
        """Get a list of objects of this type from Highrise"""

        # retrieve the data from Highrise
        objects = []
        xml = Highrise.request(path)

        # make a list of objects and return it
        for item in xml.getiterator(tag=tag):
            objects.append(cls.from_xml(item))

        return objects


    def __init__(self, parent=None, **kwargs):
        """Create a new object manually."""

        self._server = Highrise._server
        for field, settings in self.fields.iteritems():
            if field in kwargs:
                if not settings.is_editable:
                    raise KeyError, '%s is not an editable attribute' % field
                value = kwargs.pop(field)
            else:
                value = settings.default
            self.__dict__[field] = value
        
    
    def save_xml(self, include_id=False, **kwargs):
        """Return the object XML for sending back to Highrise"""
        
        # create new XML object
        if 'base_element' not in kwargs:
            kwargs['base_element'] = Highrise.class_to_key(self.__class__.__name__)
        xml = ElementTree.Element(kwargs['base_element'])
        
        # if the id should be included and it is not None, add it first
        if include_id and 'id' in self.__dict__ and self.id != None:
            xml.insert(0, ElementTree.Element(tag='id', text=str(self.id)))

        # now iterate over the editable attributes
        for field, settings in self.fields.iteritems():
            
            # get the value for this field, or pass if it is missing
            if field in self.__dict__:
                value = self.__dict__[field]
            else:
                continue
            
            # if the field is not editable, don't pass it
            if not settings.is_editable:
                continue
            
            # if the value is equal to the default, don't pass it
            if value == settings.default:
                continue
            
            # if the value is a HighriseObject, insert the XML for it
            if isinstance(value, HighriseObject):
                xml.insert(0, value.save_xml(include_id=True))
                continue
            
            # insert the remaining single-attribute elements
            e = ElementTree.Element(field.replace('_', '-'))
            if isinstance(value, int):
                e.text = str(value)
            elif isinstance(value, list):
                if len(value) == 0:
                    continue
                for item in value:
                    e.insert(0, item.save_xml(include_id=True))
            else:
                e.text = value
            xml.insert(0, e)

        # return the final XML Element object
        return xml


class HighriseField(object):
    """An object to represent the settings for an object attribute
    Note that a lot more detail could go into how this works."""

    def __init__(self, type='uneditable', options=None):
        self.type = type
        self.options = options
    
    @property
    def default(self):
        """Return the default value for this data type (e.g. '' or [])"""
        
        if self.type in ('id', 'uneditable'):
            return None
        else:
            return self.type()
    
    @property
    def is_editable(self):
        """Boolean flag for whether or not this field is editable"""
        
        return self.type not in ('id', 'uneditable')
        

class Tag(HighriseObject):
    """An object representing a Highrise tag."""

    fields = {
        'id': HighriseField(type='id'),
        'name': HighriseField(),
    }        

    @classmethod
    def all(cls):
        """Get all tags"""

        return cls._list('tags.xml', 'tag')
    
    @classmethod
    def get_by(cls, subject, subject_id):
        """Get tags for a specific person, company, case, or deal"""

        return cls._list('%s/%s/tags.xml' % (subject, subject_id), 'tag')

    @classmethod
    def add_to(cls, subject, subject_id, name):
        """Add a tag to a specific person, company, case, or deal"""
        
        xml = ElementTree.Element(tag='name')
        xml.text = name
        xml_string = ElementTree.tostring(xml)
        
        response = Highrise.request('%s/%s/tags.xml' % (subject, subject_id), method='POST', xml=xml_string)
        return cls.from_xml(response)

    @classmethod
    def remove_from(cls, subject, subject_id, tag_id):
        """Add a tag to a specific person, company, case, or deal"""

        return Highrise.request('%s/%s/tags/%s.xml' % (subject, subject_id, tag_id), method='DELETE')
            

class ContactData(HighriseObject):
    """An object representing contact data for a
    Highrise person or company."""
    
    fields = {
        'email_addresses': HighriseField(type=list),
        'phone_numbers': HighriseField(type=list),
        'addresses': HighriseField(type=list),
        'instant_messengers': HighriseField(type=list),
        'twitter_accounts': HighriseField(type=list),
        'web_addresses': HighriseField(type=list),
    }

    def save(self):
        """Save the parent parent person or company""" 
        
        return NotImplemented


class ContactDetail(HighriseObject):
    """A base class for contact details"""

    def save(self):
        """Save the parent person or company this detail belongs to""" 
        
        return NotImplemented
        

class EmailAddress(ContactDetail):
    """An object representing an email address"""

    fields = {
        'id': HighriseField(type='id'),
        'address': HighriseField(type=str),
        'location': HighriseField(type=str, options=('Work', 'Home', 'Other')),
    }        

    
class PhoneNumber(ContactDetail):
    """An object representing an phone number"""

    fields = {
        'id': HighriseField(type='id'),
        'number': HighriseField(type=str),
        'location': HighriseField(type=str, options=('Work', 'Mobile', 'Fax', 'Pager', 'Home', 'Skype', 'Other')),
    }


class Address(ContactDetail):
    """An object representing a physical address"""

    fields = {
        'id': HighriseField(type='id'),
        'city': HighriseField(type=str),
        'country': HighriseField(type=str),
        'state': HighriseField(type=str),
        'zip': HighriseField(type=str),
        'street': HighriseField(type=str),
        'location': HighriseField(type=str, options=('Work', 'Home', 'Other')),
    }
        

class InstantMessenger(ContactDetail):
    """An object representing an instant messanger"""

    fields = {
        'id': HighriseField(type='id'),
        'address': HighriseField(type=str),
        'protocol': HighriseField(type=str, options=('AIM', 'MSN', 'ICQ', 'Jabber', 'Yahoo', 'Skype', 'QQ', 'Sametime', 'Gadu-Gadu', 'Google Talk', 'other')),
        'location': HighriseField(type=str, options=('Work', 'Personal', 'Other')),
    }


class TwitterAccount(ContactDetail):
    """An object representing an Twitter account"""

    fields = {
        'id': HighriseField(type='id'),
        'username': HighriseField(type=str),
        'location': HighriseField(type=str, options=('Work', 'Personal', 'Other')),
    }


class WebAddress(ContactDetail):
    """An object representing a web address"""

    fields = {
        'id': HighriseField(type='id'),
        'url': HighriseField(type=str),
        'location': HighriseField(type=str, options=('Work', 'Personal', 'Other')),
    }


class Person(HighriseObject):
    """An object representing a Highrise person."""

    fields = {
        'id': HighriseField(type='id'),
        'first_name': HighriseField(type=str),
        'last_name': HighriseField(type=str),
        'title': HighriseField(type=str),
        'background': HighriseField(type=str),
        'company_id': HighriseField(type=int),
        'company_name': HighriseField(),
        'visible_to': HighriseField(type=str, options=('Everyone', 'Owner', 'NamedGroup')),
        'owner_id': HighriseField(type=int),
        'group_id': HighriseField(type=int),
        'contact_data': HighriseField(type=ContactData),
        'author_id': HighriseField(),
        'created_at': HighriseField(),
        'updated_at': HighriseField(),
    }
    
    @classmethod
    def all(cls):
        """Get all people"""

        return cls._list('people.xml', 'person')

    @classmethod
    def filter(cls, **kwargs):
        """Get a list of people based on filter criteria"""

        # get the path for filter methods that only take a single argument

        if 'term' in kwargs:
            path = '/people/search.xml?term=%s' % kwargs['term']
            if len(kwargs) > 1:
                raise KeyError, '"term" can not be used with any other keyward arguments'

        elif 'company_id' in kwargs:
            path = '/companies/%s/people.xml' % kwargs['company_id']
            if len(kwargs) > 1:
                raise KeyError, '"company_id" can not be used with any other keyward arguments'

        elif 'tag_id' in kwargs:
            path = '/people.xml?tag_id=%s' % kwargs['tag_id']
            if len(kwargs) > 1:
                raise KeyError, '"tag_id" can not be used with any other keyward arguments'

        elif 'title' in kwargs:
            path = '/people.xml?title=%s' % kwargs['title']
            if len(kwargs) > 1:
                raise KeyError, '"title" can not be used with any other keyward arguments'

        elif 'since' in kwargs:
            path = '/people.xml?since=%s' % datetime.datetime.strftime(kwargs['since'], '%Y%m%d%H%M%S')
            if len(kwargs) > 1:
                raise KeyError, '"since" can not be used with any other keyward arguments'

        # if we didn't get a single-argument kwarg, process using the search criteria method
        else:
            path = '/people/search.xml?'
            for key in kwargs:
                path += 'criteria[%s]=%s&' % (key, kwargs[key])
            path = path[:-1]
            search = True

        # return the list of people from Highrise
        return cls._list(path, 'person')

    @classmethod
    def get(cls, id):
        """Get a single person"""

        # retrieve the person from Highrise
        xml = Highrise.request('/people/%s.xml' % id)

        # return a person object
        for person_xml in xml.getiterator(tag='person'):
            return Person.from_xml(person_xml)

    @property
    def tags(self):
        """Get the tags associated with this person"""
        
        # sanity check: has this person been saved to Highrise yet?
        if self.id == None:
            raise ElevatorError, 'You have to save the person before you can load thier tags'
        
        # get the tags
        return Tag.get_by('people', self.id)
    
    def add_tag(self, name):
        """Add a tag to a person"""
        
        # sanity check: has this person been saved to Highrise yet?
        if self.id == None:
            raise ElevatorError, 'You have to save the person before you can load thier tags'

        # add the tag
        return Tag.add_to('people', self.id, name)

    def remove_tag(self, tag_id):
        """Remove a tag from a person"""

        # sanity check: has this person been saved to Highrise yet?
        if self.id == None:
            raise ElevatorError, 'You have to save the person before you can load thier tags'

        # remove the tag
        return Tag.remove_from('people', self.id, tag_id)
        
    def save(self):
        """Save a person to Highrise."""

        # get the XML for the request
        xml = self.save_xml()
        xml_string = ElementTree.tostring(xml)

        # if this was an initial save, update the object with the returned data
        if self.id == None:
            method = 'POST'
            path = '/people.xml'
            response = Highrise.request(path, method=method, xml=xml_string)
            new = Person.from_xml(response)

        # if this was a PUT request, we need to re-request the object
        # so we can get any new ID values for phone numbers, addresses, etc.
        else:
            method = 'PUT'
            path = '/people/%s.xml' % self.id
            response = Highrise.request(path, method=method, xml=xml_string)
            new = Person.get(self.id)

        # update the values of self to align with what came back from Highrise
        self.__dict__ = new.__dict__

    def delete(self):
        """Delete a person from Highrise."""

        Highrise.request('/people/%s.xml' % self.id, method='DELETE')    


class ElevatorError(Exception):
    pass


class BadRequest(ElevatorError):
    pass


class AuthorizationRequired(ElevatorError):
    pass


class Forbidden(ElevatorError):
    pass


class NotFound(ElevatorError):
    pass


class GatewayFailure(ElevatorError):
    pass


class GatewayConnectionError(ElevatorError):
    pass


class UnexpectedResponse(ElevatorError):
    pass


class InsufficientStorage(ElevatorError):
    pass
