cmake_minimum_required(VERSION 2.8.9)

project(SegmentationWizard)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/SegmentationWizard")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Andrew Beers (Massachussetts General Hospital)")
set(EXTENSION_DESCRIPTION "A semi-automatic high-resolution segmentation workflow built for 3D Slicer. It includes utilities for calculating subtraction maps and thresholding intensity values.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/QTIM-Lab/3D_Model_Segmentation/master/SegmentationWizard/Resources/Icons/SegmentationWizard.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/QTIM-Lab/3D_Model_Segmentation/master/SegmentationWizard/Resources/Icons/SegmentationWizard.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(SegmentationWizard)
## NEXT_MODULE

if(BUILD_TESTING)
  add_subdirectory(Testing)
endif()

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
