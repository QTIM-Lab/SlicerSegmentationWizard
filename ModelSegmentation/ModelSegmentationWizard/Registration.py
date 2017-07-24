""" This is Step 2. The user has the option to register their pre- and post-contrast images
	using the module BRAINSFit. TO-DO: add a progress bar.
"""

from __main__ import qt, ctk, slicer

from ModelSegmentationStep import *
from Helper import *

""" RegistrationStep inherits from ModelSegmentationStep, with itself inherits
	from a ctk workflow class. 
"""

class RegistrationStep( ModelSegmentationStep ) :
	
	def __init__( self, stepid ):

		self.initialize( stepid )
		self.setName( '2. Registration' )

		self.__parent = super( RegistrationStep, self )

		self.__status = "Uncalled"
	
	def createUserInterface( self ):
		
		""" This method uses qt to create a user interface of radio buttons to select
			a registration method. Note that BSpline registration is so slow and memory-consuming
			as to at one point break Slicer. There is an option to run it with limited memory,
			but this may take prohibitively long. <- NOTE this last comment was based on
			expert automated registration - not sure about other modules.
		"""

		self.__layout = self.__parent.createUserInterface()

		step_label = qt.QLabel( """Select your preferred method of registration. If you have already registered your images, or no registration is required, check the option "No Registration." The moving image will be registered to the fixed image, and then resampled at the dimensions of the fixed image. Be aware that many other modules in Slicer have more complex and/or customizable registration methods, should you require more thorough registration.
			""")
		step_label.setWordWrap(True)
		self.__primaryGroupBox = qt.QGroupBox()
		self.__primaryGroupBox.setTitle('Information')
		self.__primaryGroupBoxLayout = qt.QFormLayout(self.__primaryGroupBox)
		self.__primaryGroupBoxLayout.addRow(step_label)
		self.__layout.addRow(self.__primaryGroupBox)

		# Moving/Fixed Image Registration Order Options

		OrderGroupBox = qt.QGroupBox()
		OrderGroupBox.setTitle('Registration Order')
		self.__layout.addRow(OrderGroupBox)

		OrderGroupBoxLayout = qt.QFormLayout(OrderGroupBox)

		self.__OrderRadio1 = qt.QRadioButton("Register pre-contrast to post-contrast.")
		self.__OrderRadio1.toolTip = "Your pre-contrast image will be transformed."
		OrderGroupBoxLayout.addRow(self.__OrderRadio1)
		self.__OrderRadio1.setChecked(True)

		self.__OrderRadio2 = qt.QRadioButton("Register post-contrast to pre-contrast.")
		self.__OrderRadio2.toolTip = "Your post-contrast image will be transformed."
		OrderGroupBoxLayout.addRow(self.__OrderRadio2)

		# Registration Method Options

		RegistrationGroupBox = qt.QGroupBox()
		RegistrationGroupBox.setTitle('Registration Method')
		self.__layout.addRow(RegistrationGroupBox)

		RegistrationGroupBoxLayout = qt.QFormLayout(RegistrationGroupBox)

		self.__RegistrationRadio1 = qt.QRadioButton("No Registration")
		self.__RegistrationRadio1.toolTip = "Performs no registration."
		RegistrationGroupBoxLayout.addRow(self.__RegistrationRadio1)

		self.__RegistrationRadio2 = qt.QRadioButton("Rigid Registration")
		self.__RegistrationRadio2.toolTip = """Computes a rigid registration on the pre-contrast image with respect to the post-contrast image. This will likely be the fastest registration method"""
		RegistrationGroupBoxLayout.addRow(self.__RegistrationRadio2)

		self.__RegistrationRadio3 = qt.QRadioButton("Affine Registration")
		self.__RegistrationRadio3.toolTip = "Computes a rigid and affine registration on the pre-contrast image with respect to the post-contrast image. This method may take longer than rigid registration, but has the ability to stretch or compress images in addition to rotation and translation."
		RegistrationGroupBoxLayout.addRow(self.__RegistrationRadio3)
		self.__RegistrationRadio3.setChecked(True)

		self.__RegistrationRadio4 = qt.QRadioButton("Deformable Registration")
		self.__RegistrationRadio4.toolTip = """Computes a BSpline Registration on the pre-contrast image with respect to the post-contrast image. This method is slowest and may be necessary for only severly distorted images."""
		RegistrationGroupBoxLayout.addRow(self.__RegistrationRadio4)

		# Output Volume Preference

		OutputGroupBox = qt.QGroupBox()
		OutputGroupBox.setTitle('Registration Output')
		self.__layout.addRow(OutputGroupBox)

		OutputGroupBoxLayout = qt.QFormLayout(OutputGroupBox)

		self.__OutputRadio1 = qt.QRadioButton("Create new volume.")
		self.__OutputRadio1.toolTip = "A new volume will be created with the naming convention \"[pre]_reg_[post]\"."
		OutputGroupBoxLayout.addRow(self.__OutputRadio1)
		self.__OutputRadio1.setChecked(True)

		self.__OutputRadio2 = qt.QRadioButton("Replace existing volume.")
		self.__OutputRadio2.toolTip = "Your registered volume will be overwritten at the end of this step."
		OutputGroupBoxLayout.addRow(self.__OutputRadio2)

		# Registration Button and Progress Indicator

		RunGroupBox = qt.QGroupBox()
		RunGroupBox.setTitle('Run Registration')
		self.__layout.addRow(RunGroupBox)

		RunGroupBoxLayout = qt.QFormLayout(RunGroupBox)

		self.__registrationButton = qt.QPushButton('Run registration')
		self.__registrationStatus = qt.QLabel('Register scans')
		self.__registrationStatus.alignment = 4 # This codes for centered alignment, although I'm not sure why.
		RunGroupBoxLayout.addRow(self.__registrationStatus)
		RunGroupBoxLayout.addRow(self.__registrationButton)
		self.__registrationButton.connect('clicked()', self.onRegistrationRequest)

	def killButton(self):

		# ctk creates an unwanted final page button. This method gets rid of it.
		bl = slicer.util.findChildren(text='ReviewStep')
		if len(bl):
			bl[0].hide()

	def validate(self, desiredBranchId):

		""" This checks to make sure you are not currently registering an image, and
	  		throws an exception if so.
		"""

		self.__parent.validate( desiredBranchId )

		pNode = self.parameterNode()

		if pNode.GetParameter('followupVolumeID') == '' or pNode.GetParameter('followupVolumeID') == None:
			self.__parent.validationSucceeded(desiredBranchId)
		else:	
			if self.__status == 'Uncalled':
				if self.__RegistrationRadio1.isChecked():
					self.__parent.validationSucceeded(desiredBranchId)
				else:
					self.__parent.validationFailed(desiredBranchId, 'Error','Please click \"Run Registration\" or select the \"No Registration\" option to continue.')
			elif self.__status == 'Completed':
				self.__parent.validationSucceeded(desiredBranchId)
			else:
				self.__parent.validationFailed(desiredBranchId, 'Error','Please wait until registration is completed.')

	def onEntry(self, comingFrom, transitionType):

		super(RegistrationStep, self).onEntry(comingFrom, transitionType)

		pNode = self.parameterNode()

		if pNode.GetParameter('followupVolumeID') == None or pNode.GetParameter('followupVolumeID') == '':
			if pNode.GetParameter('currentStep') == 'VolumeSelectStep':
				self.workflow().goForward()
			if pNode.GetParameter('currentStep') == 'NormalizeSubtractStep':
				self.workflow().goBackward()

		pNode.SetParameter('currentStep', self.stepid)
		Helper.SetBgFgVolumes(pNode.GetParameter('baselineVolumeID'),pNode.GetParameter('followupVolumeID'))

		# A different attempt to get rid of the extra workflow button.
		qt.QTimer.singleShot(0, self.killButton)

	def onExit(self, goingTo, transitionType):

		super(ModelSegmentationStep, self).onExit(goingTo, transitionType) 

	def onRegistrationRequest(self, wait_for_completion=False):

		""" This method makes a call to a different slicer module, BRAINSFIT. 
			Note that this registration method computes a transform, which is 
			then applied to the followup volume in processRegistrationCompletion. 
			TO-DO: Add a cancel button and a progress bar.
		"""
		if self.__RegistrationRadio1.isChecked():
			return
		else:
			pNode = self.parameterNode()

			# Registration Order Options
			if self.__OrderRadio1.isChecked():
				fixedVolumeID = pNode.GetParameter('originalFollowupVolumeID')
				movingVolumeID = pNode.GetParameter('originalBaselineVolumeID')
			else:
				fixedVolumeID = pNode.GetParameter('originalBaselineVolumeID')
				movingVolumeID = pNode.GetParameter('originalFollowupVolumeID')

			fixedVolume = Helper.getNodeByID(fixedVolumeID)
			movingVolume = Helper.getNodeByID(movingVolumeID)

			parameters = {}
			parameters["fixedVolume"] = fixedVolume
			parameters["movingVolume"] = movingVolume
			parameters["interpolationMode"] = 'Linear'
			parameters["initializeTransformMode"] = 'useMomentsAlign'
			parameters["samplingPercentage"] = .02

			# Registration Type Options
			if self.__RegistrationRadio4.isChecked():
				self.__BSplineTransform = slicer.vtkMRMLBSplineTransformNode()
				slicer.mrmlScene.AddNode(self.__BSplineTransform)
			else:
				self.__LinearTransform = slicer.vtkMRMLLinearTransformNode()
				slicer.mrmlScene.AddNode(self.__LinearTransform)

			if self.__RegistrationRadio2.isChecked():
				pNode.SetParameter('registrationTransformID', self.__LinearTransform.GetID())
				parameters['transformType'] = 'Rigid'
			elif self.__RegistrationRadio3.isChecked():
				pNode.SetParameter('registrationTransformID', self.__LinearTransform.GetID())
				parameters['transformType'] = 'Rigid,ScaleVersor3D,ScaleSkewVersor3D,Affine'
			elif self.__RegistrationRadio4.isChecked():
				self.__BSplineTransform = slicer.vtkMRMLBSplineTransformNode()
				slicer.mrmlScene.AddNode(self.__BSplineTransform)
				pNode.SetParameter('registrationTransformID', self.__BSplineTransform.GetID())
				parameters['transformType'] = 'BSpline'

			# Output options. TODO: Make this section a bit more logical.
			if self.__OutputRadio2.isChecked():
				parameters['outputVolume'] = movingVolume
				pNode.SetParameter('registrationVolumeID', movingVolume.GetID())
			elif self.__OutputRadio1.isChecked():
				registrationID = pNode.GetParameter('registrationVolumeID')
				if registrationID == None or registrationID == '':
					registrationVolume = slicer.vtkMRMLScalarVolumeNode()
					registrationVolume.SetScene(slicer.mrmlScene)
				else:
					registrationVolume = Helper.getNodeByID(registrationID)
				registrationVolume.SetName(movingVolume.GetName() + '_reg_' + fixedVolume.GetName())
				slicer.mrmlScene.AddNode(registrationVolume)
				pNode.SetParameter('registrationVolumeID', registrationVolume.GetID())
				if self.__OrderRadio1.isChecked():
					pNode.SetParameter('baselineVolumeID', registrationVolume.GetID())
					pNode.SetParameter('originalBaselineVolumeID', movingVolumeID)
				else:
					pNode.SetParameter('followupVolumeID', registrationVolume.GetID())
					pNode.SetParameter('originalFollowupVolumeID', movingVolumeID)
				parameters['outputVolume'] = registrationVolume

			self.__cliNode = None
			self.__cliNode = slicer.cli.run(slicer.modules.brainsfit, self.__cliNode, parameters, wait_for_completion=wait_for_completion)

			# An event listener for the CLI. TODO: Add a progress bar.
			self.__cliObserverTag = self.__cliNode.AddObserver('ModifiedEvent', self.processRegistrationCompletion)
			self.__registrationStatus.setText('Wait ...')
			self.__registrationButton.setEnabled(0)

	def processRegistrationCompletion(self, node, event):

		""" This updates the registration button with the CLI module's convenient status
			indicator. Upon completion, it applies the transform to the followup node.
			Furthermore, it sets the followup node to be the baseline node in the viewer.
		"""

		self.__status = node.GetStatusString()
		self.__registrationStatus.setText('Registration ' + self.__status)

		if self.__status == 'Completed':
			self.__registrationButton.setEnabled(1)

			pNode = self.parameterNode()

			if self.__OrderRadio1.isChecked():
				Helper.SetBgFgVolumes(pNode.GetParameter('followupVolumeID'), pNode.GetParameter('registrationVolumeID'))
			else:
				Helper.SetBgFgVolumes(pNode.GetParameter('registrationVolumeID'), pNode.GetParameter('baselineVolumeID'))

