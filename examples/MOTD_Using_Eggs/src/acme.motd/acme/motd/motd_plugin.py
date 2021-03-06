""" The 'Message of the Day' plugin """


# In the interest of lazy loading you should only import from the following
# packages at the module level of a plugin::
#
# - envisage
# - traits
#
# Eveything else should be imported when it is actually required.


# Enthought library imports.
from envisage.api import ExtensionPoint, Plugin, ServiceOffer
from traits.api import Instance, List, on_trait_change


class MOTDPlugin(Plugin):
    """ The 'Message of the Day' plugin.

    When this plugin is started it prints the 'Message of the Day' to stdout.

    """

    # The Ids of the extension points that this plugin offers.
    MESSAGES = 'acme.motd.messages'

    # The Ids of the extension points that this plugin contributes to.
    SERVICE_OFFERS = 'envisage.service_offers'

    #### 'IPlugin' interface ##################################################

    # The plugin's unique identifier.
    id = 'acme.motd'

    # The plugin's name (suitable for displaying to the user).
    name = 'MOTD'

    #### Extension points offered by this plugin ##############################

    # The messages extension point.
    #
    # Notice that we use the string name of the 'IMessage' interface rather
    # than actually importing it. This makes sure that the import only happens
    # when somebody actually gets the contributions to the extension point.
    messages = ExtensionPoint(
        List(Instance('acme.motd.api.IMessage')), id=MESSAGES, desc="""

        This extension point allows you to contribute messages to the 'Message
        Of The Day'.

        """
    )

    #### Contributions to extension points made by this plugin ################

    service_offers = List(contributes_to=SERVICE_OFFERS)

    def _service_offers_default(self):
        """ Trait initializer. """

        # When you register a service offer it is best to specify the protocol
        # a string name (rather than importing the protocol right now). This
        # allows the protocol to be lazily loaded. Also, don't specify the
        # protocol as coming from an 'api.py' file as this is not the actual
        # module name known to Python.
        motd_service_offer = ServiceOffer(
            protocol = 'acme.motd.i_motd.IMOTD',
            factory  = self._create_motd_service
        )

        return [motd_service_offer]

    ###########################################################################
    # Private interface.
    ###########################################################################

    def _create_motd_service(self):
        """ Factory method for the 'MOTD' service. """

        # Only do imports when you need to! This makes sure that the import
        # only happens when somebody needs an 'IMOTD' service.
        from motd import MOTD

        return MOTD(messages=self.messages)

    # This plugin does all of its work in this method which gets called when
    # the application has started all of its plugins.
    @on_trait_change('application:started')
    def _print_motd(self):
        """ Print the 'Message of the Day' to stdout! """

        # Note that we always offer the service via its name, but look it up
        # via the actual protocol.
        from acme.motd.api import IMOTD

        # Lookup the MOTD service.
        motd = self.application.get_service(IMOTD)

        # Get the message of the day...
        message = motd.motd()

        # ... and print it.
        print '\n"%s"\n\n- %s' % (message.text, message.author)

        return

#### EOF ######################################################################
