# This programe runs imfit

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from astropy.io import fits

import os
import re
import sys
import subprocess
import shutil

import pdb

from py_info import *
from py_conf_imfit import create_conf_imfit
from py_conf_psf import create_conf_psf



def open_fits(fits_path):
    
    fits_name = fits_path.split('/')[-1].split('.')[0]
    # Open the fits with Astropy
    hdu = fits.open(f'{fits_path}')
    hdr = hdu[0].header
    img = hdu[0].data
    
    return (hdr,img,fits_name)


def create_galaxy_folder(galaxy):
    
    # Creating a folder for each galaxy
    galaxy_folder = f'{galaxy}'
    galaxy_folder_path = f'{cwd}/{galaxy_folder}'
    
    # If the folder was created previously is remvoved
    if os.path.isdir(f'{galaxy_folder_path}') == True:
        shutil.rmtree(f'{galaxy_folder_path}')
    os.mkdir(f'{galaxy_folder_path}')

    return galaxy_folder_path


def fits_mag_to_flux(fits_path,inst,zcal):
    
    hdr_mag,img_mag,fits_name = open_fits(fits_path)

    # Flux from magnitudes to counts
    fits_flux_img = 10**((img_mag - 2.5*np.log10(inst**2)-zcal)/-2.5)
    
    # Expoting the new fits
    fits_name = fits_name.split('mag')[0]
    fits_flux_name = f'{fits_name}_counts.fits'
    fits_flux_path = f'{cwd}/{galaxy}/{fits_flux_name}'
    fits.writeto(f'{fits_flux_path}', fits_flux_img, header=hdr_mag, overwrite=True)
    
    return fits_flux_path


def fits_flux_to_mag(fits_path,inst,zcal):
    
    hdr_flux,img_flux,fits_name = open_fits(fits_path)

    # Flux from counts to mag/arcsec^2
    fits_mag_img = -2.5*np.log10(img_flux) - 2.5 * np.log10(inst**2) - zcal
    
    # Expoting the new fits
    fits_name = fits_name.split('counts')[0]
    fits_mag_name  = f'{fits_name}mag.fits'
    fits_mag_path = f'{cwd}/{galaxy}/{fits_mag_name}'
    fits.writeto(f'{fits_mag_path}', fits_mag_img, header=hdr_flux, overwrite=True)
    
    return fits_mag_path  
  

def galaxy_index(df_info,galaxy):

    index = df_info.loc[df_info['galaxy'] == galaxy].index.values[0]
    return index


