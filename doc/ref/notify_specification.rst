Notification Framework
======================

The purpose of the notification framework is to be a generic, run-time
configurable and code extensible system to inform interested parties
about events in the store.

Events could include

-  orders being created
-  shipments being dispatched
-  orders being canceled
-  products reaching a given stock threshold
-  a user requesting a password reset

et cetera.

Notifications may be delivered over different channels, such as email,
SMS, phone or even instant messages, as delivery channels are also
pluggable.

It is known that the notification framework partially overlaps the
Django signal system as used in Shuup in scope. However Django signals
are not user-configurable and their purpose is different.

Glossary
--------

-  **Event** - a class of notifiable event
-  **Event Variables** - a set of typed variables pertaining to a given
   event
-  **Script** - a configurable object describing the chain of system
   actions in response to an Event
-  **Script Context** - a set of variables populated from the event
   variables before the script is begun
-  **Action** - a configured action within a script, such as "Send email
   to x@y.local"
-  **Action Class** - a type of action provided by an app (or built-in
   to the notification framework), such as "Send Email"
-  **Condition** - a configured conditional enabling actions within a
   script, such as "If Order Contains Product XYZ-1"
-  **Condition Class** - a type of condition provided by an app (or
   built-in to the notification framework), such as "If Order Contains
   Product"
-  **Template** - a possibly multilingual set of textual templates
   attached to Actions that require configurable text.
-  **Attachment** - a named, MIME-typed assumedly binary blob that may
   be delivered along a notification, such as a PDF order confirmation.
-  **ScriptTemplate** - a class which knows how to create a script logic
   based on configurations provided by user.

Events
------

An Event represents a single event that may occur in the system.

Events are registered through the Shuup Apps' ``provides`` mechanism and
must have unique identifiers ("event identifier").

Events provide typed variables that may be utilized in script items, in
either variable bindings or message templates.

In addition, a number of system variables are made available for all
events.

For instance, an "Order Created" event could provide the variables

-  ``order`` (type Order) - the order itself
-  ``customer_email`` (type email) - the customer's email address
   (extracted from the order)
-  ``customer_phone`` (type phone) - the customer's phone number
   (extracted from the order)
-  ``payment_email`` (type email) - the payment email address (extracted
   from the order)
-  ``shipment_email`` (type email) - the shipment email address
   (extracted from the order)
-  ``language`` (type language) - the customer's preferred language
   (extracted from the order)

and a default script that sends a pre-defined text template to the
customer email.

A "Password Reset" event could provide the variables

-  ``user`` (type User) - the requesting user
-  ``user_email`` (type email) - the email address of the user
-  ``password_reset_url`` (type URL) - the URL for resetting the
   password.

Scripts
-------

Event scripts define the rules, i.e. conditions and actions defining
what to do when a notification event occurs. A single event may have
multiple scripts attached; all of them are executed if they are enabled.

A script may be as simple as "Always -> Send Email -> Stop", or it may
have conditions that send emails with different templates depending on
the language of the order, or products contained within the order.

Events may provide a script template, which can be loaded for further
configuration by the shop administrator. No scripts are loaded by
default, though. If no scripts exist for an event, nothing is done when
the event occurs.

The model for scripts is a "routing table" with steps of the form
"Conditions / Actions / Next". This is somewhat modeled after `uWSGI's
Internal Routing`_ system. Note: This would be easy to upgrade to a
full-fledged flowchart/data-flow programming environment akin to `Unreal
Engine 4's Blueprint Visual Scripting`_ system.

The Conditions set for a script step may be joined with different
conditional operators. Currently, "All", "Any" and "None" are
implemented. The actions for a single step are executed sequentially.

The actions for "Next" are "Continue" and "Stop". (A "Goto" action is
also possible, but it is not considered a requirement at present.)
"Continue" will continue executing the routing table from the next step,
and "Stop" will cease script execution.

The Condition and Action classes available for notification scripts are
also provided via the ``provides`` mechanism; many actions are built-in
(provided by the notification framework itself), but may be extended by
other apps. Like Events, Condition classes and Action classes have
unique identifiers.

Conditions and Actions are configurable. The configurable variables are
set by the Condition classes and Action classes, using the same typology
as Event variables.

For instance, Conditional classes could include

-  "Language Equals" (configured by a variable of type Language and a
   constant of type Language)
-  "Order Contains Product SKU" (configured by a variable of type Order
   and a constant of type String)
-  "Order Is Paid" (configured by a variable of type Order)

and Action classes might include

-  "Send Plain-Text Email" (configured by variable/constant of type
   Email and a template (see below))
-  "Send Text and HTML Email"

Extension Action classes for, say, integration might even contain

-  "Send Order To External System XYZ"

The recipients, etc. for emails are configurable, making it possible to
easily implement merchant order notifications using the same Actions and
Conditions.

Templates
---------

Most, if not all, actions require some sort of templating. The Jinja2
language is used for the templates. Templates may contain multiple
sections, such as "Subject" or "Content"; these are set by the Action
requesting an editable template, as the template editor is embedded in
the Action's configuration view.

An action may request multilingual templates. Multilingual templates
duplicate each section for all languages set in the system
configuration. (The sending Action is naturally then expected to be
configurable by a variable or constant of type Language.)

Attachments
-----------

Many actions may also require attachments and other data such as PDF
order confirmations, product manuals, etc. that may or may not be
generated during dispatch.

To solve this, the script context also includes a list of Attachment
objects (details TBD).

Actions such as "Render Order Confirmation PDF" would add Attachment
objects to the context, while sending actions would consume them
(optionally without removing them) from the context.

Notification Dispatch
---------------------

Depending on the deployment and implementation, notification dispatch
may occur asynchronously (in a non-blocking manner).

The author currently foresees no use case where asynchronous dispatch
would cause issues, and as such, the specification contains no mechanism
for declaring an event or script to be forcibly synchronous.

Persistent Notifications
------------------------

In addition to the script core, the Notify app provides a Django model
for notifications stored in the shop's database. These are currently
used only in the admin backend, but could be used in the frontend as
well.

ScriptTemplate
--------------

This feature enable users to create scripts in a simple and fashion way
by removing complexity and saving time. Script templates are inserted
through the `notify_script_template` provide category and can be used
when creating a new Notification through a template in admin.

You can create your own script template and instantiate it as many times
as you want, changing only relevant configurations to fit yours needs.

Since templates are inserted by provide system, it is a good way to use
and share common tasks in notification logics with the community.

.. _uWSGI's Internal Routing: https://uwsgi-docs.readthedocs.org/en/latest/InternalRouting.html
.. _Unreal Engine 4's Blueprint Visual Scripting: https://docs.unrealengine.com/latest/INT/Engine/Blueprints/index.html
