#-------------------------------------------------------------------------------
# Name:        grid_osgb_classes_and_fns.py
# Purpose:     additional functions for getClimGenNC.py
# Author:      s03mm5
# Created:     08/02/2018
# Copyright:   (c) s03mm5 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

__prog__ = 'grid_osgb_classes_and_fns.py'
__author__ = 's03mm5'

from os import makedirs, listdir
from os.path import isdir, join, isfile
from glob import glob
from math import floor, ceil
from calendar import month_abbr

from pandas import read_csv
from PyQt5.QtWidgets import QApplication

from cvrtcoord import  WGS84toOSGB36

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

WTHR_STRT_YR = 2020
LTA_STRT_YR, LTA_END_YR = (1988, 2018)

SPECIES = {'sitka_spruce': 'SS'}

N_CELLS_MAX_DFLT = 10

def fetch_dir_locations(form):
    """

    """
    try:
        n_cells_max = int(form.w_ncoords.text())
    except ValueError as err:
        print(WARN_STR + str(err) + ' will set maximum xells to {}'.format(N_CELLS_MAX_DFLT))
        n_cells_max = N_CELLS_MAX_DFLT

    rcp_realis = form.w_combo10s.currentText()  + '_' + form.w_combo10r.currentText()
    lta_dir = join(form.sttngs['root_dir'], 'ECOSSE_LTA', rcp_realis)
    rcp_dir = join(form.sttngs['root_dir'], 'ECOSSE_RCP', rcp_realis)
    species = SPECIES['sitka_spruce']

    plnt_inpt_dir = form.w_pi_dir.text()
    if isdir(plnt_inpt_dir):
        form.sttngs['plnt_inpt_dir'] = plnt_inpt_dir
    else:
        print(WARN_STR + 'plant input directory ' + plnt_inpt_dir + ' does not exist')
        QApplication.processEvents()
        return

    return lta_dir, rcp_dir, rcp_realis, plnt_inpt_dir, n_cells_max

def report_spin_dir(form, spin_dir):
    """
    report spinup files
    """
    nspins = len(glob(join(spin_dir, 'spinup_*.dat')))
    form.w_spin_dtls.setText('Spinup files: ' + f'{nspins:,d}' + '\t\t')

    '''
    if nspins == 0:
        form.w_create_files.setEnabled(False)
    else:
        form.w_create_files.setEnabled(True)
    '''
    QApplication.processEvents()

    return

def report_pi_csvs(form, pi_dir):
    """
    report PI CSVs
    """
    ncsvs = len(glob(join(pi_dir, '*.csv')))
    form.w_pi_csvs.setText('PI CSVs: ' + f'{ncsvs:,d}' + '\t\t')
    if ncsvs == 0:
        form.w_create_files.setEnabled(False)
    else:
        form.w_create_files.setEnabled(True)

    QApplication.processEvents()

    return

def make_hwsd_drvr_df(form, hwsd_drvr_data_fn):
    """
     read CSV HWSD driver file using pandas
    """
    if isfile(hwsd_drvr_data_fn):
        print('\nCreating dataframe from CSV HWSD driver file:\n\t' + hwsd_drvr_data_fn)
        QApplication.processEvents()
    else:
        form.hwsd_drvr_data = None
        print(WARN_STR + 'HWSD driver file ' + hwsd_drvr_data_fn + ' does not exist')
        QApplication.processEvents()
        return

    hwsd_drvr_data = read_csv(hwsd_drvr_data_fn, sep = ',')
    nrecs, nmetrics = hwsd_drvr_data.shape
    form.w_hwsd_drvr_fn.setText(hwsd_drvr_data_fn)
    form.w_drvr_dtls.setText('Records: ' + f'{nrecs:,d}' + '\t\t')

    if 'BNG_X' and 'BNG_Y' in hwsd_drvr_data:
        form.hwsd_drvr_data = hwsd_drvr_data
        print('Created dataframe with ' + f'{nrecs:,d}' + ' records and ' + f'{nmetrics:,d}' + ' metrics ')
    else:
        print(WARN_STR + 'Invalid driver file: columns BNG_X and BNG_Y must be present')
        form.hwsd_drvr_data = None

    QApplication.processEvents()

    return

