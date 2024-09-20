"""
#-------------------------------------------------------------------------------
# Name:        prepareEcosseFiles.py
# Purpose:
# Author:      s03mm5
# Created:     08/12/2015
# Copyright:   (c) s03mm5 2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#
"""
__version__ = '1.0.00'
__prog__ = 'prepare_ecosse_files.py'

# Version history
# ---------------
#
from os.path import join, lexists, basename, isdir, isfile
from os import makedirs
from shutil import copyfile, copytree, copy as copy_file
from time import time

from PyQt5.QtWidgets import QApplication

from grid_osgb_classes_and_fns import read_lta_file
from glbl_ecss_cmmn_funcs import write_kml_file, write_manifest_file, input_txt_line_layout, write_signature_file

sleepTime = 5

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

def make_ecss_files_from_cell(form, climgen, coord, lta_csv,  wthr_dir, ltd_data, lat, lon, soil_rec):
    """
    generate sets of Ecosse files for a site
    """
    func_name = 'make_ecss_files_from_cell'

    area = 1
    province = 'Unknown'


    sims_dir = climgen.sims_dir
    fut_clim_scen = climgen.fut_clim_scen

    # write stanza for input.txt file consisting of long term average climate
    # =======================================================================
    lta = read_lta_file(lta_csv)
    hist_wthr_recs = []
    for imnth, month in enumerate(climgen.months):
        hist_wthr_recs.append(input_txt_line_layout('{}'.format(lta['precip'][imnth]), \
                                            '{} long term average monthly precipitation [mm]'.format(month)))

    for imnth, month in enumerate(climgen.months):
        hist_wthr_recs.append(input_txt_line_layout('{}'.format(lta['tas'][imnth]), \
                                            '{} long term average monthly temperature [degC]'.format(month)))

    # Create simulation input files
    # =============================
    area_for_soil = area
    sim_dir = join(sims_dir, climgen.study, coord)
    if not lexists(sim_dir):
        makedirs(sim_dir)

    # met_rel_path = '..\\..\\' + climgen.rcp_realis + '\\' + coord + '\\'
    wthr_node_path = climgen.rcp_realis + '\\' + coord + '\\'
    met_rel_path = '..\\..\\' + wthr_node_path
    ltd_data.write(sim_dir, soil_rec, lat, hist_wthr_recs, met_rel_path)

    sims_wthr_dir = join(sims_dir, wthr_node_path)
    if not isdir(sims_wthr_dir):
        copytree(wthr_dir, sims_wthr_dir)

    # write kml and signature files
    # =============================
    write_kml_file(sim_dir, coord, coord, lat, lon)
    write_signature_file(sim_dir, coord, soil_rec, lat, lon, province)

    # copy across Model_Switches.dat file
    # ===================================
    out_mdl_swtchs = join(sim_dir, basename(form.sttngs['dflt_mdl_swtchs']))
    copyfile(form.sttngs['dflt_mdl_swtchs'], out_mdl_swtchs)

    # manifest file is essential for subsequent processing
    # ====================================================
    soil_list = list([soil_rec + [100.0]])
    write_manifest_file(form.study, fut_clim_scen, sim_dir, soil_list, coord, lat, lon, area_for_soil, osgb_flag=True)

    return

def update_progress(last_time, w_prgrss, ncells_vld, icells, ngrid_cells):
    """

    """
    new_time = time()
    if new_time - last_time > 5:
        prcnt_cells = round(100* (icells/ngrid_cells), 2)
        w_prgrss.setText('Found: {} valid coords\t% cells processed: {}'.format(ncells_vld, prcnt_cells))
        QApplication.processEvents()
        last_time = new_time

    return last_time