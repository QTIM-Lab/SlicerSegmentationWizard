cmake_minimum_required(VERSION 2.8.9)

project(3D_Model_Segmentation)

#-----------------------------------------------------------------------------
# Extension meta-information
set(EXTENSION_HOMEPAGE "http://slicer.org/slicerWiki/index.php/Documentation/Nightly/Extensions/3D_Model_Segmentation")
set(EXTENSION_CATEGORY "Segmentation")
set(EXTENSION_CONTRIBUTORS "Andrew Beers (Massachussetts General Hospital)")
set(EXTENSION_DESCRIPTION "A semi-automatic 3D segmentation tool built for 3D Slicer. It includes utilities for calculating subtraction maps and thresholding intensity values.")
set(EXTENSION_ICONURL "https://raw.githubusercontent.com/QTIM-Lab/3D_Model_Segmentation/master/ModelSegmentation/Resources/Icons/ModelSegmentation.png")
set(EXTENSION_SCREENSHOTURLS "https://raw.githubusercontent.com/QTIM-Lab/3D_Model_Segmentation/master/ModelSegmentation/Resources/Icons/ModelSegmentation.png")
set(EXTENSION_DEPENDS "NA") # Specified as a space separated string, a list or 'NA' if any

#-----------------------------------------------------------------------------
# Extension dependencies
find_package(Slicer REQUIRED)
include(${Slicer_USE_FILE})

#-----------------------------------------------------------------------------
# Extension modules
add_subdirectory(ModelSegmentation)
## NEXT_MODULE

#-----------------------------------------------------------------------------
include(${Slicer_EXTENSION_CPACK})
