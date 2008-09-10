""" A view containing an interactive Python shell. """


# Standard library imports.
import logging
import traceback

# Major library imports
from IPython.kernel.core.interpreter import Interpreter

# Enthought library imports.
from enthought.envisage.api import IExtensionRegistry
from enthought.envisage.api import ExtensionPoint
from enthought.plugins.python_shell.api import IPythonShell
from enthought.plugins.ipython_shell.api import INamespaceView
from enthought.pyface.workbench.api import View
from enthought.pyface.ipython_widget import IPythonWidget
from enthought.pyface.api import GUI
from enthought.traits.api import Instance, Property, implements, Dict


# Setup a logger for this module.
logger = logging.getLogger(__name__)

class IPythonShellView(View):
    """ A view containing an IPython shell. """

    implements(IPythonShell)

    #### 'IView' interface ####################################################
    
    # The part's globally unique identifier.
    id = 'enthought.plugins.python_shell_view'

    # The part's name (displayed to the user).
    name = 'IPython'

    # The default position of the view relative to the item specified in the
    # 'relative_to' trait.
    position = 'bottom'

    #### 'PythonShellView' interface ##########################################

    # The interpreter's namespace.
    namespace = Dict

    # The names bound in the interpreter's namespace.
    names = Property(depends_on="namespace")

    #### 'IPythonShellView' interface #########################################

    # The interpreter
    interpreter = Instance(Interpreter)

    def _interpreter_default(self):
        # Create an interpreter that has a reference to our namespace.
        return Interpreter(user_ns=self.namespace)

    #### 'IExtensionPointUser' interface ######################################

    # The extension registry that the object's extension points are stored in.
    extension_registry = Property(Instance(IExtensionRegistry))

    #### Private interface ####################################################

    # Bindings.
    _bindings = ExtensionPoint(id='enthought.plugins.python_shell.bindings')

    # Commands.
    _commands = ExtensionPoint(id='enthought.plugins.python_shell.commands')

    ###########################################################################
    # 'IExtensionPointUser' interface.
    ###########################################################################

    def _get_extension_registry(self):
        """ Trait property getter. """

        return self.window.application

    ###########################################################################
    # 'View' interface.
    ###########################################################################

    def create_control(self, parent):
        """ Creates the toolkit-specific control that represents the view. """

        self.shell = IPythonWidget(parent, interp=self.interpreter)

        # Namespace contributions.
        for bindings in self._bindings:
            for name, value in bindings.items():
                self.bind(name, value)

        for command in self._commands:
            try:
                self.execute_command(command)
            except Exception, e:
                logger.exception(
                        "The command '%s' supplied to the Ipython shell "
                        "plugin has raised an exception:\n%s" % 
                        (command, traceback.format_exc()))

        # Register the view as a service.
        self.window.application.register_service(IPythonShell, self)

        ns_view = self.window.application.get_service(INamespaceView)
        if ns_view is not None:
            self.on_trait_change(ns_view._on_names_changed, 'names')
 
        def set_focus():
            self.window.application.gui.invoke_later(
                                                self.shell.control.SetFocus) 
        GUI.invoke_later(set_focus)
        
        return self.shell.control


    def destroy_control(self):
        """ Destroys the toolkit-specific control that represents the view.

        """
        
        super(IPythonShellView, self).destroy_control()

        # Remove the namespace change handler
        ns_view = self.window.application.get_service(INamespaceView)
        if ns_view is not None:
            self.on_trait_change(
                ns_view._on_names_changed, 'names', remove=True
            )


    ###########################################################################
    # 'PythonShellView' interface.
    ###########################################################################

    #### Properties ###########################################################

    def _get_names(self):
        """ Property getter. """

        return self.control.ipython0.magic_who_ls()

    #### Methods ##############################################################

    def bind(self, name, value):
        """ Binds a name to a value in the interpreter's namespace. """

        self.namespace[name] = value

        return

    def execute_command(self, command, hidden=True):
        """ Execute a command in the interpreter. """

        if hidden:
            return self.interpreter.execute(command)
        else:
            current_buffer = self.shell.control.input_buffer
            self.shell.control.input_buffer = command + '\n'
            GUI.process_events()
            self.shell.control._on_enter()
            GUI.process_events()
            self.shell.control.input_buffer = current_buffer

    def lookup(self, name):
        """ Returns the value bound to a name in the interpreter's namespace.

        """

        return self.namespace[name]

#### EOF ######################################################################
