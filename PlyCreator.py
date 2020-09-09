#!/usr/bin/env python
# coding: utf-8

# In[1]:


#
#---------author: THOMAS GRANDSAERT - 2020
#
import numpy as np # linear algebra
import pandas as pd # data processing, CSV file I/O (e.g. pd.read_csv)
from subprocess import check_output
from skimage.io import imread, imsave
from glob import glob
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import tifffile as tiff
import csv
import os
import datetime
from plyfile import PlyData, PlyElement
    
#-------------------------GENERATE POINT CLOUD------------------------------

def generatePly(options):
    
    #================SETUP===============#
    
    filepath = options.get('filepath', "")
    
    stack_image = imread(filepath)
    stack_image = np.asarray(stack_image)
    
    totalLen_X=len(stack_image)
    totalLen_Y=len(stack_image[0])
    totalLen_Z=len(stack_image[0][0])

    center_X=totalLen_X/2
    center_Y=totalLen_Y/2
    center_Z=totalLen_Z/2

    #==============MORE SETUP===================#
    
    thresholdRanges = options.get('thresholdRanges', [[0,255]])
    sampleSizes = options.get('sampleSizes', [[100,100,100]])
    decimationFactors = options.get('decimationFactors', [1])
    origin = options.get('origin', [center_X,center_Y,center_Z])
    initialRange = options.get('initialRange', [0,255])
    rescaleColors = options.get('rescaleColors', False)
    outputFilePath = options.get('outputFilePath', 'D:/DATA/test')
    outputFileName = options.get('outputFileName', "testFile_")
    binary = options.get('binary', True)
    centered = options.get('centered', True)
    

    startTime = datetime.datetime.now()
    print("Start time:",str(startTime)[10:-7])
    
    for decimationFactor, sampleSize, thresholdRange in zip(decimationFactors, sampleSizes, thresholdRanges):
        timer = datetime.datetime.now()
        
        if(centered):        
            x_i = int(origin[0]-(sampleSize[0]/2))
            y_i = int(origin[1]-(sampleSize[1]/2))
            z_i = int(origin[2]-(sampleSize[2]/2))
        else:
            x_i = origin[0]
            y_i = origin[1]
            z_i = origin[2]

        delta1 = thresholdRange[1] - thresholdRange[0]                
        delta2 = initialRange[1] - initialRange[0]

        counter = 0
        i = 0
        j = 0 

        if(sampleSize==0):
            total_points = (len(stack_image)*len(stack_image[0])*len(stack_image[0][0]))
            lenX=totalLenX
            lenY=totalLenY
            lenZ=totalLenZ
        else:
            total_points = (sampleSize[0]*sampleSize[1]*sampleSize[2])
            len_X=sampleSize[0]
            len_Y=sampleSize[1]
            len_Z=sampleSize[2]
            
        #---------------------CREATE THE ZERO PLY ARRAY-------------------------------
        ply_array = np.zeros(total_points,dtype=[('x', 'f4'), ('y', 'f4'),
                                ('z', 'f4'),
                                ('density', 'f4'), 
                                ('red', 'u1'), 
                                ('green', 'u1'),
                                ('blue', 'u1')])

        for x in range(x_i,(x_i+len_X-1)):
            
            #-----------------ESTIMATE TIME LEFT -------------------
            totalEstimatedTime = str((datetime.datetime.now()-timer)*((x_i+len_X-1)-x))[:-7]            
            print("Slice: ",x, "/", str(x_i+len_X-2)," \\\\ Time remaining: ",totalEstimatedTime, end='\r', flush=True)
            timer = datetime.datetime.now()

            for y in range(y_i,(y_i+len_Y)-1):

                for z in range(z_i,(z_i+len_Z)-1):
                    
                    #-----------------GET PIXEL VALUE AT X,Y,Z POINT-------------------
                    attenuation = stack_image[x][y][z]
                    
                    #---------------------RESCALE THE COLOR INTENSITY TO THRESHOLD MIN/MAX--------------------------------------
                    if(rescaleColors):
                        intensity = int((delta2 * (attenuation - thresholdRange[0]) / delta1) + initialRange[0])
                    else:
                        intensity = attenuation                           
                    #------------------------------------------------------------------------------------------------------------
                    #----------------------------- MAIN LOOP ------------------------------------------------------------------
                    
                    if((counter % decimationFactor == 0) 
                       and (counter != 0) 
                       and (attenuation >= thresholdRange[0]) 
                       and (attenuation <= thresholdRange[1])):

                        ply_array[j] = (x-center_X,
                                        y-center_Y,
                                        z-center_Z,
                                        intensity,
                                        intensity,
                                        intensity,
                                        intensity)
                        counter = 0

                        j += 1

                    elif (i==0):
                        ply_array[j] = (x-center_X,
                                        y-center_Y,
                                        z-center_Z,
                                        intensity,
                                        intensity,
                                        intensity,
                                        intensity)
                        counter = 0
                        j += 1
                    else:
                        counter += 1
                    i+=1

        ply_array = np.delete(ply_array,np.s_[j:(len(ply_array))],axis=0)

        file_suffix = "_Thr."+str(thresholdRange[0])+"-"+str(thresholdRange[1])+"_Dec."+str(decimationFactor)+"_Pix."+str(sampleSize)

        outputFullPath = os.path.join(outputFilePath, outputFileName + file_suffix + ".ply")
        el = PlyElement.describe(ply_array, "vertex",
                                  comments=[outputFileName])
        if(binary):
            PlyData([el]).write(outputFullPath)
        else:
            PlyData([el], text=True).write(outputFullPath)
           
        totalTime = str(datetime.datetime.now()-startTime)
        print("Succesfully parsed to: ", outputFullPath)
        print("Time elapsed:", str(totalTime)[:-7])        
        print("")        


# In[21]:


#---------NOTE: thresholds are inclusive 
options = {
        "filepath" : r'A18_3_3_d2_8bit pleural nevi_stack\A18_3_3_d2_8bit pleural nevi_stack.tif',
        "thresholdRanges" : [[80, 255]] , #DESIRED THESHOLD RANGE FOR IMAGES (IN INTENSITY)
        "sampleSizes" : [[300, 300, 300]] , #DESIRED SAMPLE SIZES IN PIXELS
        "decimationFactors" : [1], #DESIRED DECIMATION FACTORS N (SKIP EVERY N PIXEL)
#         "origin" : [200,600,600], #DESIRED ORIGIN (IF NOT CENTER)
        "initialRange" : [0,255], #INITIAL IMAGE RANGE
        "rescaleColors" : True,  #RESCALE IMAGE 0-255 FOR NEW RANGES?
        "binary" : True, #BINARY REQUIRED FOR UNITY PLY SHADER, NON-BINARY RECOMMENDED FOR OTHER SOFTWARE
        "centered" : True, #CENTER THE IMAGE SAMPLE
        "outputFilePath" : 'D:/DATA/test',
        "outputFileName" : "TOMCAT_Lungs_binary__"
    }


# In[22]:


generatePly(options)


# In[ ]:




