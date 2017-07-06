""" This is Step 3. The user has the option to normalize intensity values
	across pre- and post-contrast images before performing a subtraction
	on them. TODO: Add histogram-matching normalization (already in Slicer!)
	instead of my present method which is somewhat inexplicable.
"""

from __main__ import qt, ctk, slicer

from ModelSegmentationStep import *
from Helper import *

""" NormalizeSubtractStep inherits from ModelSegmentationStep, with itself inherits
	from a ctk workflow class. 
"""

class NormalizeSubtractStep( ModelSegmentationStep ) :

	def __init__( self, stepid ):

		""" This method creates a drop-down menu that includes the whole step.
			The description also acts as a tooltip for the button. There may be 
			some way to override this. The initialize method is inherited
			from ctk.
		"""

		self.initialize( stepid )
		self.setName( '3. Normalization and Subtraction' )

		self.__status = 'uncalled'
		self.__parent = super( NormalizeSubtractStep, self )

	def createUserInterface( self ):

		""" As of now, this user interface is fairly simple. If there are other methods of
			normalization, they could be added here.
		"""

		self.__layout = self.__parent.createUserInterface()

		step_label = qt.QLabel( """You may normalize intensities between your two images. This may help when setting an intensity threshold""")
		step_label.setWordWrap(True)
		self.__primaryGroupBox = qt.QGroupBox()
		self.__primaryGroupBox.setTitle('Information')
		self.__primaryGroupBoxLayout = qt.QFormLayout(self.__primaryGroupBox)
		self.__primaryGroupBoxLayout.addRow(step_label)
		self.__layout.addRow(self.__primaryGroupBox)

		# Normalization methods - there aren't many now, but there may be in the future.
		NormGroupBox = qt.QGroupBox()
		NormGroupBox.setTitle('Normalization Methods')
		self.__layout.addRow(NormGroupBox)

		NormGroupBoxLayout = qt.QFormLayout(NormGroupBox)

		self.__normalizationButton = qt.QPushButton('Run Gaussian Normalization')
		NormGroupBoxLayout.addRow(self.__normalizationButton)
		self.__normalizationButton.connect('clicked()', self.onGaussianNormalizationRequest)
		self.__normalizationButton.setEnabled(1)

		# Create new volumes options.
		self.__OutputRadio1 = qt.QRadioButton("Create new volumes.")
		self.__OutputRadio1.toolTip = "New volumes will be created with the naming convention \"[vol]_normalized\"."
		NormGroupBoxLayout.addRow(self.__OutputRadio1)
		self.__OutputRadio1.setChecked(True)

		self.__OutputRadio2 = qt.QRadioButton("Replace existing volumes.")
		self.__OutputRadio2.toolTip = "Original volumes will be overwritten at the end of this step."
		NormGroupBoxLayout.addRow(self.__OutputRadio2)

		# Which image is normalized to which may matter in the future. For now, I'm not sure if you one can use the Gaussian scale in two directions.
		OrderGroupBox = qt.QGroupBox()
		OrderGroupBox.setTitle('Normalization Order')
		self.__layout.addRow(OrderGroupBox)

		OrderGroupBoxLayout = qt.QFormLayout(OrderGroupBox)

		self.__OrderRadio1 = qt.QRadioButton("Normalize pre-contrast to post-contrast.")
		self.__OrderRadio1.toolTip = "Your pre-contrast image will be normalized."
		OrderGroupBoxLayout.addRow(self.__OrderRadio1)
		self.__OrderRadio1.setChecked(True)

		self.__OrderRadio2 = qt.QRadioButton("Normalize post-contrast to pre-contrast.")
		self.__OrderRadio2.toolTip = "Your post-contrast image will be normalized."
		OrderGroupBoxLayout.addRow(self.__OrderRadio2)

		# Subtraction methods - more straightforward, probably only one.
		SubtractGroupBox = qt.QGroupBox()
		SubtractGroupBox.setTitle('Calculate Subtraction Map')
		self.__layout.addRow(SubtractGroupBox)

		SubtractGroupBoxLayout = qt.QFormLayout(SubtractGroupBox)

		self.__subtractionButton = qt.QPushButton('Run Subtraction Algorithm')
		SubtractGroupBoxLayout.addRow(self.__subtractionButton)
		self.__subtractionButton.connect('clicked()', self.onSubtractionRequest)
		self.__subtractionButton.setEnabled(1)

	def killButton(self):

		# ctk creates a useless final page button. This method gets rid of it.
		bl = slicer.util.findChildren(text='ReviewStep')
		if len(bl):
			bl[0].hide()

	def validate( self, desiredBranchId ):

		pNode = self.parameterNode()

		# Does not validate while subtraction is in process, or has not yet occured.
		if pNode.GetParameter('followupVolumeID') == '' or pNode.GetParameter('followupVolumeID') == None:
			self.__parent.validationSucceeded(desiredBranchId)
		else:
			if self.__status != 'Completed':
				self.__parent.validationFailed(desiredBranchId, 'Error','You must have completed an image subtraction before moving to the next step.')
			else:
				self.__parent.validationSucceeded(desiredBranchId)

	def onEntry(self, comingFrom, transitionType):

		super(NormalizeSubtractStep, self).onEntry(comingFrom, transitionType)

		pNode = self.parameterNode()

		if pNode.GetParameter('followupVolumeID') == None or pNode.GetParameter('followupVolumeID') == '':
			if pNode.GetParameter('currentStep') == 'RegistrationStep':
				self.workflow().goForward()
			if pNode.GetParameter('currentStep') == 'ROIStep':
				self.workflow().goBackward()

		self.__status = 'uncalled'

		self.__normalizationButton.setEnabled(1)
		self.__subtractionButton.setEnabled(1)
		self.__normalizationButton.setText('Run Gaussian Normalization')
		self.__subtractionButton.setText('Run Subtraction Algorithm')

		pNode = self.parameterNode()
		pNode.SetParameter('currentStep', self.stepid)
		Helper.SetBgFgVolumes(pNode.GetParameter('followupVolumeID'),pNode.GetParameter('baselineVolumeID'))
		
		qt.QTimer.singleShot(0, self.killButton)

	def onExit(self, goingTo, transitionType):

		super(ModelSegmentationStep, self).onExit(goingTo, transitionType) 

	def onGaussianNormalizationRequest(self):

		""" This method uses vtk algorithms to perform simple image calculations. Slicer 
			images are stored in vtkImageData format, making it difficult to edit them
			without using vtk. Here, vtkImageShiftScale and vtkImageHistogramStatistics
			are used to generate max, standard deviation, and simple multiplication. Currently,
			I create an instance for both baseline and followup; a better understanding
			of vtk may lead me to consolidate them into one instance later. Sidenote: I don't
			think this method is very good -- I took it from one paper. Probably better to
			do histogram-matching. Also the following code is a little crazy and repetitive.
		"""

		self.__normalizationButton.setEnabled(0)
		self.__normalizationButton.setText('Normalization running...')

		pNode = self.parameterNode()
		volumesLogic = slicer.modules.volumes.logic()

		baselineVolumeID = pNode.GetParameter('baselineVolumeID')
		followupVolumeID = pNode.GetParameter('followupVolumeID')

		baselineNode = slicer.mrmlScene.GetNodeByID(baselineVolumeID)
		followupNode = slicer.mrmlScene.GetNodeByID(followupVolumeID)

		typeArray = ['baseline', 'followup']
		nodeArray = [baselineNode, followupNode]
		nameArray = [baselineNode.GetName(), followupNode.GetName()]
		imageArray = [baselineNode.GetImageData(), followupNode.GetImageData()]
		resultArray = ['','']
		stdArray = [0,0]
		maxArray = [0,0]
		vtkScaleArray = [vtk.vtkImageShiftScale(), vtk.vtkImageShiftScale()]
		vtkStatsArray = [vtk.vtkImageHistogramStatistics(), vtk.vtkImageHistogramStatistics()]

		# Descriptive statistics are retrieved.
		for i in [0,1]:
			vtkStatsArray[i].SetInputData(imageArray[i])
			vtkStatsArray[i].Update()
			maxArray[i] = vtkStatsArray[i].GetMaximum()
			stdArray[i] = vtkStatsArray[i].GetStandardDeviation()

		# Values are rescaled to the highest intensity value from both images.
		CommonMax = maxArray.index(max(maxArray))
		LowerMaxImage = imageArray[CommonMax]

		# Image scalar multiplication is perfored to normalize the two images.
		# New volumes are created. With the present mode of normalization, one
		# of the created volumes will be identical.

		# This method of naming normalized volumes is pretty bad, and should
		# probably be fixed during project week.
		for i in [0,1]:
			vtkScaleArray[i].SetInputData(imageArray[i])
			vtkScaleArray[i].SetOutputScalarTypeToInt()
			scalar = float(stdArray[CommonMax]) / float(stdArray[i])
			vtkScaleArray[i].SetScale(scalar)
			vtkScaleArray[i].Update()
			imageArray[i] = vtkScaleArray[i].GetOutput()

			if self.__OutputRadio1.isChecked():

				normalizeID = pNode.GetParameter(nameArray[i] + '_normalized')
				if normalizeID == None or normalizeID == '':
					resultArray[i] = volumesLogic.CloneVolumeWithoutImageData(slicer.mrmlScene, nodeArray[i], nameArray[i] + '_normalized')
				else:
					resultArray[i] = Helper.getNodeByID(normalizeID)
				resultArray[i].SetAndObserveImageData(imageArray[i])
				pNode.SetParameter(typeArray[i] + 'NormalizeVolumeID', resultArray[i].GetID())

			elif self.__OutputRadio2.isChecked():
				nodeArray[i].SetAndObserveImageData(imageArray[i])
				pNode.SetParameter(typeArray[i] + 'NormalizeVolumeID', nodeArray[i].GetID())

		Helper.SetBgFgVolumes(pNode.GetParameter('followupNormalizeVolumeID'), pNode.GetParameter('baselineNormalizeVolumeID'))

		self.__normalizationButton.setText('Normalization complete!')

	def onSubtractionRequest(self):

		""" This method subtracts two images pixel-for-pixel using Slicer's 
			subtractscalarvolumes module. It apparently can deal with differently
			sized images. A new volume is created and displayed, subtractVolume.
			Method uses normalized volumes if present.
		"""

		pNode = self.parameterNode()

		if pNode.GetParameter('followupNormalizeVolumeID') == None or pNode.GetParameter('followupNormalizeVolumeID') == '':
			baselineVolumeID = pNode.GetParameter('baselineVolumeID')
			followupVolumeID = pNode.GetParameter('followupVolumeID')
		else:
			baselineVolumeID = pNode.GetParameter('baselineNormalizeVolumeID')
			followupVolumeID = pNode.GetParameter('followupNormalizeVolumeID')

		followupVolume = Helper.getNodeByID(followupVolumeID)
		baselineVolume = Helper.getNodeByID(baselineVolumeID)

		subtractID = pNode.GetParameter('subtractVolumeID')
		if subtractID == None or subtractID == '':
			subtractVolume = slicer.vtkMRMLScalarVolumeNode()
			subtractVolume.SetScene(slicer.mrmlScene)
			subtractVolume.SetName(Helper.getNodeByID(followupVolumeID).GetName() + '_subtraction')
			slicer.mrmlScene.AddNode(subtractVolume)
		else:
			subtractVolume = Helper.getNodeByID(subtractID)

		pNode.SetParameter('subtractVolumeID', subtractVolume.GetID())

		# TO-DO: Understand the math behind interpolation order in image subtraction
		parameters = {}
		parameters["inputVolume1"] = followupVolume
		parameters["inputVolume2"] = baselineVolume
		parameters['outputVolume'] = subtractVolume
		parameters['order'] = '1'

		self.__cliNode = None
		self.__cliNode = slicer.cli.run(slicer.modules.subtractscalarvolumes, self.__cliNode, parameters)

		# An event listener for the CLI. To-Do: Add a progress bar.
		self.__cliObserverTag = self.__cliNode.AddObserver('ModifiedEvent', self.processSubtractionCompletion)
		self.__subtractionButton.setText('Subtraction running...')
		self.__subtractionButton.setEnabled(0)

	def processSubtractionCompletion(self, node, event):

		""" This updates the registration button with the CLI module's convenient status
			indicator.
		"""

		self.__status = node.GetStatusString()

		if self.__status == 'Completed':
			self.__subtractionButton.setText('Subtraction completed!')
			pNode = self.parameterNode()
			Helper.SetBgFgVolumes(pNode.GetParameter('subtractVolumeID'), pNode.GetParameter('followupNormalizeVolumeID'))
