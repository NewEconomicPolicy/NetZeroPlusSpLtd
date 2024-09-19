"""
#-------------------------------------------------------------------------------
# Name:        common_componentsGUI.p
# Purpose:     consist of high level functions invoked by main GUI
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------
#
"""

__prog__ = 'common_cmpnntsGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

# Version history
# ---------------
#
from os.path import normpath, isfile
from time import sleep

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QLabel, QLineEdit, QComboBox, QCheckBox, QApplication, QButtonGroup, QRadioButton,
                                                                                            QCheckBox, QPushButton)

from initialise_funcs import read_config_file, write_config_file
from glbl_ecss_cmmn_funcs import write_study_definition_file

WDGT_SIZE_40 = 40
WDGT_SIZE_60 = 60
WDGT_SIZE_100 = 100
WDGT_SIZE_110 = 110
PDDNG_10 = ' '*10

EQUIMODE_DFLT = '6'     # default equilibrium mode

LU_DEFNS = {'lu_type' : ['Arable','Forestry','Miscanthus','Grassland','Semi-natural', 'SRC', 'Rapeseed', 'Sugar cane'],
                   'abbrev': ['ara',   'for',      'mis',      'gra',      'nat',     'src', 'rps',      'sgc'],
                        'ilu':[1,        3,          5,          2,          4,          6,     7,          7]}
RCPS = list(['rcp26', 'rcp45', 'rcp60', 'rcp85'])
REALISATIONS = list(['01', '04', '06', '15'])
lta_strt_yr, lta_end_yr = (1988, 2018)

# run modes
# =========
SPATIAL = 1
CSV_FILE = 2

sleepTime = 3

# ====================================

