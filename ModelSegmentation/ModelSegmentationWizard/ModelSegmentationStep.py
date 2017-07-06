""" This class is the base class for all indivudal steps in this module.
	It establishes many useful methods that mostly overwrite methods from
	its parent, ctkWorkflowWidgetStep. Its methods in turn are often
	overwritten as convenient by its children. It is not significantly
	different from its parent class in ctk. Methods taken from ChangeTracker
	by Andrey Fedorov.
"""

from __main__ import qt, ctk

# Imports functions for the parameter node.
from slicer.ScriptedLoadableModule import *

class ModelSegmentationStep( ctk.ctkWorkflowWidgetStep ) :

	def __init__( self, stepid ):

		# Method inherited from ctk.
		self.initialize( stepid )

	def setParameterNode(self, parameterNode):

		# Keeps track of MRML objects, other variables in the scene.
		self.__parameterNode = parameterNode

	def parameterNode(self):

		return self.__parameterNode

	def createUserInterface( self ):

  		# Create basic layout for a step.
		self.__layout = qt.QFormLayout( self )
		self.__layout.setVerticalSpacing( 5 )

		return self.__layout

	def onEntry( self, comingFrom, transitionType ):
		
		""" Entry and exit methods are usually extended in the steps themselves.
			Trigger upon clicking Next and Previous buttons.
		"""

		print self.parameterNode()

		comingFromId = "None"
		if comingFrom: 
			comingFromId = comingFrom.id()

		print "-> onEntry - current [%s] - comingFrom [%s]" % ( self.id(), comingFromId )

		super( ModelSegmentationStep, self ).onEntry( comingFrom, transitionType )

	def onExit( self, goingTo, transitionType ):

		# Keeps track of parameters and steps for testing purposes.
		print self.__parameterNode
		goingToId = "None"
		if goingTo: 
			goingToId = goingTo.id()
		print "-> onExit - current [%s] - goingTo [%s]" % ( self.id(), goingToId )

		super( ModelSegmentationStep, self ).onExit( goingTo, transitionType )

	def validate( self, desiredBranchId ):
		
		""" A series of validation methods also overwritten in part by individual steps.
			Useful to prevent users from skipping ahead or proceeding with invalid data.
		"""
		
		return
		print "-> validate %s" % self.id()

	def validationSucceeded( self, desiredBranchId ):

		super( ModelSegmentationStep, self ).validate( True, desiredBranchId )

	def validationFailed( self, desiredBranchId, messageTitle='Error', messageText='There was an unknown error. See the console output for more details!' ):
		
		messageBox = qt.QMessageBox.warning( self, messageTitle, messageText )
		super( ModelSegmentationStep, self ).validate( False, desiredBranchId )

