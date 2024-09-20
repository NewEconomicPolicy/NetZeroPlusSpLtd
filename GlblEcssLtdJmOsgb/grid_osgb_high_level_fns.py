#-------------------------------------------------------------------------------
# Name:        grid_osgb_high_level_fns.py
# Purpose:     consist of high level functions invoked by main GUI
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
# Description:#
#-------------------------------------------------------------------------------
#
__prog__ = 'grid_osgb_high_level_fns.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

from os.path import isdir, join, isfile
from os import listdir, makedirs
from PyQt5.QtWidgets import QApplication
from time import time
from glob import glob
from shutil import move as move_file
from shutil import copyfile, copytree, copy as copy_file

from cvrtcoord import OSGB36toWGS84
from grid_osgb_classes_and_fns import ClimGenNC, fetch_cell_ecss_data, fetch_ncells_aoi, fetch_dir_locations
from make_ltd_data_files_osgb import MakeLtdDataFiles
from prepare_ecss_files_from_cell import make_ecss_files_from_cell, update_progress

WARN_STR = '*** Warning *** '

MASK_FLAG = False

def make_grid_cell_sims(form):
    """
    called from GUI
    """
    ret_code = fetch_dir_locations(form)
    if ret_code is None:
        return False

    lta_dir, rcp_dir, rcp_realis, plnt_inpt_dir, n_cells_max = ret_code

    if form.hwsd_drvr_data is None:
        print(WARN_STR + 'No driver data - cannot proceed')
        QApplication.processEvents()
        return False

    if len(glob(join(form.w_pi_dir.text(), '*.csv'))) == 0:
        print(WARN_STR + 'No plant input files - cannot proceed')
        QApplication.processEvents()
        return False

    # ==================================
    print(' ')
    QApplication.processEvents()

    climgen = ClimGenNC(form, rcp_realis)   # Initialise the climate data object
    if not climgen.ret_code:
        return False
    ltd_data = MakeLtdDataFiles(form, climgen)     # Initialise the limited data object

    # main loop
    # =========
    not_in_hwsd, built_up, empty_lta, no_plnt_inpt, ncells_vld, icells = 6*[0]
    coord_list = []
    last_time = time()
    ngrid_cells = len(form.hwsd_drvr_data)

    for indx, rec in form.hwsd_drvr_data.iterrows():
        icells += 1
        last_time = update_progress(last_time, form.w_prgrss, ncells_vld, icells, ngrid_cells)

        eastng, nrthng = rec['BNG_X'], rec['BNG_Y']
        coord = rec['UID']

        lta_csv = join(lta_dir, coord + '.csv')
        soil_rec, yrs_pi, wthr_dir = fetch_cell_ecss_data(ltd_data,
                                lta_csv, rcp_dir, plnt_inpt_dir, coord, rec, empty_lta, built_up, no_plnt_inpt)
        if yrs_pi is None:
            continue
        else:
            coord_list.append(coord)
            ncells_vld = len(coord_list)
            lon, lat = OSGB36toWGS84(eastng, nrthng)
            make_ecss_files_from_cell(form, climgen, coord, lta_csv, wthr_dir, ltd_data, lat, lon, soil_rec)

            if ncells_vld >= n_cells_max:
                break
        if ncells_vld >= n_cells_max:
            break

    print('Generated: {} grid cells\tRecords in driver file but not in HWSD file: {}\tBuilt up: {}\tEmpty lta files: {}'
                                                .format(ncells_vld, not_in_hwsd, built_up, empty_lta))
    QApplication.processEvents()

    return True