def commonSection(form, grid, irow):

    # =================
    # hist_syears, hist_eyears, fut_syears, fut_eyears, scenarios = get_wthr_parms(form, 'CRU')

    form.depths = list([30,100]) # soil depths

    luTypes = {}; lu_type_abbrevs = {}
    for lu_type, abbrev, ilu in zip(LU_DEFNS['lu_type'], LU_DEFNS['abbrev'], LU_DEFNS['ilu']):
        luTypes[lu_type] = ilu
        lu_type_abbrevs[lu_type] = abbrev

    form.land_use_types = luTypes
    form.lu_type_abbrevs = lu_type_abbrevs

    # equilibrium mode
    # ================
    irow += 1
    lbl12 = QLabel('Equilibrium mode:')
    lbl12.setAlignment(Qt.AlignRight)
    helpText = 'mode of equilibrium run, generally OK with 9.5'
    lbl12.setToolTip(helpText)
    grid.addWidget(lbl12, irow, 0)

    w_equimode = QLineEdit()
    w_equimode.setText(EQUIMODE_DFLT)
    w_equimode.setFixedWidth(WDGT_SIZE_40)
    grid.addWidget(w_equimode, irow, 1)
    form.w_equimode = w_equimode

    irow += 1
    grid.addWidget(QLabel(''), irow, 2)  # spacer

    # scenarios
    # =========
    icol = 0
    lbl10 = QLabel('Scenario:')
    lbl10.setAlignment(Qt.AlignRight)
    helpText = 'Ecosse requires future average monthly precipitation and temperature derived from climate models.\n' \
        + 'The data used here is ClimGen v1.02 created on 16.10.08 developed by the Climatic Research Unit\n' \
        + ' and the Tyndall Centre. See: http://www.cru.uea.ac.uk/~timo/climgen/'
    lbl10.setToolTip(helpText)
    grid.addWidget(lbl10, irow, icol)

    icol += 1
    w_combo10s = QComboBox()
    w_combo10s.setFixedWidth(WDGT_SIZE_100)
    grid.addWidget(w_combo10s, irow, icol)
    form.w_combo10s = w_combo10s

    for scenario in RCPS:
        form.w_combo10s.addItem(str(scenario))

    # =====================
    icol += 1
    w_all_scens = QCheckBox('Use all scenarios')
    helpText = 'Use all scenarios'
    w_all_scens.setToolTip(helpText)
    grid.addWidget(w_all_scens, irow, icol, 1, 2)
    form.w_all_scens = w_all_scens

    # realisations
    # =============
    icol += 1
    lbl10r = QLabel('Realisation:')
    lbl10r.setAlignment(Qt.AlignRight)
    helpText = ''
    lbl10r.setToolTip(helpText)
    grid.addWidget(lbl10r, irow, icol)

    icol += 1
    w_combo10r = QComboBox()
    w_combo10r.setFixedWidth(WDGT_SIZE_40)
    grid.addWidget(w_combo10r, irow, icol)
    form.w_combo10r = w_combo10r

    for realis in REALISATIONS:
        form.w_combo10r.addItem(str(realis))

    icol += 1
    w_all_realis = QCheckBox('Use all realisations')
    helpText = 'Use all realisations'
    w_all_realis.setToolTip(helpText)
    grid.addWidget(w_all_realis, irow, icol, 1, 2)
    form.w_all_realis = w_all_realis

    irow += 1
    grid.addWidget(QLabel(''), irow, 2)  # spacer

    # Simulation years
    # ================
    sim_strt_yr, sim_end_yr = (2020, 2079)
    fut_syears = list(range(sim_strt_yr, sim_end_yr))
    fut_eyears = list(range(sim_strt_yr + 1, sim_end_yr + 1))

    irow += 1
    lbl11s = QLabel('Simulation start year:')
    helpText = 'Simulation start and end years determine the number of growing seasons to simulate\n' \
               + 'CRU and CORDEX resources run to 2100 whereas EObs resource runs to 2017'
    lbl11s.setToolTip(helpText)
    lbl11s.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl11s, irow, 0)

    w_combo11s = QComboBox()
    w_combo11s.setFixedWidth(WDGT_SIZE_60)
    grid.addWidget(w_combo11s, irow, 1)
    form.w_combo11s = w_combo11s

    for year in fut_syears:
        form.w_combo11s.addItem(str(year))
    form.w_combo11s.setCurrentText(str(fut_syears[0]))
    form.w_combo11s.setEnabled(False)

    # ================
    lbl11e = QLabel('End year:')
    lbl11e.setAlignment(Qt.AlignRight)
    grid.addWidget(lbl11e, irow, 2)

    w_combo11e = QComboBox()
    w_combo11e.setFixedWidth(WDGT_SIZE_60)
    grid.addWidget(w_combo11e, irow, 3)
    form.w_combo11e = w_combo11e

    for year in fut_eyears:
        form.w_combo11e.addItem(str(year))
    form.w_combo11e.setCurrentText(str(year))
    form.w_combo11e.setEnabled(False)

    # ================
    lbl09s = QLabel('LTA period from:')
    lbl09s.setAlignment(Qt.AlignRight)
    helpText = 'Long term average (LTA) monthly precipitation and temperatures period'
    lbl09s.setToolTip(helpText)
    grid.addWidget(lbl09s, irow, 4)

    lbl09s = QLabel('{}\tto: {}'.format(lta_strt_yr, lta_end_yr))
    lbl09s.setToolTip(helpText)
    lbl09s.setAlignment(Qt.AlignTop)
    grid.addWidget(lbl09s, irow, 5, 1, 2)

    return irow

