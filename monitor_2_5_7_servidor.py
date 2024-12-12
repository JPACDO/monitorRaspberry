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



#---------End of imports
####2_2 voy a oprobar a recibir dato de 1 en 1
####2_3 dos seriales
####2_3_2 las dimensiones para el pulso y ecg seran diferentes porque el ecg enviadatos mas seguidos encomparacion al otro
####2_3_3 boton start/stop
####2_4_0   grafico para respiracion y presion muestra
####2_4_1   añado otro puerto com para presion
####2_5_0_emisor envia datos a firebase/ receptor recibe datos de firebase
####2_5_2_servidor es el servidor, aqui le pongo para ingresar manual la ip
####2_5_3_servidor lo configuro para poder usar solo un puerto si es necesario
####2_5_4_servidorrecibe mas datos en pulso (ahora solo Ir,RED  quiero IR,REd,IR,red,Ir,red... para que se vea mejor la onda)
####2_5_5_servidor envia por puerto serie los datos a un arduino que muestra en un ldc
####2_5_7_servidor para el de la presion se pone un boton de iniciar y tiempo


FONDO = 'black'
TEXTCOL = "white"
ports = serial.tools.list_ports.comports(include_links=False)
puertos = []



class Window(Frame):

    def __init__(self, master = None, puertos = None, baudios = 9600,
                 #dimension = 800, dim_array = 10,dpi = 100,     ##config para ecg
                 dimension = 750*2, dim_array = 15,dpi = 100,
                 dim_red_ir = 100, 
                 dimension2 = 50*2, dim_array2 = 5,dpi2 = 100,     ##config para pulso dim_array2 = 1
                 dim_array3 = 10,                               ##config temp
                 dimension4 = 50*2, dim_array4 = 1,dpi4 = 100,     ##config para resp
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
        self.suma = np.zeros(self.dim_array2) ##datos para clacular el spo
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

        self.tiempoP = tk.StringVar()                 #variable para controlar el tiempo del motor de presion
        self.tiempoP.set("0")
        
        self.h = 2
        self.w = 9
        print(self.h,self.w)

        self.ip = ip
        self.port = port

        self.inicarSocket = 1
        
        self.init_window()
        #self.bind("<Configure>",  self.resize)   #####efecto de cambiar de tamaño plot segun tamaño ventana
        self.master.bind('<Escape>', lambda e: self.salida())
        self.master.protocol("WM_DELETE_WINDOW", self.salida)
    ################################################################
    def salida(self):

        if (self.define == 1):
            self.ser.close()
            self.ser2.close()
            self.ser3.close()
            self.ser4.close()
            print ('serial close')
        print('salida')
        self.master.quit()
        self.master.destroy()
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
        self.ax.set_axis_off()
        
        self.line, = self.ax.plot(self.y,color="green")#self.x, np.sin(self.x))        

        self.ax.set_facecolor(self.FONDO)
        self.fig.patch.set_facecolor(self.FONDO)
        
        ###########
        self.fig2 = plt.Figure(figsize=(self.w, self.h), dpi = self.dpi)
        self.ax2 = self.fig2.add_subplot(111)
        self.ax2.set_title('PULSO', loc='left', color='green')#fontdict=fd,

        self.ax2.set_xlim([0, self.eje_x2])
        self.ax2.set_ylim([3000, 4000])
        self.ax2.set_axis_off()
        
        self.line2, = self.ax2.plot(self.y2,color="green")#self.x, np.sin(self.x))        

        self.ax2.set_facecolor(self.FONDO)
        self.fig2.patch.set_facecolor(self.FONDO)
        
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
    def init_window(self):

        self.master.title("'A - MONITOR MULTIVARIABLE e- T'")
        self.pack(fill='both', expand=1)     


        # Frame horizontal 1 grafico y parametros ECG/PULSO
        fm1 = tk.Frame(self,highlightbackground="red",
                       highlightthickness=1)
        fm1.config(bg= FONDO)
        fm1.grid(row=0, column=0,
                 rowspan = 1, #8
                 columnspan = 6,
                 padx=5, pady=5)

        # Frame para parametros ECG
        fm2 = tk.Frame(fm1,highlightbackground="red",
                       highlightthickness=1)
        fm2.config(bg= FONDO)
        fm2.grid(row=0, column=6,
                 rowspan = 1,
                 columnspan = 1,
                 padx=1, pady=1)
        # Frame para parametros PULSO
        fm2_3 = tk.Frame(fm1,highlightbackground="red",
                       highlightthickness=1)
        fm2_3.config(bg= FONDO)
        fm2_3.grid(row=1, column=6,
                 rowspan = 4,
                 columnspan = 1,
                 padx=1, pady=1)


        # Frame horizontal 2 grafico y parametros SPO/TEMP
        fm5 = tk.Frame(self,highlightbackground="red",
                       highlightthickness=1)
        fm5.config(bg= FONDO)
        fm5.grid(row=1, column=0,
                 rowspan = 1,
                 columnspan = 6,
                 padx=5, pady=5)

        # Frame para parametros SPO
        fm3 = tk.Frame(fm5,highlightbackground="red",
                       highlightthickness=1)
        fm3.config(bg= FONDO)
        fm3.grid(row=0, column=6,
                 rowspan = 1,
                 columnspan = 1,
                 padx=1, pady=1)
        
        # Frame para parametros TEMP
        fm5_3 = tk.Frame(fm5,highlightbackground="red",
                       highlightthickness=1)
        fm5_3.config(bg= FONDO)
        fm5_3.grid(row=1, column=6,
                 rowspan = 1,
                 columnspan = 1,
                 padx=1, pady=1)


        # Frame para config 
        fm4 = tk.Frame(self)
        fm4.config(bg= FONDO)
        fm4.grid(row=8, column=0,
                 rowspan = 1,
                 columnspan = 9,
                 padx=5, pady=10)


        # Frame horizontal 3 grafico y parametros RESP/PRESION
        fm6 = tk.Frame(self,highlightbackground="red",
                       highlightthickness=1)
        fm6.config(bg= FONDO)
        fm6.grid(row=2, column=0,
                 rowspan = 1,
                 columnspan = 6,
                 padx=5, pady=5)

        # Frame para parametros RESP
        fm6_1 = tk.Frame(fm6,highlightbackground="red",
                       highlightthickness=1)
        fm6_1.config(bg= FONDO)
        fm6_1.grid(row=0, column=6,
                 rowspan = 1,
                 columnspan = 1,
                 padx=1, pady=1)
        
        # Frame para parametros PRESION
        fm6_2 = tk.Frame(fm6,highlightbackground="red",
                       highlightthickness=1)
        fm6_2.config(bg= FONDO)
        fm6_2.grid(row=1, column=6,
                 rowspan = 1,
                 columnspan = 1,
                 padx=1, pady=1)


        #DATOS PARA FM2 ------------------------------
        #----------------------------------------------

        self.labelHR = Label(fm2,text="HR\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,12,'bold'),
                             fg=self.TEXTCOL)
        self.labelHR.grid(row=0,column=0, rowspan = 2)
        self.labelHRmax = Label(fm2,text="120",width=self.acho_wg,
                                font=(None,12,'bold'),bg=self.FONDO,
                                fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelHRmax.grid(row=2,column=0, sticky = tk.W)
        self.labelHRmin = Label(fm2,text="50",width=self.acho_wg,
                                font=(None,12,'bold'),bg=self.FONDO,
                                fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelHRmin.grid(row=3,column=0, sticky = tk.W)
        
        self.textHRval = Label(fm2,textvariable=self.hr_val,width=int(self.acho_wg/2),
                               fg=self.TEXTCOL,
                               bg=self.FONDO, font=(None,25,'bold'))
        self.textHRval.grid(row=0,column=1, rowspan = 4)

        
        #DATOS PARA FM3 ------------------------------
        #----------------------------------------------

        self.labelSPO = Label(fm3,text="SPO\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,12,'bold'),
                              fg=self.TEXTCOL)
        self.labelSPO.grid(row=0,column=0, rowspan = 2)
        self.labelSPOmax = Label(fm3,text="100",width=self.acho_wg,
                                font=(None,12,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelSPOmax.grid(row=2,column=0, sticky = tk.W)
        self.labelSPOmin = Label(fm3,text="90",width=self.acho_wg,
                                font=(None,12,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelSPOmin.grid(row=3,column=0, sticky = tk.W)
        
        self.textSPOval = Label(fm3,textvariable=self.spo_val,width=int(self.acho_wg/2),
                               bg=self.FONDO, font=(None,25,'bold'),
                                fg=self.TEXTCOL)
        self.textSPOval.grid(row=0,column=1, rowspan = 4)

        #DATOS PARA FM2_3 ------------------------------
        #----------------------------------------------

        self.labelPULSO = Label(fm2_3,text="PULSO\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,12,'bold'),
                              fg=self.TEXTCOL,
                               anchor="e",justify=tk.LEFT)
        self.labelPULSO.grid(row=0,column=0, rowspan = 1, sticky = tk.W)
        self.labelPULSOval = Label(fm2_3,textvariable=self.pulso_val,width=int(self.acho_wg),
                                font=(None,25,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelPULSOval.grid(row=1,column=0, sticky = tk.W)

        #DATOS PARA FM5_3 ------------------------------
        #----------------------------------------------

        self.labelTEMP = Label(fm5_3,text="TEMP\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,12,'bold'),
                              fg=self.TEXTCOL,
                                anchor="e",justify=tk.LEFT)
        self.labelTEMP.grid(row=0,column=0, rowspan = 1, sticky = tk.W)
        self.labelTEMPval = Label(fm5_3,textvariable=self.temp_val,width=int(self.acho_wg),
                                font=(None,25,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelTEMPval.grid(row=1, column=0, sticky = tk.W)

        #DATOS PARA FM6_1 ------------------------------
        #----------------------------------------------

        self.labelRESP = Label(fm6_1,text="RESP\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,12,'bold'),
                              fg=self.TEXTCOL,
                                anchor="e",justify=tk.LEFT)
        self.labelRESP.grid(row=0,column=0, rowspan = 1, sticky = tk.W)
        self.labelRESPval = Label(fm6_1,textvariable=self.resp_val,width=int(self.acho_wg),
                                font=(None,25,'bold'),bg=self.FONDO,
                                 fg=self.TEXTCOL,
                                anchor="e",justify=tk.RIGHT)
        self.labelRESPval.grid(row=1, column=0, sticky = tk.W)
        #DATOS PARA FM6_2 ------------------------------
        #----------------------------------------------

        self.labelPRESION = Label(fm6_2,text="PRESION\n",
                             width=self.acho_wg, #relief=tk.SUNKEN,
                             bg=self.FONDO,font=(None,12,'bold'),
                              fg=self.TEXTCOL,
                                anchor="e",justify=tk.LEFT)
        self.labelPRESION.grid(row=0,column=0, rowspan = 1, sticky = tk.W)
        self.labelPRESIONval = Label(fm6_2,textvariable=self.presion_val,width=int(self.acho_wg),
                                font=(None,25,'bold'),bg=self.FONDO,
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
        self.canvas.get_tk_widget().grid(column=0,row=0,# columnspan = 6,
                                         rowspan = 2)

        self.canvas2 = FigureCanvasTkAgg(self.fig2, master=fm5)
        self.canvas2.get_tk_widget().grid(column=0,row=0,# columnspan = 6,
                                          rowspan = 2)

        self.canvas4 = FigureCanvasTkAgg(self.fig4, master=fm6)
        self.canvas4.get_tk_widget().grid(column=0,row=0,# columnspan = 6,
                                          rowspan = 2)

        self.go()

        #CONEXION SERIAL ------------------------------
        #----------------------------------------------
        self.lbpuerto = tk.Label(fm4, text = "PUERTO:   ",
                                 width = self.acho_wg,
                                 fg=self.TEXTCOL) # font=(None,12,'bold'),
        self.lbpuerto.config(bg=self.FONDO)
        self.lbpuerto.grid(sticky='W',row=0,column=6) #,padx=20)
        #########
        self.portser = tk.StringVar()
        self.portser.set("SELECCIONA")
        campport = tk.ttk.Combobox(fm4, textvariable = self.portser,
                                   width= 12)#self.acho_wg)
        campport.grid(row=0,column=7)#,padx=20)
        campport["values"] = self.ports
        #########
        self.portser2 = tk.StringVar()
        self.portser2.set("SELECCIONA")
        campport2 = tk.ttk.Combobox(fm4, textvariable = self.portser2,
                                   width= 12)#self.acho_wg)
        campport2.grid(row=0,column=8)#,padx=20)
        campport2["values"] = self.ports
        #########
        self.portser3 = tk.StringVar()
        self.portser3.set("SELECCIONA")
        campport3 = tk.ttk.Combobox(fm4, textvariable = self.portser3,
                                   width= 12)#self.acho_wg)
        campport3.grid(row=0,column=9)#,padx=20)
        campport3["values"] = self.ports
        #########
        self.portser4 = tk.StringVar()
        self.portser4.set("SELECCIONA")
        campport4 = tk.ttk.Combobox(fm4, textvariable = self.portser4,
                                   width= 12)#self.acho_wg)
        campport4.grid(row=0,column=10)#,padx=20)
        campport4["values"] = self.ports

        
        if (self.define == 1):
            estado = "DESCONECTAR"
        else:
            estado = "CONECTAR"
     
        self.b1=tk.Button(fm4,text = estado,
                          width = 12, #self.acho_wg,
                          command=lambda: self.conexion())
        self.b1.grid(row=0,column=11, sticky = tk.W,padx=20)


        if (self.define2 == 1):
            estado2 = "STOP"
        else:
            estado2 = "START"
     
        self.b2=tk.Button(fm4,text = estado2,
                          width = 12, #self.acho_wg,
                          command=lambda: self.start_com())
        self.b2.grid(row=0,column=12, sticky = tk.W,padx=20)

     
        self.b3=tk.Button(fm4,text = 'Válvula',
                          width = 12, #self.acho_wg,
                          command=lambda: self.start_presion())
        self.b3.grid(row=0,column=13, sticky = tk.W,padx=20)

        teTimePresion = tk.Entry(fm4, textvariable =  self.tiempoP, borderwidth=5,width="20")
        teTimePresion.grid(row=0,column=14, sticky = tk.W,padx=10)
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
                    self.y[self.i + self.dim_array] = np.nan#np.nanmean(self.y)#None
                    self.y[self.i + self.dim_array + 1] = np.nan#np.nanmean(self.y)#None
                    
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
                puertocom = self.portser.get()
                print (puertocom,'ecg')
                if puertocom != 'SELECCIONA':
                    self.ser = serial.Serial(puertocom, self.baudios, timeout=3)
                    self.leer_ser()

                puertocom2 = self.portser2.get()
                print (puertocom2,'IR RED SPO PULSO')
                if puertocom2 != 'SELECCIONA':
                    self.ser2 = serial.Serial(puertocom2, self.baudios, timeout=3)
                    self.leer_ser2()

                puertocom3 = self.portser3.get()
                print (puertocom3,'RESP')
                if puertocom3 != 'SELECCIONA':
                    self.ser3 = serial.Serial(puertocom3, self.baudios, timeout=3)
                    self.leer_ser3()

                puertocom4 = self.portser4.get()
                print (puertocom4,'PRESION')
                if puertocom4 != 'SELECCIONA':
                    self.ser4 = serial.Serial(puertocom4, self.baudios, timeout=3)
                    self.leer_ser4()

                
                self.HEADERSIZE = 10
                if(self.inicarSocket):
                    self.inicarSocket = 0  ## se queda en cero, asi no se inicia otra vez
                    self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    if (self.ip == ""):
                        self.ip = socket.gethostname()
                        #self.s.bind((socket.gethostname(), self.port))
                        print('vacio',socket.gethostname(), self.port)
                    else:
                        print('ip',self.ip, self.port)
                    self.s.bind((self.ip, self.port))
                    self.s.listen(5)
                    self.fireConexion()     ##mantengo el nombre fire pero conecta cliente-servidor


                self.enviar_datos_lcd()

                        
                    
            else:
                estado = "CONECTAR"
                puertocom = self.portser.get()
                if puertocom != 'SELECCIONA':
                    self.ser.close()
                puertocom2 = self.portser2.get()
                if puertocom2 != 'SELECCIONA':
                    self.ser2.close()
                puertocom3 = self.portser3.get()
                if puertocom3 != 'SELECCIONA':
                    self.ser3.close()
                puertocom4 = self.portser4.get()
                if puertocom4 != 'SELECCIONA':
                    self.ser4.close()
          
                    
            self.b1.configure(text=estado)
            
        except Exception as e:
            print(e)
            self.define = 0
            estado = "CONECTAR"
            self.b1.configure(text=estado)
            if puertocom != 'SELECCIONA':
                self.ser.close()
            if puertocom2 != 'SELECCIONA':
                self.ser2.close()
            if puertocom3 != 'SELECCIONA':
                self.ser3.close()
            showerror(title="ERROR",message="VERIFIQUE EL PUERTO")
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
                if puertocom != 'SELECCIONA':
                    self.ser.write(b'\n')

                puertocom2 = self.portser2.get()
                print (puertocom2)
                if puertocom2 != 'SELECCIONA':
                    self.ser2.write(b'\n')

                puertocom3 = self.portser3.get()
                print (puertocom3)
                if puertocom3 != 'SELECCIONA':
                    self.ser3.write(b'\n')

                ## no hay port4 porque inicia solo no hay necesidad de iniciarlo
                
            else:
                estado2 = "START"
                #self.define = 0
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
    #####El boton de presion para iniciar el bombeo
    def start_presion(self):
        try:
            self.ser4.write(b'\n')

            if(self.tiempoP != '0'):
                hiloPresion = threading.Thread(target=self.esperarPresion)
                hiloPresion.start()

            
        except Exception as e:
            print(e)
            showerror(title="ERROR",message="VERIFIQUE EL PUERTO")

   ################################################################
    def esperarPresion(self):

        valor = self.tiempoP.get()
        if(valor != ''):
            valor = int(valor)

        hora  = time.time() 
        while(self.tiempoP.get() != '0'):

            current = time.time()
            if ((current - hora) > valor): 
                hora  = time.time()
                
                try:
                    self.ser4.write(b'\n')
                    
                except Exception as e:
                    print(e)
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
                    a = reading.split(',')[1:]  #valor 0 = 'B' y el 1 = ','
                    #print('ff2')
                    aa = list(map(int, a))
                    #print(aa)
                    #print('ff3')
                    
                    #self.y2[self.i2] = int(reading[2:])

                    for i in range(self.dim_array2):

                        self.suma[i] = sum(aa[2*i:2*i+1])  ##es 2*i ya que los pares serian 0,1  2,3  4,5 ...

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
                            self.pulso_val.set(int(hr))
                        else:
                            self.pulso_val.set('-')
                        
                    else:
                        self.ir[self.i_red_ir] = aa[1]
                        self.ir[self.i_red_ir+1] = aa[3]
                        self.ir[self.i_red_ir+2] = aa[5]
                        self.ir[self.i_red_ir+3] = aa[7]
                        self.ir[self.i_red_ir+4] = aa[9]
                        self.red[self.i_red_ir]= aa[0]
                        self.red[self.i_red_ir+1]= aa[2]
                        self.red[self.i_red_ir+2]= aa[4]
                        self.red[self.i_red_ir+3]= aa[6]
                        self.red[self.i_red_ir+4]= aa[8]
                        self.i_red_ir += self.dim_array2#1
                        #print(self.i_red_ir)

                    
                    self.y2[self.i2:self.i2+self.dim_array2] = self.suma*-1
                    
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
                    self.y2[self.i2 + 0] = np.nan#np.nanmean(self.y2)# None
                    self.y2[self.i2 + 1] = np.nan#np.nanmean(self.y2)#None
                    self.i2 = 0#-10
                else:
                    #pass
                    #los dos ultimos valores seran vacios
                    self.y2[self.i2 + 0] = np.nan#np.nanmean(self.y2)# None
                    self.y2[self.i2 + 1] = np.nan#np.nanmean(self.y2)#None
                #print(self.y2,'l')
                    
                #self.i2 += self.dim_array2
                #print(self.i2)
                if letra == 'C':
                    
                    
                    temp = int(reading[1:])
                    temp = temp*500/1023
                    ####falseo temperatura si es menor a 30
                    if(temp <= 30 and temp > 25):
                        temp = temp + 6
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
                    self.y4[self.i4 + self.dim_array4] = np.nan#np.nanmean(self.y4)# None
                    self.y4[self.i4 + self.dim_array4 + 1] = np.nan#np.nanmean(self.y4)# None
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
        
        while self.define:
            #print('f',self.define)
            try:
                clientsocket, address = self.s.accept()
                
                '''
                datos = {
                    'temp_val': self.temp_val.get(),
                    'pulso_val': self.pulso_val.get(),
                    'hr_val': self.hr_val.get(),
                    'spo_val': self.spo_val.get(),
                    'resp_val': self.resp_val.get(),
                    'presion_val': self.presion_val.get(),
                    'y' : self.y,
                    'y2': self.y2,
                    'y4': self.y4                
                    }
                '''
                datos = {
                    1: self.temp_val.get(),
                    2: self.pulso_val.get(),
                    3: self.hr_val.get(),
                    4: self.spo_val.get(),
                    5: self.resp_val.get(),
                    6: self.presion_val.get(),
                    7: self.y,
                    8: self.y2,
                    9: self.y4                
                    }
                msg = pickle.dumps(datos)
                    
                msg = bytes(f"{len(msg):<{self.HEADERSIZE}}", 'utf-8')+msg
                #print('o',self.define)
                clientsocket.send(msg)
                clientsocket.close()
    
                time.sleep(0.050)
            except Exception as e:
                print(e)

    ################################################################                    
    def fireConexion(self):

        try:                           
            hilo5 = threading.Thread(target=self.esperar5)
            hilo5.start()

        except Exception:
            showerror(title="ERROR",message="error conexion  firebase")  

################################################################ 
    def esperar6(self):

        puerto_envio = self.ser3
        
        while self.define:
            #print('f',self.define)
            try:
                #### mandar datos por serial al ldc
                valor = 'H'+self.hr_val.get() +'T'+self.temp_val.get()+'P'+self.presion_val.get()
                puerto_envio.write(valor.encode())
                ##ser.write(b'valores')
                ##ser.write(b'\r')
                puerto_envio.write(b'\n')
            
                time.sleep(1)
            except Exception as e:
                print(e)

################################################################               
    def enviar_datos_lcd(self):

        try:                           
            hilo6 = threading.Thread(target=self.esperar6)
            hilo6.start()

        except Exception:
            showerror(title="ERROR",message="error conexion  firebase")
            
        

       

for port in ports :
    qw = port.device
    puertos.append(qw)

root = tk.Tk()
#root.title('A - MONITOR MULTIVARIABLE - T')
#root.geometry("1000x500")
#root.minsize(950,480)
#root.config(bg= FONDO)
root.resizable (False, False)
ipIn = input('Enter your IP:') or ""
portIN = int(input("Enter the port: ") or "1234")
app = Window(root, puertos = puertos,FONDO = FONDO, TEXTCOL = TEXTCOL,
             ip = ipIn, port = portIN)
app.config(bg= FONDO)

app.baudios = 38400
app.mainloop() 
