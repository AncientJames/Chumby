# Thumby graphics base

# Written by Mason Watmough, Jason Marcum, and Ben Rose for TinyCircuits.
# 11-Jul-2022

'''
    This file is part of the Thumby API.

    The Thumby API is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    The Thumby API is distributed in the hope that it will be useful, but
    WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY
    or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.

    You should have received a copy of the GNU General Public License along with
    the Thumby API. If not, see <https://www.gnu.org/licenses/>.
'''

from st7735 import ST7735
from machine import Pin
from os import stat
from time import ticks_ms, ticks_diff, sleep_ms
from thumbyHardware import i2c, spi
from thumbyButton import buttonA, buttonB, buttonU, buttonD, buttonL, buttonR

# Last updated 17-Jan-2023
__version__ = '1.9'


@micropython.native
def colorRGB(r, g, b):
    return (r & 0xf8) | ((g & 0xe0) >> 5) | ((g & 0x1c) << 11) | ((b & 0xf8) <<5)

@micropython.native
def colorHSV(h, s, v):
    if s == 0:
        r = v
        g = v
        b = v
    else:
        region = h // 43;

        remainder = (h - (region * 43)) * 6; 

        p = (v * (255 - s)) >> 8;
        q = (v * (255 - ((s * remainder) >> 8))) >> 8;
        t = (v * (255 - ((s * (255 - remainder)) >> 8))) >> 8;

        if region == 0:
            r = v
            g = t
            b = p
        
        elif region == 1:
            r = q; 
            g = v; 
            b = p;

        elif region == 2:
            r = p; 
            g = v; 
            b = t;

        elif region == 3:
            r = p; 
            g = q; 
            b = v;

        elif region == 4:
            r = t; 
            g = p; 
            b = v;

        else: 
            r = v; 
            g = p; 
            b = q;

    return (r & 0xf8) | ((g & 0xe0) >> 5) | ((g & 0x1c) << 11) | ((b & 0xf8) <<5)

C_WHITE = 0b_11111111_11111111
C_BLACK = 0b_00000000_00000000
C_RED =   0b_00000000_11111000
C_GREEN = 0b_11100000_00000111
C_BLUE =  0b_00011111_00000000
C_YELLOW =0b_11100000_11111111
C_MAGENTA=0b_00011111_11111000
C_CYAN =  0b_11100000_11111111

