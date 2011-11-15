A Python wrapper for Highrise
----------------------------------
More just just a Python wrapper for Highrise, pyrise gives you class
objects that work a lot like Django models, making the whole experience of
integrating with Highrise just a little more awesome and Pythonic.

Here's a simple example of all the code needed to add a new person to Highrise,
then add a tag and a note to their contact record

    >>> from pyrise import *
    >>> Highrise.set_server('my-server')
    >>> Highrise.auth('api-key-goes-here')
    >>> p = Person()
    >>> p.first_name = 'Joe'
    >>> p.last_name = 'Schmoe'
    >>> p.contact_data.email_addresses.append(EmailAddress(address="joe@schmoe.com"))
    >>> p.save()
    >>> p.add_tag('new-guy')
    >>> p.add_note('just added this new guy!')


Work in progress
-------------------
Please bear in mind that this module is not quite finished. If you want to contribute
to finishing it out, please feel free. As it is, we're just building feature as we
need them.

###Completed objects

* People
* Companies
* Deals
* Tags
* Notes
* Emails
* Tasks (partial)

###Not implemented yet:

* Cases
* Comments
* Users
* Groups
* Memberships
* Account operations
* Custom Fields


Installation
------------

    $ sudo pip install pyrise

or

    $ sudo easy_install pyrise

Alternately, you can just clone the GitHub repository anywhere in your PythonPath like this

    $ git clone http://github.com/feedmagnet/pyrise.git

Note that if you are installing manually, you'll need to get httplib2 if you don't
already have it.

Once you've done one of the above, you can test to see if it is installed from
the Python interactive terminal:

    >>> import pyrise

If you don't get an error, you should be good to go.


Connect to Highrise
--------------------

Set up your Highrise login info

    >>> from pyrise import *
    >>> Highrise.set_server('my-server')
    >>> Highrise.auth('api-key-goes-here')

Once configured you can use the pyrise classes to directly interact with Highrise


The Person class
-------------------

Create a new person

    >>> inky = Person()
    >>> inky.first_name = 'Inkbert'
    >>> inky.last_name = 'McSquibbles'
    >>> inky.contact_data = ContactData(
    ...     email_addresses=[
    ...         EmailAddress(address='inkbert@feedmagnet.com', location='Work'),
    ...         EmailAddress(address='inkbert@gmail.com', location='Home'),
    ...     ],
    ...     phone_numbers=[PhoneNumber(number='512-555-1234', location='Work')],
    ... )
    >>> inky.save()

Then you can edit them like this

    >>> inky.title = 'Chief Sea Squid'
    >>> inky.save()

You can pull all their notes and emails like this

    >>> notes = inky.notes
    >>> emails = inky.emails

Get a single person based on their id, edit, and save

    >>> underdog = Person.get(12345)
    >>> underdog.title = 'The new CEO'
    >>> underdog.save()

Get a list of all people in Highrise

    >>> people = Person.all()
    >>> for person in people:
    ...     print "%s %s" % (person.first_name person.last_name)

Get a list of people from basic keyword search

    >>> people = Person.filter(term='john')

Get a list of all the people in a specific company

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

Delete a person

    >>> person = Person.get(12345)
    >>> person.delete()


The Company class
---------------------

The Company class works just like the Person class, with the only exception being that
it does not support the `company_id` and `title` arguments in the `.search()` method.

    >>> company = Company.get(12345)
    >>> company.name = 'Amazing Corp."
    >>> company.save()
    >>> company.delete()

See the Person class documentation above for additional examples.


The Deals class
---------------------

Add a deal

    >>> deal = Deal()
    >>> deal.name = 'Super Huge Amazing Deal.'
    >>> deal.party_id = 123456
    >>> deal.responsible_party_id = 654321
    >>> deal.category_id = 1234
    >>> deal.background = 'Selling a whole bunch of ice to Eskimos.'
    >>> deal.currency = 'USD'
    >>> deal.price = 1000000
    >>> deal.price_type = 'fixed'
    >>> deal.save()
    
