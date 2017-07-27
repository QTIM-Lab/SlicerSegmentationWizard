
import os
import unittest
from __main__ import vtk, qt, ctk, slicer

class SegmentationWizardSelfTest:
  def __init__(self, parent):
    parent.title = "SegmentationWizardSelfTest" # TODO make this more human readable by adding spaces
    parent.categories = ["Testing.TestCases"]
    parent.dependencies = ["SegmentationWizard"]
    parent.contributors = ["Andrew Beers (MGH)"] # replace with "Firstname Lastname (Org)"
    parent.helpText = """
    This module was developed as a self test to perform the operations done in SegmentationWizard module
    """
    parent.acknowledgementText = """
    This file was templated off the test case module from ChangeTracker by Andrey Fedorov and Steve Pieper.
""" # replace with organization, grant and thanks.
    self.parent = parent

    # Add this test to the SelfTest module's list for discovery when the module
    # is created.  Since this module may be discovered before SelfTests itself,
    # create the list if it doesn't already exist.
    try:
      slicer.selfTests
    except AttributeError:
      slicer.selfTests = {}
    slicer.selfTests['SegmentationWizardSelfTestTest'] = self.runTest

  def runTest(self):
    tester = SegmentationWizardSelfTestTest()
    tester.runTest()

#
# qSegmentationWizardTestWidget
#

class SegmentationWizardSelfTestWidget:
  def __init__(self, parent = None):
    if not parent:
      self.parent = slicer.qMRMLWidget()
      self.parent.setLayout(qt.QVBoxLayout())
      self.parent.setMRMLScene(slicer.mrmlScene)
    else:
      self.parent = parent
    self.layout = self.parent.layout()
    if not parent:
      self.setup()
      self.parent.show()

  def setup(self):
    # Instantiate and connect widgets ...

    # Collapsible button
    testsCollapsibleButton = ctk.ctkCollapsibleButton()
    testsCollapsibleButton.text = "A collapsible button"
    self.layout.addWidget(testsCollapsibleButton)

    # Layout within the collapsible button
    formLayout = qt.QFormLayout(testsCollapsibleButton)

    # test buttons
    tests = ( ("SegmentationWizard", self.ontestSegmentationWizard), )
    for text,slot in tests:
      testButton = qt.QPushButton(text)
      testButton.toolTip = "Run the test."
      formLayout.addWidget(testButton)
      testButton.connect('clicked(bool)', slot)

    # Add vertical spacer
    self.layout.addStretch(1)

  def ontestSegmentationWizard(self):
    tester = SegmentationWizardSelfTestTest()
    tester.setUp()
    tester.testSegmentationWizard()

#
# SegmentationWizardTestLogic
#

class SegmentationWizardSelfTestLogic:
  """This class should implement all the actual 
  computation done by your module.  The interface 
  should be such that other python code can import
  this class and make use of the functionality without
  requiring an instance of the Widget
  """
  def __init__(self):
    pass

  def hasImageData(self,volumeNode):
    """This is a dummy logic method that 
    returns true if the passed in volume
    node has valid image data
    """
    if not volumeNode:
      print('no volume node')
      return False
    if volumeNode.GetImageData() == None:
      print('no image data')
      return False
    return True


