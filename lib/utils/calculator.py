# -*- coding: utf-8 -*-
"""
Created on Thu Dec  9 16:26:03 2021

@author: lemzias1
"""
import scipy.io as sio
import os 
import re
import numpy as np
import matplotlib.pyplot as plt
from IPython.display import display, Math, Latex
# from .resonator_tools import circuit

import scipy.special as spf
from scipy.optimize import curve_fit

e = 1.60217662e-19
kb = 1.38064852e-23
Delta = e*1.8e-4
h_bar = 1.054571817e-34
h = 6.62607015e-34
GHz = 1e9

###Tmon parameters

#matrix element for charge operator
def n_10(EJ, EC):
    return np.sqrt(1/2)*(EJ/8/EC)**0.25

#dispersive shift
def chi(g, delta, Ec):
    return -((g**2)*Ec)/(delta*(delta-Ec))

#dispersive shift and lambda for i-level
def chi_i(g_i, delta_i):
    return g_i**2/delta_i

def lambda_i(g_i, delta_i):
    return -g_i/delta_i

#next-order components for Kerr coeff
def gl_second(lambda_i, lambda_i1, delta_i, delta_i1):
    return -(lambda_i*lambda_i1*(delta_i1 - delta_i))**2/(delta_i1 + delta_i)

#Kerr coeff and linear corrections K0 and K1
def zeta_suri(chi_01, chi_12, lambda01, lambda12):
    return chi_12*lambda12**2 - 2*chi_01*lambda01**2 + (7*chi_12*lambda01**2)/4 - (5*chi_01*lambda12**2)/4

def zeta_pr_suri(chi_01, chi_12, lambda01, lambda12):
    return (chi_01-chi_12)*(lambda01**2+lambda12**2)

def K0(chi_0, chi_1, lambda0, lambda1, gl0):
    return 0.25*(chi_0*lambda1**2 - 3*chi_1*lambda0**2)+chi_0*lambda0**2+gl0

def K1(chi_0, chi_1, lambda0, lambda1):
    return (chi_1-chi_0)*(lambda0**2 + lambda1**2)

def zeta(K_0, K_1):
    return (K_1 - K_0)*0.5

def zeta_pr(K_0, K_1):
    return (K_1 + K_0)*0.5

def fr_shift(n, fr, chi, zeta, zeta_pr):
    return fr + chi + zeta*n+zeta_pr*n

###TLS resonator parameters
def df_TLS(T, freq, delta):
    Psi = spf.digamma(0.5 - h*GHz*freq/(2j*np.pi*kb*T))
    return delta*(Psi.real-np.log(h*GHz*freq/(2*np.pi*kb*T)))/np.pi

def QTLS(T, freq, delta):
    return delta*np.tanh(h*GHz*freq/(2*kb*T))

def QTLS_corr(T, freq, delta, A):
    tan = np.tanh(h*GHz*freq/(2*kb*T))
    return delta*tan/(np.sqrt(1+A*tan/T))

def QTSL_pow(n_av, n_c, beta, Delta):
    return Delta/np.sqrt(1+(n_av/n_c)**beta)

###Others

def dBm_to_W(PdBm):
    return 10**((PdBm-30)/10)

def n_from_Q(P, Ql, Qc, f):
    omega = 2*np.pi*f
    return 4*P*Ql**2/(Qc*h_bar*omega**2)

def from_dB_to_lin(mag):
    return 10**(mag/20)-1

def power_to_rate(P_W, Ampl, w, gamma):
    #P in watts!!!
    h_bar = 1.054571817e-34
    return 2*np.sqrt(Ampl*gamma*P_W/(h_bar*w))

def kappa(fr, Ql):
    return fr/Ql

def n_crit(delta, g):
    return delta**2/(4*g**2)

def EJ(R, T):
    Ic = np.tanh(Delta/(kb*T))*np.pi*Delta/(2*e*R)
    return Ic/(4*np.pi*e)

def n_T(T, w):
    return np.exp(-h_bar*w*GHz/(kb*T))/(1 - np.exp(-h_bar*w*GHz/(kb*T)))
#-----------------------------------------------------------------------------
#work with files
def findpath(database,dataname):

    for root, dirs, files in os.walk(database, topdown=False):
        for name in files:  
            if name==dataname:
                print("Data source:")
                print(os.path.join(root,name))
                datapath=os.path.join(root,name)
    return datapath

