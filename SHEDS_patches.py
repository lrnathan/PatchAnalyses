## Uses SHEDS catchment data to make new patches, to compare with EBTJV patches
##
##Author: Lucas Nathan
##Contact: lucas.nathan@uconn.edu
##


#############################################################################################
##                                 Specify Tool Inputs                                     ##
#############################################################################################
#specify upstream impervious surface threshold
impThresh=3
#catchment file
catchments=r"P:\GIS files\EBTJV\my_revised_patches\SHEDS_CT_EBTJV_clip.shp"
#barriers
#barriers=r"P:\GIS files\EBTJV\my_revised_patches\modifiedBarriers\ebtjv_barriers_MODIFIED.shp"
barriers=r"P:\GIS files\EBTJV\ebjtv_barriers_09_23_15_CT.shp"
#sheds upstream file (if not already in catchments shapefile)
#shedsFile=r"C:\Users\lrn14001\Desktop\Dissertation\chapter4_COA\COA_analysis\CT\SHEDS_LocUp_Data_Connecticut.csv"


#Catchment output
catchOut=r"P:\GIS files\EBTJV\my_revised_patches\originalBarriers\NEWPATCH_EBTJV_SHEDS.shp"
#Patch output
patchOut=r"P:\GIS files\EBTJV\my_revised_patches\originalBarriers\NEWPATCH_EBTJV.shp"







#############################################################################################
##                            Import modules and Set Up Workspace                          ##
#############################################################################################

## import modules
import arcpy, csv, os, sys

## allow outputs to be overwritten
arcpy.env.overwriteOutput = 1

#specify workspace
arcpy.env.workspace=r"in_memory"
#create duplicate feature layers
arcpy.CopyFeatures_management(catchments,"catchmentsCopy")
arcpy.MakeFeatureLayer_management("catchmentsCopy", "catchmentsLyr")
arcpy.CopyFeatures_management(barriers,"barriersCopy")
arcpy.MakeFeatureLayer_management("barriersCopy", "barriersLyr")


###################################################################################
##                              Input Data                                       ##
###################################################################################
print("Reading in input files..")
#loop through catchments and store "featureid" and "nextdownID"
featureidList=[]
nextdownList=[]
impCatches=[]
##create search cursor for spatial join file 
rows=arcpy.SearchCursor("catchmentsLyr")
for row in rows:
        #get IDs and store in list
        featureidList.append(int(row.getValue("FEATUREID")))
        nextdownList.append(int(row.getValue("NextDownID")))
        if float(row.getValue("impervUP"))>impThresh:
                impCatches.append(int(row.getValue("FEATUREID")))
del row, rows

#get headwater streams-- i.e. those that are not in the "nextdownID" list
headwatersList=[x for x in featureidList if x not in nextdownList]

#identify catchments with dams in them
arcpy.SelectLayerByLocation_management("catchmentsLyr", "INTERSECT", "barriersLyr",selection_type="NEW_SELECTION")

#loop through catchments and store "featureid" and "nextdownID"
dams=[]
##create search cursor for spatial join file 
rows=arcpy.SearchCursor("catchmentsLyr")
for row in rows:
	#get IDs and store in list
	dams.append(int(row.getValue("FEATUREID")))
del row, rows

#unselect catchments
arcpy.SelectLayerByAttribute_management("catchmentsLyr", "CLEAR_SELECTION")