def spinup_inp_out_mode(form, grid, irow):
    """
    write line enabling spinup input/output mode: 0 = off, 1 = read spinup data; 2 = save spinup data to spinup.dat
    """
    irow += 1
    icol = 0
    w_lbl07 = QLabel('Spinup input/output mode:')
    w_lbl07.setAlignment(Qt.AlignRight)
    w_lbl07.setToolTip('These settings control the spinup input/output mode setting in the Model_Switches.dat file')
    grid.addWidget(w_lbl07, irow, icol)

    help_mess = 'Set spinup input/output mode setting in Model_Switches.dat file to '

    icol += 1
    w_spin_off = QRadioButton('off')
    w_spin_off.setToolTip(help_mess + ' 0 = off')
    grid.addWidget(w_spin_off, irow, icol)
    form.w_spin_off = w_spin_off

    icol += 1
    w_spin_read = QRadioButton('read spinup data')
    w_spin_read.setToolTip(help_mess + ' 1 = read previously generated spinup data stored under the spinup path')
    grid.addWidget(w_spin_read, irow, icol)
    form.w_spin_read = w_spin_read

    icol += 1
    w_spin_save = QRadioButton('save spinup data')
    w_spin_save.setToolTip(help_mess + '2 = save spinup data')
    grid.addWidget(w_spin_save, irow, icol)
    form.w_spin_save = w_spin_save

    w_inpts_choice = QButtonGroup()
    w_inpts_choice.addButton(w_spin_off)
    w_inpts_choice.addButton(w_spin_read)
    w_inpts_choice.addButton(w_spin_save)
    w_spin_read.setChecked(True)

    # assign check values to radio buttons
    # ====================================
    w_inpts_choice.setId(w_spin_off, 0)
    w_inpts_choice.setId(w_spin_read, 1)
    w_inpts_choice.setId(w_spin_save, 2)
    form.w_inpts_choice = w_inpts_choice

    # ================================
    irow += 1
    w_spin_pb = QPushButton('Spinup path')
    helpText = 'Path for storing spinup files from the grid cells, '
    helpText += 'each spinup.dat file is recorded as spinup_easting_northing.dat'
    w_spin_pb.setToolTip(helpText)
    w_spin_pb.setFixedWidth(WDGT_SIZE_110)
    w_spin_pb.setEnabled(True)
    grid.addWidget(w_spin_pb, irow, 0)
    w_spin_pb.clicked.connect(form.fetchSpinupDir)

    w_spin_dir = QLabel()
    grid.addWidget(w_spin_dir, irow, 1, 1, 5)
    form.w_spin_dir = w_spin_dir

    w_spin_dtls = QLabel()
    grid.addWidget(w_spin_dtls, irow, 7)
    form.w_spin_dtls = w_spin_dtls

    return irow

def adjust_model_switches(form):
    """
    write last GUI selections Model_Switches.dat file
    """

    if form.w_spin_save.isChecked():
        spin_mode = '2'
    elif form.w_spin_read.isChecked():
        spin_mode = '1'
    else:
        spin_mode = '0'

    dflt_mdl_swtchs = form.sttngs['dflt_mdl_swtchs']
    with open(dflt_mdl_swtchs, 'r') as finp:
        lines = finp.readlines()

    lines[15] = spin_mode + lines[15][1:]
    with open(dflt_mdl_swtchs, 'w') as finp:
        rc = finp.writelines(lines)

    return


def save_clicked(form):
    """
    write last GUI selections
    """
    write_config_file(form)
    write_study_definition_file(form, glbl_ecss_variation='jm')

    return

def exit_clicked(form, write_config_flag = True):
    """
    write last GUI selections
    """
    print('Closing down...')
    QApplication.processEvents()

    sleep(sleepTime)

    if write_config_flag:
        save_clicked(form)

    # close various files
    if hasattr(form, 'fobjs'):
        for key in form.fobjs:
            form.fobjs[key].close()

    # close logging
    # =============
    try:
        form.lgr.handlers[0].close()
    except AttributeError:
        pass

    form.close()

def change_config_file(form):
    """
    identify and read the new configuration file
    """
    new_study = form.w_combo00s.currentText()
    new_config = 'global_ecosse_config_hwsd_' + new_study
    config_file = normpath(form.sttngs['config_dir'] + '/' + new_config + '.json')

    if isfile(config_file):
        form.sttngs['config_fn'] = config_file
        read_config_file(form)
        form.study = new_study
        form.w_study.setText(new_study)

    return

def study_text_changed(form):
    """
     replace spaces with underscores and rebuild study list
     """
    study = form.w_study.text()
    form.w_study.setText(study.replace(' ','_'))