def find_files(folder_name):
    name = []
    regex = re.compile(r'\d+')
    Temp = []

    for file in os.listdir(folder_name):
        if file.endswith(".mat"):
            name.append(os.path.join(folder_name, file))
            Temp.append(regex.findall(file)[0])
        
    Temp = [float(x) for x in Temp]
    name = [x for _, x in sorted(zip(Temp, name))]
    Temp.sort()
    
    return (name, Temp)

def loadmatfile(path):
    return sio.loadmat(path)
#-----------------------------------------------------------------------------
def Z_serial(w, wr, R, C):
    return R+1j*(1/wr - 1/w)/C

def Z_rCR(w, wr, R, C_q, C_r, Z0):
    t = np.pi/(wr)
    Z_C_q = 1.0/(-1j*w*C_q)
    Z_C_r = 1.0/(-1j*w*C_r)
    Coeff = ((R+Z_C_r)*np.cos(w*t)-1j*Z0*np.sin(w*t))/(Z0*np.cos(w*t)-1j*(R+Z_C_r)*np.sin(w*t)) 
    return Z0*Coeff+Z_C_q

def Z_tan(w, wr, R, C_q, C_r, Z0):
    t = np.pi/(wr)
    Z_C_q = 1.0/(-1j*w*C_q)
    Z_C_r = 1.0/(-1j*w*C_r)
    alpha = 0.5*np.log((Z0+R+Z_C_r)/(Z0-R-Z_C_r))
    return Z_C_q - 1j*Z0*np.tan(w*t + 1j*alpha)

def Qc(Z0, R0, Cc, f):
    w = 2*np.pi*f
    return np.pi/(4*Z0*R0*Cc**2*w**2)

#Functions for Analitycal Fitting

def n_plus(eps, kappa, chi, delta):
    return eps**2/(0.25*kappa**2 + (delta+chi)**2)

def n_minus(eps, kappa, chi, delta):
    return eps**2/(0.25*kappa**2 + (delta-chi)**2)

def D_s(n_p, n_m, kappa, chi, delta):
    return 2*(n_p+n_m)*chi**2/(0.25*kappa**2 + delta**2 + chi**2)

def Gamma_m(Ds, kappa):
    return Ds*kappa/2

def A_coeff(Ds, kappa, chi, delta):
    return Ds*(kappa/2 - 1j*chi - 1j*delta)/(kappa/2 + 1j*chi + 1j*delta)

def B_coeff(Ds, n_p, n_m, chi):
    return chi*(n_p+n_m-Ds)

def S(f, f0, chi, delta, eps, kappa, gamma0, alpha):
    def lor(n, f, f0, A, B, chi, delta, kappa, Gamma_0):
        fn = f0 + B + n*(chi+delta)
        Gamma_n = 2*Gamma_0 + n*kappa
        Im = (-A)**n * np.exp(A)/(Gamma_n/2 - 1j*(f-fn))
        return Im.real/np.math.factorial(n)
    
    N = 20
    n_p = n_plus(eps, kappa, chi, delta)
    n_m = n_minus(eps, kappa, chi, delta)
    Ds = D_s(n_p, n_m, kappa, chi, delta)
    Gamma_0 = Gamma_m(Ds, kappa) + gamma0
    A = A_coeff(Ds, kappa, chi, delta)
    B = B_coeff(Ds, n_p, n_m, chi)
    
    #print(n_p, n_m, Ds, A, B)
    
    SN = 0
    for i in range(0,N):
        Si = lor(i,f, f0, A, B, chi, delta, kappa, Gamma_0)
        SN = SN + Si
    return SN/(np.pi*alpha)

#plot simple 2D graph
def plot_2d(X, Y, Z, flip = False, cmap = 'Reds'):
    #plt.rcParams['font.size'] = '100'

    fig, ax = plt.subplots(figsize=(10, 6))

    #plt.rcParams['font.size'] = '40'

    for label in (ax.get_xticklabels() + ax.get_yticklabels()):
        label.set_fontsize(14)

    step_x = np.min(np.abs(np.diff(X)))
    step_y = np.min(np.abs(np.diff(Y)))

    extent = [np.min(X) - step_x / 2, np.max(X) + step_x / 2,
              np.min(Y) - step_y / 2, np.max(Y) + step_y / 2]
    
    if flip == True:
        Z = np.flip(Z,1)
        
    if np.reshape(X, (-1,))[0]>np.reshape(X, (-1,))[-1]:
        Z = np.flip(Z,0)

    cax = ax.imshow(Z.T, origin='lower', extent = extent, cmap=cmap, aspect='auto', interpolation='none')
    
    return cax

