slicer_add_python_unittest(
  SCRIPT SegmentationWizardSelfTest.py
  SLICER_ARGS --additional-module-path
  "${CMAKE_BINARY_DIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}"
  )

slicerMacroBuildScriptedModule(
  NAME SegmentationWizardSelfTest
  SCRIPTS "SegmentationWizardSelfTest.py"
  RESOURCES ""
  )