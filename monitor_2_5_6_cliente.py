#---------Imports

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation

import random
from scipy import signal
import time
#from datetime import datetime
import serial
import threading
import serial.tools.list_ports

from tkinter import Frame,Label,Entry,Button
from tkinter.messagebox import showerror

import filtro
import hrcalc
from scipy.signal import find_peaks
from scipy.signal import argrelextrema

import socket
import pickle

#from playsound import playsound
from gpiozero import Buzzer
import time
from tkinter import messagebox as MessageBox
import sys

#---------End of imports
####2_2 voy a oprobar a recibir dato de 1 en 1
####2_3 dos seriales
####2_3_2 las dimensiones para el pulso y ecg seran diferentes porque el ecg enviadatos mas seguidos encomparacion al otro
####2_3_3 boton start/stop
####2_4_0   grafico para respiracion y presion muestra
####2_4_1   añado otro puerto com para presion
####2_5_0_emisor envia datos a firebase/ receptor recibe datos de firebase
####2_5_2_cliente es el cliente del servidor, aqui le pongo para ingresar manual la ip
####2_5_3_cliente le pongo la funcion de poner una alarma cunado un parametro salga de lo normal
####2_5_4_cliente de momento solo para emparejar con el servidor
####2_5_4_cliente le oloco un tiempo minimo que debe haber entre alarmas para que no suene todo el tiempo

FONDO = 'black'
TEXTCOL = "white"
ports = serial.tools.list_ports.comports(include_links=False)
puertos = []
buzzer = Buzzer(17)
fontSize = 8 # tamano letra cuadros titulos
fontSize2 = 50 #tamano letra contenido valor del cuadro