def plot_with_errors(X, Y, ERR, label = 'data', alpha = 0.2):
    plt.plot(X, Y, 'o-', label = label)
    plt.fill_between(X, Y-ERR, Y+ERR, alpha = alpha)
    plt.legend

# def res_fit_STSpower(mat_data, N = 60):
#     power = mat_data['power'].T
#     freq = mat_data['freq_scan'].T
    
#     Mfreq = []
#     port = []
    
#     for i in range(0, len(power)):
#         mag = mat_data['mag_2darray'][i,:]
#         pha = mat_data['pha_2darray'][i,:]
        
#         min_point = np.argmin(mag)
#         Mfreq.append(freq[min_point])
        
#         mag_cat = mag[min_point-N:min_point+N]
#         pha_cat = pha[min_point-N:min_point+N]
#         freq_cat = freq[min_point-N:min_point+N].reshape((-1,))
#         s21_i = (10**(mag_cat/20)*np.exp(1j*pha_cat)).T
#         port1 = circuit.notch_port()
#         port1.add_data(freq_cat,s21_i)
#         port1.autofit()
#         port.append(port1)
        
#     return port

def shift_flux(fr, flux):
    #works only for data with less than one period!
    fmax = np.argmax(fr)
    fmin = np.argmin(fr)
    
    period = 2*np.absolute(flux[fmax]-flux[fmin])
    zero_flux = flux[fmax]
    return zero_flux, period

