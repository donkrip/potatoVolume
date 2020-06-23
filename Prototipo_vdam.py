# -*- coding: utf-8 -*-
"""
Created on Tue Jul 10 10:13:51 2018

@author: Victor A
"""
from PIL import Image
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
#import matplotlib.pyplot as plt
#import matplotlib.pyplot as plt, mpld3
import matplotlib.patches as mpatches
from osgeo import gdal
import base64
from skimage.segmentation import clear_border
from skimage.filters import threshold_otsu
from skimage.morphology import closing, diamond, rectangle
from skimage.measure import label, regionprops
from io import BytesIO

class Raster(object):
    '''Clase Raster'''
    numeroRaster= 0
    
    def __init__(self,nombre, ruta):
         '''Contructor de objetos Raster.'''
         self.__nombre = nombre
         self.__ruta = ruta
         self.__informacion = self.leer()
         Raster.numeroRaster = Raster.numeroRaster + 1
         self.__codigo = Raster.numeroRaster
         print("Se ha creado el objeto Raster:", self)

    def convertirRaster2Array(self):
       '''Convierte el objeto Raster en un arreglo con los valores digitales del objeto'''
       im=Image.open(self.verRuta())
       im=np.array(im, dtype=np.float64)
       return im

    def leer(self):
        '''Obtiene la informacion espacial del Objeto Raster, como el numero de columnas, filas, las coordenadas de origen y el tamaño de pixel'''
        dataset = gdal.Open(self.verRuta())
        columnas = dataset.RasterXSize
        filas = dataset.RasterYSize
        transform = dataset.GetGeoTransform()
        xOrigen = transform[0]
        yOrigen = transform[3]
        pixelWidth = transform[1]
        pixelHeight = -transform[5]
        return (columnas,filas,xOrigen,yOrigen,pixelWidth,pixelHeight)
    
    def cortar(self,minr,minc,maxr,maxc):
        '''Corta el objeto raster con los parametros en pixeles minr,minc,maxr,maxc'''
        im = Image.open(self.verRuta())
        im = im.crop((minr,minc,maxr,maxc))
        im = np.array(im)
        return im
    
    def graficarObjeto(self,planta):
        '''Grafica el objeto Planta en el objeto raster'''
        fig, ax = plt.subplots(ncols=1, figsize=(10, 10))
        minr,minc,maxr,maxc=planta.cuadroDeliminitador(self)
        rastercut= self.cortar(minr,minc,maxr,maxc)
        ax.imshow(rastercut)
        figfile = BytesIO()
        plt.savefig(figfile, format='png')
        figfile.seek(0)
        figdata_png = base64.b64encode(figfile.getvalue())
        return figdata_png
        #plt.tight_layout()
        #plt.show()
        
    def graficar(self,plantas):
        '''Grafica todos los objeto Planta en el objeto raster'''
        fig, ax = plt.subplots(ncols=1, figsize=(10, 10))
        for planta in plantas:
            minc,minr,maxc,maxr=planta.cuadroDeliminitador(self)
            y0, x0 = planta.centroideRaster(self)
            ax.text(x0-2, y0+2, planta.verId(), fontsize=10)
            rect = mpatches.Rectangle((minc, minr), maxc+1 - minc, maxr+1 - minr,fill=False, edgecolor='red', linewidth=1)
            ax.add_patch(rect)
        ax.imshow(self.convertirRaster2Array())
        figfile = BytesIO()
        plt.savefig(figfile, format='png')
        figfile.seek(0)
        figdata_png = base64.b64encode(figfile.getvalue())
        return figdata_png
        #plt.tight_layout()
        #plt.show()
  
    def verNumeroRaster():
        '''Devuelve el numero de objetos Raster creados'''
        return(Raster.numeroRaster)
    
    def verNombre(self):
        '''Devuelve el atrubuto Nombre del objeto Raster'''    
        return (self.__nombre)
    
    def verRuta(self):
        '''Devuelve el atrubuto Ruta del objeto Raster''' 
        return (self.__ruta)
    
    def verInformacion(self):
        '''Devuelve el atrubuto Informacion del objeto Raster''' 
        return (self._informacion)
    
    def ponNombre(self, nombre):
        '''Cambia el atributo Nombre del objeto Raster'''    
        self.__nombre = nombre
        return (self)
    
    def ponRuta(self, ruta):
        '''Cambia el atributo Ruta del objeto Raster''' 
        self.__ruta = ruta
        return (self)
    
    def __str__(self):
        '''Devuelve una cadena con la descripción de un objeto raster'''
        return("[Objeto Raster -" + str(self.__codigo)+"]")


