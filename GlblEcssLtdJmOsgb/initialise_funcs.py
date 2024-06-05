"""
#-------------------------------------------------------------------------------
# Name:        initialise_funcs.py
# Purpose:     script to read and write the setup and configuration files
# Author:      Mike Martin
# Created:     31/07/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
"""

__prog__ = 'initialise_funcs.py'
__version__ = '0.0.0'

# Version history
# ---------------
# 
from os.path import exists, normpath, isfile, isdir, join, lexists, split, splitext
from os import getcwd, remove, makedirs, name as os_name
from json import load as json_load, dump as json_dump
from json.encoder import JSONEncoder
from json.decoder import JSONDecodeError

from time import sleep
import sys

from PyQt5.QtWidgets import QApplication

from glbl_ecss_cmmn_funcs import build_and_display_studies, check_sims_dir, check_runsites, fetch_notepad_path
from glbl_ecss_cmmn_cmpntsGUI import print_resource_locations
from set_up_logging import set_up_logging

from grid_osgb_classes_and_fns import make_hwsd_drvr_df
from shape_funcs import format_bbox, calculate_area

WARN_STR = '*** Warning *** '
ERROR_STR = '*** Error *** '
BBOX_DEFAULT = [-4.8, 52.54, -3.42, 53.33] # lon_ll, lat_ll, lon_ur, lat_ur - Gwynedd, Wales
sleepTime = 5

MNDTRY_GRPS_SETUP = ['glbl_ecss_sttngs', 'osgb_setup']
GLBL_ECSS_STTNGS = ['config_dir', 'fname_png', 'log_dir', 'python_exe', 'runsites_py', 'sims_dir']
OSGB_SETUP = ['hwsd_driver_data', 'lta_dir', 'rcp_dir', 'root_dir']

MNDTRY_GRPS_CONFIG = ['cmnGUI', 'minGUI']
MIN_GUI_LIST = ['wthrRsrce', 'bbox', 'use_drvr_flag']
CMN_GUI_LIST = ['study', 'climScnr', 'realis', 'eqilMode', 'hwsd_drvr_fn', 'n_coords', 'test_data_dir']

# ==============================================================

def initiation(form):
    """
    this function is called to initiate the programme to process non-GUI settings.
    """
    glbl_ecsse_str = 'global_ecosse_config_hwsd_'
    fname_setup = 'glbl_ecss_setup_ltd_jm_osgb.json'

    # retrieve settings
    # =================
    form.sttngs = _read_setup_file(form, fname_setup)
    form.sttngs['glbl_ecsse_str'] = glbl_ecsse_str
    fetch_notepad_path(form.sttngs)

    config_files = build_and_display_studies(form, glbl_ecsse_str)
    if len(config_files) > 0:
        form.sttngs['config_fn'] = config_files[0]
    else:
        form.sttngs['config_fn'] = form.sttngs['config_dir'] + '/' + glbl_ecsse_str + 'dummy.txt'

    fname_model_switches = 'Model_Switches.dat'
    cwDir = getcwd()
    default_model_switches = join(cwDir, fname_model_switches)
    if isfile(default_model_switches):
        form.default_model_switches = default_model_switches
    else:
        print('{0} file does not exist in directory {1}'.format(fname_model_switches,cwDir))
        sleep(sleepTime)
        sys.exit(0)

    if not check_sims_dir(form.lgr, form.sttngs['sims_dir']):
        sleep(sleepTime)
        sys.exit(0)

    # create dump files for grid point with mu_global 0
    form.fobjs = {}
    output_fnames = list(['nodata_muglobal_cells_v2b.csv'])
    if form.sttngs['zeros_file']:
        output_fnames.append('zero_muglobal_cells_v2b.csv')
    for file_name in output_fnames:
        long_fname = join(form.sttngs['log_dir'], file_name)
        key = file_name.split('_')[0]
        if exists(long_fname):
            try:
                remove(long_fname)
            except (PermissionError) as e:
                mess = 'Failed to delete mu global zeros dump file: {}\n\t{} '.format(long_fname, e)
                print(mess + '\n\t- check that there are no other instances of GlblEcosse'.format(long_fname, e))
                sleep(sleepTime)
                sys.exit(0)

        form.fobjs[key] = open(long_fname,'w')

    return

def _read_setup_file(form, fname_setup):
    """
    read settings used for programme from the setup file, if it exists,
    or create setup file using default values if file does not exist
    """
    func_name =  __prog__ +  ' _read_setup_file'

    setup_file = join(getcwd(), fname_setup)
    if exists(setup_file):
        try:
            with open(setup_file, 'r') as fsetup:
                settings = json_load(fsetup)
        except (OSError, IOError) as e:
                sleep(sleepTime)
                exit(0)
    else:
        print(ERROR_STR + 'setup file ' + setup_file + ' must exist')
        sleep(sleepTime)
        exit(0)

    # validate setup file
    # ===================
    mess_setup = 'in setup file:\n\t' + setup_file
    for grp in MNDTRY_GRPS_SETUP:
        if grp not in settings:
            print(ERROR_STR + 'group ' + grp + ' is required' +  mess_setup)
            sleep(sleepTime)
            exit(0)

    # ============================== glbl_ecss_sttngs ============
    grp = 'glbl_ecss_sttngs'
    for key in GLBL_ECSS_STTNGS:
        if key not in settings[grp]:
            print(ERROR_STR + 'setting ' + key + ' is required in group ' + grp + ' +  mess_setup')
            sleep(sleepTime)
            exit(0)

    form.fname_png = settings[grp]['fname_png']

    config_dir = settings[grp]['config_dir']
    if not lexists(config_dir):
        makedirs(config_dir)

    log_dir = settings[grp]['log_dir']
    if not lexists(log_dir):
        makedirs(log_dir)
    #
    form.settings = {}
    form.settings['log_dir'] = log_dir
    set_up_logging(form, 'glbl_ecss_odgb')

    sims_dir = settings[grp]['sims_dir']
    runsites_py = settings[grp]['runsites_py']
    python_exe = settings[grp]['python_exe']

    # additional settings to enable ECOSSE to be run
    # ==============================================
    runsites_cnfg_fn = join(config_dir,'global_ecosse_ltd_data_runsites_config.json')
    sttngs_tmp = {}
    check_runsites(setup_file, sttngs_tmp, config_dir, runsites_cnfg_fn, python_exe, runsites_py)
    settings[grp]['run_ecosse_flag'] = sttngs_tmp['run_ecosse_flag']
    settings[grp]['runsites_cnfg_fn'] = runsites_cnfg_fn
    settings[grp]['zeros_file'] = False   # legacy
    settings[grp]['wthr_rsrc'] = 'CHESS'
    settings[grp]['req_resol_upscale'] = 1
    settings[grp]['stdout_path'] = join(sims_dir, 'stdout.txt')     # location of job output from run sites script

    if settings[grp]['run_ecosse_flag']:
        # ascertain which version of Ecosse is defined in the runsites file
        # =================================================================
        if type(runsites_cnfg_fn) is str:
            with open(runsites_cnfg_fn, 'r') as fconfig:
                config = json_load(fconfig)
                # print('Read config file ' + runsites_cnfg_fn)
        try:
            fn = split(config['Simulations']['exepath'])[1]
        except KeyError as err:
            print(WARN_STR + 'could not identify Ecosse version in run sites file: ' + runsites_cnfg_fn + '\n')
        else:
            settings[grp]['ecosse_exe'] = splitext(fn)[0].lower()
    else:
        settings[grp]['ecosse_exe'] = None

    # ============================== osgb_setup ============
    grp = 'osgb_setup'
    for key in OSGB_SETUP:
        if key not in settings[grp]:
            print(ERROR_STR + 'setting ' + key + ' is required in group ' + grp + ' +  mess_setup')
            sleep(sleepTime)
            exit(0)

    root_dir = settings[grp]['root_dir']
    lta_dir = join(root_dir, settings[grp]['lta_dir'])
    rcp_dir = join(root_dir, settings[grp]['rcp_dir'])
    hwsd_drvr_data_fn = join(root_dir, settings[grp]['hwsd_driver_data'])

    # ==============
    run_sims_flag = True
    mess = ' does not exist - cannot run simulations'
    if isfile(hwsd_drvr_data_fn):
        print('CSV HWSD driver file ' + hwsd_drvr_data_fn + ' exists\n')
    else:
        print('\n' + WARN_STR + 'CSV HWSD driver file ' + hwsd_drvr_data_fn + mess)
        run_sims_flag = False

    # ======= LTA ========
    if not isdir(lta_dir):
        print(WARN_STR + 'LTA NC directory ' + lta_dir + mess)
        run_sims_flag = False

    # weather is crucial
    # ===================
    if not isdir(rcp_dir):
        print(WARN_STR + 'Climate directory {}'.format(rcp_dir) + mess)
        run_sims_flag = False

    print_resource_locations(setup_file, config_dir, hwsd_drvr_data_fn, rcp_dir, lta_dir, sims_dir, log_dir)
    settings[grp]['run_sims_flag'] = run_sims_flag

    # return a single list
    # ====================
    settings['glbl_ecss_sttngs'].update(settings['osgb_setup'])
    return settings['glbl_ecss_sttngs']

