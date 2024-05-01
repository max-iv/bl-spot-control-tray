from picamera import PiCamera
import picamera.array
import numpy as np
#from PIL import Image
import math
import sys
import json
import struct
import time

def getReading(camera,cameraSettings):
    tstart = time.process_time()
    with picamera.array.PiRGBArray(camera) as output:
        camera.resolution = (2944, 1920)
        camera.shutter_speed = cameraSettings['shutter_speed']
        cameraSettings['shutter_speed'] = camera.shutter_speed
        camera.exposure_mode = 'off'
        camera.awb_mode = 'off'
        camera.awb_gains = (1.464,1.937)
        camera.iso = 100
        camera.capture(output, 'rgb')
        maxAddr = output.array.argmax();
        nrows = output.array.shape[0]
        ncols = output.array.shape[1]
        ncolr = output.array.shape[2]
        maxRawSignal = output.array.max()
        row = int(maxAddr / (ncols * ncolr))
        col = int((maxAddr - row * (ncols * ncolr)) / ncolr)
        clr = maxAddr - row * (ncols * ncolr) - col * ncolr
        maxRawSignal = output.array.max()
        crop = np.zeros([cameraSettings['cropPix'] , cameraSettings['cropPix'] ])
        if maxRawSignal < cameraSettings['minIntensity']:
          readingString = '{"command":"reading","intensity":'+ str(maxRawSignal) + ',"posX":' + str(0) + ',"posY":' + str(0) + ',"beamSize":' + str(0) + '}'
          im = Image.fromarray(crop)
          im = im.convert('RGB')
          im.save("crop.jpg")
          print(readingString)
          return
        cropPix2 = round(cameraSettings['cropPix'] / 2)
        irow = -cropPix2
        if row < cropPix2:
          row = cropPix2
        if row > (nrows - cropPix2 - 1):
          row = nrows - cropPix2 - 1
        if col < cropPix2:
          col = cropPix2
        if col > (ncols - cropPix2 - 1):
          col = ncols - cropPix2 - 1
        for x in crop:
          icol = -cropPix2
          for y in x:
            crop[irow + cropPix2][icol + cropPix2] =  output.array[row + irow][col + icol][0]
            crop[irow + cropPix2][icol + cropPix2] =  crop[irow + cropPix2][icol + cropPix2] + output.array[row + irow][col + icol][1]   
            crop[irow + cropPix2][icol + cropPix2] =  crop[irow + cropPix2][icol + cropPix2] + output.array[row + irow][col + icol][2]
            icol += 1
          irow += 1  
        cut = round(crop.max() * cameraSettings['noiseFloorCut'])
        sum0 = 0
        posX = 0
        posY = 0
        irow = -cropPix2
        for x in crop:
          icol = -cropPix2
          for y in x:
            if crop[irow + cropPix2][icol + cropPix2] < cut:
              crop[irow + cropPix2][icol + cropPix2] = 0
            sum0 = sum0 + crop[irow + cropPix2][icol + cropPix2]
            posX = posX + crop[irow + cropPix2][icol + cropPix2] * (row + irow)
            posY = posY + crop[irow + cropPix2][icol + cropPix2] * (col + icol)
            icol += 1
          irow += 1  
        posX =  posX / sum0;
        posY =  posY / sum0;
        varX = 0
        varY = 0
        irow = -cropPix2
        for x in crop:
          icol = -cropPix2
          for y in x:
            varX = varX + crop[irow + cropPix2][icol + cropPix2] * (row + irow - posX) * (row + irow - posX)
            varY = varY + crop[irow + cropPix2][icol + cropPix2] * (col + icol - posY) * (col + icol - posY)
            icol += 1
          irow += 1  
        varX =  varX / sum0;
        varY =  varY / sum0;
        beamSize = round(math.sqrt(varX + varY),2)
        posX = round(posX,2)
        posY = round(posY,2)
#        im = Image.fromarray(crop)
#        im = im.convert('RGB')
#        im.save("html-static/laser-spot.jpg")
        readingString = '{"command":"reading","intensity":'+ str(maxRawSignal) + ',"posX":' + str(posX) + ',"posY":' + str(posY) + ',"beamSize":' + str(beamSize) 
        readingString = readingString  + ',"shutter_speed":' + str(cameraSettings['shutter_speed']) 
        readingString = readingString  + ',"minIntensity":'  + str(cameraSettings['minIntensity']) 
        readingString = readingString  + ',"noiseFloorCut":' + str(cameraSettings['noiseFloorCut']) 
        readingString = readingString  + ',"cropPix":'       + str(cameraSettings['cropPix']) + '}'
        print(readingString)
#        print(time.process_time() - tstart)
        output.close()
    return
def writeSetting(setting,cameraSettings):
    cameraSettings['shutter_speed'] = setting['shutter_speed']
    cameraSettings['minIntensity']  = setting['minIntensity']
    cameraSettings['noiseFloorCut'] = setting['noiseFloorCut']
    cameraSettings['cropPix']       = setting['cropPix']
    return

cameraSettings = {'shutter_speed': 50, 'minIntensity': 100, 'noiseFloorCut':0.05,   'cropPix':50 }
camera = PiCamera()
camera.resolution = (2944, 1920)
camera.shutter_speed = cameraSettings['shutter_speed']
cameraSettings['shutter_speed'] = camera.shutter_speed
camera.exposure_mode = 'off'
camera.awb_mode = 'off'
camera.awb_gains = (1.464,1.937)
camera.iso = 100
# print("Warmup camera")
time.sleep(2)

while True:
    instructionText = sys.stdin.readline().strip('\n')
    instruction = json.loads(instructionText)
    if instruction["command"] == "setting":
        writeSetting(instruction,cameraSettings)
        print(instructionText)
    if instruction["command"] == "reading":
        getReading(camera,cameraSettings)