def create_psf(fits_path,galaxy,df_sky,df_psf):
    
    # Open the fits with Astropy
    hdr,img,fits_name = open_fits(fits_path)
    
    # We are going to create a PSF of the size
    # of the galaxy's image
    x_len = img.shape[1]//2
    y_len = img.shape[0]//2
    
    # We need odd shape because we need to center
    # the PSF
    if x_len%2 == 0:
        x_len += 1
    elif y_len%2 == 0:
        y_len += 1
        
    max_len = min(x_len,y_len)
    x_len = max_len
    y_len = max_len
        
    x_center = x_len/2 + 0.5
    y_center = y_len/2 + 0.5
    
    # These are the size parameters for the PSF
    psf_shape = (x_len,y_len)
    psf_center = (x_center,y_center)
    
    # Moffat psf parameters in pixeles
    galaxy_sky_index = galaxy_index(df_sky,galaxy)
    inst_arcsec_pix = df_sky.loc[galaxy_sky_index]['inst']
    
    # Original value in arcsec
    galaxy_psf_index = galaxy_index(df_psf,galaxy)
    fwhm_value_arcsec = df_psf.loc[galaxy_psf_index]['FWHM_i']
    beta_value_arcsec = df_psf.loc[galaxy_psf_index]['Beta_i']
    
    # Changing to pix
    fwhm_value_pix = fwhm_value_arcsec / inst_arcsec_pix
    beta_value_pix = beta_value_arcsec / inst_arcsec_pix
    
    # Creating the configuration script for the psf
    psf_conf_file_name = f'{galaxy}_conf_psf.txt'
    psf_conf_file_path = f'{cwd}/{galaxy}/{psf_conf_file_name}'
    psf_conf_file = open(psf_conf_file_path,'w+')
    create_conf_psf(file=psf_conf_file,
                     galaxy = galaxy,
                     shape = psf_shape,
                     center = psf_center,
                     fwhm = fwhm_value_pix,
                     beta = beta_value_pix
                     )
    psf_conf_file.close()
    
    # Creating the PSF
    fits_psf_name = f'{galaxy}_psf.fits'
    fits_psf_path = f'{cwd}/{galaxy}/{fits_psf_name}'

    subprocess.run(['makeimage',
                    psf_conf_file_path,
                    '-o', fits_psf_path])
    
    # Opening the psf to normalizate it
    hdr_psf,img_psf,fits_name = open_fits(fits_psf_path)
    
    # Dividing between the total flux
    psf_total_flux = np.nansum(img_psf)
    img_psf_norm = img_psf / psf_total_flux
    
    # Saving the results
    fits_psf_norm_name = f'{galaxy}_psf_norm.fits'
    fits_psf_norm_path = f'{cwd}/{galaxy}/{fits_psf_norm_name}'
    
    fits.writeto(f'{fits_psf_norm_path}',img_psf_norm,hdr_psf,overwrite=True)

    return fits_psf_norm_path