# Graphics class, from which the gfx namespace is defined.
class GraphicsClass:
    def __init__(self, display, width, height):
        self.fg = C_WHITE
        self.bg = C_BLACK
        self.display = display
        self.frameRate = 0
        self.lastUpdateEnd = 0
        self.setResolution(width, height)
        self.setFont('lib/font5x7.bin', 5, 7, 1)
        self.fill(0)
        
    def setResolution(self, width=0, height=0):
        self.display.set_resolution(width, height)
        self.width = self.display.bufferwidth
        self.height = self.display.bufferheight
        self.max_x = self.width-1
        self.max_y = self.height-1

    @micropython.native
    def setFont(self, fontFile, width, height, space):
        self.textBitmapSource = fontFile
        self.textBitmapFile = open(self.textBitmapSource, 'rb')
        self.textWidth = width
        self.textHeight = height
        self.textSpaceWidth = space
        self.textBitmap = bytearray(self.textWidth)
        self.textCharCount = stat(self.textBitmapSource)[6] // self.textWidth
        
    @micropython.native
    def setFPS(self, newFrameRate):
        self.frameRate = newFrameRate
    
    # Push the buffer to the hardware display.
    @micropython.native
    def update(self):
        self.display.show()
        if self.frameRate>0:
            frameTimeRemaining = round(1000/self.frameRate) - ticks_diff(ticks_ms(), self.lastUpdateEnd)
            while(frameTimeRemaining>1):
                buttonA.update()
                buttonB.update()
                buttonU.update()
                buttonD.update()
                buttonL.update()
                buttonR.update()
                sleep_ms(1)
                frameTimeRemaining = round(1000/self.frameRate) - ticks_diff(ticks_ms(), self.lastUpdateEnd)
            while(frameTimeRemaining>0):
                frameTimeRemaining = round(1000/self.frameRate) - ticks_diff(ticks_ms(), self.lastUpdateEnd)
        self.lastUpdateEnd=ticks_ms()

    # Set display brightness, valid values 0 to 127
    @micropython.native
    def brightness(self,setting):
        if(setting>127):
            setting=127
        if(setting<0):
            setting=0
        self.display.contrast(setting)

    # Fill the buffer with a given color.
    @micropython.viper
    def fill(self, color:int):
        buf = ptr16(self.display.buffer)
        if color==1:
            color=int(C_WHITE)
            
        for i in range(int(len(self.display.buffer))>>1):
            buf[int(i)]=color

    @micropython.viper
    def setPixel(self, x:int, y:int, color:int):
        screenWidth = int(self.width)
        screenHeight = int(self.height)
        if not 0<=x<screenWidth:
            return
        if not 0<=y<screenHeight:
            return
        if color==1:
            color=int(C_WHITE)
        buf = ptr16(self.display.buffer)
        buf[y * screenWidth + x] = color
    
    @micropython.viper
    def getPixel(self, x:int, y:int) -> int:
        screenWidth = int(self.width)
        screenHeight = int(self.height)
        if not 0<=x<int(screenWidth):
            return 0
        if not 0<=y<int(screenHeight):
            return 0
        buf = ptr16(self.display.buffer)
        return buf[y * screenWidth + x]

    # Draw a line from (x1, y1) to (x2, y2) in a given color- taken from MicroPython FrameBuf implementation
    @micropython.viper
    def drawLine(self, x1:int, y1:int, x2:int, y2:int, color:int):
        buf = ptr16(self.display.buffer)
        dx = int(x2 - x1)
        sx = int(1)
        if (dx <= 0):
            dx = 0-dx
            sx = 0-1

        dy = int(y2 - y1)
        sy = int(1)
        if (dy <= 0):
            dy = 0-dy
            sy = 0-1

        steep = False
        if (dy > dx):
            temp = x1
            x1 = y1
            y1 = temp
            temp = dx
            dx = dy
            dy = temp
            temp = sx
            sx = sy
            sy = temp
            steep = True
        
        screenWidth = int(self.width)
        screenHeight = int(self.height)
        
        if color==1:
            color=int(C_WHITE)
        
        e = 2 * dy - dx
        for i in range(dx):
            if (steep):
                if (0 <= y1 and y1 < screenWidth and 0 <= x1 and x1 < screenHeight):
                    buf[x1 * screenWidth + y1] = color
            else:
                if (0 <= x1 and x1 < screenWidth and 0 <= y1 and y1 < screenHeight):
                    buf[y1 * screenWidth + x1] = color
            while (e >= 0) :
                y1 += sy
                e -= 2 * dx
            x1 += sx
            e += 2 * dy

        if (0 <= x2 and x2 < screenWidth and 0 <= y2 and y2 < screenHeight):
            buf[y2 * screenWidth + x2] = color

    @micropython.viper
    def drawRectangle(self, x:int, y:int, width:int, height:int, color:int):
        self.drawLine(x, y, x+width-1, y, color)
        self.drawLine(x+width-1, y, x+width-1, y+height-1, color)
        self.drawLine(x, y, x, y+height-1, color)
        self.drawLine(x, y+height-1, x+width-1, y+height-1, color)

    # Fill a rectangle with top left corner (x, y) and size (width, height) in a given color.
    @micropython.viper
    def drawFilledRectangle(self, x:int, y:int, width:int, height:int, color:int):
        width-=1
        height-=1
        if(x+width<0 or x>71):
            return
        if(y+height<0 or y>39):
            return
        if(x<0):
            width+=x
            x=0
        if(y<0):
            height+=y
            y=0
        if(x+width>int(self.max_x)):
            width=int(self.max_x)-x
        if(y+height>int(self.max_y)):
            height=int(self.max_y)-y
        buf = ptr16(self.display.buffer)
        yMax=y+height+1
        stride=int(self.width)
        if color==1:
            color=int(C_WHITE)
        while y < yMax:
            px=x
            while px < x+width+1:
                buf[y * stride + px] = color
                px+=1
            y+=1

    # Draw a string with top left corner (x, y) in a given color.
    @micropython.viper
    def drawText(self, stringToPrint:ptr8, x:int, y:int, color:int):
        xPos=int(x)
        charNum=int(0)
        charBitMap=int(0)
        ptr = ptr16(self.display.buffer)
        sprtptr = ptr8(self.textBitmap)
        screenWidth=int(self.width)
        screenHeight=int(self.height)
        textHeight=int(self.textHeight)
        textWidth=int(self.textWidth)
        maxChar=int(self.textCharCount)
        textSpaceWidth=int(self.textSpaceWidth)
        if color==1:
            color=int(C_WHITE)
        while(stringToPrint[charNum]):
            charBitMap=int(stringToPrint[charNum] - 0x20)
            if int(0) <= charBitMap <= maxChar:
                if xPos+textWidth>0 and xPos<screenWidth and y+textHeight>0 and y<screenHeight:
                    self.textBitmapFile.seek(textWidth*charBitMap)
                    self.textBitmapFile.readinto(self.textBitmap)
                    xStart=int(xPos)
                    yStart=int(y)
                    blitHeight=textHeight
                    yFirst=0-yStart
                    if yFirst<0:
                        yFirst=0
                    if yStart+textHeight>screenHeight:
                        blitHeight = screenHeight-yStart
                    yb=int(yFirst)
                    xFirst=0-xStart
                    blitWidth=textWidth
                    if xFirst<0:
                        xFirst=0
                    if xStart+textWidth>screenWidth:
                        blitWidth = screenWidth-xStart
                    while yb < blitHeight:
                        x=xFirst
                        while x < blitWidth:
                            if(sprtptr[(yb >> 3) * textWidth + x] & (1 << (yb & 0x07))):
                                ptr[(yStart+yb) * screenWidth + xStart+x] = color
                            x+=1
                        yb+=1
            charNum+=1
            xPos+=(textWidth+textSpaceWidth)

    @micropython.viper
    def blit(self, sprtptr:ptr8, x:int, y:int, width:int, height:int, key:int, mirrorX:int, mirrorY:int):
        if(x+width<0 or x>int(self.max_x)):
            return
        if(y+height<0 or y>int(self.max_y)):
            return
        xStart=int(x)
        yStart=int(y)
        ptr = ptr16(self.display.buffer)
        screenWidth = int(self.width)
        screenHeight = int(self.height)
        
        yFirst=0-yStart
        blitHeight=height
        if yFirst<0:
            yFirst=0
        if yStart+height>screenHeight:
            blitHeight = screenHeight-yStart
        
        xFirst=0-xStart
        blitWidth=width
        if xFirst<0:
            xFirst=0
        if xStart+width>screenWidth:
            blitWidth = screenWidth-xStart

        bg=int(self.bg)
        fg=int(self.fg)

        y=yFirst
        if(key==0):
            while y < blitHeight:
                x=xFirst
                while x < blitWidth:
                    if(sprtptr[((height-1-y if mirrorY==1 else y) >> 3) * width + (width-1-x if mirrorX==1 else x)] & (1 << ((height-1-y if mirrorY==1 else y) & 0x07))):
                        ptr[(yStart+y) * screenWidth + xStart+x] = fg
                    x+=1
                y+=1
        elif(key==1):
            while y < blitHeight:
                x=xFirst
                while x < blitWidth:
                    if(sprtptr[((height-1-y if mirrorY==1 else y) >> 3) * width + (width-1-x if mirrorX==1 else x)] & (1 << ((height-1-y if mirrorY==1 else y) & 0x07))==0):
                        ptr[(yStart+y) * screenWidth + xStart+x] = bg
                    x+=1
                y+=1
        else:
            while y < blitHeight:
                x=xFirst
                while x < blitWidth:
                    if(sprtptr[((height-1-y if mirrorY==1 else y) >> 3) * width + (width-1-x if mirrorX==1 else x)] & (1 << ((height-1-y if mirrorY==1 else y) & 0x07))):
                        ptr[(yStart+y) * screenWidth + xStart+x] = fg
                    else:
                        ptr[(yStart+y) * screenWidth + xStart+x] = bg
                    x+=1
                y+=1

    # Draw a sprite to the screen
    @micropython.native
    def drawSprite(self, s):
        fg = self.fg
        self.fg = s.color
        self.blit(s.bitmap, int(s.x), int(s.y), s.width, s.height, s.key, s.mirrorX, s.mirrorY)
        self.fg = fg

    @micropython.viper
    def blitWithMask(self, sprtptr:ptr8, x:int, y:int, width:int, height:int, key:int, mirrorX:int, mirrorY:int, maskptr:ptr8):
        if(x+width<0 or x>int(self.max_x)):
            return
        if(y+height<0 or y>int(self.max_y)):
            return
        xStart=int(x)
        yStart=int(y)
        ptr = ptr16(self.display.buffer)
        screenWidth = int(self.width)
        screenHeight = int(self.height)

        yFirst=0-yStart
        blitHeight=height
        if yFirst<0:
            yFirst=0
        if yStart+height>screenHeight:
            blitHeight = screenHeight-yStart
        
        xFirst=0-xStart
        blitWidth=width
        if xFirst<0:
            xFirst=0
        if xStart+width>screenWidth:
            blitWidth = screenWidth-xStart
        y=yFirst
        if(key==key): # ignore key value?
            bg=int(self.bg)
            fg=int(self.fg)
            stride=int(self.width)

            while y < blitHeight:
                x=xFirst
                while x < blitWidth:
                    if(maskptr[((height-1-y if mirrorY==1 else y) >> 3) * width + (width-1-x if mirrorX==1 else x)] & (1 << ((height-1-y if mirrorY==1 else y) & 0x07))):
                        if(sprtptr[((height-1-y if mirrorY==1 else y) >> 3) * width + (width-1-x if mirrorX==1 else x)] & (1 << ((height-1-y if mirrorY==1 else y) & 0x07))):
                            ptr[(yStart+y) * stride + xStart+x] = fg
                        else:
                            ptr[(yStart+y) * stride + xStart+x] = bg
                    x+=1
                y+=1

    @micropython.native
    def drawSpriteWithMask(self, s, m):
        fg = self.fg
        self.fg = s.color
        self.blitWithMask(s.bitmap, int(s.x), int(s.y), s.width, s.height, s.key, s.mirrorX, s.mirrorY, m.bitmap)
        self.fg = fg
    
# Graphics instantiation
if(spi):
    display = GraphicsClass(ST7735(96, 56, spi, dc=Pin(17), res=Pin(20), cs=Pin(16)), 72, 40)
else:
    assert False
    from ssd1306 import SSD1306_I2C
    display = GraphicsClass(SSD1306_I2C(72, 40, i2c, res=Pin(18)), 72, 40)


