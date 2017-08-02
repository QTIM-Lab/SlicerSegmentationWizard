#-----------------------------------------------------------------------------
set(MODULE_NAME SegmentationWizard)

#-----------------------------------------------------------------------------
set(MODULE_PYTHON_SCRIPTS
  ${MODULE_NAME}.py
  )

set(MODULE_PYTHON_RESOURCES
  Resources/Icons/${MODULE_NAME}.png
  ${MODULE_NAME}_Lib/__init__.py
  ${MODULE_NAME}_Lib/Helper.py
  ${MODULE_NAME}_Lib/SegmentationWizardStep.py
  ${MODULE_NAME}_Lib/NormalizeSubtract.py
  ${MODULE_NAME}_Lib/Registration.py
  ${MODULE_NAME}_Lib/Review.py
  ${MODULE_NAME}_Lib/ROI.py
  ${MODULE_NAME}_Lib/Threshold.py
  ${MODULE_NAME}_Lib/VolumeClipWithModel.py
  ${MODULE_NAME}_Lib/VolumeSelect.py
  ${MODULE_NAME}_Lib/MarkupsMouseModePlace.png
  )

#-----------------------------------------------------------------------------
slicerMacroBuildScriptedModule(
  NAME ${MODULE_NAME}
  SCRIPTS ${MODULE_PYTHON_SCRIPTS}
  RESOURCES ${MODULE_PYTHON_RESOURCES}
  WITH_GENERIC_TESTS
  )

#-----------------------------------------------------------------------------
if(BUILD_TESTING)

  # Register the unittest subclass in the main script as a ctest.
  # Note that the test will also be available at runtime.
  slicer_add_python_unittest(SCRIPT ${MODULE_NAME}.py)

  # Additional build-time testing
  add_subdirectory(Testing)
endif()
