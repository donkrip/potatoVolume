
# -*- coding: utf-8 -*-

from flask import Flask, render_template, flash, request
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField
from Prototipo_vdam import *

# App config.
DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'


class ReusableForm(Form):
    name = TextField('Name:', validators=[validators.required()])


@app.route("/", methods=['GET', 'POST'])
def hello():
    form = ReusableForm(request.form)
    print(form.errors)
    if request.method == 'POST':
        name = request.form['name']
        print(name)
        if form.validate():
            grafica1, grafica2, grafica3, grafica4, volumen1, volumen2=ejecutar(name)
            return render_template('output.html', result1=str(grafica1)[2:-1],result2=str(grafica2)[2:-1],result3=str(grafica3)[2:-1],result4=str(grafica4)[2:-1],result5=volumen1,result6=volumen2,result7=name)
            flash('Thanks for registration ' + name)
        else:
            flash('Error: Todos los campos son necesarios. ')

    return render_template('index.html', form=form)
def ejecutar(name):
    name = int(name)
    vuelodroneNIR = OrtoFoto("OrtoFoto1", "./datos/mosaicoNIR_3.tif")
    mosaico = vuelodroneNIR.convertirRaster2Array()
    regiones = vuelodroneNIR.identificarObjetos(mosaico)
    papas=[]
    for region in regiones:
        papa = Planta(region[0]-1, region[1], region[2])
        papas.append(papa)
    vuelodroneDEM = Dem("dem", "./datos/dem_3.tif")
    print("El volumen calculado de la papa:" + str(papas[name].verId()) + " es: " + str(papas[name].volumen(vuelodroneDEM)) + " m3")
    print("El volumen calculado de las papas es: " + str(vuelodroneDEM.volumen(papas)) + " m3")
    grafica1=vuelodroneNIR.graficar(papas)
    grafica2=vuelodroneNIR.graficarObjeto(papas[name])
    grafica3=vuelodroneDEM.graficar(papas)
    grafica4=vuelodroneDEM.graficarObjeto(papas[name])
    volumen1=str(papas[name].volumen(vuelodroneDEM))
    volumen2=str(vuelodroneDEM.volumen(papas))
    return grafica1,grafica2,grafica3,grafica4,volumen1,volumen2
if __name__ == "__main__":
    app.run(host='0.0.0.0',port='5000')
