import time

NOP = 0x00
SWRESET = 0x01
RDDID = 0x04
RDDST = 0x09
SLPIN  = 0x10
SLPOUT  = 0x11
PTLON  = 0x12
NORON  = 0x13
INVOFF = 0x20
INVON = 0x21
DISPOFF = 0x28
DISPON = 0x29
CASET = 0x2A
RASET = 0x2B
RAMWR = 0x2C
RAMRD = 0x2E
VSCRDEF = 0x33
VSCSAD = 0x37
COLMOD = 0x3A
MADCTL = 0x36
FRMCTR1 = 0xB1
FRMCTR2 = 0xB2
FRMCTR3 = 0xB3
INVCTR = 0xB4
DISSET5 = 0xB6
PWCTR1 = 0xC0
PWCTR2 = 0xC1
PWCTR3 = 0xC2
PWCTR4 = 0xC3
PWCTR5 = 0xC4
VMCTR1 = 0xC5
RDID1 = 0xDA
RDID2 = 0xDB
RDID3 = 0xDC
RDID4 = 0xDD
GMCTRP1 = 0xE0
GMCTRN1 = 0xE1
PWCTR6 = 0xFC
RAMW = 128
RAMH = 160

class ST7735():
    def __init__(self, width, height, spi, dc, res, cs):
        self.spi = spi
        self.spi.init(baudrate=48000000, polarity=0, phase=0)

        dc.init(dc.OUT, value=0)
        res.init(res.OUT, value=1)
        cs.init(cs.OUT, value=1)

        self.dc = dc
        self.res = res
        self.cs = cs

        self.displaywidth = width
        self.displayheight = height
        
        self.bufferwidth = width
        self.bufferheight = height
        self.buffer = bytearray(self.bufferwidth * self.bufferheight * 2)
        
    def set_window(self, x, y, w, h):
        self.write_cmd(CASET)
        self.write_data(bytearray([0, x, 0, x + w - 1]))
        self.write_cmd(RASET)
        self.write_data(bytearray([0, y, 0, y + h - 1]))

    def set_resolution(self, width, height):
        self.init_display()

        if width > self.displaywidth or width < 1:
            width = self.displaywidth
        if height > self.displayheight or height < 1:
            height = self.displayheight
        
        self.bufferwidth = width
        self.bufferheight = height
        
        buffersize = self.bufferwidth * self.bufferheight * 2
        self.buffer = bytearray(buffersize)

        self.set_window(0, 0, RAMW, RAMH)

        self.write_cmd(RAMWR)
        count = RAMW * RAMH * 2
        chunks = count // buffersize
        remainder = count % buffersize
        for _ in range(chunks):
            self.write_data(self.buffer)
        if remainder:
            self.write_data(self.buffer[:remainder])
        
        displayoffsetx = (RAMW - self.displaywidth) // 2
        displayoffsety = (RAMH - self.displayheight)
        bufferoffsetx = (self.displaywidth - self.bufferwidth) // 2
        bufferoffsety = (self.displayheight - self.bufferheight) // 2
        
        self.set_window(displayoffsetx + bufferoffsetx, displayoffsety + bufferoffsety, self.bufferwidth, self.bufferheight)

    def init_display(self):
        self.reset()

        self.write_cmd(SWRESET)
        time.sleep_us(150)
        self.write_cmd(SLPOUT)
        time.sleep_us(500)

        frmctr = bytearray([0x01, 0x2C, 0x2D])
        self.write_cmd(FRMCTR1)
        self.write_data(frmctr)

        self.write_cmd(FRMCTR2)
        self.write_data(frmctr)

        self.write_cmd(FRMCTR3)
        self.write_data(bytearray([0x01, 0x2c, 0x2d, 0x01, 0x2c, 0x2d]))
        time.sleep_us(10)

        self.write_cmd(INVCTR)
        self.write_data(bytearray([0x07]))

        self.write_cmd(PWCTR1)
        self.write_data(bytearray([0xA2, 0x02, 0x84]))

        self.write_cmd(PWCTR2)
        self.write_data(bytearray([0xC5]))

        self.write_cmd(PWCTR3)
        self.write_data(bytearray([0x0A, 0x00]))

        self.write_cmd(PWCTR4)
        self.write_data(bytearray([0x8A, 0x2A]))

        self.write_cmd(PWCTR5)
        self.write_data(bytearray([0x8A, 0xEE]))

        self.write_cmd(VMCTR1)
        self.write_data(bytearray([0x0E]))

        self.write_cmd(INVOFF)

        self.write_cmd(MADCTL)
        self.write_data(bytearray([0xC8]))

        self.write_cmd(COLMOD)
        self.write_data(bytearray([0x05]))

        self.set_window((RAMW - self.displaywidth) // 2, RAMH - self.displayheight, self.displaywidth, self.displayheight)

        self.write_cmd(GMCTRP1)
        self.write_data(bytearray([0x0f, 0x1a, 0x0f, 0x18, 0x2f, 0x28, 0x20, 0x22, 0x1f, 0x1b, 0x23, 0x37, 0x00, 0x07, 0x02, 0x10]))

        self.write_cmd(GMCTRN1)
        self.write_data(bytearray([0x0f, 0x1b, 0x0f, 0x17, 0x33, 0x2c, 0x29, 0x2e, 0x30, 0x30, 0x39, 0x3f, 0x00, 0x07, 0x03, 0x10]))
        time.sleep_us(10)

        self.write_cmd(DISPON)
        time.sleep_us(100)

        self.write_cmd(NORON)
        time.sleep_us(10)


    def poweroff(self):
        self.write_cmd(DISPOFF)

    def poweron(self):
        self.write_cmd(DISPON)

    def contrast(self, contrast):
        pass

    def invert(self, invert):
        if invert:
            self.write_cmd(INVON)
        else:
            self.write_cmd(INVOFF)

    @micropython.native
    def show(self):
        self.spi.init(baudrate=48000000, polarity=0, phase=0)

        self.write_cmd(RAMWR)
        self.write_data(self.buffer)

    def reset(self):
        self.dc(0)
        self.res(1)
        time.sleep_us(500)
        self.res(0)
        time.sleep_us(500)
        self.res(1)
        time.sleep_us(500)

    @micropython.native
    def write_cmd(self, cmd):
        self.cs(1)
        self.dc(0)
        self.cs(0)
        self.spi.write(bytearray([cmd]))
        self.cs(1)

    @micropython.native
    def write_data(self, buf):
        self.cs(1)
        self.dc(1)
        self.cs(0)
        self.spi.write(buf)
        self.cs(1)
        