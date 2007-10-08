""" Tests for plugins. """


# Standard library imports.
import random, unittest

# Enthought library imports.
from enthought.envisage.api import Application, ExtensionPoint, Plugin
from enthought.envisage.api import PluginManager, bind_extension_point
from enthought.traits.api import HasTraits, Instance, Int, Interface, List, Str
from enthought.traits.api import implements


def listener(obj, trait_name, old, new):
    """ A useful trait change handler for testing! """

    listener.obj = obj
    listener.trait_name = trait_name
    listener.old = old
    listener.new = new

    return


class PluginTestCase(unittest.TestCase):
    """ Tests for plugins. """

    ###########################################################################
    # 'TestCase' interface.
    ###########################################################################

    def setUp(self):
        """ Prepares the test fixture before each test method is called. """

        return

    def tearDown(self):
        """ Called immediately after each test method has been called. """
        
        return
    
    ###########################################################################
    # Tests.
    ###########################################################################

    def test_service(self):
        """ service """

        class Foo(HasTraits):
            pass

        class PluginA(Plugin):
            id = 'A'
            foo = Instance(Foo, (), service=True)

        a = PluginA()

        application = Application(
            id='plugin.test.case', plugin_manager=PluginManager(plugins=[a])
        )
        application.start()

        # Make sure the service was registered.
        self.assertNotEqual(None, application.get_service(Foo))
        self.assertEqual(a.foo, application.get_service(Foo))

        application.stop()

        # Make sure the service was unregistered.
        self.assertEqual(None, application.get_service(Foo))

        return

    def test_service_protocol(self):
        """ service protocol """

        class IFoo(Interface):
            pass

        class IBar(Interface):
            pass
        
        class Foo(HasTraits):
            implements(IFoo, IBar)

        class PluginA(Plugin):
            id = 'A'
            foo = Instance(Foo, (), service=True, service_protocol=IBar)

        a = PluginA()
        
        application = Application(
            id='plugin.test.case', plugin_manager=PluginManager(plugins=[a])
        )
        application.start()

        # Make sure the service was registered with the 'IBar' protocol.
        self.assertNotEqual(None, application.get_service(IBar))
        self.assertEqual(a.foo, application.get_service(IBar))

        application.stop()

        # Make sure the service was unregistered.
        self.assertEqual(None, application.get_service(IBar))

        return

    def test_extension_point_declarations(self):
        """ extension point declarations """

        class PluginA(Plugin):
            id = 'A'
            x  = ExtensionPoint(List, id='a.x')

        class PluginB(Plugin):
            id = 'B'
            x  = List(Int, [1, 2, 3], extension_point='a.x')

        a = PluginA()
        b = PluginB()

        application = Application(
            id='plugin.test.case', plugin_manager=PluginManager(plugins=[a, b])
        )
        application.start()
        application.stop()
        
        # Make sure we get all of the plugin's contributions.
        extensions = application.get_extensions('a.x')
        extensions.sort()
        
        self.assertEqual(3, len(extensions))
        self.assertEqual([1, 2, 3], extensions)
        
        # Add another contribution to one of the plugins.
        b.x.append(99)

        # Make sure we have picked up the new contribution.
        extensions = application.get_extensions('a.x')
        extensions.sort()
        
        self.assertEqual(4, len(extensions))
        self.assertEqual([1, 2, 3, 99], extensions)

        return

    def test_trait_contributions(self):
        """ trait contributions """

        class PluginA(Plugin):
            id = 'A'
            x  = List(Int, [1, 2, 3], extension_point='x')

        class PluginB(Plugin):
            id = 'B'
            x  = List(Int, [4, 5, 6], extension_point='x')

        a = PluginA()
        b = PluginB()

        application = Application(
            id='plugin.test.case', plugin_manager=PluginManager(plugins=[a, b])
        )

        # Make sure we get all of the plugin's contributions.
        extensions = application.get_extensions('x')
        extensions.sort()
        
        self.assertEqual(6, len(application.get_extensions('x')))
        self.assertEqual([1, 2, 3, 4, 5, 6], extensions)
        
        # Add another contribution to one of the plugins.
        a.x.append(99)

        # Make sure we have picked up the new contribution.
        extensions = application.get_extensions('x')
        extensions.sort()
        
        self.assertEqual(7, len(application.get_extensions('x')))
        self.assertEqual([1, 2, 3, 4, 5, 6, 99], extensions)

        return

    def test_trait_contributions_with_binding(self):
        """ trait contributions with binding """

        class PluginA(Plugin):
            id = 'A'
            x  = List(Int, [1, 2, 3], extension_point='x')

        class PluginB(Plugin):
            id = 'B'
            x  = List(Int, [4, 5, 6], extension_point='x')

        a = PluginA()
        b = PluginB()

        application = Application(
            id='plugin.test.case', plugin_manager=PluginManager(plugins=[a, b])
        )

        # Create an arbitrary object that has a trait bound to the extension
        # point.
        class Foo(HasTraits):
            """ A class! """

            x = List(Int)

        f = Foo(); bind_extension_point(f, 'x', 'x')
        f.on_trait_change(listener)

        # Make sure we get all of the plugin's contributions via the bound
        # trait.
        f.x.sort()
        self.assertEqual(6, len(f.x))
        self.assertEqual([1, 2, 3, 4, 5, 6], f.x)
        
        # Add another contribution to one of the plugins.
        b.x.append(99)

        # Make sure that the correct trait change event was fired.
        self.assertEqual(f, listener.obj)
        self.assertEqual('x', listener.trait_name)
        self.assertEqual(7, len(listener.new))
        
        # Make sure we have picked up the new contribution via the bound trait.
        f.x.sort()
        self.assertEqual(7, len(f.x))
        self.assertEqual([1, 2, 3, 4, 5, 6, 99], f.x)

        return

#### EOF ######################################################################