class SegmentationWizardSelfTestTest(unittest.TestCase):
  """
  This is the test case for your scripted module.
  """

  def delayDisplay(self,message,msec=1000):
    """This utility method displays a small dialog and waits.
    This does two things: 1) it lets the event loop catch up
    to the state of the test so that rendering and widget updates
    have all taken place before the test continues and 2) it
    shows the user/developer/tester the state of the test
    so that we'll know when it breaks.
    """
    print(message)
    self.info = qt.QDialog()
    self.infoLayout = qt.QVBoxLayout()
    self.info.setLayout(self.infoLayout)
    self.label = qt.QLabel(message,self.info)
    self.infoLayout.addWidget(self.label)
    qt.QTimer.singleShot(msec, self.info.close)
    self.info.exec_()

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    self.delayDisplay("Closing the scene")
    layoutManager = slicer.app.layoutManager()
    layoutManager.setLayout(slicer.vtkMRMLLayoutNode.SlicerLayoutConventionalView)
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.testSegmentationWizard()

  def testSegmentationWizard(self):
    """ Test the ChangeTracker module
    """
    self.delayDisplay("Starting the test")

    try:

        self.delayDisplay("Loading sample data")

        import SampleData
        sampleDataLogic = SampleData.SampleDataLogic()
        head = sampleDataLogic.downloadMRHead()
        braintumor1 = sampleDataLogic.downloadMRBrainTumor1()
        braintumor2 = sampleDataLogic.downloadMRBrainTumor2()

        self.delayDisplay("Getting scene variables")

        mainWindow = slicer.util.mainWindow()
        layoutManager = slicer.app.layoutManager()
        threeDView = layoutManager.threeDWidget(0).threeDView()
        redWidget = layoutManager.sliceWidget('Red')
        redController = redWidget.sliceController()
        viewNode = threeDView.mrmlViewNode()
        cameras = slicer.util.getNodes('vtkMRMLCameraNode*')

        mainWindow.moduleSelector().selectModule('SegmentationWizard')
        modelsegmentation_module = slicer.modules.modelsegmentation.widgetRepresentation().self()

        self.delayDisplay('Select Volumes')
        baselineNode = braintumor1
        followupNode = braintumor2
        modelsegmentation_module.Step1._VolumeSelectStep__enableSubtractionMapping.setChecked(True)
        modelsegmentation_module.Step1._VolumeSelectStep__baselineVolumeSelector.setCurrentNode(baselineNode)
        modelsegmentation_module.Step1._VolumeSelectStep__followupVolumeSelector.setCurrentNode(followupNode)

        self.delayDisplay('Go Forward')
        modelsegmentation_module.workflow.goForward()

        self.delayDisplay('Register Images')
        modelsegmentation_module.Step2.onRegistrationRequest(wait_for_completion=True)

        self.delayDisplay('Go Forward')
        modelsegmentation_module.workflow.goForward()

        self.delayDisplay('Normalize Images')
        modelsegmentation_module.Step3.onGaussianNormalizationRequest()

        self.delayDisplay('Subtract Images')
        modelsegmentation_module.Step3.onSubtractionRequest(wait_for_completion=True)

        self.delayDisplay('Go Forward')
        modelsegmentation_module.workflow.goForward()

        self.delayDisplay('Load model')

        displayNode = slicer.vtkMRMLMarkupsDisplayNode()
        slicer.mrmlScene.AddNode(displayNode)
        inputMarkup = slicer.vtkMRMLMarkupsFiducialNode()
        inputMarkup.SetName('Test')
        slicer.mrmlScene.AddNode(inputMarkup)
        inputMarkup.SetAndObserveDisplayNodeID(displayNode.GetID())

        modelsegmentation_module.Step4._ROIStep__clippingMarkupSelector.setCurrentNode(inputMarkup)

        inputMarkup.AddFiducial(35,-10,-10)
        inputMarkup.AddFiducial(-15,20,-10)
        inputMarkup.AddFiducial(-25,-25,-10)
        inputMarkup.AddFiducial(-5,-60,-15)
        inputMarkup.AddFiducial(-5,5,60)
        inputMarkup.AddFiducial(-5,-35,-30)

        self.delayDisplay('Go Forward')
        modelsegmentation_module.workflow.goForward()

        self.delayDisplay('Set Thresholds')
        modelsegmentation_module.Step5._ThresholdStep__threshRange.minimumValue = 50
        modelsegmentation_module.Step5._ThresholdStep__threshRange.maximumValue = 150

        self.delayDisplay('Go Forward')
        modelsegmentation_module.workflow.goForward()

        self.delayDisplay('Restart Module')
        modelsegmentation_module.Step6.Restart()

        self.delayDisplay('Test passed!')
        
    except Exception, e:
        import traceback
        traceback.print_exc()
        self.delayDisplay('Test caused exception!\n' + str(e))