def fetch_ncells_aoi(form):
    """
    use bounding box to calculate number of grid cells
    """
    lon_ll = float(form.w_ll_lon.text())
    lat_ll = float(form.w_ll_lat.text())
    lon_ur = float(form.w_ur_lon.text())
    lat_ur = float(form.w_ur_lat.text())
    form.sttngs['bbox'] = list([lon_ll, lat_ll, lon_ur, lat_ur])

    # use Hannah Fry functions to generate AOI coordinates
    # ====================================================
    eastng_ll, nrthng_ll = WGS84toOSGB36(lon_ll, lat_ll)
    east_ll = 1000 * floor(eastng_ll / 1000) - 500
    nrth_ll = 1000 * floor(nrthng_ll / 1000) - 500

    eastng_ur, nrthng_ur = WGS84toOSGB36(lon_ur, lat_ur)
    east_ur = 1000 * ceil(eastng_ur / 1000) + 500
    nrth_ur = 1000 * ceil(nrthng_ur / 1000) + 500

    ngrid_cells = int(((nrth_ur - nrth_ll) / 1000 - 1) * ((east_ur - east_ll) / 1000 - 1))
    print('Will process AOI comprising: {} cells'.format(ngrid_cells))
    QApplication.processEvents()

    return ngrid_cells, nrth_ur, nrth_ll, east_ur, east_ll

def fetch_cell_ecss_data(ltd_data, lta_csv, rcp_dir, plnt_inpt_dir, coord, rec, empty_lta, built_up, no_plnt_inpt):
    """
     rec is a dataframe
    """
    soil_rec = None
    yrs_pi = None
    wthr_dir = None
    if isfile(lta_csv):
        if _check_lta_file(lta_csv):
            wthr_dir = join(rcp_dir, coord)
            if isdir(wthr_dir):
                ecss_lu, soil_rec = _fetch_hwsd_data_from_rec(rec)
                if ecss_lu == 0:
                    built_up += 1
                else:
                    plnt_inpt_csv = join(plnt_inpt_dir, coord + '.csv')
                    if isfile(plnt_inpt_csv):
                        yrs_pi = _read_plnt_inpt_csv_file(plnt_inpt_csv)
                        ltd_data.add_lus_and_pis(ecss_lu, yrs_pi)
                    else:
                        no_plnt_inpt += 1
        else:
            empty_lta += 1

    return soil_rec, yrs_pi, wthr_dir

def read_lta_file(lta_csv):
    """
    assumes LTA file is validated via function _check_lta_file
    """
    df = read_csv(lta_csv, sep = ',')
    lta = {}
    lta['precip'] = df['mean_precip_mm'].to_list()
    lta['tas'] = df['mean_Tair_degC'].to_list()

    return lta

def _check_lta_file(lta_csv):
    """

    """
    valid_flag = True
    with open(lta_csv, 'r') as fobj:
        lines = [line.strip() for line in fobj]

    rec_list = lines[1].split(',')
    if rec_list[-1] == 'NA':
        valid_flag = False

    return valid_flag

def _read_plnt_inpt_csv_file(plnt_inpt_csv):
    """

    """
    yrs_pi = None

    df = read_csv(plnt_inpt_csv)
    yrs = df['year'].to_list()
    pis = df['PI_kg_ha'].to_list()
    yrs_pi = {'yrs': yrs, 'pis': pis}

    return yrs_pi