def adjust_model_switches_files(form):
    """
    move spinup files from grid cells to the spinup path
    """
    study = form.w_study.text()
    study_dir = join(form.sttngs['sims_dir'], study)
    dir_list = listdir(study_dir)

    if form.w_spin_save.isChecked():
        spin_mode = '2'
    elif form.w_spin_read.isChecked():
        spin_mode = '1'
    else:
        spin_mode = '0'

    nadjust = 0
    nspin = 0
    for coord in dir_list:
        sim_dir = join(study_dir, coord)
        if isdir(sim_dir):

            mdl_swtchs_fn = join(sim_dir,'Model_Switches.dat')
            if isfile(mdl_swtchs_fn):

                with open(mdl_swtchs_fn, 'r') as finp:
                    lines = finp.readlines()

                lines[15] = spin_mode + lines[15][1:]
                with open(mdl_swtchs_fn, 'w') as finp:
                    rc = finp.writelines(lines)

                nadjust += 1

                # copy spinup
                # ===========
                if spin_mode == '1':
                    spin_dir = form.w_spin_dir.text()
                    spin_ref_fn = join(spin_dir, 'spinup_' + coord + '.dat')
                    if isfile(spin_ref_fn):
                        spin_fn = join(sim_dir, 'spinup.dat')
                        copy_file(spin_ref_fn, spin_fn)
                        nspin += 1
                    else:
                        print(spin_ref_fn + ' does not exist')
                        QApplication.processEvents()

    print('Adjusted {} Model Switches and copied {} spinup files'.format(nadjust, nspin))
    QApplication.processEvents()

    return

def move_spinup_files(form):
    """
    move spinup files from grid cells to the spinup path
    """
    study = form.w_study.text()
    study_dir = join(form.sttngs['sims_dir'], study)
    dir_list = listdir(study_dir)
    spin_dir = form.w_spin_dir.text()
    if not isdir(spin_dir):
        makedirs(spin_dir)
        print('Created ' + spin_dir)

    imove = 0
    for dirn in dir_list:
        dirn_full = join(study_dir, dirn)
        if isdir(dirn_full):
            spinup_fn = join(dirn_full, 'spinup.dat')
            if isfile(spinup_fn):
                spin_ref_fn = join(spin_dir, 'spinup_' + dirn + '.dat')
                try:
                    move_file(spinup_fn, spin_ref_fn)
                except PermissionError as err:
                    form.lgr.info(str(err))
                else:
                    imove += 1

    print('Moved {} spinup files to {}'.format(imove, spin_dir))
    QApplication.processEvents()

    return
def make_bbox_sims(form):
    """
    called from GUI
    """
    ret_code = fetch_dir_locations(form)
    if ret_code is None:
        return False

    lta_dir, rcp_dir, rcp_realis, plnt_inpt_dir, n_cells_max = ret_code

    ngrid_cells, nrth_ur, nrth_ll, east_ur, east_ll = fetch_ncells_aoi(form)

    # ==================================
    climgen = ClimGenNC(form, rcp_realis)  # Initialise the climate data object
    if not climgen.ret_code:
        return False
    ltd_data = MakeLtdDataFiles(form, climgen)     # Initialise the limited data object

    # main loops
    # ==========
    not_in_hwsd, built_up, empty_lta, no_plnt_inpt, ncells_vld, icells = 6 * [0]
    coord_list = []
    last_time = time()
    for nrthng in range(nrth_ll, nrth_ur, 1000):
        for eastng in range(east_ll, east_ur, 1000):
            icells += 1
            last_time = update_progress(last_time, form.w_prgrss, ncells_vld, icells, ngrid_cells)

            # coordinate must be present in the HWSD driver dataframe
            # =======================================================
            coord = str(eastng) + '_' + str(nrthng)
            rec_df = form.hwsd_drvr_data.loc[form.hwsd_drvr_data['UID'] == coord]
            if rec_df.shape[0] == 0:
                not_in_hwsd += 1
                continue

            for indx, rec in rec_df.iterrows():     # returns a Series
                pass

            lta_csv = join(lta_dir, coord + '.csv')
            soil_rec, yrs_pi, wthr_dir = fetch_cell_ecss_data(ltd_data,
                                    lta_csv, rcp_dir, plnt_inpt_dir, coord, rec, empty_lta, built_up, no_plnt_inpt)
            if yrs_pi is None:
                continue
            else:
                coord_list.append(coord)
                ncells_vld = len(coord_list)
                if ncells_vld >= n_cells_max:
                    break

                lon, lat = OSGB36toWGS84(eastng, nrthng)
                make_ecss_files_from_cell(form, climgen, coord, lta_csv, wthr_dir, ltd_data, lat, lon, soil_rec)

        if ncells_vld >= n_cells_max:
            break

    print('Found: {} valid coords\tNot in HWSD file: {}\tBuilt up: {}\tEmpty lta files: {}'
                                                .format(ncells_vld, not_in_hwsd, built_up, empty_lta))
    QApplication.processEvents()

    return True
