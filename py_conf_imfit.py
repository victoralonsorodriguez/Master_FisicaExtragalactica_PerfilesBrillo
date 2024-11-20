
# This file creates the required template for Galfit
def create_conf_imfit(file,funct,galaxy,img_center_x,img_center_y,pos_ang,ellip,
                     n=[None,None,None],I_e=[None,None,None],r_e=[None,None,None],I_0=[None,None,None],h=[None,None,None]):
	
    if len(funct) != 0:
        
        file.write(f'# Configuration file for the galaxy {galaxy}\n')
        file.write(f'X0    {img_center_x[0]}    {img_center_x[1]},{img_center_x[2]}\n')
        file.write(f'Y0    {img_center_y[0]}    {img_center_y[1]},{img_center_y[2]}\n')

        for f in funct:
            if f == 'Sersic':
                file.write(f'FUNCTION {f}\n')
                file.write(f'PA    {pos_ang[0]}    {pos_ang[1]},{pos_ang[2]}\n')
                file.write(f'ell    {ellip[0]}    {ellip[1]},{ellip[2]}\n')
                file.write(f'n    {n[0]}    {n[1]},{n[2]}\n')
                file.write(f'I_e    {I_e[0]}    {I_e[1]},{I_e[2]}\n')
                file.write(f'r_e    {r_e[0]}    {r_e[1]},{r_e[2]}\n')

            
            elif f == 'Exponential':
                file.write(f'FUNCTION {f}\n')
                file.write(f'PA    {pos_ang[0]}    {pos_ang[1]},{pos_ang[2]}\n')
                file.write(f'ell    {ellip[0]}    {ellip[1]},{ellip[2]}\n')
                file.write(f'I_0    {I_0[0]}    {I_0[1]},{I_0[2]}\n')
                file.write(f'h    {h[0]}    {h[1]},{h[2]}\n')

    else:
        print('No functions for the fitting were selected')
        return None
	
	