##if using a csv file for SHEDS data
##impCatches=[]
###open input SHEDS data file
##infile=open(shedsFile,"rb")
###create csv reader
##reader=csv.reader(infile)
##i=0
###loop through SHEDS file
##for row in reader:
##        #get column indices
##        if(i==0):
##                zoneIndex=row.index("zone")
##                variableIndex=row.index("variable")
##                valueIndex=row.index("value")
##                catchIndex=row.index("featureid")
##        else:
##                if row[zoneIndex] == "upstream":
##                        if row[variableIndex] == "impervious":
##                                upImp=float(row[valueIndex])
##                                if upImp > float(impThresh):
##                                        catchID=int(row[catchIndex])
##                                        impCatches.append(int(catchID))
##        i=i+1
##del row, reader
##infile.close()
print(str(len(featureidList))+" Total Catchments")
print(str(len(dams))+" Catchments with dams")
print(str(len(impCatches))+" Catchments > %s%% upstream imp surface"%impThresh)
###################################################################################
##                      Assign Catchments to Patches                             ##
###################################################################################
print("Assigning Catchments to Patches..")
newPatches=[]
#loop through headwater catchments
for hw in headwatersList:
        #create new patch
        patch=[hw]
        #create indicator for duplicates (i.e. a catchment is already in another patch)
        duplicate=0
        #if the headwater catchment contains a dam or is above impThresh
        if hw in dams or hw in impCatches:
                newPatches.append(patch)
                nextDown=nextdownList[featureidList.index(hw)]
                if nextDown in featureidList:
                        patch=[nextDown]
                else:
                        continue
        else:
                nextDown=nextdownList[featureidList.index(hw)]
        while(nextDown in nextdownList):
                #check to see if the nextDown catchment is already in a patch
                for p in newPatches:
                        if nextDown in p:
                             newPatches[newPatches.index(p)].extend(patch)
                             duplicate=1
                             nextDown=0
                             break
                if nextDown not in dams and nextDown not in impCatches:
                        patch.append(nextDown)
                        if nextDown in featureidList:
                                nextDown=nextdownList[featureidList.index(nextDown)]
                        else:
                                nextDown=0
                else:
                        patch.append(nextDown)
                        nextDown=0
        if duplicate==0:
                newPatches.append(patch)

#find catchments that weren't assigned a patch-- probably because they are downstream of a barrier
loneCatches=[]
for catch in featureidList:
        for patch in newPatches:
                #if the catchment is in the patch, move to next catchment
                if catch in patch:
                        break
                #if it's the last patch, then store the catchment in the loneCatches list
                elif newPatches.index(patch)==len(newPatches)-1:
                        loneCatches.append(catch)
                #if it's not the last patch, then keep looking
                else:
                        continue
                
#loop through lone catchments
for c in loneCatches:
        #create new patch
        patch=[c]
        #create indicator for duplicates (i.e. a catchment is already in another patch)
        duplicate=0
        #if the catchment contains a dam or is above impThresh
        if c in dams or c in impCatches:
                newPatches.append(patch)
                nextDown=nextdownList[featureidList.index(c)]
                if nextDown in featureidList:
                        patch=[nextDown]
                else:
                        continue
        else:
                nextDown=nextdownList[featureidList.index(c)]
        while(nextDown in nextdownList):
                #check to see if the nextDown catchment is already in a patch
                for p in newPatches:
                        if nextDown in p:
                             newPatches[newPatches.index(p)].extend(patch)
                             duplicate=1
                             nextDown=0
                             break
                if nextDown not in dams and nextDown not in impCatches:
                        patch.append(nextDown)
                        if nextDown in featureidList:
                                nextDown=nextdownList[featureidList.index(nextDown)]
                        else:
                                nextDown=0
                else:
                        patch.append(nextDown)
                        nextDown=0
        if duplicate==0:
                newPatches.append(patch)
numPatches=len(newPatches)
print(str(numPatches)+" Patches Created")
###################################################################################
##                              Create Patches                                   ##
###################################################################################
print("Storing PatchIDs in Catchment Shapefile...")

##add patch ID to catchment shapefile
arcpy.AddField_management("catchmentsLyr", "NewPatchID", "short")
rows=arcpy.UpdateCursor("catchmentsLyr")
for row in rows:
        #get catchmentID
        catchID=int(row.getValue("FEATUREID"))
        #find patch with catchment in it
        for p in range(0,numPatches):
                #if the catchment is in the patch, store NewPatchID
                if catchID in newPatches[p]:
                        row.setValue("NewPatchID",p)
                        #go to next catchment
                        break
                #if the catchment isn't in the patch..
                else:
                        #and its the last one..
                        if p ==(numPatches-1):
                                #store a null value (9999)
                                row.setValue("NewPatchID",9999)
        # Update the cursor
        rows.updateRow(row)
#delete search cursor
del row,rows

#merge catchments based on NewPatchID
print("Dissolving Catchments into Patches...")
arcpy.Dissolve_management("catchmentsLyr","newPatches",dissolve_field="NewPatchID")

#save output
arcpy.CopyFeatures_management("catchmentsLyr",catchOut)
arcpy.CopyFeatures_management("newPatches",patchOut)
print("Catchment file saved to "+str(catchOut))
print("Patch file saved to "+str(patchOut))

#clear in_memory workspace
arcpy.Delete_management("in_memory")
