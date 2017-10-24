# -*- coding: utf-8 -*-
"""
Created on Thu Oct 19 13:06:54 2017

@author: geddesag
"""

from numpy import *


import Tkinter as tk
import pygubu
import pyqtgraph as pg
from pyqtgraph.Qt import QtGui, QtCore
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
import os
pg.setConfigOption('background', 'w')
pg.setConfigOption('foreground', 'k')

import u12


class Application:
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title('Analog Inputs')
        self.builder = builder = pygubu.Builder()
        builder.add_from_file('window.ui')
        self.mainwindow = builder.get_object('mainwindow', self.root)
        self.samp_flag=False

        """Grab all the needed items"""
        """Channel checkboxes"""
        
        self.single_ai0_cb=builder.get_object('single_ai0_cb',self.root)
        

        self.channel_buttons=[]
        self.channel_status=[]
        for i in range(8):
            #print i
            self.channel_status.append(tk.IntVar())
            self.channel_status[i].set(1)
            self.channel_buttons.append(builder.get_object('single_ai'+str(i)+'_cb',self.root))
            self.channel_buttons[i].config(variable=self.channel_status[i],command= lambda i2=i: self.select_channels(i2))
         
        for i in range(4):
            self.channel_status.append(tk.IntVar())
            self.channel_status[i+8].set(0)
            self.channel_buttons.append(builder.get_object('diff_ai'+str(i+8)+'_cb',self.root))
            self.channel_buttons[i+8].config(variable=self.channel_status[i+8],command= lambda i2=i+8: self.select_channels(i2))
        
        """Gains"""
        self.gain_sb=[]
        self.gain_values_list=[(20,10,5,4,2.5,2,1.25,1),(1,2,4,5,8,10,16,20)]
        for i in range(4):
            self.gain_sb.append(builder.get_object('diff_ai'+str(i+8)+'_sb',self.root))
            self.gain_sb[i].config(values=self.gain_values_list[0])
        
        """options"""
        
        self.sampspeed_sb=builder.get_object('sampspeed_sb',self.root)
        self.sampspeed_sb.configure(from_=0.1,to=100,increment=0.1)
        self.plot_flag=tk.IntVar()
        self.plot_flag.set(1)
        self.plot_cb=builder.get_object('plot_cb',self.root)
        self.plot_cb.config(variable=self.plot_flag)

        self.log_flag=tk.IntVar()
        self.log_flag.set(1)

        self.log_cb=builder.get_object('log_cb',self.root)
        self.log_cb.config(variable=self.log_flag)
        """buttons"""
        
        self.start_bu=builder.get_object('start_bu',self.root)
        self.reset_bu=builder.get_object('reset_bu',self.root)
        self.start_bu.config(command=self.toggle_sampling)
        self.reset_bu.config(command=self.reset_gui)
        self.gather_channels()
        self.initialise_diag()

        self.placeholder_bu=builder.get_object('placeholder_bu',self.root)        
        self.root.mainloop()
        
    def toggle_sampling(self):
        if self.samp_flag==False:
            self.start_bu.config(text="Stop")
            self.samp_flag=True
            if self.log_flag.get()==1:
                self.create_log()
            self.sampling()
            for i in self.channel_buttons:
                i.config(state="disabled")
            for i in self.gain_sb:
                i.config(state="disabled")
            self.sampspeed_sb.config(state="disabled")
            self.log_cb.config(state="disabled")
            self.plot_cb.config(state="disabled")
            self.reset_bu.config(state="disabled")
        elif self.samp_flag==True:
            self.root.after_cancel(self.samp_job)
            self.start_bu.config(text="Start")
            self.samp_flag=False     
            for i in self.channel_buttons:
                i.config(state="normal")
            for i in self.gain_sb:
                i.config(state="normal")   
            self.sampspeed_sb.config(state="normal")
            self.log_cb.config(state="normal")
            self.plot_cb.config(state="normal")
            self.reset_bu.config(state="normal")

    def initialise_diag(self):
        self.win = pg.GraphicsWindow(title="Voltages")
        windowwidth = 1000                       
        self.plots=[]
        self.plots_c=[]
        self.plot_xm=[]
        self.diff_plots=[]
        self.diff_plots_c=[]
        self.diff_plot_xm=[]
        i=0
        for i in range(len(self.single_ended)):
            self.plots.append(self.win.addPlot(title="EHT",row=i+1,col=1)  )
            self.plots_c.append(self.plots[i].plot())
            self.plot_xm.append(linspace(0,0,windowwidth))
            
        for j in range(len(self.differentials)):
            self.diff_plots.append(self.win.addPlot(title="EHT",row=i+j+2,col=1)  )
            self.diff_plots_c.append(self.diff_plots[j].plot())
            self.diff_plot_xm.append(linspace(0,0,windowwidth))
                      
        self.ptr = -windowwidth    
        self.time_to_wait=1./float(self.sampspeed_sb.get())
    
    def create_log(self):
        now=datetime.datetime.now()
        year=str(now.year)
        month="%02d" % now.month
        day="%02d" % now.day
        hour="%02d" % now.hour
        suffix=0
        todayspath=year+month+day
        filepath_out=todayspath
        
        filename_out=year+"_"+month+"_"+day+"_"+hour+"_LJ_log."+str(suffix)
        
        while suffix<999:
            filename_out=year+month+day+hour+"."+str(suffix)
            if os.path.exists(filepath_out+"\\"+filename_out)==False:
                break
            suffix=suffix+1
        self.log_file=filepath_out+"\\"+filename_out
   
        if not os.path.exists(os.path.dirname(self.log_file)):
            try:
                os.makedirs(os.path.dirname(self.log_file))
            except:
                passs
        f=open(self.log_file,"a")
        f.write("** LJ Log File, channels")
        for i in self.single_ended:
            f.write(str(i)+",")
        for i in self.differentials:
            f.write(str(i)+",")
        f.write("\n")
        f.close()
    def sampling(self):
        if self.samp_flag:
            single_ended_data,differential_data=sample_channels(self.single_ended_group1,self.single_ended_group2,self.differentials,self.gains)
            if self.plot_flag.get()==1:
                self.ptr += 1                          
               # print single_ended_data
    
                for i in range(len(self.single_ended)):
                    self.plot_xm[i][:-1] = self.plot_xm[i][1:] 
                    self.plot_xm[i][-1] = single_ended_data[i]
                    self.plots_c[i].setData(self.plot_xm[i])
                    self.plots_c[i].setPos(self.ptr,0)
                    
                for i in range(len(self.differentials)):
                    self.diff_plot_xm[i][:-1] = self.diff_plot_xm[i][1:] 
                    self.diff_plot_xm[i][-1] = differential_data[i]   
                    self.diff_plots_c[i].setData(self.diff_plot_xm[i])
                    self.diff_plots_c[i].setPos(self.ptr,0)
                               
                QtGui.QApplication.processEvents() 
            if self.log_flag.get()==1:
                f=open(self.log_file,"a")
                f.write(str(datetime.datetime.now())+',')
                for i in range(len(self.single_ended)):
                    f.write(str(single_ended_data[i])+',')
                for i in range(len(self.differentials)):
                    f.write(str(differential_data[i])+',')
                f.write('\n')
                f.close()
            self.samp_job=self.root.after(int(float(self.sampspeed_sb.get())*1000), self.sampling)
    
    def select_channels(self,number):
        if number==1 or number==0:
            if self.channel_status[number].get()==0:
                self.channel_buttons[8].config(state="normal")
            if self.channel_status[number].get()==1:
                self.channel_buttons[8].config(state="disabled")
                self.channel_status[8].set(0)
        if number==2 or number==3:
            if self.channel_status[number].get()==0:
                self.channel_buttons[9].config(state="normal")
            if self.channel_status[number].get()==1:
                self.channel_buttons[9].config(state="disabled")
                self.channel_status[9].set(0)
        if number==4 or number==5:
            if self.channel_status[number].get()==0:
                self.channel_buttons[10].config(state="normal")
            if self.channel_status[number].get()==1:
                self.channel_buttons[10].config(state="disabled")
                self.channel_status[10].set(0)
        if number==6 or number==7:
            if self.channel_status[number].get()==0:
                self.channel_buttons[11].config(state="normal")
            if self.channel_status[number].get()==1:
                self.channel_buttons[11].config(state="disabled")
                self.channel_status[11].set(0)
        if number==8:
            if self.channel_status[number].get()==0:
                self.channel_buttons[0].config(state="normal")
                self.channel_buttons[1].config(state="normal")

            if self.channel_status[number].get()==1:
                self.channel_buttons[0].config(state="disabled")
                self.channel_status[0].set(0)
                self.channel_buttons[1].config(state="disabled")
                self.channel_status[1].set(0)
        if number==9:
            if self.channel_status[number].get()==0:
                self.channel_buttons[2].config(state="normal")
                self.channel_buttons[3].config(state="normal")

            if self.channel_status[number].get()==1:
                self.channel_buttons[2].config(state="disabled")
                self.channel_status[2].set(0)
                self.channel_buttons[3].config(state="disabled")
                self.channel_status[3].set(0)
        if number==10:
            if self.channel_status[number].get()==0:
                self.channel_buttons[4].config(state="normal")
                self.channel_buttons[5].config(state="normal")

            if self.channel_status[number].get()==1:
                self.channel_buttons[4].config(state="disabled")
                self.channel_status[4].set(0)
                self.channel_buttons[5].config(state="disabled")
                self.channel_status[5].set(0)
        if number==11:
            if self.channel_status[number].get()==0:
                self.channel_buttons[6].config(state="normal")
                self.channel_buttons[7].config(state="normal")

            if self.channel_status[number].get()==1:
                self.channel_buttons[6].config(state="disabled")
                self.channel_status[6].set(0)
                self.channel_buttons[7].config(state="disabled")
                self.channel_status[7].set(0)
        self.gather_channels()
        self.initialise_diag()

    def gather_channels(self):
        self.differentials=[]
        self.single_ended=[]
        for i in range(len(self.channel_status)):
            if self.channel_status[i].get()==1:
                if i <=7:
                    self.single_ended.append(i)
                if i >=8:
                    self.differentials.append(i)
        self.single_ended_group1,self.single_ended_group2=configure_channel_groups(self.single_ended)
       # print self.single_ended
       # print self.single_ended_group1
       # print self.single_ended_group2
        self.gains=[]
        
        for i in range(4):
            gains_temp=float(self.gain_sb[i].get())
            gain_index=list(self.gain_values_list[0]).index(gains_temp)
            self.gains.append(self.gain_values_list[1][gain_index])
       # print self.gains

    def reset_gui(self):
        for i in range(8):
            self.channel_status[i].set(1)
            self.channel_buttons[i].config(state='normal')
        
        for i in range(4):
            self.channel_status[i+8].set(0)
            self.channel_buttons[i+8].config(state='disabled')
            self.gain_sb[i].config(values=self.gain_values_list[0])

        
    
    