Get a single deal based on id, edit, and save

    >>> deal = Deal(12345)
    >>> print deal.name
    Super Huge Amazing Deal.
    >>> deal.name = 'The Biggest Deal Ever.'
    >>> deal.save()
    
Get the notes and emails for a deal

    >>> deal = Deal(12345)
    >>> notes = deal.notes
    >>> emails = deal.emails

Get a list of all deals in Highrise

    >>> deals = Deal.all()
    >>> for deal in deals:
    ...     print deal.name
    
Add a note to a deal

    >>> deal = Deal(12345)
    >>> deal.add_note('Getting close to closing this deal...')

Add an email to a deal

    >>> deal = Deal(12345)
    >>> deal.add_email('Email subect', 'Body text of the email.')

Change the status of a deal

    >>> deal = Deal(12345)
    >>> deal.set_status('won') # could also be 'lost' or 'pending'

Delete a deal

    >>> deal = Deal(12345)
    >>> deal.delete()



The Tag class
-------------------

Add a tag to a person

    >>> person = Person.get(12345)
    >>> person.add_tag('freaking-amazing')

Get a list of tags for a person

    >>> tags = person.tags
    >>> for tag in tags:
    ...     print tag.name

Get a list of all tags on your account

    >>> tags = Tag.all()
    >>> for tag in tags:
    ...     print tag.name

Remove a tag from a person

    >>> person.remove_tag(123)


The Note class
-------------------

Add a note to a person

    >>> person = Person.get(12345)
    >>> person.add_note('Just got off the phone with this guy. He rocks.')

Add an email to a person

    >>> person = Person.get(12345)
    >>> person.add_email('Email subject line', 'Body text of the email goes here.')

Add a note to a company

    >>> company = Company.get(12345)
    >>> company.add_note('This company is freaking awesome.')

More advanced way to add a note

    >>> note = Note()
    >>> note.body = 'This is the best note ever.\n-----------------\nSee how I separated text with a line? Blamo.'
    >>> note.subject_type = 'Party'
    >>> note.subject_id = 12345
    >>> note.visible_to = 'Owner'
    >>> note.owner_id = 23456
    >>> note.collection_type = 'Deal'
    >>> note.collection_id = 345
    >>> note.save()
    
Get details for a note, edit them, and save

    >>> note = Note(1234)
    >>> print note.body
    >>> note.body += '\n------------\nMore details added to the note!'
    >>> note.save()

Get all the notes for a person, company, deal, or case

    >>> notes = Note.filter(person=12345)
    >>> notes = Note.filter(company=12345)
    >>> notes = Note.filter(deal=12345)
    >>> notes = Note.filter(kase=12345)

Delete a note

    >>> note = Note(1234)
    >>> note.delete()


The Email class
---------------------

The Email class works just like the Note class, with the addition of the title 
argument (the email subject line) in addition to body.

    >>> email = Email()
    >>> email.title = 'Be sure to read this email'
    >>> email.body = 'This is a super important email. Glad you read it.'
    >>> email.subject_type = 'Party'
    >>> email.subject_id = 12345
    >>> email.save()
    >>> email.delete()

See the Note class documentation above for additional examples.

    
Time zone shortcut support
------------------------------
It is probably best do all your date interactions with Highrise using UTC
timestamps, but if you prefer to work with Python datetime objects with a
timezone offset, you can use the set_timezone_offset method to do so.

    >>> from datetime import datetime
    >>> Highrise.set_timezone_offset(-5) # Central Daylight Time
    >>> local_datetime = datetime.now()
    >>> person = Person.get(12345)
    >>> person.add_note('Hi there.', created_at=local_datetime)

Assuming your local system is set to Central Daylight Time, the local_datetime
variable above will be in your system's timezone (CDT), but will be sent to
Highrise in UTC. Conversely, new objects created by pulling data from Highrise
will be in local time in your Python objects and converted when saving.
