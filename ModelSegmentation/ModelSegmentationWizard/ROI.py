""" This is Step 4. The user selects a ROI and subtracts the two images.
	Much of this step is copied from ChangeTracker, located at 
	https://github.com/fedorov/ChangeTrackerPy. Previously, I had been
	using the cubic ROI tool. This tool, although built in to Slicer,
	could cause painful slowdowns, and sometimes crashed. I also was
	having trouble applying transformations to the ROI. It also was
	not very intuitive. I now instead use the VolumeClip with Model module
	created by Andras Lasso. Its logic is copied wholesale into this code,
	which is unnessecary; it can be imported. However, I want to be able
	to do spot-edits while debugging. The VolumeClip module uses Delaunay
	Triangulation. This is very good at creating convex bubbles, but terrible
	at creating concave, complicated segmentations. Perhaps someone at project
	week will know an even better method.
"""

from __main__ import qt, ctk, slicer

from ModelSegmentationStep import *
from Helper import *
import PythonQt
import os 
from VolumeClipWithModel import *

""" ROIStep inherits from ModelSegmentationStep, with itself inherits
	from a ctk workflow class. PythonQT is required for this step
	in order to get the ROI selector widget.
"""

class ROIStep( ModelSegmentationStep ) :

	def __init__( self, stepid ):

		""" This method creates a drop-down menu that includes the whole step.
		The description also acts as a tooltip for the button. There may be 
		some way to override this. The initialize method is inherited
		from ctk.I got into the habit of creating a gratuitous amount of internal 
		variables in this step. Where possible, some of these should be
		pruned because they are hard to keep track of.
		"""

		self.initialize( stepid )
		self.setName( '4. Define Region(s) of Interest' )
		self.__logic = VolumeClipWithModelLogic()

		# Does declaring this one achieve anything? It doesn't happen in other steps.
		# It may even hurt things..
		self.__parameterNode = None

		self.__parameterNodeObserver = None

		self.__clippingModelNode = None
		self.__clippingMarkupNode = None
		self.__clippingMarkupNodeObserver = None
		
		# For future implementation of multiple models.
		self.__modelList = []
		self.__markupList = []
		self.__outputList = []

		# 3D Rendering Variables
		self.__vrDisplayNode = None
		self.__vrDisplayNodeID = ''
		self.__vrOpacityMap = None
		self.__threshRange = [ -1, -1 ]

		# These don't seem necessary; investigate.
		self.__roiTransformNode = None
		self.__baselineVolume = None
		self.__fillValue = 0

		# TODO: Remove portions about Cubic ROIs. This will not be in final program.
		self.__roi = None
		self.__roiObserverTag = None
		self.__CubicROI = False
		self.__ConvexROI = True

		self.__parent = super( ROIStep, self )

	def createUserInterface( self ):

		""" This UI currently is not easy to use.
		"""

		# Intialize Volume Rendering...
		# Why here, if not init?
		self.__vrLogic = slicer.modules.volumerendering.logic()

		self.__layout = self.__parent.createUserInterface()

		step_label = qt.QLabel( """Create either a 3D volumetric ROI around the area you wish to threshold. Only voxels inside these ROIs will be thresholded in the next step. Click to add points to the volumetric ROI, or click and drag existing points to move them. A curved ROI will be filled in around these points. Similarly, click and drag the points on the box ROI to change its location and size.""")
		step_label.setWordWrap(True)
		self.__primaryGroupBox = qt.QGroupBox()
		self.__primaryGroupBox.setTitle('Information')
		self.__primaryGroupBoxLayout = qt.QFormLayout(self.__primaryGroupBox)
		self.__primaryGroupBoxLayout.addRow(step_label)
		self.__layout.addRow(self.__primaryGroupBox)

		# Toolbar with model buttons.
		self.__roiToolbarGroupBox = qt.QGroupBox()
		self.__roiToolbarGroupBox.setTitle('ROI Toolbar')
		self.__roiToolbarGroupBoxLayout = qt.QFormLayout(self.__roiToolbarGroupBox)

		self.__markupButton = qt.QToolButton()
		self.__markupButton.icon = qt.QIcon(os.path.join(os.path.dirname(__file__), 'MarkupsMouseModePlace.png'))
		self.__markupButton.setCheckable(1)
		self.__markupButton.connect('clicked()', self.onMarkupClicked)
		self.__roiToolbarGroupBoxLayout.addRow('Model Marker Placement Tool', self.__markupButton)

		self.__layout.addRow(self.__roiToolbarGroupBox)

		# I'm referring to the Delaunay Triangulation as a "Convex ROI"
		# I don't think this is very clear; a better title would be good.
		self.__convexGroupBox = qt.QGroupBox()
		self.__convexGroupBox.setTitle('Volumetric ROI')
		self.__convexGroupBoxLayout = qt.QFormLayout(self.__convexGroupBox)

		""" There is an interesting entanglement between markups and models
			here which I believe is confusing to the user. Markups is a list
			of nodes, while the model is the 3D representation created from
			those nodes. It MIGHT be useful, or overly complicated, to have
			users be able to load previous models at this point. But then
			what would they be loading -- the model, or the markups? Which
			should they prefer? It's not clear where one saves models in
			Slicer, so that's a good reason to perhaps abandon it...
		"""
		self.__clippingModelSelector = slicer.qMRMLNodeComboBox()
		self.__clippingModelSelector.nodeTypes = (("vtkMRMLModelNode"), "")
		self.__clippingModelSelector.addEnabled = True
		self.__clippingModelSelector.removeEnabled = False
		self.__clippingModelSelector.noneEnabled = True
		self.__clippingModelSelector.showHidden = False
		self.__clippingModelSelector.renameEnabled = True
		self.__clippingModelSelector.selectNodeUponCreation = True
		self.__clippingModelSelector.showChildNodeTypes = False
		self.__clippingModelSelector.setMRMLScene(slicer.mrmlScene)
		self.__clippingModelSelector.setToolTip("Choose the clipping surface model.")
		self.__convexGroupBoxLayout.addRow("Current Convex ROI Model: ", self.__clippingModelSelector)

		self.__layout.addRow(self.__convexGroupBox)

		# Below is a markups box that I would rather not have, because
		# it is confusing when matched with Models.

		# self.__clippingMarkupSelector = slicer.qMRMLNodeComboBox()
		# self.__clippingMarkupSelector.nodeTypes = (("vtkMRMLMarkupsFiducialNode"), "")
		# self.__clippingMarkupSelector.addEnabled = True
		# self.__clippingMarkupSelector.removeEnabled = False
		# self.__clippingMarkupSelector.noneEnabled = True
		# self.__clippingMarkupSelector.showHidden = False
		# self.__clippingMarkupSelector.renameEnabled = True
		# self.__clippingMarkupSelector.baseName = "Markup"
		# self.__clippingMarkupSelector.setMRMLScene(slicer.mrmlScene)
		# self.__clippingMarkupSelector.setToolTip("Use markup points to determine a convex ROI.")
		# ModelFormLayout.addRow("Convex ROI Markups: ", self.__clippingMarkupSelector)

		""" Below is a gameplan for making loading previous models
			more obvious. Most Slice users understand loading nifti
			files or DICOMsegs, even if they don't understand vtk
			models. Converting labelmaps to models may be the way to
			go. Better yet, integrating with the Segmentations module,
			if users can easily understand that.
		"""

		# self.__addConvexGroupBox = qt.QGroupBox()
		# self.__addConvexGroupBox.setTitle('Add Labelmap as Convex ROI')
		# self.__addConvexGroupBoxLayout = qt.QFormLayout(self.__addConvexGroupBox)

		# self.__convexLabelMapSelector = slicer.qMRMLNodeComboBox()
		# self.__convexLabelMapSelector.nodeTypes = (("vtkMRMLLabelMapVolumeNode"), "")
		# self.__convexLabelMapSelector.addEnabled = True
		# self.__convexLabelMapSelector.removeEnabled = False
		# self.__convexLabelMapSelector.noneEnabled = True
		# self.__convexLabelMapSelector.showHidden = False
		# self.__convexLabelMapSelector.renameEnabled = True
		# self.__convexLabelMapSelector.selectNodeUponCreation = True
		# self.__convexLabelMapSelector.showChildNodeTypes = False
		# self.__convexLabelMapSelector.setMRMLScene(slicer.mrmlScene)
		# self.__convexLabelMapSelector.setToolTip("Choose a labelmap to turn into a convex ROI.")
		# self.__addConvexGroupBoxLayout.addRow("Labelmap: ", self.__convexLabelMapSelector)

		# self.__addConvexButton = qt.QPushButton('Add Labelmap')
		# self.__addConvexGroupBoxLayout.addRow(self.__addConvexButton)
		# self.__addConvexGroupBox.setEnabled(0)

		# self.__layout.addRow(self.__addConvexGroupBox)

		""" How to describe the 3D Visualization threshold? I don't think
			most people will know what it means. It controls how transparent
			different intensities are in the visualization - it's bit hard
			to get an intuitive handle on it.
		"""

		self.__threshRange = slicer.qMRMLRangeWidget()
		self.__threshRange.decimals = 0
		self.__threshRange.singleStep = 1
		self.__threshRange.connect('valuesChanged(double,double)', self.onThresholdChanged)
		qt.QTimer.singleShot(0, self.killButton)

		# ThreshGroupBox = qt.QGroupBox()
		# ThreshGroupBox.setTitle('3D Visualization Intensity Threshold')
		# ThreshGroupBoxLayout = qt.QFormLayout(ThreshGroupBox)
		# ThreshGroupBoxLayout.addRow(self.__threshRange)
		# self.__layout.addRow(ThreshGroupBox)

		# In case we wanted to set specific parameters for Volume Clip...

		# self.valueEditWidgets = {"ClipOutsideSurface": True, "FillValue": 0}
		# # self.nodeSelectorWidgets = {"InputVolume": self.inputVolumeSelector, "ClippingModel": self.clippingModelSelector, "ClippingMarkup": self.clippingMarkupSelector, "OutputVolume": self.outputVolumeSelector}

		qt.QTimer.singleShot(0, self.killButton)

		# Likely more functions will need to be connected here.

		self.__clippingModelSelector.connect("currentNodeChanged(vtkMRMLNode*)", self.onClippingModelSelect)

	def onMarkupClicked(self):

		self.__originalMarkupButton.click()
		if not self.__persistentButton.checked:
			self.__persistentButton.trigger()
		if self.__clippingModelSelector.currentNode() == None or self.__clippingModelSelector.currentNode() == '':
			self.__clippingModelSelector.addNode()

	def onClippingModelSelect(self, node):

		if node != None and node != '':
			if node.GetID() not in self.__modelList:
				self.__modelList.append(node.GetID())
				new_clippingMarkupNode = slicer.vtkMRMLMarkupsFiducialNode()
				new_clippingMarkupNode.SetScene(slicer.mrmlScene)
				slicer.mrmlScene.AddNode(new_clippingMarkupNode)
				self.__markupList.append([node.GetID(), new_clippingMarkupNode.GetID(), 'Convex'])
			
			self.__clippingModelNode = node
			self.setAndObserveClippingMarkupNode(Helper.getNodeByID(self.__markupList[self.__modelList.index(node.GetID())][1]))

	def setAndObserveClippingMarkupNode(self, clippingMarkupNode):

		# Remove observer to old parameter node
		if self.__clippingMarkupNode and self.__clippingMarkupNodeObserver:
			self.__clippingMarkupNode.RemoveObserver(self.__clippingMarkupNodeObserver)
			self.__clippingMarkupNodeObserver = None

		# Set and observe new parameter node
		self.__clippingMarkupNode = clippingMarkupNode
		if self.__clippingMarkupNode:
			self.__clippingMarkupNodeObserver = self.__clippingMarkupNode.AddObserver(vtk.vtkCommand.ModifiedEvent, self.onClippingMarkupNodeModified)

		# Update GUI
		self.updateModelFromClippingMarkupNode()

	def onClippingMarkupNodeModified(self, observer, eventid):

		self.updateModelFromClippingMarkupNode()

	def updateModelFromClippingMarkupNode(self):

		if not self.__clippingMarkupNode or not self.__clippingModelSelector.currentNode():
			return
		self.__logic.updateModelFromMarkup(self.__clippingMarkupNode, self.__clippingModelSelector.currentNode())

	def onThresholdChanged(self): 
	
		# This is for controlling the 3D Visualization.

		if self.__vrOpacityMap == None:
			return
		
		range0 = self.__threshRange.minimumValue
		range1 = self.__threshRange.maximumValue

		# 75 is a pretty arbitrary number. Might fail for very wide ranges of intensities.
		self.__vrOpacityMap.RemoveAllPoints()
		self.__vrOpacityMap.AddPoint(range0-75,0)
		self.__vrOpacityMap.AddPoint(range0,.02)
		self.__vrOpacityMap.AddPoint(range1,.04)
		self.__vrOpacityMap.AddPoint(range1+75,.1)

	def killButton(self):

		# ctk creates a useless final page button. This method gets rid of it.
		bl = slicer.util.findChildren(text='ReviewStep')
		if len(bl):
			bl[0].hide()

	def validate( self, desiredBranchId ):

		if self.__modelList == []:
			self.__parent.validationFailed(desiredBranchId, 'Error', 'You must choose at least one ROI to continue.')
			
		self.__parent.validationSucceeded(desiredBranchId)

	def onEntry(self,comingFrom,transitionType):

		""" This method calls most other methods in this function to initialize the ROI
			wizard. This step in particular applies the ROI IJK/RAS coordinate transform
			calculated in the previous step and checks for any pre-existing ROIs. Also
			intializes the volume-rendering node.
		"""

		super(ROIStep, self).onEntry(comingFrom, transitionType)

		pNode = self.parameterNode()

		self.updateWidgetFromParameters(pNode)

		# I believe this changes the layout to four-up; will check.
		lm = slicer.app.layoutManager()
		lm.setLayout(3)
		pNode = self.parameterNode()
		Helper.SetLabelVolume(None)

		if self.__markupList != None and self.__markupList != '':
			for ROI in self.__markupList:
				Helper.getNodeByID(ROI[1]).GetDisplayNode().VisibilityOn()
				self.setAndObserveClippingMarkupNode(Helper.getNodeByID(ROI[1]))

		# Unsure about this step... might be a hold-over.
		if self.__roi != None:
			self.__roi.SetDisplayVisibility(1)

		pNode.SetParameter('currentStep', self.stepid)
		
		qt.QTimer.singleShot(0, self.killButton)

	def updateWidgetFromParameters(self, pNode):

		if pNode.GetParameter('followupVolumeID') == None or pNode.GetParameter('followupVolumeID') == '':
			Helper.SetBgFgVolumes(pNode.GetParameter('baselineVolumeID'), '')
			self.__visualizedVolume = Helper.getNodeByID(pNode.GetParameter('baselineVolumeID'))
		else:
			Helper.SetBgFgVolumes(pNode.GetParameter('subtractVolumeID'), pNode.GetParameter('followupVolumeID'))
			self.__visualizedVolume = Helper.getNodeByID(pNode.GetParameter('subtractVolumeID'))

		# These may seem redundant - maybe they are - but I think they are useful for
		# multiple program runs.
		if pNode.GetParameter('modelList') == '' or pNode.GetParameter('modelList') == None:
			self.__markupList = []
			self.__modelList = []
			self.__outputList = []

		# Gratuitous?
		self.__baselineVolumeID = pNode.GetParameter('baselineVolumeID')
		self.__followupVolumeID = pNode.GetParameter('followupVolumeID')
		self.__subtractVolumeID = pNode.GetParameter('subtractVolumeID')
		self.__vrDisplayNodeID = pNode.GetParameter('vrDisplayNodeID') 

		if self.__vrDisplayNodeID != None and self.__vrDisplayNodeID != '':
			self.__vrDisplayNode = slicer.mrmlScene.GetNodeByID(self.__vrDisplayNodeID)

		# self.InitVRDisplayNode()

	def InitVRDisplayNode(self):

		"""	This method calls a series of steps necessary to initailizing a volume 
			rendering node with an ROI.
		"""
		if self.__vrDisplayNode == None or self.__vrDisplayNode == '':
			pNode = self.parameterNode()
			self.__vrDisplayNode = self.__vrLogic.CreateVolumeRenderingDisplayNode()
			slicer.mrmlScene.AddNode(self.__vrDisplayNode)

			# Documentation on UnRegister is scant so far..
			self.__vrDisplayNode.UnRegister(self.__vrLogic) 

			Helper.InitVRDisplayNode(self.__vrDisplayNode, self.__visualizedVolume.GetID(), '')
			self.__visualizedVolume.AddAndObserveDisplayNodeID(self.__vrDisplayNode.GetID())

		# This is a bit messy. Is there a more specific way to get the view window?
		viewNode = slicer.util.getNode('vtkMRMLViewNode1')
		self.__vrDisplayNode.AddViewNodeID(viewNode.GetID())
		
		self.__vrLogic.CopyDisplayToVolumeRenderingDisplayNode(self.__vrDisplayNode)

		# Is this redundant with the portion below?
		self.__vrOpacityMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetScalarOpacity()
		self.__vrColorMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetRGBTransferFunction()

		# Renders in yellow, like the label map in the next steps.
		# Maybe ask radiologists what color they would prefer. I favor solid colors
		# to deal with images with non-normalized itensities.

		vrRange = self.__visualizedVolume.GetImageData().GetScalarRange()

		# Custom color-maps? Someday.
		self.__vrColorMap.RemoveAllPoints()
		self.__vrColorMap.AddRGBPoint(vrRange[0], 0.8, 0.8, 0) 
		self.__vrColorMap.AddRGBPoint(vrRange[1], 0.8, 0.8, 0) 

		self.__threshRange.minimum = vrRange[0]
		self.__threshRange.maximum = vrRange[1]

		pNode = self.parameterNode()

		if pNode.GetParameter('vrThreshRangeMin') == '' or pNode.GetParameter('vrThreshRangeMin') == None:
			self.__threshRange.setValues(vrRange[1]/3, 2*vrRange[1]/3)
		else:
			self.__threshRange.setValues(float(pNode.GetParameter('vrThreshRangeMin')), float(pNode.GetParameter('vrThreshRangeMax')))

		self.__vrOpacityMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetScalarOpacity()

	def onExit(self, goingTo, transitionType):

		pNode = self.parameterNode()

		if self.__markupButton.isChecked():
			self.__markupButton.click()

		if goingTo.id() == 'ThresholdStep':
			
			pNode = self.parameterNode()
			baselineVolumeID = pNode.GetParameter('baselineVolumeID')
			followupVolumeID = pNode.GetParameter('followupVolumeID')

			followupVolume = Helper.getNodeByID(followupVolumeID)
			baselineVolume = Helper.getNodeByID(baselineVolumeID)

			for ROI_idx, ROI in enumerate(self.__markupList):
				if ROI[2] == 'Convex' and ROI_idx == 0:

					if pNode.GetParameter('croppedVolumeID') == '' or pNode.GetParameter('croppedVolumeID') == None:
						outputVolume = slicer.vtkMRMLScalarVolumeNode()
						slicer.mrmlScene.AddNode(outputVolume)
					else:
						outputVolume = Helper.getNodeByID(pNode.GetParameter('croppedVolumeID'))

					Helper.SetLabelVolume(None)

					# Crop volume to Convex ROI
					inputVolume = self.__visualizedVolume
					clippingModel = Helper.getNodeByID(ROI[0])
					clipOutsideSurface = True

					# Bit of an arbitrary value.. One less than the minimum of the image.
					self.__fillValue = inputVolume.GetImageData().GetScalarRange()[0] - 1

					self.__logic.clipVolumeWithModel(inputVolume, clippingModel, clipOutsideSurface, self.__fillValue, outputVolume)

					# I don't think OutputList is currently useful. The better tool would be to merge several models.
					self.__outputList.append(outputVolume.GetID())

					outputVolume.SetName(baselineVolume.GetName() + '_roi_cropped')

			pNode.SetParameter('outputList', '__'.join(self.__outputList))
			pNode.SetParameter('modelList', '__'.join(self.__modelList))
			pNode.SetParameter('croppedVolumeID',outputVolume.GetID())
			pNode.SetParameter('ROIType', 'convex')

			# Get starting threshold parameters.
			roiRange = outputVolume.GetImageData().GetScalarRange()
			pNode.SetParameter('intensityThreshRangeMin', str(roiRange[0]+1))
			pNode.SetParameter('intensityThreshRangeMax', str(roiRange[1]))

			# Create a label node for segmentation. Should one make a new one each time? Who knows
			vl = slicer.modules.volumes.logic()

			# Instantiate non-thresholded label.
			if pNode.GetParameter('nonThresholdedLabelID') == '' or pNode.GetParameter('nonThresholdedLabelID') == None:
				roiSegmentation = vl.CreateLabelVolume(slicer.mrmlScene, outputVolume, baselineVolume.GetName() + '_roi_label')
				pNode.SetParameter('nonThresholdedLabelID', roiSegmentation.GetID())

			# Instantiate thresholded label.
			if pNode.GetParameter('thresholdedLabelID') == '' or pNode.GetParameter('thresholdedLabelID') == None:
				roiSegmentation = vl.CreateLabelVolume(slicer.mrmlScene, outputVolume, baselineVolume.GetName() + '_roi_label_thresholded')
				pNode.SetParameter('thresholdedLabelID', roiSegmentation.GetID())

			self.__clippingMarkupNode.RemoveObserver(self.__clippingMarkupNodeObserver)
			self.__clippingMarkupNodeObserver = None

			pNode.SetParameter('clippingModelNodeID', self.__clippingModelSelector.currentNode().GetID())
			for ROI in self.__markupList:
				Helper.getNodeByID(ROI[1]).GetDisplayNode().VisibilityOff()

			if self.__vrDisplayNode != None and self.__vrDisplayNode != '':
				pNode.SetParameter('vrDisplayNodeID', self.__vrDisplayNode.GetID())

		super(ROIStep, self).onExit(goingTo, transitionType)
