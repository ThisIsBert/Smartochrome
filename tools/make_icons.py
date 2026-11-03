"""Original raster icons generated without third-party packages."""
from pathlib import Path
import math, struct, zlib
def chunk(kind,data):
    return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
def make(size):
    pixels=bytearray()
    for y in range(size):
        pixels.append(0)
        for x in range(size):
            xx,yy=(x+.5)*100/size,(y+.5)*100/size;c=(23,42,44)
            for cx,cy,color in [(43,44,(216,114,72)),(59,46,(155,173,126)),(51,60,(162,155,186))]:
                if abs(math.hypot(xx-cx,yy-cy)-19)<3.3:c=color
            if math.hypot(xx-51,yy-50)<5:c=(243,240,231)
            pixels.extend(c)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',size,size,8,2,0,0,0))+chunk(b'IDAT',zlib.compress(pixels))+chunk(b'IEND',b'')
if __name__=='__main__':
    target=Path(__file__).resolve().parents[1]/'icons'
    target.mkdir(exist_ok=True)
    for size in (192,512):(target/f'icon-{size}.png').write_bytes(make(size))