def main(gal_pos,galaxy):
    
    # Creating a folder for each galaxy
    galaxy_folder_path = create_galaxy_folder(galaxy)
    
    # Fits file to analyze
    fits_file = fits_image_list[gal_pos]
    fits_path = f'{files_path}/{fits_file}'
    
    # Opening the galaxy image 
    hdr_gal,img_gal,fits_name = open_fits(fits_path)

    # obtaining the shape of the fits
    x_len = img_gal.shape[1]
    y_len = img_gal.shape[0]
    
    # Mask file 
    mask_file = fits_mask_list[gal_pos]
    mask_path = f'{files_path}/{mask_file}'
    
    # Opening the mask
    hdr_mask,img_mask,mask_name = open_fits(mask_path)
    
    # Changing from 0/1 mask to True/False mask
    img_mask = img_mask == 0
    
    # OBTAINING THE CENTER OF THE GALAXY
    
    # Cropping to focus on the galaxy center
    # For a centered image of a galaxy
    crop_factor = 10
    x_len_crop = (x_len//crop_factor)
    y_len_crop = (y_len//crop_factor)
    
    img_crop_center = img_gal[x_len//2 - x_len_crop:x_len//2 + x_len_crop, y_len//2 - y_len_crop:y_len//2 + y_len_crop]
    max_pix_value_center = np.nanmax(img_crop_center)
    
    # For a non centered image galaxy or for a masked one 
    # Applying the mask to the image to remove stars
    img_gal_mask = img_gal[img_mask]

    # Finding the value in the image
    max_pix_value_center = np.nanmax(img_gal_mask)
    x_center = np.where(img_gal == max_pix_value_center)[1][0]+1
    y_center = np.where(img_gal == max_pix_value_center)[0][0]+1

    # How much deviation we allow for the center
    center_dev = 1
    
    # Position angle
    pos_ang = [105,0,180]
    
    # Ellipticity
    ellip = [0.5,0,180]
    
    # SERSIC FUNCTION: Bulge
    # Sersic Index
    ser_ind = [2,0.6,6]
    
    # Effective Raidus
    rad_ef = [60,0,200]
    # Intensity at effective radius
    int_ef = [120,0,200]
    
    # EXPONENTIAL FUNCTION: Disk
    # Center intensity
    I_0_disk = max_pix_value_center
    int_cent = [I_0_disk,0,I_0_disk+I_0_disk*0.1]
    
    # Length scale disk
    len_sca_disk = [80,0,200]
    
    # Configuration file
    conf_file_name = f'{galaxy}_conf_imfit.txt'
    conf_file_path = f'{galaxy_folder_path}/{conf_file_name}'
    conf_file = open(f'{conf_file_path}','w+')
    create_conf_imfit(file=conf_file,
                     funct=['Sersic','Exponential'],
                     galaxy = galaxy,
                     img_center_x = [x_center,x_center-center_dev,x_center+center_dev],
                     img_center_y = [y_center,y_center-center_dev,y_center+center_dev],
                     pos_ang = pos_ang,
                     ellip = ellip,
                     n=ser_ind,
                     r_e=rad_ef,
                     I_e=int_ef,
                     I_0=int_cent,
                     h=len_sca_disk)
    conf_file.close()
    
    # Position of the galaxy in the sky info dataframe
    galaxy_sky_index = galaxy_index(df_sky_info,galaxy)
    
    # Gain value
    gain_value = df_sky_info.loc[galaxy_sky_index]['gain']
    
    # Readnoise value
    noise_value = df_sky_info.loc[galaxy_sky_index]['RON']
    
    # Sky value
    sky_value = df_sky_info.loc[galaxy_sky_index]['sky']
    
    # PSF image
    psf_path = create_psf(fits_path,galaxy,df_sky_info,df_psf_info)
    
    # Output files
    fits_model_name = f'{fits_name}_model_counts.fits'
    fits_model_path = f'{galaxy_folder_path}/{fits_model_name}'
    
    # Output files
    residual_model_name = f'{fits_name}_residual_model_counts.fits'
    residual_model_path = f'{galaxy_folder_path}/{residual_model_name}'

    
    # Changing the directory to run imfit
    os.chdir(f'{galaxy}')
    
    # These lines execute imfit as it was a 
    # terminal command 
    subprocess.run(['imfit',
                    fits_path,
                    '-c', conf_file_path,
                    '--mask',mask_path,
                    '--gain=',f'{gain_value}',
                    '--readnoise=',f'{noise_value}',
                    '--sky',f'{sky_value}',
                    '--psf',psf_path,
                    '--save-model=',fits_model_path,
                    '--save-residual=',residual_model_path])
    
    # Returning to the main directory to continue the programe
    os.chdir(f'{cwd}')
    
    # Instrumental pixel scale
    inst_arcsec_pix = df_sky_info.loc[galaxy_sky_index]['inst']
    
    # Calibration constant
    zcal = df_sky_info.loc[galaxy_sky_index]['zcal']
    
    fits_model_mag_path = fits_flux_to_mag(fits_model_path,inst_arcsec_pix,zcal)
    
    

if __name__ == '__main__':
    
    cwd = os.getcwd()
    galaxy_original_folder = 'galaxy_files'
    files_path = f'{cwd}/{galaxy_original_folder}'
    
    fits_list = []
    fits_image_list = []
    fits_mask_list = []
    galaxy_list = []
    
    for file in sorted(os.listdir(files_path)):
        if '.fits' in file:
        
            fits_list.append(file)
            
            fits_name = file.split('.')[0]
            galaxy = fits_name.split('_')[0]
            
            if galaxy not in galaxy_list:
                galaxy_list.append(galaxy)
            
            if '_i.fits' in file:
                fits_image_list.append(file)
            elif '_mask' in file:
                fits_mask_list.append(file)
                
        elif '.csv' in file and 'info' in file:
            csv_path = f'{files_path}/{file}'
            if 'sky' in file:
                df_sky_info = sky_info(csv_path)
            elif 'psf' in file:
                df_psf_info = psf_info(csv_path)
    
    if len(galaxy_list) != 0:
        for gal_pos,galaxy in enumerate(galaxy_list):
            main(gal_pos,galaxy)        
    
    else:
        
        print('There is no galaxies in the directory')