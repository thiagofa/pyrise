import httplib2
from exceptions import *
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
    def request(cls, path):
        """Process an arbitrary request to Highrise.
        
        Ordinarily, you shouldn't have to call this method directly,
        but it's available to send arbitrary requests if needed."""
        
        # build the base request URL
        url = '%s/%s' % (cls._server, path.strip('/'))
        
        # create the curl command
        request, content = cls._http.request(url, method = 'GET')
        
        # parse the XML
        try:
            content = ElementTree.fromstring(content)
        except:
            raise UnexpectedResponse, "The server sent back something that wasn't valid XML."
            
        # raise appropriate exceptions if there is an error
        status = int(request['status'])
        if status >= 400 or content.tag == 'error':
            if status == 400:
                raise BadRequest, content.text
            elif status == 401:
                raise AuthorizationRequired, content.text
            elif status == 403:
                raise Forbidden, content.text
            elif status == 404:
                raise NotFound, content.text
            elif status == 422:
                raise GatewayFailure, content.text
            elif status == 502:
                raise GatewayConnectionError, content.text
            else:
                raise UnexpectedResponse, content.text
    
        # return the processed content from Highrise
        return content
