slicer_add_python_unittest(
  SCRIPT ModelSegmentationSelfTest.py
  SLICER_ARGS --additional-module-path
  "${CMAKE_BINARY_DIR}/${Slicer_QTLOADABLEMODULES_LIB_DIR}"
  )

slicerMacroBuildScriptedModule(
  NAME ModelSegmentationSelfTest
  SCRIPTS "ModelSegmentationSelfTest.py"
  RESOURCES ""
  )