class Window(Frame):

    def __init__(self, master = None, puertos = None, baudios = 9600,
                 #dimension = 800, dim_array = 10,dpi = 100,     ##config para ecg
                 dimension = 750*2, dim_array = 15,dpi = 70,
                 dim_red_ir = 100, 
                 dimension2 = 50*2, dim_array2 = 1,dpi2 = 70,     ##config para pulso
                 dim_array3 = 10,                               ##config temp
                 dimension4 = 50*2, dim_array4 = 1,dpi4 = 70,     ##config para resp
                 ip = "", port = 1234,
                 FONDO = None, TEXTCOL = None):
        Frame.__init__(self, master)
        self.master = master
        self.TEXTCOL = TEXTCOL
        self.FONDO = FONDO
        self.ports = puertos
        self.define = 0
        self.baudios = baudios
        self.dpi = dpi

        self.define2 = 0

        self.acho_wg = 7  #ancho de los widgets

        self.eje_x = dimension +2
        self.dim_array = dim_array
        self.eje_x2 = dimension2 +2
        self.dim_array2 = dim_array2
        self.eje_x4 = dimension4 +2
        self.dim_array4 = dim_array4
        self.i = 0  #para array ecg
        self.i2 = 0 #para array pulso
        self.i4 = 0 #para array resp
        
        self.i_red_ir = 0 #para array que calcula spo y heart rate
        self.red = np.zeros(dim_red_ir)
        self.ir = np.zeros(dim_red_ir)
        self.dim_red_ir = dim_red_ir

        self.temp = np.zeros(dim_array3)  #un array de 10 zeros para temp
        self.i3 = 0 #para array temp
        self.dim_array3 = dim_array3
        
        self.y = np.zeros(self.eje_x)   #datos ECG
        #self.y[:] = np.nan
        self.y2 = np.zeros(self.eje_x2)  #datos SPO PULSO
        #self.y2[:] = np.nan
        self.y4 = np.zeros(self.eje_x4)  #datos RESP
        #self.y4[:] = np.nan
        self.temp_val = tk.StringVar()              #variable temp
        self.temp_val.set('-')
        self.pulso_val = tk.StringVar()             #variable pulso
        self.pulso_val.set('-')
        self.hr_val = tk.StringVar()                #valiable del hear ratio
        self.hr_val.set('-')
        self.spo_val = tk.StringVar()               #variable valor saturacion de ocigeno
        self.spo_val.set('-')
        self.resp_val = tk.StringVar()           #variable valor frecuencia respiratoria
        self.resp_val.set('-')
        self.presion_val = tk.StringVar()           #variable valor presion sis/dias
        self.presion_val.set('-/-')
        
        self.h = 1          #tamano del plot
        self.w = 6          #tamano del plot
        print(self.h,self.w)

        self.ip = ip
        self.port = port

        self.hrMin = tk.StringVar()
        self.hrMin.set("50")
        self.hrMax = tk.StringVar()
        self.hrMax.set("150")
        self.pulsoMin = tk.StringVar()
        self.pulsoMin.set("50")
        self.pulsoMax = tk.StringVar()
        self.pulsoMax.set("150")
        self.spoMin = tk.StringVar()
        self.spoMin.set("95")
        self.spoMax = tk.StringVar()
        self.spoMax.set("100")
        self.tempMin = tk.StringVar()
        self.tempMin.set("34")
        self.tempMax = tk.StringVar()
        self.tempMax.set("38")
        self.respMin = tk.StringVar()
        self.respMin.set("12")
        self.respMax = tk.StringVar()
        self.respMax.set("10")
        self.presionSisMin = tk.StringVar()
        self.presionSisMin.set("160")
        self.presionSisMax = tk.StringVar()
        self.presionSisMax.set("100")
        self.presionDiaMin = tk.StringVar()
        self.presionDiaMin.set("100")
        self.presionDiaMax = tk.StringVar()
        self.presionDiaMax.set("60")

        self.reproducirArlarma = True
        self.hora  = 0
        
        self.filewinA = tk.Toplevel()
        self.filewinA.destroy()
        
        self.menu_top()
        self.init_window()
        #self.bind("<Configure>",  self.resize)   #####efecto de cambiar de tamaño plot segun tamaño ventana
        self.master.bind('<Escape>', lambda e: self.salida())
        self.master.protocol("WM_DELETE_WINDOW", self.salida)


        self.tiempoanterior = 0
        self.tiempoactual = time.time() #datetime.now()
        self.lapsoMinAlarma = tk.StringVar() #30segundos de tiempo minimo entre alarmas
        self.lapsoMinAlarma.set("30")
    ################################################################
    def salida(self):
        '''
        if (self.define == 1):
            self.ser.close()
            self.ser2.close()
            self.ser3.close()
            self.ser4.close()
            print ('serial close')
        '''
        print('salida')

        self.define=0
        #self.hilo5.join()
        self.master.quit()
        self.master.destroy()
        sys.exit()
    ################################################################
    def resize(self,event):
        #self.i_resize = 1 - self.i_resize
        try:
            pass
            '''
            print(event,event.height, event.width,self.winfo_width(), self.winfo_height())
            w = self.winfo_width()#(event.width-200)
            h = self.winfo_height()#(event.height-50)
            resta = 200
            self.fig.set_size_inches((w-resta)/self.dpi, h/2*self.dpi-0.5)
            self.canvas.get_tk_widget().config(width=w-resta,height=h/2 - 30)
            
            self.fig2.set_size_inches((w-resta)/self.dpi, h/2*self.dpi-0.5)
            self.canvas2.get_tk_widget().config(width=w-resta,height=h/2 - 30)
            '''
        except:
            pass
        
    ################################################################
    def Clear(self):      
        print("clear")
        self.textAmplitude.insert(0, "1.0")
        self.textSpeed.insert(0, "1.0")       

    ################################################################
    def Plot(self):
        self.v = float(self.textSpeed.get())
        self.A = float(self.textAmplitude.get())

    ################################################################
    def animate(self,i):
        self.line.set_ydata(self.y)  # update the data
        return self.line,

    def animate2(self,i):
        self.line2.set_ydata(self.y2)  # update the data
        return self.line2,
    
    def animate4(self,i):
        self.line4.set_ydata(self.y4)  # update the data
        return self.line4,
    ################################################################
    def creation_plot(self):
        self.fig = plt.Figure(figsize=(self.w, self.h), dpi = self.dpi)
        self.ax = self.fig.add_subplot(111)
        self.ax.set_title('ECG', loc='left', color='green')#fontdict=fd,

        self.ax.set_xlim([0, self.eje_x])
        self.ax.set_ylim([100, 600])
        #self.ax.set_axis_off()
        
        
        self.line, = self.ax.plot(self.y,color="green")#self.x, np.sin(self.x))        

        self.ax.set_facecolor(self.FONDO)
        self.fig.patch.set_facecolor(self.FONDO)
        
        self.ax.patch.set_edgecolor('green')  
        self.ax.patch.set_linewidth(2)
        
        ###########
        self.fig2 = plt.Figure(figsize=(self.w, self.h), dpi = self.dpi)
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_title('PULSO', loc='left', color='green')#fontdict=fd,

        self.ax2.set_xlim([0, self.eje_x2])
        self.ax2.set_ylim([3000, 4000])
        #self.ax2.set_axis_off()
        
        self.line2, = self.ax2.plot(self.y2,color="green")#self.x, np.sin(self.x))        

        self.ax2.set_facecolor(self.FONDO)
        self.fig2.patch.set_facecolor(self.FONDO)
        
        self.ax2.patch.set_edgecolor('green')  
        self.ax2.patch.set_linewidth(2)
        
        ###########
        self.fig4 = plt.Figure(figsize=(self.w, self.h), dpi = self.dpi)
        self.ax4 = self.fig4.add_subplot(111)
        self.ax4.set_title('RESP', loc='left', color='green')#fontdict=fd,

        self.ax4.set_xlim([0, self.eje_x4])
        self.ax4.set_ylim([3000, 4000])
        self.ax4.set_axis_off()
        
        self.line4, = self.ax4.plot(self.y4,color="green")#self.x, np.sin(self.x))        

        self.ax4.set_facecolor(self.FONDO)
        self.fig4.patch.set_facecolor(self.FONDO)        
    ################################################################ 
    def go(self):
        print('a')
        self.ani = animation.FuncAnimation(self.fig, self.animate,
                                           interval=50, blit=False)
        self.ani2 = animation.FuncAnimation(self.fig2, self.animate2,
                                           interval=50, blit=False)
        self.ani4 = animation.FuncAnimation(self.fig4, self.animate4,
                                           interval=50, blit=False)
    ################################################################
    def editar_title(self):

        try:
            print(self.filewinIP.winfo_exists())
            self.filewinIP.destroy()
        except:
            pass
        
        self.filewinIP = tk.Toplevel()
        self.filewinIP.resizable (False, False)

        #filewinIP.resizable (False, False)
        AFrame = tk.Frame(self.filewinIP)
        AFrame.pack(padx=10, pady=5,side = tk.LEFT)
        
        IZQframe = tk.Frame(AFrame)
        IZQframe.pack(padx=10, pady=5)

        lbConfIzq= tk.Label(IZQframe, text = "CONFIGURACION HR", font=(None,10,'bold'))
        lbConfIzq.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)
        lbIPIzq= tk.Label(IZQframe, text = "MIN: ")
        lbIPIzq.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        teIPIzq = tk.Entry(IZQframe, textvariable =  self.hrMin, borderwidth=5,width="20")
        teIPIzq.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        lbPortIzq= tk.Label(IZQframe, text = "MAX: ")
        lbPortIzq.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        tePortIzq = tk.Entry(IZQframe, textvariable = self.hrMax, borderwidth=5,width="5")
        tePortIzq.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)

        DERframe = tk.Frame(AFrame)
        DERframe.pack(padx=10, pady=5)

        lbConfDer= tk.Label(DERframe, text = "CONFIGURACION PULSO", font=(None,10,'bold'))
        lbConfDer.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)
        lbIPDer= tk.Label(DERframe, text = "MIN: ")
        lbIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        teIPDer = tk.Entry(DERframe, textvariable = self.pulsoMin, borderwidth=5,width="20")
        teIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        lbPortDer= tk.Label(DERframe, text = "MAX: ")
        lbPortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        tePortDer = tk.Entry(DERframe, textvariable = self.pulsoMax, borderwidth=5,width="5")
        tePortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)


        SPOframe = tk.Frame(AFrame)
        SPOframe.pack(padx=10, pady=5)

        lbConfDer= tk.Label(SPOframe, text = "CONFIGURACION SPO", font=(None,10,'bold'))
        lbConfDer.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)
        lbIPDer= tk.Label(SPOframe, text = "MIN: ")
        lbIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        teIPDer = tk.Entry(SPOframe, textvariable = self.spoMin, borderwidth=5,width="20")
        teIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        lbPortDer= tk.Label(SPOframe, text = "MAX: ")
        lbPortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        tePortDer = tk.Entry(SPOframe, textvariable = self.spoMax, borderwidth=5,width="5")
        tePortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)

        TEMPframe = tk.Frame(AFrame)
        TEMPframe.pack(padx=10, pady=5)
        
        lbConfDer= tk.Label(TEMPframe, text = "CONFIGURACION TEMP", font=(None,10,'bold'))
        lbConfDer.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)
        lbIPDer= tk.Label(TEMPframe, text = "MIN: ")
        lbIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        teIPDer = tk.Entry(TEMPframe, textvariable = self.tempMin, borderwidth=5,width="20")
        teIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        lbPortDer= tk.Label(TEMPframe, text = "MAX: ")
        lbPortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        tePortDer = tk.Entry(TEMPframe, textvariable = self.tempMax, borderwidth=5,width="5")
        tePortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)

        BFrame = tk.Frame(self.filewinIP)
        BFrame.pack(padx=10, pady=5,side = tk.RIGHT)

        RESPframe = tk.Frame(BFrame)
        RESPframe.pack(padx=10, pady=5)

        lbConfDer= tk.Label(RESPframe, text = "CONFIGURACION RESP", font=(None,10,'bold'))
        lbConfDer.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)
        lbIPDer= tk.Label(RESPframe, text = "MIN: ")
        lbIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        teIPDer = tk.Entry(RESPframe, textvariable = self.respMin, borderwidth=5,width="20")
        teIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        lbPortDer= tk.Label(RESPframe, text = "MAX: ")
        lbPortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        tePortDer = tk.Entry(RESPframe, textvariable = self.respMax, borderwidth=5,width="5")
        tePortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        
        SISframe = tk.Frame(BFrame)
        SISframe.pack(padx=10, pady=5)

        lbConfDer= tk.Label(SISframe, text = "CONFIGURACION PRESION SISTOLICA", font=(None,10,'bold'))
        lbConfDer.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)
        lbIPDer= tk.Label(SISframe, text = "MIN: ")
        lbIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        teIPDer = tk.Entry(SISframe, textvariable = self.presionSisMin, borderwidth=5,width="20")
        teIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        lbPortDer= tk.Label(SISframe, text = "MAX: ")
        lbPortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        tePortDer = tk.Entry(SISframe, textvariable = self.presionSisMax, borderwidth=5,width="5")
        tePortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)

        DIAframe = tk.Frame(BFrame)
        DIAframe.pack(padx=10, pady=5)

        lbConfDer= tk.Label(DIAframe, text = "CONFIGURACION PRESION DIASTOLICA", font=(None,10,'bold'))
        lbConfDer.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)
        lbIPDer= tk.Label(DIAframe, text = "MIN: ")
        lbIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        teIPDer = tk.Entry(DIAframe, textvariable = self.presionDiaMin, borderwidth=5,width="20")
        teIPDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        lbPortDer= tk.Label(DIAframe, text = "MAX: ")
        lbPortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        tePortDer = tk.Entry(DIAframe, textvariable = self.presionDiaMax, borderwidth=5,width="5")
        tePortDer.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        
        ALARframe = tk.Frame(BFrame)
        ALARframe.pack(padx=10, pady=5)

        lbConfAlar= tk.Label(ALARframe, text = "CONFIGURACION TIEMPO ENTRE ALARMAS", font=(None,10,'bold'))
        lbConfAlar.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)
        lbIPConfAlar= tk.Label(ALARframe, text = "SEG: ")
        lbIPConfAlar.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)
        teConfAlar = tk.Entry(ALARframe, textvariable = self.lapsoMinAlarma, borderwidth=5,width="20")
        teConfAlar.pack(expand=True, fill=tk.BOTH,side = tk.LEFT)