def _enable_methodology(form, use_drvr_flag):
    """

    """
    if use_drvr_flag:
        use_bbox_flag = False
    else:
        use_bbox_flag = True

    form.w_ur_lon.setEnabled(use_bbox_flag)
    form.w_ur_lat.setEnabled(use_bbox_flag)
    form.w_ll_lon.setEnabled(use_bbox_flag)
    form.w_ll_lat.setEnabled(use_bbox_flag)

    form.w_drvr_pb.setEnabled(use_drvr_flag)

    return

def read_config_file(form):
    """
    read widget settings used in the previous programme session from the config file, if it exists,
    or create config file using default settings if config file does not exist
    """
    func_name =  __prog__ +  ' read_config_file'

    config_file = form.sttngs['config_fn']
    if exists(config_file):
        try:
            with open(config_file, 'r') as fconfig:
                config = json_load(fconfig)
                print('Read config file ' + config_file)
        except (OSError, IOError) as err:
                print(err)
                return False
    else:
        config = _write_default_config_file(config_file)

    # validate config file
    # ====================
    for grp in MNDTRY_GRPS_CONFIG:
        if grp not in config:
            print(ERROR_STR + 'group {} is required in config file {} '.format(grp, config_file))
            sleep(sleepTime)
            exit(0)

    # ============================== minGUI ============
    grp = 'minGUI'
    for key in MIN_GUI_LIST:
        if key not in config[grp]:
            print(ERROR_STR + 'setting {} is required in configuration file {} '.format(key, config_file))
            form.sttngs['bbox'] = BBOX_DEFAULT
            return False

    use_drvr_flag = config[grp]['use_drvr_flag']
    if use_drvr_flag:
        form.w_use_drvr.setChecked(True)
    else:
        form.w_use_bbox.setChecked(True)
    _enable_methodology(form, use_drvr_flag)

    form.sttngs['bbox'] = config[grp]['bbox']

    # common area
    # ===========
    grp = 'cmnGUI'
    for key in CMN_GUI_LIST:
        if key not in config[grp]:
            if key == 'realis':
                config[grp]['realis'] = '01'
            else:
                print(ERROR_STR + 'in group: {} - setting {} is required in config file {}'.format(grp, key, config_file))
                return False

    form.w_study.setText(str(config[grp]['study']))

    # post weather settings
    # =====================
    form.w_combo10s.setCurrentText(config[grp]['climScnr'])
    form.w_combo10r.setCurrentText(config[grp]['realis'])

    # =====================
    if use_drvr_flag:
        make_hwsd_drvr_df(form, config[grp]['hwsd_drvr_fn'])

    form.w_test_dir.setText(config[grp]['test_data_dir'])
    form.w_equimode.setText(str(config[grp]['eqilMode']))
    form.w_ncoords.setText(config[grp]['n_coords'])

    # ===================
    # bounding box set up
    # ===================
    area = calculate_area(form.sttngs['bbox'])
    ll_lon, ll_lat, ur_lon, ur_lat = form.sttngs['bbox']
    form.w_ur_lon.setText(str(ur_lon))
    form.w_ur_lat.setText(str(ur_lat))
    form.fstudy = ''
    form.w_ll_lon.setText(str(ll_lon))
    form.w_ll_lat.setText(str(ll_lat))
    form.w_bbox.setText(format_bbox(form.sttngs['bbox'],area))

    return True