class OrtoFoto(Raster):
    '''Define objetos de tipo OrtoFoto que heredan de Raster'''
    def __init__(self, nombre, ruta):
        '''Contructor de objetos OrtoFoto.'''
        Raster.__init__(self, nombre, ruta)
           
    def identificarObjetos(self, arreglo):
        '''Rutina para identificar objetos a partir de un arreglo en un objeto OrtoFoto y devuelve un conjunto de regiones compuestas por pixeles'''
        thresh = threshold_otsu(arreglo)
        bw = closing(arreglo >= thresh, diamond(1))
        bw = clear_border(bw)
        bw = closing(bw,rectangle(2,2))
        label_image = label(bw)
        regiones = []
        rasterinfo = self.leer()
        for region in regionprops(label_image):
            centroide = Pixel(int(region.centroid[0]),int(region.centroid[1]),rasterinfo, arreglo)
            pixeles =  []
            for coordenada in region.coords:
                pixel = Pixel(int(coordenada[0]),int(coordenada[1]),rasterinfo, arreglo) 
                pixeles.append(pixel)
            pixelarray = np.asarray(pixeles)
            nombre = region.label
            index = (nombre,pixelarray,centroide)
            regiones.append(index)
        return regiones    

    def area(self, plantas):
        '''Devuelve la suma del area de todos los objetos planta presentes en el objeto OrtoFoto'''
        area = 0
        for planta in plantas:
            area = area + planta.area(self)
        return (area)
    
    def __str__(self):
        '''Visualiza un objeto OrtoFoto con nombre y ruta del archivo'''
        return ("[Nombre: "+ self.verNombre() + " - Ruta: "+str(self.verRuta())+"]")


class Dem(Raster):
    '''Define objetos de tipo DEM que heredan de Raster'''
    def __init__(self, nombre, ruta):
        '''Contructor de objetos OrtoFoto.'''
        Raster.__init__(self, nombre, ruta)
        
    def volumen(self, plantas):
        '''Devuelve la suma del volumen de todos los objetos planta presentes en el objeto Dem'''
        volumen = 0
        for planta in plantas:
            volumen = volumen + planta.volumen(self)
        return (volumen)
            
    def __str__(self):
        '''Visualiza un objeto Dem con nombre y ruta del archivo'''
        return ("[Nombre: "+ self.verNombre() + " - Ruta: "+str(self.verRuta())+"]")
    
    
class Planta():
    '''Define Objetos de tipo Planta'''
    def __init__(self, id, coordenadas, centroide):
        '''Constructor de Objetos Planta.'''
        self.__id = id
        self.__coordenadas = []
        for coordenada in coordenadas:
            xy = [coordenada.verGeoX() , coordenada.verGeoY()]
            self.__coordenadas.append(xy)
        self.__coordenadas = np.asarray(self.__coordenadas)
        self.__centroide = (centroide.verGeoX(),centroide.verGeoY())
        #print("Se ha creado el objeto Planta:", self)
        
    def verId(self):
        '''Devuelve el atributo Id del objeto Planta''' 
        return (self.__id)
    
    def ponId(self, identificador):
        '''Cambia el Id del objeto Planta'''
        self.__id= identificador
        return (self)
    
    def verCoordenadas(self):
        '''Devuelve el atributo Coordenadas del objeto Planta'''
        return (self.__coordenadas)
    
    def verCentroide(self):
        '''Devuelve el atributo Centroide del objeto Planta'''
        return (self.__centroide)
    
    def cuadroDeliminitador(self,raster):
        '''Determina un cuadrado al rededor del objeto en el formato: minimo_de_filas, minimo_de_columnas, maximo_de_filas, maximo_de_columnas'''
        rasterInformacion=raster.leer()
        rasterArray=raster.convertirRaster2Array()
        minimo=Pixel(min(self.verCoordenadas()[:,0]),min(self.verCoordenadas()[:,1]),rasterInformacion,rasterArray)
        maximo=Pixel(max(self.verCoordenadas()[:,0]),max(self.verCoordenadas()[:,1]),rasterInformacion,rasterArray)
        minc=minimo.verX()-1
        minr=maximo.verY()-1
        maxc=maximo.verX()+1
        maxr=minimo.verY()+1
        return (minr,minc,maxr,maxc)
    
    def centroideRaster(self,raster):
        '''Determina las coordenadas de un arreglo de un Objeto Raster del centroide de la Planta''' 
        rasterInformacion=raster.leer()
        rasterArray=raster.convertirRaster2Array()
        centroPixel = Pixel(self.verCentroide()[0],self.verCentroide()[1],rasterInformacion,rasterArray)
        return (centroPixel.verX(),centroPixel.verY())
        
    def volumen(self,dem):
        '''Calcula el volumen del objeto Planta a partir de la información de DEM'''
        volumen = 0
        altura = 0
        lista = []
        deminfo = dem.leer()
        demarray = dem.convertirRaster2Array()
        minr,minc,maxr,maxc=self.cuadroDeliminitador(dem)
        rastercut= dem.cortar(minr,minc,maxr,maxc)
        base = rastercut.min()
        for coordenada in self.__coordenadas:
            pixel = Pixel(coordenada[0],coordenada[1],deminfo,demarray)
            coor= (int(pixel.verX()),int(pixel.verY()))
            if coor not in lista:
                try: altura= altura + (demarray[int(pixel.verX()),int(pixel.verY())]-base)
                except: altura = altura + 0
                lista.append(coor)
        pixelHeight=dem.leer()[5]
        pixelWidth=dem.leer()[4]
        volumen = altura * pixelHeight * pixelWidth
        return volumen
    
    def area(self,raster):
        '''Determina el area del objeto'''
        area=0
        lista = []
        rasterinfo = raster.leer()
        rasterarray = raster.convertirRaster2Array()
        for coordenada in self.verCoordenadas():
            pixel = Pixel(coordenada[0],coordenada[1],rasterinfo,rasterarray)
            coor= (int(pixel.verX()),int(pixel.verY()))
            if coor not in lista:
                area = area + 1
                lista.append(coor)
        pixelHeight=raster.leer()[5]
        pixelWidth=raster.leer()[4]
        area = area * pixelHeight * pixelWidth
        return (area)
        
    def __str__(self):
        '''Visualiza un objeto Planta con id y centroide'''
        return ("[ID : "+ str(self.__id) + " - Centroide (GeoX,GeoY): "+str(self.__centroide)+"]")
    

    
