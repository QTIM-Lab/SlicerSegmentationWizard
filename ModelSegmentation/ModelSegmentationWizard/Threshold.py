""" This is Step 5. The user has the opportunity to threshold a segment 
	of the subtraction map for analysis.
"""

from __main__ import qt, ctk, slicer

from ModelSegmentationStep import *
from Helper import *

import string

""" ThresholdStep inherits from ModelSegmentationStep, with itself inherits
	from a ctk workflow class. 
"""

class ThresholdStep( ModelSegmentationStep ) :

	def __init__( self, stepid ):

		""" This method creates a drop-down menu that includes the whole step.
			The description also acts as a tooltip for the button. There may be 
			some way to override this. The initialize method is inherited
			from ctk.
		"""

		self.initialize( stepid )
		self.setName( '5. Threshold' )

		self.__vrDisplayNode = None
		self.__threshold = [ -1, -1 ]
		
		# Initialize volume rendering.
		self.__vrLogic = slicer.modules.volumerendering.logic()
		self.__vrOpacityMap = None
		self.__vrColorMap = None

		self.__thresholdedLabelNode = None
		self.__roiVolume = None
		self.__visualizedVolume = None

		self.__parent = super( ThresholdStep, self )

	def createUserInterface( self ):

		""" This UI takes advantage of a pre-built slicer thresholding widget.
		"""

		self.__layout = self.__parent.createUserInterface()

		step_label = qt.QLabel( """Use the slider bar below to set an intensity threshold. Any pixels within your ROI and within the intensity threshold will be segmented.""")
		step_label.setWordWrap(True)
		self.__primaryGroupBox = qt.QGroupBox()
		self.__primaryGroupBox.setTitle('Information')
		self.__primaryGroupBoxLayout = qt.QFormLayout(self.__primaryGroupBox)
		self.__primaryGroupBoxLayout.addRow(step_label)
		self.__layout.addRow(self.__primaryGroupBox)

		self.__thresholdGroupBox = qt.QGroupBox()
		self.__thresholdGroupBox.setTitle('Threshold Range')
		self.__thresholdGroupBoxLayout = qt.QFormLayout(self.__thresholdGroupBox)
		threshLabel = qt.QLabel('Select Intensity Range:')
		threshLabel.alignment = 4

		self.__threshRange = slicer.qMRMLRangeWidget()
		self.__threshRange.decimals = 0
		self.__threshRange.singleStep = 1

		self.__thresholdGroupBoxLayout.addRow(threshLabel)
		self.__thresholdGroupBoxLayout.addRow(self.__threshRange)
		self.__layout.addRow(self.__thresholdGroupBox)

		self.__threshRange.connect('valuesChanged(double,double)', self.onThresholdChanged)
		qt.QTimer.singleShot(0, self.killButton)

	def onThresholdChanged(self):
	
		""" Upon changing the slider (or intializing this step), this method
			updates the volume rendering node and label volume accordingly.
		"""

		range0 = self.__threshRange.minimumValue
		range1 = self.__threshRange.maximumValue

		# Use vtk to threshold the label volume.
		if self.__roiVolume != None:
			thresh = vtk.vtkImageThreshold()
			if vtk.VTK_MAJOR_VERSION <= 5:
				thresh.SetInput(self.__roiVolume.GetImageData())
			else:
				thresh.SetInputData(self.__roiVolume.GetImageData())
			thresh.ThresholdBetween(range0, range1)
			thresh.SetInValue(1)
			thresh.SetOutValue(0)
			thresh.ReplaceOutOn()
			thresh.ReplaceInOn()
			thresh.Update()

			self.__thresholdedLabelNode.SetAndObserveImageData(thresh.GetOutput())

	def killButton(self):
		# ctk creates a useless final page button. This method gets rid of it.
		bl = slicer.util.findChildren(text='ReviewStep')
		if len(bl):
			bl[0].hide()

	def validate( self, desiredBranchId ):
		# For now, no validation required.
		self.__parent.validationSucceeded(desiredBranchId)

	def onEntry(self, comingFrom, transitionType):

		""" This method removes and adds nodes necessary to for a segementation
			display, intializes color and opacity maps, and calls the main 
			thresholding function for the first time.
		"""

		super(ThresholdStep, self).onEntry(comingFrom, transitionType)

		pNode = self.parameterNode()

		# What if someone goes to the Volume Rendering module, creates a new VRNode,
		# and then returns? Need some way to check if self.__vrNode is currently
		# being viewed.

		self.__vrDisplayNode = Helper.getNodeByID(pNode.GetParameter('vrDisplayNodeID'))
		self.updateWidgetFromParameters(pNode)

		# Retrieves necessary nodes.
		self.__roiVolume = Helper.getNodeByID(pNode.GetParameter('croppedVolumeID'))
		self.__thresholdedLabelNode = Helper.getNodeByID(pNode.GetParameter('thresholdedLabelID'))
		self.__nonThresholdedLabelNode = Helper.getNodeByID(pNode.GetParameter('nonThresholdedLabelID'))

		# self.InitVRDisplayNode()

		# Not sure why this is here..
		# self.__vrDisplayNode.VisibilityOn()

		# Adds segementation label volume.
		Helper.SetLabelVolume(self.__thresholdedLabelNode.GetID())

		threshRange = [self.__threshRange.minimumValue, self.__threshRange.maximumValue]

		# Segments the entire vtk model. I assume there's a more concise way
		# to do it than thresholding over its entire intensity range...
		range0 = self.__threshRange.minimum
		range1 = self.__threshRange.maximum
		thresh = vtk.vtkImageThreshold()
		if vtk.VTK_MAJOR_VERSION <= 5:
			thresh.SetInput(self.__roiVolume.GetImageData())
		else:
			thresh.SetInputData(self.__roiVolume.GetImageData())
		thresh.ThresholdBetween(range0, range1)
		thresh.SetInValue(1)
		thresh.SetOutValue(0)
		thresh.ReplaceOutOn()
		thresh.ReplaceInOn()
		thresh.Update()
		self.__nonThresholdedLabelNode.SetAndObserveImageData(thresh.GetOutput())

		# Adjusts threshold information.
		self.onThresholdChanged()

		pNode.SetParameter('currentStep', self.stepid)
	
		qt.QTimer.singleShot(0, self.killButton)

	def updateWidgetFromParameters(self, pNode):

		""" Intializes the threshold and label volume established in the previous step.
		"""

		if pNode.GetParameter('followupVolumeID') == None or pNode.GetParameter('followupVolumeID') == '':
			Helper.SetBgFgVolumes(pNode.GetParameter('baselineVolumeID'), '')
			self.__visualizedVolume = Helper.getNodeByID(pNode.GetParameter('baselineVolumeID'))
		else:
			Helper.SetBgFgVolumes(pNode.GetParameter('subtractVolumeID'), pNode.GetParameter('followupVolumeID'))
			self.__visualizedVolume = Helper.getNodeByID(pNode.GetParameter('subtractVolumeID'))

		thresholdRange = [float(pNode.GetParameter('intensityThreshRangeMin')), float(pNode.GetParameter('intensityThreshRangeMax'))]

		if thresholdRange != '':
			self.__threshRange.maximum = thresholdRange[1]
			self.__threshRange.minimum = thresholdRange[0]
			self.__threshRange.maximumValue = thresholdRange[1]
			self.__threshRange.minimumValue = thresholdRange[0]
		else:
			Helper.Error('Unexpected parameter values! Error code CT-S03-TNA. Please report')

		labelID = pNode.GetParameter('thresholdedLabelID')
		self.__thresholdedLabelNode = Helper.getNodeByID(labelID)

	def onExit(self, goingTo, transitionType):   
		pNode = self.parameterNode()
		if self.__vrDisplayNode != None:
			# self.__vrDisplayNode.VisibilityOff()
			pNode.SetParameter('vrDisplayNodeID', self.__vrDisplayNode.GetID())

		roiRange = self.__threshRange
		pNode.SetParameter('intensityThreshRangeMin', str(roiRange.minimumValue))
		pNode.SetParameter('intensityThreshRangeMax', str(roiRange.maximumValue))
		pNode.SetParameter('vrThreshRangeMin', str(roiRange.minimumValue))
		pNode.SetParameter('vrThreshRangeMax', str(roiRange.maximumValue))

		super(ModelSegmentationStep, self).onExit(goingTo, transitionType) 

	def InitVRDisplayNode(self):

		"""	This method calls a series of steps necessary to initailizing a volume 
			rendering node with an ROI.
		"""
		if self.__vrDisplayNode == None or self.__vrDisplayNode == '':
			pNode = self.parameterNode()
			self.__vrDisplayNode = self.__vrLogic.CreateVolumeRenderingDisplayNode()
			slicer.mrmlScene.AddNode(self.__vrDisplayNode)
			# Documentation on UnRegister is scant so far.
			self.__vrDisplayNode.UnRegister(self.__vrLogic) 

			Helper.InitVRDisplayNode(self.__vrDisplayNode, self.__roiVolume.GetID(), '')
			self.__roiVolume.AddAndObserveDisplayNodeID(self.__vrDisplayNode.GetID())
		else:
			self.__vrDisplayNode.SetAndObserveVolumeNodeID(self.__roiVolume.GetID())

		# This is a bit messy.
		viewNode = slicer.util.getNode('vtkMRMLViewNode1')

		self.__vrDisplayNode.AddViewNodeID(viewNode.GetID())
		
		self.__vrLogic.CopyDisplayToVolumeRenderingDisplayNode(self.__vrDisplayNode)

		self.__vrOpacityMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetScalarOpacity()
		self.__vrColorMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetRGBTransferFunction()

		vrRange = self.__visualizedVolume.GetImageData().GetScalarRange()

		# Renders in yellow, like the label map in the next steps.
		self.__vrColorMap.RemoveAllPoints()
		self.__vrColorMap.AddRGBPoint(vrRange[0], 0.8, 0.8, 0) 
		self.__vrColorMap.AddRGBPoint(vrRange[1], 0.8, 0.8, 0) 