def _fetch_hwsd_data_from_rec(rec):
    """
     rec is a Series
    """
    vals = rec.to_dict()
    if 'ECOSSE_lu_code' in vals:
        ecss_lu = vals['ECOSSE_lu_code']
    else:
        ecss_lu = vals['ECOSSE_land_use_code']

    s_bulk = vals['S_BULK_DENSITY']
    s_clay = vals['S_CLAY']
    s_ph_h2o = vals['S_PH_H2O']
    s_sand = vals['S_SAND']
    s_silt = vals['S_SILT']
    s_soc_kg_ha = vals['S_soc_kg_ha']
    t_bulk = vals['T_BULK_DENSITY']
    t_clay = vals['T_CLAY']
    t_ph_h2o = vals['T_PH_H2O']
    t_sand = vals['T_SAND']
    t_silt = vals['T_SILT']
    t_soc_kg_ha = vals['T_soc_kg_ha']

    soil_rec = list([s_soc_kg_ha, s_bulk, s_ph_h2o, s_clay, s_sand, s_silt,
                     t_soc_kg_ha, t_bulk, t_ph_h2o, t_clay, t_sand, t_silt])
    return ecss_lu, soil_rec

class ClimGenNC(object,):

    def __init__(self, form, rcp_realis, wthr_rsrc = 'CHESS'):
        """
        # typically form.inpnc_dir = r'E:\mark2mike\climgenNC'  (get climgen future climate netCDF4 data from here)
        #           form.inp_hist_dir = r'E:\mark2mike\fut_data'  (get CRU historic climate netCDF4 data from here)
        """
        func_name =  __prog__ +  ' ClimGenNC __init__'

        ret_code = True

        if wthr_rsrc != 'CHESS':
            print('weather resource ' + wthr_rsrc + ' not recognised in ' + func_name + ' - cannot continue')
            QApplication.processEvents()
            ret_code = False

        # determine user choices
        # ======================
        fut_clim_scen = form.w_combo10s.currentText()
        realis = form.w_combo10r.currentText()
        hist_strt_yr = LTA_STRT_YR
        hist_end_yr = LTA_END_YR
        ave_wthr_flag = False

        # read a plant input file to get start and end years
        # ==================================================
        plnt_inpt_dir = form.w_pi_dir.text()
        coord_dirs = listdir(plnt_inpt_dir)
        coord_fn = coord_dirs[0]
        plnt_inpt_csv = join(plnt_inpt_dir, coord_fn)
        yrs_pi = _read_plnt_inpt_csv_file(plnt_inpt_csv)
        sim_strt_yr = yrs_pi['yrs'][0] - 1  # first year is for existing land use
        sim_end_yr = yrs_pi['yrs'][-1]

        if sim_strt_yr < WTHR_STRT_YR:
            mess = 'simulation start year {} is before weather start year {}'.format(sim_strt_yr, WTHR_STRT_YR)
            print(WARN_STR + mess + ' cannot proceed')
            QApplication.processEvents()
            ret_code = False

        # TODO: needs tidying
        # ===================
        study = form.w_study.text()
        study_dir = join(form.sttngs['sims_dir'], study)
        if not isdir(study_dir):
            makedirs(study_dir)
            print('Created simulations dir: ' + study_dir)

        self.study = study
        self.sims_dir = form.sttngs['sims_dir']
        self.wthr_rsrc = wthr_rsrc
        self.rcp_realis = rcp_realis
        self.w_prgrss = form.w_prgrss
        try:
            self.max_cells = int(form.w_ncoords.text())
        except ValueError as err:
            self.max_cells = 10

        self.lgr = form.lgr

        # make sure start and end years are within dataset limits
        # =======================================================
        self.ave_wthr_flag = ave_wthr_flag
        self.nhist_yrs = hist_end_yr - hist_strt_yr + 1
        self.hist_strt_yr = hist_strt_yr
        self.hist_end_yr   = hist_end_yr
        self.months = [mnth for mnth in month_abbr[1:]]

        self.fut_clim_scen = fut_clim_scen
        wthr_rsrc_key = 'chess_' + fut_clim_scen + '_' + realis
        self.wthr_rsrc_key = wthr_rsrc_key

        self.mnthly_flag = True

        self.nsim_yrs = sim_end_yr - sim_strt_yr + 1
        self.sim_strt_yr = sim_strt_yr
        self.sim_end_yr  = sim_end_yr
        self.sim_yrs = [yr for yr in range(sim_strt_yr, sim_end_yr + 1)]

        self.ret_code = ret_code