class Qfactor():
    #Class for the resonator quality-factor analisys
    def __init__(self, file_name, Att = -74):
        self.file_name = file_name #full path and name of .mat file for analysis
        self.mat_STS = sio.loadmat(self.file_name)
        self.power = self.mat_STS['power'].T
        self.flux = self.mat_STS['flux'].T
        self.Att = Att #Full attenuation between VNA and the sample
        
        if self.flux.shape==(1,1):
            self.x = np.squeeze(self.power)
            self.xlabel = 'Power, dBm'
        elif self.power.shape==(1,1):
            self.x = np.squeeze(self.flux)
            self.power = np.squeeze(np.ones(len(self.x))*self.power)
            self.xlabel = 'Coil current, mA'
        else:
            return('Can not recognize sweep type!')
        
    def find_files(self):
        pass
    
    def corr_base_level(self):
        N_fscan = len(self.mat_STS['freq_scan'].T)
        for i in range(len(self.x)):
            M_start = self.mat_STS['mag_2darray'][i,0]
            M_stop = self.mat_STS['mag_2darray'][i,-1]
            offset = np.linspace(M_start, M_stop, num = N_fscan)-(M_stop+M_start)/2
            mag_corr = self.mat_STS['mag_2darray'][i,:]-offset
            self.mat_STS['mag_2darray'][i,:] = mag_corr
    
    def calc(self, N):
        self.N = N #number of points both side around minimum 
        self.port = self.res_fit_STS(self.mat_STS, self.N) #fit calculation
        #extracting of the most interesting data
        fr = []
        Ql = []
        Qc = []
        Qi = []
        n_av = []
        
        fr_err = []
        Ql_err = []
        Qc_err = []
        Qi_err = []


        for i in range(0, len(self.port)):
            fr.append(self.port[i].fitresults['fr']/1e9)
            Ql.append(self.port[i].fitresults['Ql'])
            Qc.append(self.port[i].fitresults['absQc'])
            Qi.append(self.port[i].fitresults['Qi_dia_corr'])
            n_av.append(self.port[i].get_photons_in_resonator(self.Att+self.power[i],unit='dBm',diacorr=True)/4)
        
            fr_err.append(self.port[i].fitresults['fr_err']/1e9)
            Ql_err.append(self.port[i].fitresults['Ql_err'])
            Qc_err.append(self.port[i].fitresults['absQc_err'])
            Qi_err.append(self.port[i].fitresults['Qi_dia_corr_err'])
            
        self.fr = np.array(fr)
        self.Ql = np.array(Ql)
        self.Qc = np.array(Qc)
        self.Qi = np.array(Qi)
        self.n_av = np.array(n_av)
        
        self.fr_err = np.array(fr_err)
        self.Ql_err = np.array(Ql_err)
        self.Qc_err = np.array(Qc_err)
        self.Qi_err = np.array(Qi_err)
        
    # def res_fit_STS(self, mat_data, N = 60):
    #     x = self.x
    #     freq = mat_data['freq_scan'].T
    
    #     Mfreq = []
    #     port = []
    
    #     for i in range(0, len(x)):
    #         mag = mat_data['mag_2darray'][i,:]
    #         pha = mat_data['pha_2darray'][i,:]
        
    #         min_point = np.argmin(mag)
    #         Mfreq.append(freq[min_point])
        
    #         mag_cat = mag[min_point-N:min_point+N]
    #         pha_cat = pha[min_point-N:min_point+N]
    #         freq_cat = freq[min_point-N:min_point+N].reshape((-1,))
    #         s21_i = (10**(mag_cat/20)*np.exp(1j*pha_cat)).T
    #         port1 = circuit.notch_port()
    #         port1.add_data(freq_cat,s21_i)
    #         port1.autofit()
    #         port.append(port1)
        
    #     return port

    def plot_Q(self):
        #simple plot of the Q-factors
        fig = plt.figure()
        plt.plot(self.x, self.Ql)
        plt.fill_between(self.x, self.Ql-self.Ql_err, self.Ql+self.Ql_err, alpha = 0.2)
        
        plt.plot(self.x, self.Qc)
        plt.fill_between(self.x, self.Qc-self.Qc_err, self.Qc+self.Qc_err, alpha = 0.2)
        
        plt.plot(self.x, self.Qi)
        plt.fill_between(self.x, self.Qi-self.Qi_err, self.Qi+self.Qi_err, alpha = 0.2)
        
        plt.xlabel(self.xlabel)
        plt.ylabel('Q-factor')
        
        plt.legend(['$Q_l$', '$Q_{ext}$', '$Q_{int}$'])

    def plot_f(self):
        #simple plot of the resonator frequency
        plt.plot(self.x, self.fr)
        plt.fill_between(self.x, self.fr-self.fr_err, self.fr+self.fr_err, alpha = 0.2)
        
        plt.xlabel(self.xlabel)
        plt.ylabel('Frequency, GHz')
        
    def plot_data(self):
        #heat map plot of initial data
        mag = self.mat_STS['mag_2darray']
        x_count = self.x
        freq_count = self.mat_STS['freq_scan']

        cax = plot_2d(x_count, freq_count/1e9, mag)
        
        plt.xlabel(self.xlabel)
        plt.ylabel('Frequency, GHz')
        
        return cax
    
    def save_data(self, name):
        #save into the file frequency and quality factors with fit errors
        Data = np.column_stack((self.x, self.fr, self.Ql, self.Qc, self.Qi, self.Ql_err, self.Qc_err, self.Qi_err, self.fr_err))
        f = open(name, 'w')
        np.savetxt(f, Data, header = self.xlabel + '    Power     Freq    Ql   Qc   Qi   Ql_err    Qc_err     Qi_err     fr_err')
        f.close()
        
        
