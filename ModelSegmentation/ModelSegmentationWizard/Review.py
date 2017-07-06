""" This is Step 6, the final step. This merely takes the label volume
	and applies it to the pre- and post-contrast images. It also does
	some volume rendering. There is much left to do on this step, including
	screenshots and manual cleanup of erroneous pixels. A reset button upon
	completion would also be helpful. This step has yet to be fully commented.
"""

from __main__ import qt, ctk, slicer

from ModelSegmentationStep import *
from Helper import *
from Editor import EditorWidget
from EditorLib import EditorLib

import string

""" ReviewStep inherits from ModelSegmentationStep, with itself inherits
	from a ctk workflow class. 
"""

class ReviewStep( ModelSegmentationStep ) :

	def __init__( self, stepid ):

		""" This method creates a drop-down menu that includes the whole step.
			The description also acts as a tooltip for the button. There may be 
			some way to override this. The initialize method is inherited
			from ctk.
		"""
		self.initialize( stepid )
		self.setName( '6. Review' )

		self.__vrDisplayNode = None
		self.__threshold = [ -1, -1 ]
		
		# initialize VR stuff
		self.__vrLogic = slicer.modules.volumerendering.logic()
		self.__vrOpacityMap = None
		self.__vrColorMap = None

		self.__thresholdedLabelNode = None
		self.__roiVolume = None

		self.__parent = super( ReviewStep, self )
		self.__RestartActivated = False

	def createUserInterface( self ):

		""" This step is mostly empty. A volume rendering threshold is added to be useful.
		"""

		self.__layout = self.__parent.createUserInterface()

		step_label = qt.QLabel( """Review your segmentation. Use the 3D Visualization slider to see your segmentation in context with your image. Use the Editor panel to apply spot edits to your segmentation. If you would like to start over, see the Restart box below""")
		step_label.setWordWrap(True)
		self.__primaryGroupBox = qt.QGroupBox()
		self.__primaryGroupBox.setTitle('Information')
		self.__primaryGroupBoxLayout = qt.QFormLayout(self.__primaryGroupBox)
		self.__primaryGroupBoxLayout.addRow(step_label)
		self.__layout.addRow(self.__primaryGroupBox)

		# self.__threshRange = slicer.qMRMLRangeWidget()
		# self.__threshRange.decimals = 0
		# self.__threshRange.singleStep = 1
		# self.__threshRange.connect('valuesChanged(double,double)', self.onThresholdChanged)
		# qt.QTimer.singleShot(0, self.killButton)

		# ThreshGroupBox = qt.QGroupBox()
		# ThreshGroupBox.setTitle('3D Visualization Intensity Threshold')
		# ThreshGroupBoxLayout = qt.QFormLayout(ThreshGroupBox)
		# ThreshGroupBoxLayout.addRow(self.__threshRange)
		# self.__layout.addRow(ThreshGroupBox)

		editorWidgetParent = slicer.qMRMLWidget()
		editorWidgetParent.setLayout(qt.QVBoxLayout())
		editorWidgetParent.setMRMLScene(slicer.mrmlScene)
		self.EditorWidget = EditorWidget(parent=editorWidgetParent)
		self.EditorWidget.setup()
		self.__layout.addRow(editorWidgetParent)

		RestartGroupBox = qt.QGroupBox()
		RestartGroupBox.setTitle('Restart')
		RestartGroupBoxLayout = qt.QFormLayout(RestartGroupBox)

		self.__RestartButton = qt.QPushButton('Return to Step 1')
		RestartGroupBoxLayout.addRow(self.__RestartButton)

		self.__RemoveRegisteredImage = qt.QCheckBox()
		self.__RemoveRegisteredImage.checked = True
		self.__RemoveRegisteredImage.setToolTip("Delete new images resulting from registration.")
		RestartGroupBoxLayout.addRow("Delete Registered images: ", self.__RemoveRegisteredImage)  

		self.__RemoveNormalizedImages = qt.QCheckBox()
		self.__RemoveNormalizedImages.checked = True
		self.__RemoveNormalizedImages.setToolTip("Delete images produced via normalization.")
		RestartGroupBoxLayout.addRow("Delete Normalized images: ", self.__RemoveNormalizedImages)   

		self.__RemoveSubtractionMap = qt.QCheckBox()
		self.__RemoveSubtractionMap.checked = True
		self.__RemoveSubtractionMap.setToolTip("Delete the full version of your subtraction map.")
		RestartGroupBoxLayout.addRow("Delete Subtraction map: ", self.__RemoveSubtractionMap)    

		self.__RemoveCroppedMap = qt.QCheckBox()
		self.__RemoveCroppedMap.checked = True
		self.__RemoveCroppedMap.setToolTip("Delete the cropped version of your segmented volume.")
		RestartGroupBoxLayout.addRow("Delete Cropped volume: ", self.__RemoveCroppedMap)     

		self.__RemoveROI = qt.QCheckBox()
		self.__RemoveROI.checked = False
		self.__RemoveROI.setToolTip("Delete the ROI resulting from thresholding your original ROI.")
		RestartGroupBoxLayout.addRow("Delete Full ROI: ", self.__RemoveROI)    

		self.__RemoveROIModel = qt.QCheckBox()
		self.__RemoveROIModel.checked = False
		self.__RemoveROIModel.setToolTip("Delete the ROI resulting from thresholding your original ROI.")
		RestartGroupBoxLayout.addRow("Delete Thresholded ROI: ", self.__RemoveROIModel) 

		self.__RemoveMarkups = qt.QCheckBox()
		self.__RemoveMarkups.checked = True
		self.__RemoveMarkups.setToolTip("Delete the markup points you used to make your ROI.")
		RestartGroupBoxLayout.addRow("Delete Markup Model: ", self.__RemoveMarkups) 

		self.__RestartButton.connect('clicked()', self.Restart)
		self.__RestartActivated = True

		self.__layout.addRow(RestartGroupBox)

	def hideUnwantedEditorUIElements(self):

		""" We import the Editor module wholesale, which is useful, but it means
			we have to manually hide parts we don't want after the fact..
			If we could somehow import the segmentations module instaed, that
			might be better. On the other hand, first-time users often don't know
			how to use the segmentations module.
		"""

		self.EditorWidget.setMergeNode(self.__thresholdedLabelNode)
		self.EditorWidget.volumes.collapsed = True
		self.EditorWidget.editLabelMapsFrame.collapsed = False
		try:
			self.EditorWidget.segmentEditorLabel.hide()
			self.EditorWidget.infoIconLabel.hide()
		except:
			pass
		# Useful testing code
		# for widgetName in slicer.util.findChildren(self.EditorWidget.editBoxFrame):
		# for widgetName in slicer.util.findChildren(self.EditorWidget.helper):
			# widget = slicer.util.findChildren(self.EditorWidget.editBoxFrame)
			# print widgetName.objectName
			# print widgetName.parent.name
			# widgetName.hide()
		# print slicer.util.findChildren('','EditColorFrame')

		# for widget in ['DrawEffectToolButton', 'RectangleEffectToolButton', 'IdentifyIslandsEffectToolButton', 'RemoveIslandsEffectToolButton', 'SaveIslandEffectToolButton', 'RowFrame2']:
		# 	slicer.util.findChildren(self.EditorWidget.editBoxFrame, widget)[0].hide()

	def Restart( self ):

		self.__DefaultToolButton.click()

		pNode = self.parameterNode()
		print pNode

		slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('clippingModelNodeID')))
		slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('clippingMarkupNodeID')))
		slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('vrDisplayNodeID')))

		if self.__RemoveRegisteredImage.checked:
			slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('registrationVolumeID')))

		if self.__RemoveNormalizedImages.checked:
			for node in [pNode.GetParameter('baselineNormalizeVolumeID'), pNode.GetParameter('followupNormalizeVolumeID')]:
				if node != pNode.GetParameter('baselineVolumeID') and node != pNode.GetParameter('followupVolumeID'):
					slicer.mrmlScene.RemoveNode(Helper.getNodeByID(node))

		if self.__RemoveSubtractionMap.checked:
			slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('subtractVolumeID')))

		if self.__RemoveCroppedMap.checked:
			slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('croppedVolumeID')))

		if self.__RemoveROI.checked:
			slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('nonThresholdedLabelID')))

		if self.__RemoveROIModel.checked:
			slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('thresholdedLabelID')))

		if self.__RemoveMarkups.checked:
			slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('clippingModelNodeID')))
			slicer.mrmlScene.RemoveNode(Helper.getNodeByID(pNode.GetParameter('clippingMarkupNodeID')))		

		pNode.SetParameter('baselineVolumeID', '')	
		pNode.SetParameter('followupVolumeID', '')
		pNode.SetParameter('originalBaselineVolumeID', '')	
		pNode.SetParameter('originalFollowupVolumeID', '')

		pNode.SetParameter('registrationVolumeID', '')

		pNode.SetParameter('baselineNormalizeVolumeID', '')
		pNode.SetParameter('followupNormalizeVolumeID', '')
		pNode.SetParameter('subtractVolumeID', '')

		pNode.SetParameter('clippingMarkupNodeID', '')
		pNode.SetParameter('clippingModelNodeID', '')
		pNode.SetParameter('outputList', '')	
		pNode.SetParameter('modelList', '')	

		pNode.SetParameter('thresholdedLabelID', '')
		pNode.SetParameter('croppedVolumeID', '')
		pNode.SetParameter('nonThresholdedLabelID', '')

		pNode.SetParameter('roiNodeID', '')
		pNode.SetParameter('roiTransformID', '')

		pNode.SetParameter('vrDisplayNodeID', '')
		pNode.SetParameter('intensityThreshRangeMin', '')
		pNode.SetParameter('intensityThreshRangeMax', '')
		pNode.SetParameter('vrThreshRange', '')

		Helper.SetLabelVolume('')

		self.EditorWidget.exit()

		if self.__RestartActivated:
			self.workflow().goForward()

	def onThresholdChanged(self): 
	
		if self.__vrOpacityMap == None:
			return
		
		range0 = self.__threshRange.minimumValue
		range1 = self.__threshRange.maximumValue

		self.__vrOpacityMap.RemoveAllPoints()
		self.__vrOpacityMap.AddPoint(range0-75,0)
		self.__vrOpacityMap.AddPoint(range0,.02)
		self.__vrOpacityMap.AddPoint(range1,.04)
		self.__vrOpacityMap.AddPoint(range1+75,.1)

	def killButton(self):

		stepButtons = slicer.util.findChildren(className='ctkPushButton')
		
		backButton = ''
		nextButton = ''
		for stepButton in stepButtons:
			if stepButton.text == 'Next':
				nextButton = stepButton
			if stepButton.text == 'Back':
				backButton = stepButton

		nextButton.hide()

		# ctk creates a useless final page button. This method gets rid of it.
		bl = slicer.util.findChildren(text='ReviewStep')
		ex = slicer.util.findChildren('','EditColorFrame')
		if len(bl):
			bl[0].hide()
		if len(ex):
			ex[0].hide()
		else:
			print 'fail'

		self.__editLabelMapsFrame = slicer.util.findChildren('','EditLabelMapsFrame')[0]
		self.__toolsColor = EditorLib.EditColor(self.__editLabelMapsFrame)

	def validate( self, desiredBranchId ):

		# For now, no validation required.
		self.__parent.validationSucceeded(desiredBranchId)

	def onEntry(self, comingFrom, transitionType):
		super(ReviewStep, self).onEntry(comingFrom, transitionType)

		self.__RestartActivated = True
		self.__DefaultToolButton = slicer.util.findChildren(name='DefaultToolToolButton')[0]

		pNode = self.parameterNode()

		self.updateWidgetFromParameters(pNode)

		# What does this do?
		# self.__vrDisplayNode.VisibilityOn()

		Helper.SetBgFgVolumes(self.__visualizedID,'')
		Helper.SetLabelVolume(self.__thresholdedLabelNode.GetID())

		self.onThresholdChanged()

		pNode.SetParameter('currentStep', self.stepid)
	
		qt.QTimer.singleShot(0, self.killButton)

	def updateWidgetFromParameters(self, pNode):

		# Many of these are obviously redundant. Not sure why they were
		# all typed out in the first place.

		self.__clippingModelNode = Helper.getNodeByID(pNode.GetParameter('clippingModelNodeID'))
		self.__baselineVolumeID = pNode.GetParameter('baselineVolumeID')
		self.__followupVolumeID = pNode.GetParameter('followupVolumeID')
		self.__subtractVolumeID = pNode.GetParameter('subtractVolumeID')
		self.__croppedVolumeID = pNode.GetParameter('cropedVolumeID')
		self.__baselineVolumeNode = Helper.getNodeByID(self.__baselineVolumeID)
		self.__followupVolumeNode = Helper.getNodeByID(self.__followupVolumeID)
		self.__subtractVolumeNode = Helper.getNodeByID(self.__subtractVolumeID)
		self.__vrDisplayNodeID = pNode.GetParameter('vrDisplayNodeID') 
		self.__thresholdedLabelNode = Helper.getNodeByID(pNode.GetParameter('thresholdedLabelID'))

		self.__clippingModelNode.GetDisplayNode().VisibilityOn()

		if self.__followupVolumeID == None or self.__followupVolumeID == '':
			self.__visualizedNode = self.__baselineVolumeNode
			self.__visualizedID = self.__baselineVolumeID
		else:
			self.__visualizedID = self.__followupVolumeID
			self.__visualizedNode = self.__followupVolumeNode

		vrRange = self.__visualizedNode.GetImageData().GetScalarRange()

		if self.__vrDisplayNode == None:
			if self.__vrDisplayNodeID != '':
				self.__vrDisplayNode = slicer.mrmlScene.GetNodeByID(self.__vrDisplayNodeID)

		# Replace this, most likely.
		# self.__visualizedNode.AddAndObserveDisplayNodeID(self.__vrDisplayNode.GetID())
		# Helper.InitVRDisplayNode(self.__vrDisplayNode, self.__visualizedID, self.__croppedVolumeID)

		# self.__threshRange.minimum = vrRange[0]
		# self.__threshRange.maximum = vrRange[1]

		# if pNode.GetParameter('vrThreshRangeMin') == '' or pNode.GetParameter('vrThreshRangeMin') == None:
		# 	self.__threshRange.setValues(vrRange[1]/3, 2*vrRange[1]/3)
		# else:
		# 	self.__threshRange.setValues(float(pNode.GetParameter('vrThreshRangeMin')), float(pNode.GetParameter('vrThreshRangeMax')))

		# self.__vrOpacityMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetScalarOpacity()
		# self.__vrColorMap = self.__vrDisplayNode.GetVolumePropertyNode().GetVolumeProperty().GetRGBTransferFunction()

		# self.__vrColorMap.RemoveAllPoints()
		# self.__vrColorMap.AddRGBPoint(vrRange[0], 0.8, 0.8, 0) 
		# self.__vrColorMap.AddRGBPoint(vrRange[1], 0.8, 0.8, 0) 

		self.hideUnwantedEditorUIElements()

	def onExit(self, goingTo, transitionType):   

		self.__DefaultToolButton.click()

		# extra error checking, in case the user manages to click ReportROI button
		super(ModelSegmentationStep, self).onExit(goingTo, transitionType) 