def initialize_labjack():
    device=u12.U12()
    return device
    


        
    

def check_inputs(single_ended,differential,gains):
    """check channels based on the lists inputed, note that the differntial will need
    to start at 8 in this function, i.e configure inputs([1,2,3,4],[10,11])"""
    
    new_differentials=[]
    new_gains=[]
    for i in range(len(differential)):
        if differential[i]==8:
            channels=[1,2]
        if differential[i]==9:
            channels=[3,4]
        if differential[i]==10:
            channels=[5,6]
        if differential[i]==11:
            channels=[7,8]
        
        if channels[0] not in single_ended and channels[1] not in single_ended:
                new_differentials.append(differential[i])
                new_gains.append(gains[i])
                
                
    return new_differentials,new_gains

def configure_channel_groups(single_ended):
    if len(single_ended)==0:
        single_ended_group1=None
        single_ended_group2=None
    elif len(single_ended)<=4:
        single_ended_group1=single_ended
        single_ended_group2=None
    if len(single_ended)>4:
        single_ended_group1=single_ended[0:4]
        single_ended_group2=single_ended[4:]
    return single_ended_group1,single_ended_group2
    
def sample_channels(single_ended_group1,single_ended_group2,differentials,gains=diff_gains):
    single_ended_voltages=None
    differential_voltages=None
    if single_ended_group1!=None:
        single_ended_voltages=device.aiSample(len(single_ended_group1),single_ended_group1)["voltages"]
    if single_ended_group2!=None:
        single_ended_voltages2=device.aiSample(len(single_ended_group2),single_ended_group2)["voltages"]
        single_ended_voltages=concatenate((single_ended_voltages,single_ended_voltages2))
    if len(differentials)>0:
        differential_voltages=device.aiSample(len(differentials),differentials,gains=diff_gains)["voltages"]
    #print single_ended_voltages
    
    return single_ended_voltages,differential_voltages

if __name__=='__main__':
    device=initialize_labjack()
#    single_ended=list(arange(0,6))
#    differentials=list(arange(8,12))
#    diff_gains=list(zeros(4,dtype=int))
#    single_ended_group1,single_ended_group2=configure_channel_groups()
#    differentials,diff_gains=check_inputs(single_ended,differentials,diff_gains)
    Application()
    """Now i need to build the actual gui, lets take a lot of the blocks from the jypy code and bring that 
    on over, its gonna be clean and simple, not much on it"""
    
    """Channel Select, Gain Select"""
    
    """Samp Speed"""
    
    """Log check, Plot check"""
    
    """Start/ Stop Reset"""
    
    