class Pixel():
    '''Define Objetos de tipo Pixel'''
    def __init__(self, x, y, rasterInfo, rasterArray):
        '''Constructor de los objetos Pixel'''
        if isinstance(x, int):
            self.__x = x
            self.__y = y
            self.__data = rasterArray[int(self.__x),int(self.__y)]
            self.__rasterInfo=rasterInfo
            self.__geox=self.convertir_pixel_geo()[0]
            self.__geoy=self.convertir_pixel_geo()[1]
        else:
            self.__geox = x
            self.__geoy = y
            self.__rasterInfo=rasterInfo
            self.__x=self.convertir_geo_pixel()[0]
            self.__y=self.convertir_geo_pixel()[1]
            try: 
                self.__data = rasterArray[int(self.__x),int(self.__y)]
            except:
                self.__data = 0

    def convertir_geo_pixel(self):
        '''Convierte de coordenadas geograficas a coordenadas de un arreglo x,y '''
        columnas,filas,xOrigen,yOrigen,pixelWidth,pixelHeight = self.__rasterInfo
        pixelX = int(round((self.verGeoX() - xOrigen) / pixelWidth))
        pixelY = int(round((yOrigen - self.verGeoY() ) / pixelHeight))
        return(pixelX,pixelY)
        
    def convertir_pixel_geo(self):
        '''Convierte de coordenadas de un arreglo x,y a coordenadas geograficas'''
        columnas,filas,xOrigen,yOrigen,pixelWidth,pixelHeight = self.__rasterInfo
        puntoX = ((self.verX())*pixelWidth) + xOrigen
        puntoY = yOrigen-((self.verY())*pixelHeight)
        return(puntoX,puntoY)
    
    def verX(self):
        '''Devuelve el atributo X del objeto Pixel''' 
        return (self.__x)
    
    def verY(self):
        '''Devuelve el atributo Y del objeto Pixel''' 
        return (self.__y)
    
    def verGeoX(self):
        '''Devuelve el atributo GeoX del objeto Pixel''' 
        return (self.__geox)
    
    def verGeoY(self):
        '''Devuelve el atributo GeoY del objeto Pixel''' 
        return (self.__geoy)
    
    def verData(self):
        '''Devuelve el atributo Data del objeto Pixel''' 
        return (self.__data)
    
    def __str__(self):
        '''Visualiza un objeto Pixel con coordenadas X,Y y con el valor data'''
        return ("[Coordenadas (x,y) : "+ str(self.__geox)+"," + str(self.__geoy)+" y valor: "+str(self.__data)+"]")


def main():
    help(Raster)
    help(OrtoFoto)
    help(Dem)
    help(Planta)
    help(Pixel)
    vuelodroneNIR = OrtoFoto("OrtoFoto1", "./datos/mosaicoNIR_3.tif")
    mosaico = vuelodroneNIR.convertirRaster2Array()
    regiones = vuelodroneNIR.identificarObjetos(mosaico)
    papas=[]
    for region in regiones:
        papa = Planta(region[0]-1, region[1], region[2]) 
        papas.append(papa)
    #vuelodroneNIR.graficar(papas)
    #vuelodroneNIR.graficarObjeto(papas[32])
    vuelodroneDEM= Dem("dem", "./datos/dem_3.tif")
    #vuelodroneDEM.graficar(papas)
    #vuelodroneDEM.graficarObjeto(papas[32])
    print("El volumen calculado de la papa:"+str(papas[32].verId()) + " es: " + str(papas[32].volumen(vuelodroneDEM))+ " m3")
    print("El volumen calculado de la papa:"+str(papas[110].verId()) + " es: " + str(papas[110].volumen(vuelodroneDEM))+ " m3")
    print("El volumen calculado de la papa:"+str(papas[139].verId()) + " es: " + str(papas[139].volumen(vuelodroneDEM))+ " m3")
    print("El volumen calculado de la papa:"+str(papas[180].verId()) + " es: " + str(papas[180].volumen(vuelodroneDEM))+ " m3")
    print("El volumen calculado de las papas es: "+ str(vuelodroneDEM.volumen(papas))+ " m3")
    
    
if __name__ == "__main__":
    main()
