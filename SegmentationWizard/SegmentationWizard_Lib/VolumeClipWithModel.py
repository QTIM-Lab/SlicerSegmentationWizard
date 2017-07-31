from __main__ import qt, ctk, slicer
from SegmentationWizardStep import *
from Helper import *

class VolumeClipWithModelLogic(ScriptedLoadableModuleLogic):
	"""This class should implement all the actual
	computation done by your module.  The interface
	should be such that other python code can import
	this class and make use of the functionality without
	requiring an instance of the Widget
	"""

	def createParameterNode(self):
		# Set default parameters
		node = ScriptedLoadableModuleLogic.createParameterNode(self)
		node.SetName(slicer.mrmlScene.GetUniqueNameByString(self.moduleName))
		node.SetParameter("ClipOutsideSurface", "1")
		node.SetParameter("FillValue", "-1")
		return node

	def clipVolumeWithModel(self, inputVolume, clippingModel, clipOutsideSurface, fillValue, outputVolume):
		"""
		Fill voxels of the input volume inside/outside the clipping model with the provided fill value
		"""
		
		# Determine the transform between the box and the image IJK coordinate systems
		
		rasToModel = vtk.vtkMatrix4x4()    
		if clippingModel.GetTransformNodeID() != None:
			modelTransformNode = slicer.mrmlScene.GetNodeByID(clippingModel.GetTransformNodeID())
			boxToRas = vtk.vtkMatrix4x4()
			modelTransformNode.GetMatrixTransformToWorld(boxToRas)
			rasToModel.DeepCopy(boxToRas)
			rasToModel.Invert()
			
		ijkToRas = vtk.vtkMatrix4x4()
		inputVolume.GetIJKToRASMatrix( ijkToRas )

		ijkToModel = vtk.vtkMatrix4x4()
		vtk.vtkMatrix4x4.Multiply4x4(rasToModel,ijkToRas,ijkToModel)
		modelToIjkTransform = vtk.vtkTransform()
		modelToIjkTransform.SetMatrix(ijkToModel)
		modelToIjkTransform.Inverse()
		
		transformModelToIjk=vtk.vtkTransformPolyDataFilter()
		transformModelToIjk.SetTransform(modelToIjkTransform)
		transformModelToIjk.SetInputConnection(clippingModel.GetPolyDataConnection())

		# Use the stencil to fill the volume
		
		# Convert model to stencil
		polyToStencil = vtk.vtkPolyDataToImageStencil()
		polyToStencil.SetInputConnection(transformModelToIjk.GetOutputPort())
		polyToStencil.SetOutputSpacing(inputVolume.GetImageData().GetSpacing())
		polyToStencil.SetOutputOrigin(inputVolume.GetImageData().GetOrigin())
		polyToStencil.SetOutputWholeExtent(inputVolume.GetImageData().GetExtent())
		
		# Apply the stencil to the volume
		stencilToImage=vtk.vtkImageStencil()
		stencilToImage.SetInputConnection(inputVolume.GetImageDataConnection())
		stencilToImage.SetStencilConnection(polyToStencil.GetOutputPort())
		if clipOutsideSurface:
			stencilToImage.ReverseStencilOff()
		else:
			stencilToImage.ReverseStencilOn()
		stencilToImage.SetBackgroundValue(fillValue)
		stencilToImage.Update()

		# Update the volume with the stencil operation result
		outputImageData = vtk.vtkImageData()
		outputImageData.DeepCopy(stencilToImage.GetOutput())
		
		outputVolume.SetAndObserveImageData(outputImageData);
		outputVolume.SetIJKToRASMatrix(ijkToRas)

		# Add a default display node to output volume node if it does not exist yet
		if not outputVolume.GetDisplayNode:
			displayNode=slicer.vtkMRMLScalarVolumeDisplayNode()
			displayNode.SetAndObserveColorNodeID("vtkMRMLColorTableNodeGrey")
			slicer.mrmlScene.AddNode(displayNode)
			outputVolume.SetAndObserveDisplayNodeID(displayNode.GetID())

		return True

	def updateModelFromMarkup(self, inputMarkup, outputModel):
		"""
		Update model to enclose all points in the input markup list
		"""
		
		# Delaunay triangulation is robust and creates nice smooth surfaces from a small number of points,
		# however it can only generate convex surfaces robustly.
		useDelaunay = True
		
		# Create polydata point set from markup points
		
		points = vtk.vtkPoints()
		cellArray = vtk.vtkCellArray()
		
		numberOfPoints = inputMarkup.GetNumberOfFiducials()

		# Surface generation algorithms behave unpredictably when there are not enough points
		# return if there are very few points
		if useDelaunay:
			if numberOfPoints<3:
				return
		else:
			if numberOfPoints<10:
				return

		points.SetNumberOfPoints(numberOfPoints)
		new_coord = [0.0, 0.0, 0.0]

		for i in range(numberOfPoints):
			inputMarkup.GetNthFiducialPosition(i,new_coord)
			points.SetPoint(i, new_coord)

		cellArray.InsertNextCell(numberOfPoints)
		for i in range(numberOfPoints):
			cellArray.InsertCellPoint(i)

		pointPolyData = vtk.vtkPolyData()
		pointPolyData.SetLines(cellArray)
		pointPolyData.SetPoints(points)

		
		# Create surface from point set

		if useDelaunay:
					
			delaunay = vtk.vtkDelaunay3D()
			delaunay.SetInputData(pointPolyData)

			surfaceFilter = vtk.vtkDataSetSurfaceFilter()
			surfaceFilter.SetInputConnection(delaunay.GetOutputPort())

			smoother = vtk.vtkButterflySubdivisionFilter()
			smoother.SetInputConnection(surfaceFilter.GetOutputPort())
			smoother.SetNumberOfSubdivisions(3)
			smoother.Update()

			outputModel.SetPolyDataConnection(smoother.GetOutputPort())
			
		else:
			
			surf = vtk.vtkSurfaceReconstructionFilter()
			surf.SetInputData(pointPolyData)
			surf.SetNeighborhoodSize(20)
			surf.SetSampleSpacing(80) # lower value follows the small details more closely but more dense pointset is needed as input

			cf = vtk.vtkContourFilter()
			cf.SetInputConnection(surf.GetOutputPort())
			cf.SetValue(0, 0.0)

			# Sometimes the contouring algorithm can create a volume whose gradient
			# vector and ordering of polygon (using the right hand rule) are
			# inconsistent. vtkReverseSense cures this problem.
			reverse = vtk.vtkReverseSense()
			reverse.SetInputConnection(cf.GetOutputPort())
			reverse.ReverseCellsOff()
			reverse.ReverseNormalsOff()

			outputModel.SetPolyDataConnection(reverse.GetOutputPort())

		# Create default model display node if does not exist yet
		if not outputModel.GetDisplayNode():
			modelDisplayNode = slicer.mrmlScene.CreateNodeByClass("vtkMRMLModelDisplayNode")
			modelDisplayNode.SetColor(0,0,1) # Blue
			modelDisplayNode.BackfaceCullingOff()
			modelDisplayNode.SliceIntersectionVisibilityOn()
			modelDisplayNode.SetOpacity(0.3) # Between 0-1, 1 being opaque
			slicer.mrmlScene.AddNode(modelDisplayNode)
			outputModel.SetAndObserveDisplayNodeID(modelDisplayNode.GetID())
	
		outputModel.GetDisplayNode().SliceIntersectionVisibilityOn()
			
		outputModel.Modified()

	def showInSliceViewers(self, volumeNode, sliceWidgetNames):
		# Displays volumeNode in the selected slice viewers as background volume
		# Existing background volume is pushed to foreground, existing foreground volume will not be shown anymore
		# sliceWidgetNames is a list of slice view names, such as ["Yellow", "Green"]
		if not volumeNode:
			return
		newVolumeNodeID = volumeNode.GetID()
		for sliceWidgetName in sliceWidgetNames:
			sliceLogic = slicer.app.layoutManager().sliceWidget(sliceWidgetName).sliceLogic()
			foregroundVolumeNodeID = sliceLogic.GetSliceCompositeNode().GetForegroundVolumeID()
			backgroundVolumeNodeID = sliceLogic.GetSliceCompositeNode().GetBackgroundVolumeID()
			if foregroundVolumeNodeID == newVolumeNodeID or backgroundVolumeNodeID == newVolumeNodeID:
				# new volume is already shown as foreground or background
				continue
			if backgroundVolumeNodeID:
				# there is a background volume, push it to the foreground because we will replace the background volume
				sliceLogic.GetSliceCompositeNode().SetForegroundVolumeID(backgroundVolumeNodeID)
			# show the new volume as background
			sliceLogic.GetSliceCompositeNode().SetBackgroundVolumeID(newVolumeNodeID)