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
        if method == 'GET':
            request, content = cls._http.request(url, method='GET')
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
    
        # if this was a PUT request, return status (hopefully success)
        if method == 'PUT':
            print content
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
        
            # if there is no data, just set a None value
            if child.text == None:
                self.__dict__[key] = None
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
        try: 
            objects = []
            xml = Highrise.request(path)

            # make a list of objects and return it
            for item in xml.getiterator(tag=tag):
                objects.append(cls.from_xml(item))

            return objects

        except NotFound:
            return []

    def __init__(self, parent=None, **kwargs):
        """Create a new object manually."""

        self.id = None
        self._server = Highrise._server
        self._editable = ()

        # iterate over the keyword arguments provided
        # and set them to the object
        for i in kwargs:
            self.__dict__[i] = kwargs[i]
    
    def save_xml(self, **kwargs):
        """Return the object XML for sending back to Highrise"""

        # create new XML object
        if 'base_element' not in kwargs:
            kwargs['base_element'] = Highrise.class_to_key(self.__class__.__name__)
        xml = ElementTree.Element(kwargs['base_element'])
        
        # iterate over the object attributes
        for key, value in self.__dict__.iteritems():
            # ignore attribute if it is not editable and not and id that we want to include
            if key not in self._editable and not ('include_id' in kwargs and key == 'id'):
                continue
            
            # if the value is a HighriseObject, insert the XML for it
            if isinstance(value, HighriseObject):
                xml.insert(0, value.save_xml(include_id=True))
                continue
            
            # don't include the id value if it is not set
            if 'include_id' in kwargs and key == 'id' and value == None:
                continue

            # insert the remaining single-attribute elements
            e = ElementTree.Element(key.replace('_', '-'))
            if value != None:
                if isinstance(value, int):
                    e.text = str(value)
                elif isinstance(value, list):
                    for item in value:
                        e.insert(0, item.save_xml(include_id=True))
                else:
                    e.text = value
            xml.insert(0, e)

        return xml
    

class Person(HighriseObject):
    """An object representing a Highrise person."""

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
    
    def __init__(self, parent=None, **kwargs):
        HighriseObject.__init__(self, parent, **kwargs)
        self._editable = ('first_name', 'last_name', 'title', 'company_id', 'background', 'contact_data', 'subject_datas')
    
    def save(self):
        """Writing to the Highrise API hasn't been implemented yet."""

        xml = self.save_xml()
        xml_string = ElementTree.tostring(xml)
                
        if self.id == None:
            method = 'POST'
            path = '/people.xml'
        else:
            method = 'PUT'
            path = '/people/%s.xml' % self.id
            
        response = Highrise.request(path, method=method, xml=xml_string)
        
        # if this was an initial save, update the object with the returned data
        if method == 'POST':
            new = Person.from_xml(response)
            self.__dict__ = new.__dict__
        
        # if this was a PUT request, we need to re-request the object
        # so we can get any new ID values for phone numbers, addresses, etc.
        elif method == 'PUT':
            new = Person.get(self.id)
            self.__dict__ = new.__dict__
        
        
    def delete(self):
        """Deleting via the Highrise API has not been implemented yet."""

        return NotImplemented
    

class Tag(HighriseObject):
    """An object representing a Highrise tag."""

    @classmethod
    def all(cls):
        """Get all tags"""

        return cls._list('tags.xml', 'tag')


class ContactData(HighriseObject):
    """An object representing contact data for a
    Highrise person or company."""

    def __init__(self, parent=None, **kwargs):
        HighriseObject.__init__(self, parent, **kwargs)
        self._editable = ('email_addresses', 'phone_numbers', 'addresses', 'instant_messengers', 'twitter_accounts', 'web_addresses')

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

    def __init__(self, parent=None, **kwargs):
        HighriseObject.__init__(self, parent, **kwargs)
        self._editable = ('address', 'location')
        
    
class PhoneNumber(ContactDetail):
    """An object representing an phone number"""

    def __init__(self, parent=None, **kwargs):
        HighriseObject.__init__(self, parent, **kwargs)
        self._editable = ('number', 'location')


class Address(ContactDetail):
    """An object representing a physical address"""

    def __init__(self, parent=None, **kwargs):
        HighriseObject.__init__(self, parent, **kwargs)
        self._editable = ('city', 'country', 'state', 'street', 'zip', 'location')
        

class InstantMessenger(ContactDetail):
    """An object representing an instant messanger"""

    def __init__(self, parent=None, **kwargs):
        HighriseObject.__init__(self, parent, **kwargs)
        self._editable = ('address', 'protocol', 'location')


class TwitterAccount(ContactDetail):
    """An object representing an Twitter account"""

    def __init__(self, parent=None, **kwargs):
        HighriseObject.__init__(self, parent, **kwargs)
        self._editable = ('username', 'url', 'location')


class WebAddress(ContactDetail):
    """An object representing a web address"""

    def __init__(self, parent=None, **kwargs):
        HighriseObject.__init__(self, parent, **kwargs)
        self._editable = ('url', 'location')


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