##        buttonCon = tk.Button(filewinIP,text="GUARDAR CAMBIOS",command = lambda:config_general())
##        buttonCon.pack(expand=True, pady=10,side = tk.LEFT)

    ################################################################        
    def menu_top(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)

        filemenu.add_command(label="CONFIGURAR ALARMA", command=self.editar_title)
        filemenu.add_separator()
        filemenu.add_command(label="Exit", command=self.salida)
        menubar.add_cascade(label="Menú", menu=filemenu)
        
        self.master.config(menu=menubar)
    ################################################################
    def init_window(self):

        self.master.title("'A - MONITOR MULTIVARIABLE r- T'")
        self.pack(fill='both', expand=1)     


        # Frame horizontal 1 grafico y parametros ECG/PULSO
        fm1 = tk.Frame(self,highlightbackground="red",
                       highlightthickness=1)
        fm1.config(bg= FONDO)
        fm1.grid(row=0, column=0,
                 sticky="nsew",
                 #rowspan = 3, #8
                 #columnspan = 3,
                 #padx=5, pady=5
                 )
        self.grid_columnconfigure(0, weight=1) 
        self.grid_columnconfigure(1, weight=1) 
        self.grid_rowconfigure(0, weight=1) 
        self.grid_rowconfigure(1, weight=1)

        # Frame para parametros ECG
        fm2 = tk.Frame(fm1,
                        #highlightbackground="red",
                       #highlightthickness=1
                       )
        fm2.config(bg= FONDO)
        fm2.grid(row=0, column=0,
                 rowspan = 3,
                 columnspan = 1,
                 padx=1, pady=1)
        # Frame para parametros PULSO
        '''
        fm2_3 = tk.Frame(fm1,highlightbackground="red",
                       highlightthickness=1)
        fm2_3.config(bg= FONDO)
        fm2_3.grid(row=0, column=1,
                 rowspan = 1,
                 columnspan = 1,
                 padx=1, pady=1)
        '''

        # Frame horizontal 2 grafico y parametros SPO/TEMP
        fm5 = tk.Frame(self,highlightbackground="red",
                       highlightthickness=1)
        fm5.config(bg= FONDO)
        fm5.grid(row=0, column=1,
                sticky="nsew",
                 #rowspan = 3,
                 #columnspan = 3,
                 #padx=5, pady=5
                 )

        # Frame para parametros SPO
        fm3 = tk.Frame(fm5,
                        #highlightbackground="red",
                       #highlightthickness=1
                       )
        fm3.config(bg= FONDO)
        fm3.grid(row=0, column=0,
                 rowspan = 2,
                 columnspan = 1,
                 padx=1, pady=1)
        
        
        # Frame horizontal 4 TEMP
        fm7 = tk.Frame(self,
                        highlightbackground="red",
                       highlightthickness=1
                       )
        fm7.config(bg= FONDO)
        fm7.grid(row=1, column=1,
                sticky="nsew",
                 #rowspan = 3,
                 #columnspan = 3,
                 #padx=5, pady=5
                 )
        # Frame para parametros TEMP
        
        fm5_3 = tk.Frame(fm7,
                        #highlightbackground="red",
                       #highlightthickness=1
                       )
        fm5_3.config(bg= FONDO)
        fm5_3.grid(row=0, column=1,
                 sticky="nsew",
                 #rowspan = 3,
                 #columnspan = 3,
                 padx=10, pady=10)


        # Frame para config 
        fm4 = tk.Frame(self)
        fm4.config(bg= FONDO)
        fm4.grid(row=0, column=6,
                 rowspan = 1,
                 columnspan = 1,
                 padx=5, pady=10)


        # Frame horizontal 3 grafico y parametros RESP/PRESION
        fm6 = tk.Frame(self,highlightbackground="red",
                       highlightthickness=1)
        fm6.config(bg= FONDO)
        fm6.grid(row=1, column=0,
                sticky="nsew",
                 #rowspan = 3,
                 #columnspan = 3,
                 #padx=5, pady=5
                 )

        # Frame para parametros RESP
        '''fm6_1 = tk.Frame(fm6,highlightbackground="red",
                       highlightthickness=1)
        fm6_1.config(bg= FONDO)
        fm6_1.grid(row=0, column=6,
                 rowspan = 1,
                 columnspan = 1,
                 padx=1, pady=1)
        '''
        
        # Frame para parametros PRESION
        fm6_2 = tk.Frame(fm6,
                        #highlightbackground="red",
                       #highlightthickness=1
                       )
        fm6_2.config(bg= FONDO)
        fm6_2.grid(row=0, column=0,
                sticky="nsew",
                 #rowspan = 3,
                 #columnspan = 3,
                 padx=10, pady=10)


        #DATOS PARA FM2 ------------------------------
        #----------------------------------------------

        self.labelHR = Label(fm2,text="HR\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,fontSize,'bold'),
                             fg=self.TEXTCOL)
        self.labelHR.grid(row=0,column=0, rowspan = 2)
        self.labelHRmax = Label(fm2,textvariable=self.hrMax,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelHRmax.grid(row=2,column=0, sticky = tk.W)
        self.labelHRmin = Label(fm2,textvariable=self.hrMin,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelHRmin.grid(row=3,column=0, sticky = tk.W)
        
        self.textHRval = Label(fm2,textvariable=self.hr_val,width=int(self.acho_wg/2),
                               fg=self.TEXTCOL,
                               bg=self.FONDO, font=(None,fontSize2,'bold'))
        self.textHRval.grid(row=0,column=1, rowspan = 4)

        
        #DATOS PARA FM3 ------------------------------
        #----------------------------------------------

        self.labelSPO = Label(fm3,text="SPO\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,fontSize,'bold'),
                              fg=self.TEXTCOL)
        self.labelSPO.grid(row=0,column=0, rowspan = 2)
        self.labelSPOmax = Label(fm3,textvariable=self.spoMax,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelSPOmax.grid(row=2,column=0, sticky = tk.W)
        self.labelSPOmin = Label(fm3,textvariable=self.spoMin,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelSPOmin.grid(row=3,column=0, sticky = tk.W)
        
        self.textSPOval = Label(fm3,textvariable=self.spo_val,width=int(self.acho_wg/2),
                               bg=self.FONDO, font=(None,fontSize2,'bold'),
                                fg=self.TEXTCOL)
        self.textSPOval.grid(row=0,column=1, rowspan = 4)

        #DATOS PARA FM2_3 ------------------------------
        #----------------------------------------------
        '''
        self.labelPULSO = Label(fm2_3,text="PULSO\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,fontSize,'bold'),
                              fg=self.TEXTCOL,
                               anchor="e",justify=tk.LEFT)
        self.labelPULSO.grid(row=0,column=0, rowspan = 1, sticky = tk.W)


        self.labelPULSOmax = Label(fm2_3,textvariable=self.pulsoMax,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelPULSOmax.grid(row=2,column=0, sticky = tk.W)
        self.labelPULSOmin = Label(fm2_3,textvariable=self.pulsoMin,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelPULSOmin.grid(row=3,column=0, sticky = tk.W)
        
        self.textPULSOval = Label(fm2_3,textvariable=self.pulso_val,width=int(self.acho_wg/2),
                               bg=self.FONDO, font=(None,fontSize2,'bold'),
                                fg=self.TEXTCOL)
        self.textPULSOval.grid(row=0,column=1, rowspan = 4)
        
##        self.labelPULSOval = Label(fm2_3,textvariable=self.pulso_val,width=int(self.acho_wg),
##                                font=(None,25,'bold'),bg=self.FONDO,
##                                 fg=self.TEXTCOL,
##                                anchor="e",justify=tk.RIGHT)
##        self.labelPULSOval.grid(row=1,column=0, sticky = tk.W)
        '''
        #DATOS PARA FM5_3 ------------------------------
        #----------------------------------------------

        self.labelTEMP = Label(fm5_3,text="TEMP\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,fontSize,'bold'),
                              fg=self.TEXTCOL,
                                anchor="e",justify=tk.LEFT)
        self.labelTEMP.grid(row=0,column=0, rowspan = 1, sticky = tk.W)


        self.labelTEMPmax = Label(fm5_3,textvariable=self.tempMax,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelTEMPmax.grid(row=2,column=0, sticky = tk.W)
        self.labelTEMPmin = Label(fm5_3,textvariable=self.tempMin,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelTEMPmin.grid(row=3,column=0, sticky = tk.W)
        
        self.textTEMPval = Label(fm5_3,textvariable=self.temp_val,width=int(self.acho_wg/2),
                               bg=self.FONDO, font=(None,fontSize2,'bold'),
                                fg=self.TEXTCOL)
        self.textTEMPval.grid(row=0,column=1, rowspan = 4)
        
##        self.labelTEMPval = Label(fm5_3,textvariable=self.temp_val,width=int(self.acho_wg),
##                                font=(None,25,'bold'),bg=self.FONDO,
##                                 fg=self.TEXTCOL,
##                                anchor="e",justify=tk.RIGHT)
##        self.labelTEMPval.grid(row=1, column=0, sticky = tk.W)

        #DATOS PARA FM6_1 ------------------------------
        #----------------------------------------------
        '''
        self.labelRESP = Label(fm6_1,text="RESP\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,fontSize,'bold'),
                              fg=self.TEXTCOL,
                                anchor="e",justify=tk.LEFT)
        self.labelRESP.grid(row=0,column=0, rowspan = 1, sticky = tk.W)


        self.labelRESPmax = Label(fm6_1,textvariable=self.respMax,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelRESPmax.grid(row=2,column=0, sticky = tk.W)
        self.labelRESPmin = Label(fm6_1,textvariable=self.respMin,width=self.acho_wg,
                                font=(None,fontSize,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelRESPmin.grid(row=3,column=0, sticky = tk.W)
        
        self.textRESPval = Label(fm6_1,textvariable=self.resp_val,width=int(self.acho_wg/2),
                               bg=self.FONDO, font=(None,fontSize2,'bold'),
                                fg=self.TEXTCOL)
        self.textRESPval.grid(row=0,column=1, rowspan = 4)
        
##        self.labelRESPval = Label(fm6_1,textvariable=self.resp_val,width=int(self.acho_wg),
##                                font=(None,25,'bold'),bg=self.FONDO,
##                                 fg=self.TEXTCOL,
##                                anchor="e",justify=tk.RIGHT)
##        self.labelRESPval.grid(row=1, column=0, sticky = tk.W)
        '''
        
        #DATOS PARA FM6_2 ------------------------------
        #----------------------------------------------

        self.labelPRESION = Label(fm6_2,text="PRESION\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,fontSize,'bold'),
                              fg=self.TEXTCOL,
                                anchor="e",justify=tk.LEFT)
        self.labelPRESION.grid(row=0,column=0, rowspan = 1, sticky = tk.W)
        self.labelPRESIONval = Label(fm6_2,textvariable=self.presion_val,width=int(self.acho_wg),
                                font=(None,fontSize2,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelPRESIONval.grid(row=1, column=0, sticky = tk.W)
##        self.textAmplitude.insert(0, "1.0")
##        self.textSpeed.insert(0, "1.0")
##        self.v = float(self.textSpeed.get())
##        self.A = float(self.textAmplitude.get())


##        self.buttonPlot = Button(self,text="Plot",command=self.Plot,width=self.acho_wg)        
##        self.buttonPlot.grid(row=2,column=4)
##
##        self.buttonClear = Button(self,text="Clear",command=self.Clear,width=self.acho_wg)
##        self.buttonClear.grid(row=2,column=5)
##        self.buttonClear.bind(lambda e:self.Clear)

        fd = dict(
            fontsize=15, # [ size in points | relative size, e.g., 'smaller', 'x-large' ]
            fontweight='bold', # [ 'normal' | 'bold' | 'heavy' | 'light' | 'ultrabold' | 'ultralight']
            fontstyle='normal', # [ 'normal' | 'italic' | 'oblique' ]
            color='black', # name ex: 'black' or hex ex: '#30302f'
            verticalalignment='baseline', # [ 'center' | 'top' | 'bottom' | 'baseline' ]
            # horizontalalignment='left' # [ 'center' | 'right' | 'left' ]
        )

        #tk.Label(self,text="SHM Simulation",bg=self.FONDO).grid(column=0, row=3)


        #CRACION DE LOS PLOT ------------------------------
        #----------------------------------------------
        self.creation_plot()
        self.canvas = FigureCanvasTkAgg(self.fig, master=fm1)
        self.canvas.get_tk_widget().grid(column=0,row=3, columnspan = 3,
                                         #rowspan = 2
                                         )

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=fm5)
        self.canvas2.get_tk_widget().grid(column=0,row=6, columnspan = 3,
                                          #rowspan = 2
                                          )

        #self.canvas4 = FigureCanvasTkAgg(self.fig4, master=fm6)
        #self.canvas4.get_tk_widget().grid(column=0,row=0,# columnspan = 6,
         #                                 rowspan = 2)

        self.go()
        '''
        #CONEXION SERIAL ------------------------------
        #----------------------------------------------
        self.lbpuerto = tk.Label(fm4, text = "PUERTO:   ",
                                 width = self.acho_wg,
                                 fg=self.TEXTCOL) # font=(None,12,'bold'),
        self.lbpuerto.config(bg=self.FONDO)
        self.lbpuerto.grid(sticky='W',row=0,column=6) #,padx=20)
        #########
        self.portser = tk.StringVar()
        self.portser.set("SELECCIONA1")
        campport = tk.ttk.Combobox(fm4, textvariable = self.portser,
                                   width= 12)#self.acho_wg)
        campport.grid(row=0,column=7)#,padx=20)
        campport["values"] = self.ports
        #########
        self.portser2 = tk.StringVar()
        self.portser2.set("SELECCIONA2")
        campport2 = tk.ttk.Combobox(fm4, textvariable = self.portser2,
                                   width= 12)#self.acho_wg)
        campport2.grid(row=0,column=8)#,padx=20)
        campport2["values"] = self.ports
        #########
        self.portser3 = tk.StringVar()
        self.portser3.set("SELECCIONA3")
        campport3 = tk.ttk.Combobox(fm4, textvariable = self.portser3,
                                   width= 12)#self.acho_wg)
        campport3.grid(row=0,column=9)#,padx=20)
        campport3["values"] = self.ports
        #########
        self.portser4 = tk.StringVar()
        self.portser4.set("SELECCIONA3")
        campport4 = tk.ttk.Combobox(fm4, textvariable = self.portser4,
                                   width= 12)#self.acho_wg)
        campport4.grid(row=0,column=10)#,padx=20)
        campport4["values"] = self.ports

        '''
        if (self.define == 1):
            estado = "DESCONECTAR"
        else:
            estado = "CONECTAR"
     
        self.b1=tk.Button(fm4,text = estado,
                          width = 12, #self.acho_wg,
                          command=lambda: self.conexion())
        self.b1.grid(row=0,column=11, sticky = tk.W,padx=20)

        '''
        if (self.define2 == 1):
            estado2 = "STOP"
        else:
            estado2 = "START"
     
        self.b2=tk.Button(fm4,text = estado2,
                          width = 12, #self.acho_wg,
                          command=lambda: self.start_com())
        self.b2.grid(row=0,column=12, sticky = tk.W,padx=20)
        '''
 ################################################################ 
    def esperar(self):
        while self.define:
            
            #self.ser.reset_input_buffer()
            valor_bruto = self.ser.readline()
                
            reading = valor_bruto.decode()
                
            #print (reading)
            try:
                if reading == '':
                    print('ni')
                    continue
                #a = reading.split(',')[:2*self.dim_array+4]
                #aa = list(map(int, a))
                #print(aa)
                
                    
                #valores ECG
                letra = reading[0]
                if letra == 'A':
                    ##self.y[self.i:self.i+self.dim_array] = aa[0:self.dim_array]
                    a = reading.split(',')[1:] #valor 0 es 'A' y el 1 es ','
                    aa = list(map(int, a))
                    #self.y[self.i] = int(reading[1:])
                    self.y[self.i:self.i+self.dim_array] = aa
                    self.i += self.dim_array



                                       
                    peaks = find_peaks(np.array(self.y), distance=150)
                    #print((peaks[0]))

                    
                    m = 0
                    d =len(peaks[0])
                    peak_temp = np.zeros(d)
                    peak_temp[:] = np.nan
                    
                    if (d) > 2:
                        #print(d,peaks[0][0])
                        for a in range(0,d-1):
                            h = peaks[0][a+1]-peaks[0][a]
                            #print('5555',h,peaks[0][a+1],peaks[0][a])
                            if h > 5:
                                peak_temp[m] = h
                                m += 1
                            
                    mean_peak= np.nanmedian(peak_temp)
                    #en miliseg
                    solu = 60000/(mean_peak*5)
                    if solu >= 0:
                        self.hr_val.set(int(solu))
                    #print(peak_temp,mean_peak,solu)
                    #print(mean_peak)
                    
    ##
    ##            if (self.i >= self.eje_x-2):
    ##                self.i = 0#-10
    ##            else:
    ##                self.y[self.i + self.dim_array] = None
    ##                self.y[self.i + self.dim_array + 1] = None
    ##
                '''
                #print(self.y,'p')
                #valores SPO
                if letra == 'B':
                #self.y2[self.i2:self.i2+self.dim_array] = aa[self.dim_array:2*self.dim_array]
                    a = reading.split(',')[1:]  #valor 0 es 'B' y el 1 es ','
                    aa = list(map(int, a))
                    #self.y2[self.i2] = int(reading[1:])
                    self.y2[self.i2:self.i2+self.dim_array] = aa
                    self.i2 += self.dim_array
                    self.ax2.set_ylim([min(self.y2), max(self.y2)])
                '''
                if (self.i >= self.eje_x-2):
                    self.i = 0#-10
                else:
                    #los dos ultimos valores seran vacios
                    self.y[self.i + self.dim_array] = np.nan#None#np.nanmean(self.y)#None
                    self.y[self.i + self.dim_array + 1] = np.nan#None#np.nanmean(self.y)#None
                    
                '''
                if (self.i2 >= self.eje_x-2):
                    self.i2 = 0#-10
                else:
                    #los dos ultimos valores seran vacios
                    self.y2[self.i2 + self.dim_array] = None
                    self.y2[self.i2 + self.dim_array + 1] = None
                #print(self.y2,'l')
                
                #temp, spo, pulso, hr = aa[2*self.dim_array:]
                if letra == 'C':
                    temp = int(reading[1:])
                    self.temp_val.set(float(temp))
                if letra == 'D':
                    spo = int(reading[1:])
                    self.spo_val.set(int(spo))
                if letra == 'E':
                    pulso = int(reading[1:])
                    self.pulso_val.set(int(pulso))
                if letra == 'F':
                    hr = int(reading[1:])
                    self.hr_val.set(int(hr))                           
                '''        
                time.sleep(0.001)
            except Exception as e:
                print(e)
                # x = np.zeros(self.dim_array)
                # reading = np.array2string(x, precision=2, separator=',',
                #       suppress_small=True)
                #pass
                showerror(title="ERROR",message="SIN LECTURA a")
                self.ser.close()
                self.define = 0
                estado = "CONECTAR"
                self.b1.configure(text=estado)
           
                
                #break
    ################################################################                    
    def leer_ser(self):

        if (self.ser.isOpen()):
            try:                           
                hilo1 = threading.Thread(target=self.esperar)
                hilo1.start()

            except Exception:
                showerror(title="ERROR",message="error al leer 1")
        else:
            showerror(title="ERROR",message="no conectado 1")

    ################################################################
    def conexion(self):
        try:
            self.define = 1 - self.define
            
            if (self.define == 1):
                estado = "DESCONECTAR"
                '''
                puertocom = self.portser.get()
                print (puertocom,'ecg')
                self.ser = serial.Serial(puertocom, self.baudios, timeout=3)
                self.leer_ser()

                puertocom2 = self.portser2.get()
                print (puertocom2,'IR RED SPO PULSO')
                self.ser2 = serial.Serial(puertocom2, self.baudios, timeout=3)
                self.leer_ser2()

                puertocom3 = self.portser3.get()
                print (puertocom3,'RESP')
                self.ser3 = serial.Serial(puertocom3, self.baudios, timeout=3)
                self.leer_ser3()

                puertocom4 = self.portser4.get()
                print (puertocom4,'PRESION')
                self.ser4 = serial.Serial(puertocom4, self.baudios, timeout=3)
                self.leer_ser4()
                '''

                self.HEADERSIZE = 10
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                if (self.ip == ""):
                    self.ip = socket.gethostname()
                    #self.s.connect((socket.gethostname(), self.port))
                    print('vacio',socket.gethostname(), self.port)
                else:
                    print('ip',self.ip, self.port)
                self.s.connect((self.ip, self.port))
                self.fireConexion()  ##mantengo el nombre fire pero conecta cliente-servidor
                
            else:
                estado = "CONECTAR"
##                self.ser.close()
##                self.ser2.close()                
##                self.ser3.close()
                
            self.b1.configure(text=estado)
            
        except Exception as e:
            print(e)
            self.define = 0
            estado = "CONECTAR"
            self.b1.configure(text=estado)
##            self.ser.close()
##            self.ser2.close()
##            self.ser3.close()
            showerror(title="ERROR",message="NO SE PUDO CONECTAR")
    ################################################################
    #####El boton de stat/stop para que empiezen a enviar datos al mismo tiempo
    def start_com(self):
        try:
            self.define2 = 1 - self.define2
            
            if (self.define2 == 1):
                self.define = 1
                estado2 = "STOP"
                puertocom = self.portser.get()
                print (puertocom)
                self.ser.write(b'\n')

                puertocom2 = self.portser2.get()
                print (puertocom2)
                self.ser2.write(b'\n')

                puertocom3 = self.portser3.get()
                print (puertocom3)
                self.ser3.write(b'\n')
                
            else:
                estado2 = "START"
                self.define = 0
                self.i = 0
                self.i2 = 0
                self.i4 = 0
                self.conexion()
                
            self.b2.configure(text=estado2)
            
        except Exception as e:
            print(e)
            self.define2 = 0
            estado2 = "CONECTAR"
            self.b2.configure(text=estado2)
            self.define = 0
            showerror(title="ERROR",message="VERIFIQUE EL PUERTO")
################################################################ 
    def esperar2(self):
        while self.define:
            
            #self.ser.reset_input_buffer()
            valor_bruto = self.ser2.readline()
                
            reading = valor_bruto.decode()
            #print(reading)
                
            try:
                if reading == '':
                    print('ni')
                    continue
                #a = reading.split(',')[:2*self.dim_array+4]
                #aa = list(map(int, a))
                #print(aa)
                
                    
                #valores ECG
                letra = reading[0]
                if letra == 'B':
                #self.y2[self.i2:self.i2+self.dim_array] = aa[self.dim_array:2*self.
                    
                    #print('ff1')
                    a = reading.split(',')[1:]  #valor 0 es 'B' y el 1 es ','
                    #print('ff2')
                    aa = list(map(int, a))
                    #print('ff3')
                    
                    #self.y2[self.i2] = int(reading[2:])

                    suma = sum(aa)

                    '''
                    spo = 100*aa[1]/suma
                    self.spo_val.set(int(spo))
                    '''

                    if self.i_red_ir == self.dim_red_ir:
                        #print(self.ir,self.red)
                        hr,hrb,spo,spob = hrcalc.calc_hr_and_spo2(self.ir,self.red)
                        self.i_red_ir = 0
                        #print(hr+20,hrb,spo,spob)
                        if spob:
                            self.spo_val.set(int(spo))
                        else:
                            self.spo_val.set('-')
                        if hrb:
                            valor = int(hr)+20
                            self.pulso_val.set(valor)
                            print(valor)
                            print(int(self.pulsoMax.get()))
                            if(valor > int(self.pulsoMax.get())):
                                print('alarrma')
                                self.mensajeAlarma('sobre self.pulsoMaxpulso')
                        else:
                            self.pulso_val.set('-')
                        
                    else:
                        self.ir[self.i_red_ir] = aa[1]
                        self.red[self.i_red_ir]= aa[0]
                        self.i_red_ir += 1

                    
                    self.y2[self.i2:self.i2+self.dim_array2] = suma*-1
                    
                    #self.y2 = filtro.butter_highpass_filter(self.y2, 0.01, 12.4)
                    #print('ff4')
                    #print(self.y2)
                    self.i2 += self.dim_array2
                    self.ax2.set_ylim([min(self.y2)-1, max(self.y2)+1])
                    #print(min(self.y2)-1, max(self.y2)+1)


                    '''
                    peaks = argrelextrema(np.array(self.y2), np.greater)
                    print((peaks[0]))

                    
                    m = 0
                    d =len(peaks[0])
                    peak_temp = np.zeros(d)
                    peak_temp[:] = np.nan
                    
                    if (d) > 2:
                        #print(d,peaks[0][0])
                        for a in range(0,d-1):
                            h = peaks[0][a+1]-peaks[0][a]
                            #print('5555',h,peaks[0][a+1],peaks[0][a])
                            if h > 5:
                                peak_temp[m] = h
                                m += 1
                            
                    mean_peak= np.nanmedian(peak_temp)
                    solu = 60000/(mean_peak*80.4)
                    print(peak_temp,mean_peak,solu)
                    #print(solu)
                    '''

                    
                if (self.i2 >= self.eje_x2-2):#-2
                    self.i2 = 0#-10
                else:
                    pass
                    #los dos ultimos valores seran vacios
                    self.y2[self.i2 + self.dim_array2] = np.nan#None#np.nanmean(self.y2)# None
                    self.y2[self.i2 + self.dim_array2 + 1] = np.nan#None#np.nanmean(self.y2)#None
                #print(self.y2,'l')

                if letra == 'C':
                    
                    
                    temp = int(reading[1:])
                    temp = temp*500/1023
                    if self.i3 == self.dim_array3:
                        prom = np.mean(self.temp)
                        self.temp_val.set(int(prom))
                        self.i3 = 0
                    else:
                        self.temp[self.i3] = temp
                        self.i3 += 1
                    
                #if letra == 'D':
                    #spo = int(reading[1:])
                    #self.spo_val.set(int(spo))
##                if letra == 'E':
##                    pulso = int(reading[1:])
##                    self.pulso_val.set(int(pulso))
##                if letra == 'F':
##                    hr = int(reading[1:])
##                    self.hr_val.set(int(hr))   

                time.sleep(0.001)
            except Exception as e:
                print(e)
                # x = np.zeros(self.dim_array)
                # reading = np.array2string(x, precision=2, separator=',',
                #       suppress_small=True)
                #pass
                showerror(title="ERROR",message="SIN LECTURA b")
                self.ser2.close()
                self.define = 0
                estado = "CONECTAR"
                self.b1.configure(text=estado)
           
                
                #break
    ################################################################                    
    def leer_ser2(self):

        if (self.ser2.isOpen()):
            try:                           
                hilo2 = threading.Thread(target=self.esperar2)
                hilo2.start()

            except Exception:
                showerror(title="ERROR",message="error al leer 2")
        else:
            showerror(title="ERROR",message="no conectado 2")

################################################################ 
    def esperar3(self):
        while self.define:
            
            #self.ser.reset_input_buffer()
            valor_bruto = self.ser3.readline()
                
            reading = valor_bruto.decode()
            #print(reading)
                
            try:
                if reading == '':
                    print('ni3')
                    continue
                #a = reading.split(',')[:2*self.dim_array+4]
                #aa = list(map(int, a))
                #print(aa)
                
                    
                #valores ECG
                letra = reading[0]
                if letra == 'R':
                #self.y2[self.i2:self.i2+self.dim_array] = aa[self.dim_array:2*self.
                    
                    #print('ff1')
                    a = reading.split(',')[1:]  #valor 0 es 'B' y el 1 es ','
                    #print('ff2')
                    aa = list(map(float, a))
                    aa = list(map(int, aa))
                    #print('ff3')
                    #print(aa)
                    #self.y4[self.i4] = int(reading[2:])

                    
                    self.y4[self.i4:self.i4+self.dim_array4] = aa
                    
                    #self.y2 = filtro.butter_highpass_filter(self.y2, 0.01, 12.4)
                    #print('ff4')
                    #print(self.y2)
                    self.i4 += self.dim_array4
                    self.ax4.set_ylim([min(self.y4)-20, max(self.y4)+20])
                    #print(min(self.y2)-1, max(self.y2)+1)


                    peaks = find_peaks(np.array(self.y4), distance=15)
                    #print((peaks[0]))
                    

                    
                    m = 0
                    d =len(peaks[0])
                    peak_temp = np.zeros(d)
                    peak_temp[:] = np.nan
                    
                    if (d) > 2:
                        #print(d,peaks[0][0])
                        for a in range(0,d-1):
                            h = peaks[0][a+1]-peaks[0][a]
                            #print('5555',h,peaks[0][a+1],peaks[0][a])
                            if h > 5:
                                peak_temp[m] = h
                                m += 1
                            
                    mean_peak= np.nanmedian(peak_temp)
                    #en miliseg
                    solu = 60000/(mean_peak*164)#muestreo cada 164 ms
                    if solu >= 0:
                        self.resp_val.set(int(solu))
                    
                if (self.i4 >= self.eje_x4-2):#-2
                    self.i4 = 0#-10
                else:
                    pass
                    #los dos ultimos valores seran vacios
                    self.y4[self.i4 + self.dim_array4] = np.nan#None#np.nanmean(self.y4)# None
                    self.y4[self.i4 + self.dim_array4 + 1] = np.nan#None#np.nanmean(self.y4)# None
                #print(self.y2,'l')
                    
                time.sleep(0.001)
            except Exception as e:
                print(e)
                # x = np.zeros(self.dim_array)
                # reading = np.array2string(x, precision=2, separator=',',
                #       suppress_small=True)
                #pass
                showerror(title="ERROR",message="SIN LECTURA c")
                self.ser3.close()
                self.define = 0
                estado = "CONECTAR"
                self.b1.configure(text=estado)
           
                
                #break
    ################################################################                    
    def leer_ser3(self):

        if (self.ser3.isOpen()):
            try:                           
                hilo3 = threading.Thread(target=self.esperar3)
                hilo3.start()

            except Exception:
                showerror(title="ERROR",message="error al leer 3")
        else:
            showerror(title="ERROR",message="no conectado 3")        
################################################################ 
    def esperar4(self):
        while self.define:
            
            #self.ser.reset_input_buffer()
            valor_bruto = self.ser4.readline()
                
            reading = valor_bruto.decode()
            #print(reading)
                
            try:
                if reading == '':
                    print('ni4')
                    continue
                #a = reading.split(',')[:2*self.dim_array+4]
                #aa = list(map(int, a))
                #print(aa)
                
                    
                #valores ECG
                letra = reading[0]
                if letra == 'P':
                #self.y2[self.i2:self.i2+self.dim_array] = aa[self.dim_array:2*self.
                    
                    #print('ff1')
                    a = reading.split(',')[1:]  #valor 0 es 'B' y el 1 es ','
                    #print('ff2')
                    aa = list(map(float, a))
                    
                    #print('ff3')
                    #print(aa)


                    dato = str(int(aa[0]*1.15))+'/' + str(int(aa[0]*0.8))

                    self.presion_val.set(dato)


                    
                time.sleep(0.010)
            except Exception as e:
                print(e)
                # x = np.zeros(self.dim_array)
                # reading = np.array2string(x, precision=2, separator=',',
                #       suppress_small=True)
                #pass
                showerror(title="ERROR",message="SIN LECTURA d")
                self.ser4.close()
                self.define = 0
                estado = "CONECTAR"
                self.b1.configure(text=estado)
           
                
                #break
    ################################################################                    
    def leer_ser4(self):

        if (self.ser4.isOpen()):
            try:                           
                hilo4 = threading.Thread(target=self.esperar4)
                hilo4.start()

            except Exception:
                showerror(title="ERROR",message="error al leer 4")
        else:
            showerror(title="ERROR",message="no conectado 4")        

################################################################ 
    def esperar5(self):


        full_msg = b''
        new_msg = True
        
        while self.define:
            #print('f',self.define)
            try:


                msg = self.s.recv(16)
                if new_msg:
                    #print("new msg len:",msg[:HEADERSIZE])
                    msglen = int(msg[:self.HEADERSIZE])
                    new_msg = False

                #print(f"full message length: {msglen}")

                full_msg += msg

                #print(len(full_msg))

                if len(full_msg)-self.HEADERSIZE == msglen:
                    #print("full msg recvd")
                    #print(full_msg[HEADERSIZE:])
                    leer = pickle.loads(full_msg[self.HEADERSIZE:])
                    #print(a)
                    new_msg = True
                    full_msg = b""
                    #print(type(a),type(a[2]))
                            
                    #leer = self.firebase.get('/prueba/datos_post','-NB8xDJejQG3fyEjT8wg')
                    self.temp_val.set(leer[1])
                    self.pulso_val.set(leer[2])
                    self.hr_val.set(leer[3])
                    self.spo_val.set(leer[4])
                    self.resp_val.set(leer[5])
                    self.presion_val.set(leer[6])
                    #a = np.asarray(leer['y'])
                    #a[a==-1] = None
                    #b = np.asarray(leer['y2'])
                    #b[b==-1] = None
                    #c = np.asarray(leer['y4'])
                    #c[c==-1] = None
                    
                    self.y= leer[7]#a
                    self.y2= leer[8]#b
                    self.y4= leer[9]#c


                    self.ax2.set_ylim([np.nanmin(self.y2)-1, np.nanmax(self.y2)+1])
                    self.ax4.set_ylim([np.nanmin(self.y4)-20, np.nanmax(self.y4)+20])
                    
                    #print('o',self.define)
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.s.connect((self.ip, self.port))

                    #self.tiempoactual = datetime.now()
                    #dif_tiempo = (self.tiempoactual - self.tiempoanterior).total_seconds()
                    self.tiempoactual = time.time()
                    dif_tiempo = self.tiempoactual - self.tiempoanterior
                    if (dif_tiempo >= int(self.lapsoMinAlarma.get())):

                        valor = self.temp_val.get()
                        if(valor != '-'):
                            valor = int(valor)
                            if(valor > int(self.tempMax.get())):
                                self.alarma('TEMPERATURA MÁXIMO')
                            elif (valor < int(self.tempMin.get())):
                                self.alarma('TEMPERATURA MÍNIMO')
                            
                        valor = self.pulso_val.get()
                        if(valor != '-'):
                            valor = int(valor)
                            if(valor > int(self.pulsoMax.get())):
                                #print('alarrma')
                                self.alarma('PULSO MÁXIMO')
                            elif (valor < int(self.pulsoMin.get())):
                                self.alarma('PULSO MÍNIMO')
                            
                        valor = self.hr_val.get()
                        if(valor != '-'):
                            valor = int(valor)
                            if(valor > int(self.hrMax.get())):
                                self.alarma('HR MÁXIMO')
                            elif (valor < int(self.hrMin.get())):
                                self.alarma('HR MÍNIMO')

                        valor = self.spo_val.get()
                        if(valor != '-'):
                            valor = int(valor)                    
                            if(valor > int(self.spoMax.get())):
                                self.alarma('SPO MÁXIMO')
                            elif (valor < int(self.spoMin.get())):
                                self.alarma('SPO MÍNIMO')
                            
                        valor = self.resp_val.get()
                        if(valor != '-'):
                            valor = int(valor)
                            if(valor > int(self.respMax.get())):
                                self.alarma('RESPIRACIÓN MÁXIMO')
                            elif (valor < int(self.respMin.get())):
                                self.alarma('RESPIRACIÓN MÍNIMO')



                        valor = self.presion_val.get()
                        if(valor != '-/-'):
                            a = valor.split('/')
                            
                            valor = int(a[0])
                            if(valor > int(self.presionSisMax.get())):
                                self.alarma('PRESION SIST. MÁXIMO')
                            elif (valor < int(self.presionSisMin.get())):
                                self.alarma('PRESION SIST. MÍNIMO')

                            valor = int(a[1])
                            if(valor > int(self.presionDiaMax.get())):
                                self.alarma('PRESION DIAST. MÁXIMO')
                            elif (valor < int(self.presionDiaMin.get())):
                                self.alarma('PRESION DIAST. MÍNIMO')


        
                #time.sleep(0.001)
                
            except Exception as e:
                print(e)
                print('no se fin')
                sys.exit()
                return 'salir'
        
        return 'fin'
    
    ################################################################                    
    def fireConexion(self):

        try:                           
            self.hilo5 = threading.Thread(target=self.esperar5)
            self.hilo5.start()

        except Exception:
            showerror(title="ERROR",message="error conexion  firebase")  
   ################################################################
    def alarma(self, mensaje):
##        try:
##            print('jjjjjjjj')
##            print(self.filewinA.winfo_exists())
##            print('kkkkkkkkk')
##             #self.filewinA.destroy()
##        except:
        if  not(self.filewinA.winfo_exists())  :
        
            self.filewinA = tk.Toplevel()
            #self.filewinA.geometry("400x400")
            self.filewinA.configure(bg='orange')

            #filewinIP.resizable (False, False)
            
            IZQframe = tk.Frame(self.filewinA)
            IZQframe.pack(padx=150, pady=150)

            lbConfIzq= tk.Label(IZQframe, text = mensaje, font=(None,10,'bold'))
            lbConfIzq.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)

            #button = Button(IZQframe, text="CERRAR", command=self.filewinA.destroy)
            button = Button(IZQframe, text="CERRAR", command= lambda:self.cerrar_ventana())
            button.pack(expand=True, fill=tk.BOTH,padx=10, pady=10)

            
            #playsound('alarma.mp3', block = False)
            buzzer.off()
            self.hora  = time.time()            ##tiempo para la duracion de sonido
            
            
        else:
            current = time.time()
            if ((current - self.hora) > 5): 
                self.hora  = time.time()
                
                #print('playing sound using  playsound')
                #playsound('alarma.mp3', block = False)
                buzzer.on()
        
    ################################################################
    def cerrar_ventana(self):
        self.filewinA.destroy()
        self.tiempoanterior = time.time() ##tiempo entre alarmas
    ################################################################    

for port in ports :
    qw = port.device
    puertos.append(qw)

root = tk.Tk()
#root.title('A - MONITOR MULTIVARIABLE - T')
root.geometry("1000x500")
#root.minsize(950,480)
#root.config(bg= FONDO)
root.resizable (False, False)
ipIn = input('Enter IP server:') or ""
portIN = int(input("Enter the port: ") or "1234")
app = Window(root, puertos = puertos,FONDO = FONDO, TEXTCOL = TEXTCOL,
             ip = ipIn, port = portIN )
app.config(bg= FONDO)

app.baudios = 38400
app.mainloop() 
