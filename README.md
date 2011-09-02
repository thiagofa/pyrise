A Python wrapper for Highrise
----------------------------------
More just just a Python wrapper for Highrise, pyrise gives you class
objects that work a lot like Django models, making the whole experience of
integrating with Highrise just a little more awesome and Pythonic.


Installation
------------
Just clone this repository anywhere in your PythonPath like this:

    $ git clone http://github.com/feedmagnet/pyrise.git

Note that you'll also need to get httplib2 if you don't already have it.

Once you've done one of the above, you can test to see if it is installed from
the Python interactive terminal:

    >>> import pyrise

If you don't get an error, you should be good to go.


Connect to Highrise
--------------------

Set up your Highrise login info:

    >>> from pyrise import *
    >>> Highrise.server('my-server')
    >>> Highrise.auth('api-key-goes-here')

Once configured you can use the pyrise classes to directly interact with Highrise


The Person class
-------------------

Create a new person

    >>> inky = Person(
    ...     first_name='Inkbert',
    ...     last_name='McSquibbles'
    ...     contact_data=ContactData(
    ...         email_addresses=[
    ...             EmailAddress(address='inkbert@feedmagnet.com', location='Work'),
    ...             EmailAddress(address='inkbert@gmail.com', location='Home'),
    ...         ],
    ...         phone_numbers=[PhoneNumber(number='512-555-1234', location='Work'),
    ...     ),
    ... )
    >>> inky.save()

Then you can edit them like this:

    >>> inky.title = 'Chief Sea Squid'
    >>> inky.save()

Get a single person based on their id, edit, and save

    >>> underdog = Person.get(12345)
    >>> underdog.title = 'The new CEO'
    >>> underdog.save()

Get a list of all people in Highrise:

    >>> people = Person.all()
    >>> for person in people:
    ...     print "%s %s" % (person.first_name person.last_name)

Get a list of people from basic keyword search:

    >>> people = Person.filter(term='john')

Get a list of all the people in a specific company:

    >>> people = Person.filter(company_id=1234)

Get a list of all the people with a specific tag

    >>> people = Person.filter(tag_id=1234)

Get a list of all the people with the word 'manager' in their job title

    >>> people = Person.filter(title='manager')

Get a list of all the people records that have changed since a specific date/time:

    >>> from datetime import datetime
    >>> people = Person.filter(since=datetime(2011, 9, 1, 0, 0, 0))

Perform an advanced search using the criteria options from the website:

    >>> people = Person.filter(email='gmail.com', city='austin, state='tx')