def write_config_file(form, message_flag = True):
    """
    write current selections to config file
    """
    study = form.w_study.text()

    # facilitate multiple config file choices
    # =======================================
    glbl_ecsse_str = form.sttngs['glbl_ecsse_str']
    config_file = join(form.sttngs['config_dir'], glbl_ecsse_str + study + '.json')

    # prepare the bounding box
    # ========================
    ll_lon, ll_lat , ur_lon,  ur_lat = 4*[0.0]
    try:
        ll_lon = float(form.w_ll_lon.text())
        ll_lat = float(form.w_ll_lat.text())
        ur_lon = float(form.w_ur_lon.text())
        ur_lat = float(form.w_ur_lat.text())
    except ValueError as err:
        print('Problem writing bounding box to config file: ' + str(err))
        ur_lon = 0.0
        ur_lat = 0.0

    form.sttngs['bbox'] = list([ll_lon,ll_lat,ur_lon,ur_lat])

    config = {
        'minGUI': {
            'bbox' : form.sttngs['bbox'],
            'use_drvr_flag': form.w_use_drvr.isChecked(),
            'wthrRsrce' : form.sttngs['wthr_rsrc']
        },
        'cmnGUI': {
            'study' : form.w_study.text(),
            'climScnr'  : form.w_combo10s.currentText(),
            'hwsd_drvr_fn': form.w_hwsd_drvr_fn.text(),
            'test_data_dir': form.w_test_dir.text(),
            'eqilMode'  : form.w_equimode.text(),
            'realis': form.w_combo10r.currentText(),
            'n_coords'  : form.w_ncoords.text()
            }
        }
    if isfile(config_file):
        descriptor = 'Overwrote existing'
    else:
        descriptor = 'Wrote new'
    if study != '':
        with open(config_file, 'w') as fconfig:
            json_dump(config, fconfig, indent=2, sort_keys=True)
            if message_flag:
                print('\n' + descriptor + ' configuration file ' + config_file)
            else:
                print()
    return

def write_runsites_cnfg_fn(form):

    func_name =  __prog__ +  ' write_runsites_cnfg_fn'

    # read the runsites config file and edit one line
    # ======================================
    runsites_cnfg_fn = form.sttngs['runsites_cnfg_fn']
    try:
        with open(runsites_cnfg_fn, 'r') as fcnfg:
            config = json_load(fcnfg)
            print('\nRead config file ' + runsites_cnfg_fn)
    except (OSError, IOError) as err:
            print(err)
            return False

    # overwrite config file
    # =====================
    sims_dir = normpath(join(form.sttngs['sims_dir'], form.w_study.text()))
    config['Simulations']['sims_dir'] = sims_dir
    with open(runsites_cnfg_fn, 'w') as fcnfg:
        try:
            json_dump(config, fcnfg, indent=2, sort_keys=True)
        except (JSONEncoder, JSONDecodeError, NameError) as err:
            print(ERROR_STR + 'writing json file ' + runsites_cnfg_fn + str(err))

        print('Edited ' + runsites_cnfg_fn + '\n\twith simulation location: ' + sims_dir)
        QApplication.processEvents()

    return True

def _write_default_config_file(config_file):
    """
    default configuration file if it needs to be created
    """
    _default_config = {
        'minGUI': {
            'bbox': BBOX_DEFAULT,
            'wthrRsrce': 'CHESS'
        },
        'cmnGUI': {
            'climScnr' : 'rcp26',
            'eqilMode' : '2',
            'hwsd_drvr_fn': '',
            'n_coords': '10',
            'realis': '01',
            'study'    : '',
            'test_data_dir': ''
        }
    }
    # if config file does not exist then create it...
    with open(config_file, 'w') as fconfig:
        json_dump(_default_config, fconfig, indent=2, sort_keys=True)
        fconfig.close()
        return _default_config