class Resonator_T_P():
    def __init__(self, file_name_list, Temp, Att = -75):
        self.T = np.array(Temp)*1e-3
        self.N_temp = len(Temp)
        
        self.Res = []
        for i in range(self.N_temp):
            self.Res.append(Qfactor(file_name_list[i], Att = Att))
        
        self.power = self.Res[0].x
        self.N_power = len(self.power)
        
        print('Data was added. Total attenuation %f dBm.' %Att )
    
    def fit_data(self, corr = 'no', N = 500):
        if corr == 'yes':
            print('Correction applyed')
        elif corr == 'no':
            print('No correction')
        else:
            print('Invalid corr command format')
            
        for i in range(self.N_temp):
            if corr == 'yes':
                self.Res[i].corr_base_level()
            self.Res[i].calc(N)
        
        return('Resonator fit in window +-%f.' %N)
        
    def make_data_array(self):
        self.fr = np.zeros((self.N_temp, self.N_power))
        self.fr_err = np.zeros((self.N_temp, self.N_power))
        
        self.Ql = np.zeros((self.N_temp, self.N_power))
        self.Ql_err = np.zeros((self.N_temp, self.N_power))
        
        self.Qc = np.zeros((self.N_temp, self.N_power))
        self.Qc_err = np.zeros((self.N_temp, self.N_power))
        
        self.Qi = np.zeros((self.N_temp, self.N_power))
        self.Qi_err = np.zeros((self.N_temp, self.N_power))
        
        self.n_av = np.zeros((self.N_temp, self.N_power))
        
        for i in range(self.N_temp):
            for k in range(self.N_power):
                self.fr[i,k] = self.Res[i].fr[k]
                self.fr_err[i,k] = self.Res[i].fr_err[k]
        
                self.Ql[i,k] = self.Res[i].Ql[k]
                self.Ql_err[i,k] = self.Res[i].Ql_err[k]
        
                self.Qc[i,k] = self.Res[i].Qc[k]
                self.Qc_err[i,k] = self.Res[i].Qc_err[k]
        
                self.Qi[i,k] = self.Res[i].Qi[k]
                self.Qi_err[i,k] = self.Res[i].Qi_err[k]
        
                self.n_av[i,k] = self.Res[i].n_av[k]
                
    def fit_fTdep(self):
        p0 = np.array([1e-5, self.fr[0,0]])
        
        self.fT_popt = np.zeros((len(p0), self.N_power))
        self.fT_pcov = np.zeros((len(p0), len(p0), self.N_power))
        self.fT_perr = np.zeros((len(p0), self.N_power))
        
        self.fit_fT_result = []
        
        for k in range(self.N_power):
            freq = self.fr[:,k]
            
            def helper_df_TLS(T, delta, f0):
                F = []
                for i in range(len(T)):
                    F.append(df_TLS(T[i], freq[i], delta))
                return f0*(np.array(F)+1)
            
            self.fT_popt[:,k], self.fT_pcov[:,:,k] = curve_fit(helper_df_TLS, self.T, freq, p0 = p0)
            self.fT_perr[:,k] = np.sqrt(np.diag(self.fT_pcov[:,:,k]))
            
            self.fit_fT_result.append(helper_df_TLS(self.T, self.fT_popt[0,k], self.fT_popt[1,k]))
            
    def fit_QTdep(self, func = 'corr', p0 = np.array([1e-4, 100, 1e-4]), bounds = ([0.,0.1,0],[1e-3,1e4,1e-3])):
        #p0 = np.array([1e-4, 100])
        #bounds = ([0.,0.1,0],[1e-3,1e4,1e-3])

        self.QT_popt = np.zeros((len(p0), self.N_power))
        self.QT_pcov = np.zeros((len(p0), len(p0), self.N_power))
        self.QT_perr = np.zeros((len(p0), self.N_power))
        
        self.fit_QT_result = []
        

        for k in range(self.N_power):
            freq = self.fr[:,k]
        
            def helper_QTLS_corr(T, delta, A, Q0):
                F = []
                for i in range(len(T)):
                    F.append(QTLS_corr(T[i], freq[i], delta, A))
                return (np.array(F)+Q0)*1e-4
        
            self.QT_popt[:,k], self.QT_pcov[:,:,k] = curve_fit(helper_QTLS_corr, self.T, 1/self.Qi[:,k], p0 = p0, bounds = bounds)
            self.QT_perr[:,k] = np.sqrt(np.diag(self.QT_pcov[:,:,k]))
            p0 = self.QT_popt[:,k]
            
            self.fit_QT_result.append(1/helper_QTLS_corr(self.T, self.QT_popt[0,k], self.QT_popt[1,k], self.QT_popt[2,k]))
            
    def fit_QPdep(self, beta = 1):
        p0 = np.array([3000, 1e-4])
        
        self.QP_popt = np.zeros((len(p0), self.N_temp))
        self.QP_pcov = np.zeros((len(p0), len(p0), self.N_temp))
        self.QP_perr = np.zeros((len(p0), self.N_temp))
        
        self.fit_QP_result = []
        
        #beta = 0.73
            
        def helper_QTLS_pow(n_av, n_c, Delta):
            return QTSL_pow(n_av, n_c, beta, Delta)
        
        for i in range(len(self.T)):
            self.QP_popt[:,i], self.QP_pcov[:,:,i] = curve_fit(helper_QTLS_pow, self.n_av[0,:], 1/self.Qi[i,:], p0 = p0)
            self.QP_perr[:,i] = np.sqrt(np.diag(self.QP_pcov[:,:,i]))
            
            self.fit_QP_result.append(1/helper_QTLS_pow(self.n_av[0,:], self.QP_popt[0,i], self.QP_popt[1,i]))
            