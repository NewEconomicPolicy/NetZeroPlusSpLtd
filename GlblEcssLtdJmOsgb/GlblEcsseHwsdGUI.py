#-------------------------------------------------------------------------------
# Name:
# Purpose:     Creates a GUI with five administrative levels plus country
# Author:      Mike Martin
# Created:     11/12/2015
# Licence:     <your licence>
#-------------------------------------------------------------------------------

__prog__ = 'GlblEcsseHwsdGUI.py'
__version__ = '0.0.1'
__author__ = 's03mm5'

import sys
from os.path import join, isfile, normpath
from os import walk, getcwd, remove, chdir, listdir
from time import time
from datetime import timedelta
from shutil import rmtree
from subprocess import Popen, PIPE, STDOUT, DEVNULL

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPixmap, QFont
from PyQt5.QtWidgets import (QLabel, QWidget, QHBoxLayout, QVBoxLayout, QGridLayout, QLineEdit, QRadioButton,
                QButtonGroup, QComboBox, QPushButton, QCheckBox, QFileDialog, QTextEdit, QMessageBox, QApplication)

from shape_funcs import format_bbox, calculate_area
from common_cmpnntsGUI import (commonSection, change_config_file, study_text_changed, exit_clicked, save_clicked,
                                                                 spinup_inp_out_mode, adjust_model_switches)
from glbl_ecss_cmmn_cmpntsGUI import calculate_grid_cell
from glbl_ecss_cmmn_funcs import write_study_definition_file

from grid_osgb_high_level_fns import make_grid_cell_sims, make_bbox_sims
from grid_osgb_classes_and_fns import make_hwsd_drvr_df

from initialise_funcs import initiation, read_config_file, build_and_display_studies, write_runsites_cnfg_fn
from set_up_logging import OutLog

WDGT_SIZE_100 = 100
WDGT_SIZE_80 = 80
WDGT_SIZE_60 = 60
WDGT_SIZE_150 = 150
WDGT_SIZE_40 = 40
PADDING = '   '
PDDNG_10 = ' '*1

RESOLUTIONS = [1, 2, 4, 5, 10]

ERROR_STR = '*** Error *** '
WARN_STR = '*** Warning *** '

# ========================

class Form(QWidget):

    def __init__(self, parent=None):

        super(Form, self).__init__(parent)

        self.version = 'HWSD_grid'
        initiation(self)
        font = QFont(self.font())
        font.setPointSize(font.pointSize() + 2)
        self.setFont(font)

        # The layout is done with the QGridLayout
        grid = QGridLayout()
        grid.setSpacing(10)	# set spacing between widgets

        # line 0
        # ======
        irow = 0
        lbl00 = QLabel('Study:')
        lbl00.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl00, irow, 0)

        w_study = QLineEdit()
        w_study.setFixedWidth(WDGT_SIZE_150)
        grid.addWidget(w_study, irow, 1, 1, 2)
        self.w_study = w_study

        lbl00s = QLabel(PADDING + 'Studies:')
        lbl00s.setAlignment(Qt.AlignRight)
        helpText = 'list of studies'
        lbl00s.setToolTip(helpText)
        grid.addWidget(lbl00s, irow, 2)

        w_combo00s = QComboBox()
        for study in self.studies:
            w_combo00s.addItem(study)
        w_combo00s.setFixedWidth(WDGT_SIZE_150)
        grid.addWidget(w_combo00s, irow, 3, 1, 2)
        w_combo00s.currentIndexChanged[str].connect(self.changeConfigFile)
        self.w_combo00s = w_combo00s
        
        # ===========================

        irow += 1
        w_lbl06b = QLabel('Methodology:')
        w_lbl06b.setAlignment(Qt.AlignRight)
        grid.addWidget(w_lbl06b, irow, 0)

        w_use_bbox = QRadioButton('Use bounding box')
        helpText_nc = 'Use bounding box'
        w_use_bbox.setToolTip(helpText_nc)
        grid.addWidget(w_use_bbox, irow, 1)

        w_use_drvr = QRadioButton("HWSD driver file")
        helpText = 'Use a Excel file comprising a list of grid coordinates'
        w_use_drvr.setToolTip(helpText)
        grid.addWidget(w_use_drvr, irow, 2)
        self.w_use_drvr = w_use_drvr

        w_inpts_choice = QButtonGroup()
        w_inpts_choice.addButton(w_use_bbox)
        w_inpts_choice.addButton(w_use_drvr)
        w_use_drvr.setChecked(True)

        # assign check values to radio buttons
        # ====================================
        w_inpts_choice.setId(w_use_bbox, 2)
        w_inpts_choice.setId(w_use_drvr, 1)
        self.w_use_bbox = w_use_bbox
        self.w_inpts_choice = w_inpts_choice

        irow = spinup_inp_out_mode(self, grid, irow)  # extra line for spinup mode

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        # UR lon/lat
        # ==========
        irow += 1
        lbl02a = QLabel('Upper right longitude:')
        lbl02a.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl02a, irow, 0)

        w_ur_lon = QLineEdit()
        w_ur_lon.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_ur_lon, irow, 1)
        self.w_ur_lon = w_ur_lon

        lbl02b = QLabel('latitude:')
        lbl02b.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl02b, irow, 2)

        w_ur_lat = QLineEdit()
        w_ur_lat.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_ur_lat, irow, 3)
        self.w_ur_lat = w_ur_lat

        # LL lon/lat
        # ==========
        irow += 1
        lbl01a = QLabel('Lower left longitude:')
        lbl01a.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl01a, irow, 0)

        w_ll_lon = QLineEdit()
        w_ll_lon.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_ll_lon, irow, 1)
        self.w_ll_lon = w_ll_lon

        lbl01b = QLabel('latitude:')
        lbl01b.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl01b, irow, 2)

        w_ll_lat = QLineEdit()
        w_ll_lat.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_ll_lat, irow, 3)
        w_ll_lat.setFixedWidth(80)
        self.w_ll_lat = w_ll_lat

        # report on bbox
        # ==============
        irow += 1
        lbl03a = QLabel('Study bounding box:')
        lbl03a.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl03a, irow, 0)

        w_bbox = QLabel()
        w_bbox.setAlignment(Qt.AlignTop)
        grid.addWidget(w_bbox, irow, 1, 1, 5)
        self.w_bbox = w_bbox

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        # ========================================================
        irow += 1
        w_drvr_pb = QPushButton('HWSD driver file')
        w_drvr_pb.setToolTip('CSV HWSD driver file')
        w_drvr_pb.clicked.connect(self.fetchHwsdDrvrFn)
        grid.addWidget(w_drvr_pb, irow, 0)
        self.w_drvr_pb = w_drvr_pb

        w_hwsd_drvr_fn = QLabel('')
        grid.addWidget(w_hwsd_drvr_fn, irow, 1, 1, 6)
        self.w_hwsd_drvr_fn = w_hwsd_drvr_fn

        w_drvr_dtls = QLabel('Records:' + PDDNG_10)
        grid.addWidget(w_drvr_dtls, irow, 7)
        self.w_drvr_dtls = w_drvr_dtls

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        # ================================
        irow += 1
        w_plnt_pb = QPushButton('Plant inputs')
        helpText = 'Path for plant inputs'
        w_plnt_pb.setToolTip(helpText)
        grid.addWidget(w_plnt_pb, irow, 0)
        w_plnt_pb.clicked.connect(self.fetchTstDir)

        w_test_dir = QLabel()
        grid.addWidget(w_test_dir, irow, 1, 1, 5)
        self.w_test_dir = w_test_dir

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        # =================================
        irow = commonSection(self, grid, irow)  # create weather etc

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        irow += 1
        lbl05 = QLabel('Maximum cells:')
        helpText = 'Maximum number of simulation cells to generate'
        lbl05.setAlignment(Qt.AlignRight)
        lbl05.setToolTip(helpText)
        grid.addWidget(lbl05, irow, 0)

        w_ncoords = QLineEdit()
        w_ncoords.setFixedWidth(WDGT_SIZE_60)
        grid.addWidget(w_ncoords, irow, 1)
        self.w_ncoords = w_ncoords

        # ==============
        lbl10 = QLabel('Operation progress:')
        lbl10.setAlignment(Qt.AlignRight)
        grid.addWidget(lbl10, irow, 2)

        self.w_prgrss = QLabel()
        self.w_prgrss.setAlignment(Qt.AlignTop)
        grid.addWidget(self.w_prgrss, irow, 3, 1, 5)

        irow += 1
        grid.addWidget(QLabel(''), irow, 2)  # spacer

        # command line
        # ============
        irow += 1
        w_create_files = QPushButton("Create sim files")
        helpText = 'Generate ECOSSE simulation file sets corresponding to ordered HWSD global mapping unit set in CSV file'
        w_create_files.setToolTip(helpText)
        w_create_files.setFixedWidth(WDGT_SIZE_100)
        grid.addWidget(w_create_files, irow, 0)
        w_create_files.clicked.connect(self.createSimsClicked)
        self.w_create_files = w_create_files

        w_auto_spec = QCheckBox('Auto run Ecosse')
        helpText = 'Select this option to automatically run Ecosse'
        w_auto_spec.setToolTip(helpText)
        grid.addWidget(w_auto_spec, irow, 1)
        self.w_auto_spec = w_auto_spec

        w_run_ecosse = QPushButton('Run Ecosse')
        helpText = 'Select this option to create a configuration file for the spec.py script and run it.\n' \
                   + 'The spec.py script runs the ECOSSE programme'
        w_run_ecosse.setToolTip(helpText)
        w_run_ecosse.setFixedWidth(WDGT_SIZE_80)
        w_run_ecosse.clicked.connect(self.runEcosseClicked)
        grid.addWidget(w_run_ecosse, irow, 2)
        self.w_run_ecosse = w_run_ecosse

        w_clr_psh = QPushButton('Clear', self)
        helpText = 'Clear reporting window'
        w_clr_psh.setToolTip(helpText)
        w_clr_psh.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_clr_psh, irow, 3)  # , alignment=Qt.AlignRight
        w_clr_psh.clicked.connect(self.clearReporting)

        w_cancel = QPushButton("Cancel")
        helpText = 'Leaves GUI without saving configuration and study definition files'
        w_cancel.setToolTip(helpText)
        w_cancel.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_cancel, irow, 4)
        w_cancel.clicked.connect(self.cancelClicked)

        w_save = QPushButton("Save")
        helpText = 'Save configuration and study definition files'
        w_save.setToolTip(helpText)
        w_save.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_save, irow, 5)
        w_save.clicked.connect(self.saveClicked)

        w_exit = QPushButton("Exit", self)
        grid.addWidget(w_exit, irow, 6)
        w_exit.setFixedWidth(WDGT_SIZE_80)
        w_exit.clicked.connect(self.exitClicked)

        # ========
        irow += 1
        w_test_sock = QPushButton('Test socket', self)
        helpText = 'Test socket'
        w_test_sock.setToolTip(helpText)
        w_test_sock.setFixedWidth(WDGT_SIZE_80)
        w_test_sock.setEnabled(True)
        grid.addWidget(w_test_sock, irow, 1)
        w_test_sock.clicked.connect(self.testSocket)
        self.w_test_sock = w_test_sock

        w_view_log = QPushButton('Ecosse log', self)
        helpText = 'View Ecosse log for all simulations'
        w_view_log.setToolTip(helpText)
        w_view_log.setFixedWidth(WDGT_SIZE_80)
        w_view_log.setEnabled(False)
        grid.addWidget(w_view_log, irow, 2)
        w_view_log.clicked.connect(self.viewStdout)
        self.w_view_log = w_view_log

        w_del_sims = QPushButton('Del sims', self)
        helpText = 'Delete all simulations'
        w_del_sims.setToolTip(helpText)
        w_del_sims.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_del_sims, irow, 3)
        w_del_sims.clicked.connect(self.delSims)

        w_del_stdy = QPushButton('Del study', self)
        helpText = 'Delete study and all simulations'
        w_del_stdy.setToolTip(helpText)
        w_del_stdy.setFixedWidth(WDGT_SIZE_80)
        grid.addWidget(w_del_stdy, irow, 4)
        w_del_stdy.clicked.connect(lambda: self.delSims(True))

        # =====================================
        w_san_disk = QPushButton('SanDisk', self)
        helpText = 'SanDisk overview'
        w_san_disk.setToolTip(helpText)
        w_san_disk.setFixedWidth(WDGT_SIZE_80)
        w_san_disk.setEnabled(False)
        grid.addWidget(w_san_disk, irow, 5, alignment=Qt.AlignRight)
        w_san_disk.clicked.connect(self.sanDisk)

        # LH vertical box consists of png image
        # =====================================
        lh_vbox = QVBoxLayout()

        lbl20 = QLabel()
        lbl20.setPixmap(QPixmap(self.fname_png))
        lbl20.setScaledContents(True)

        lh_vbox.addWidget(lbl20)

        # add grid consisting of combo boxes, labels and buttons to RH vertical box
        # =========================================================================
        rh_vbox = QVBoxLayout()
        rh_vbox.addLayout(grid)

        # add reporting
        # =============
        bot_hbox = QHBoxLayout()
        w_report = QTextEdit()
        w_report.verticalScrollBar().minimum()
        w_report.setMinimumHeight(230)
        w_report.setMinimumWidth(1000)
        w_report.setStyleSheet('font: bold 10.5pt Courier')  # big jump to 11pt
        bot_hbox.addWidget(w_report, 1)
        self.w_report = w_report

        sys.stdout = OutLog(self.w_report, sys.stdout)
        # sys.stderr = OutLog(self.w_report, sys.stderr, QColor(255, 0, 0))

        # add LH and RH vertical boxes to main horizontal box
        # ===================================================
        main_hbox = QHBoxLayout()
        main_hbox.setSpacing(10)
        main_hbox.addLayout(lh_vbox)
        main_hbox.addLayout(rh_vbox, stretch = 1)

        # feed horizontal boxes into the window
        # =====================================
        outer_layout = QVBoxLayout()
        outer_layout.addLayout(main_hbox)
        outer_layout.addLayout(bot_hbox)
        self.setLayout(outer_layout)

        # posx, posy, width, height
        self.setGeometry(200, 100, 690, 250)
        self.setWindowTitle('Global Ecosse Ver 2b - generate sets of ECOSSE input files based on HWSD grid')

        # reads and set values from last run
        # ==================================
        read_config_file(self)
        if self.sttngs['run_sims_flag']:
            w_create_files.setEnabled(True)
        else:
            w_create_files.setEnabled(False)

    def testSocket(self):
        """
        create a socket object that supports the context manager type, so you can use it in a with statement
        if conn.recv() returns an empty bytes object, b'', that signals that the client closed the connection
        """
        from socket import (socket, setdefaulttimeout, AF_INET, SOCK_STREAM,
                                                                    gethostbyname, gethostname, gaierror, timeout)

        HOST = gethostname()  # Standard loopback interface address (localhost)
        PORT = 65432        # Port to listen on (non-privileged ports are > 1023)
        TIMEOUT = 60

        # setdefaulttimeout(TIMEOUT)

        try:
            ip = gethostbyname('www.google.com')
        except socket.gaierror:
            print('error resolving the host')

        sockobj = socket(AF_INET, SOCK_STREAM)    # specify the address family and socket type
        sockobj.settimeout(TIMEOUT)
        print('Socket successfully created - timeout set to ' + str(timedelta(seconds=TIMEOUT)))
        QApplication.processEvents()

        # bind to the port - ip field can be an empty string which makes the server listen to requests
        # coming from other computers on the network
        # =========================================
        sockobj.bind((HOST, PORT))        # associate the socket with a specific network interface and port number

        ret_code = sockobj.listen(1)   # make server a listening socket by enabling connection acceptance
        print('socket is listening')
        QApplication.processEvents()

        # a forever loop until we interrupt it or an error occurs
        # =======================================================
        while True:
            try:
                conn, addr = sockobj.accept()   # block execution and wait for an incoming connection
            except timeout as err:
                print('timeout')
                break

            print('Got connection from: ', addr)
            QApplication.processEvents()

            # send thank you message to the client. encoding to send byte type
            # ================================================================
            conn.send('Thank you for connecting'.encode())

            # Close the connection with the client
            conn.close()
            break

        var = sockobj.close()

        QApplication.processEvents()
        return

    def viewStdout(self):
        """
        C
        """
        notepad_path, stdout_path = self.sttngs['notepad_path'], self.sttngs['stdout_path']
        if notepad_path is not None and stdout_path is not None:
            Popen( list([self.sttngs['notepad_path'], self.sttngs['stdout_path']]), stdout=DEVNULL)

        return

    def sanDisk(self):
        """

        """
        lta_dir = join(self.sttngs['root_dir'], self.sttngs['lta_dir'])
        for rcp in listdir(lta_dir):
            dirnm = join(lta_dir, rcp)
            print('Checking lta dir: ' + dirnm)
            fns = listdir(dirnm)
            print('Found {} files e.g. {}'.format(len(fns), fns[0]))
            QApplication.processEvents()

        print('Copied {} files e.g. {}'.format(len(fns), fns[0]))
        QApplication.processEvents()

        wthr_dir = join(self.sttngs['root_dir'], self.sttngs['rcp_dir'])
        for rcp in listdir(wthr_dir):
            rcp_dir = join(wthr_dir, rcp)
            print('Checking wthr dir: ' + rcp_dir)
            dirs = listdir(rcp_dir)
            print('Found {} dirs e.g. {}'.format(len(dirs), dirs[0]))
            QApplication.processEvents()

        return

    def fetchTstDir(self):
        """

        """
        dialog = QFileDialog(self)
        dialog.ShowDirsOnly = False

        test_dir = self.w_test_dir.text()
        test_dir = dialog.getExistingDirectory(self, 'Select directory containing plant inputs', test_dir)

        if test_dir != '':
            test_dir = normpath(test_dir)
            self.w_test_dir.setText(test_dir)

        return
            
    def delSims(self, del_study_flag=False):
        """

        """
        from glob import glob
        config_dir = self.sttngs['config_dir']
        glbl_ecsse_str = self.sttngs['glbl_ecsse_str']

        study = self.w_study.text()
        study_dir = join(self.sttngs['sims_dir'], study)

        if del_study_flag:
            config_files = glob(config_dir + '/' + glbl_ecsse_str + '*.json')
            if len(config_files) == 1:
                print(WARN_STR + 'Cannot delete ' + study + ' there must be at least one study in this project')
                QApplication.processEvents()
                return

        num_sims = 0
        nmanis = 0
        for directory, subdirs_raw, manifests in walk(study_dir):
            num_sims = len(subdirs_raw)
            nmanis = len(manifests)
            break

        if num_sims == 0 and nmanis == 0:
            print(WARN_STR + 'no grid_cells or manifests files to delete from study: ' + study)
            QApplication.processEvents()
            if not del_study_flag:
                return

        mess_content = 'Will delete '
        if del_study_flag:
            mess_content += 'study {} comprising {} cells and {} manifest files'.format(study, num_sims, nmanis)
        else:
            mess_content += '{} cells and {} manifest files from study: {}'.format(num_sims, nmanis, study)
        mess_content += '\n\n\tAre you sure?'
        w_mess_box = QMessageBox()
        w_mess_box.setWindowTitle('Cleaner')
        w_mess_box.setText(mess_content)
        w_mess_box.setStandardButtons(QMessageBox.Yes | QMessageBox.Cancel)
        w_mess_box = w_mess_box.exec()

        if w_mess_box == QMessageBox.Yes:
            if num_sims > 0:
                for subdir in subdirs_raw:
                    grid_dir = join(study_dir, subdir)
                    rmtree(grid_dir, ignore_errors=True)

            if nmanis > 0:
                for mani in manifests:
                    mani_fn = join(study_dir, mani)
                    remove(mani_fn)

            print('Deleted {} cells and {} manifest files'.format(num_sims, nmanis))
            QApplication.processEvents()

        if del_study_flag:
            rmtree(study_dir, ignore_errors=True)
            config_fn = join(config_dir, glbl_ecsse_str +  study + '.json')
            if isfile(config_fn):
                remove(config_fn)
                print('Deleted configuration file ' + config_fn)
                build_and_display_studies(self, glbl_ecsse_str)
            else:
                print(WARN_STR + 'Could not delete configuration file ' + config_fn + ' file not found')

            QApplication.processEvents()

        return

    def createSimsClicked(self):
        """

        """
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
            return

        # check for spaces
        # ================
        if study.find(' ') >= 0:
            print('*** study name must not have spaces ***')
            return

        self.study = study
        adjust_model_switches(self)
        if self.w_use_drvr.isChecked():
            ret_code = make_grid_cell_sims(self)
        else:
            ret_code = make_bbox_sims(self)
        if not ret_code:
            return

        write_study_definition_file(self, glbl_ecss_variation='jm')

        # run further steps
        # =================
        if self.w_auto_spec.isChecked():
            self.runEcosseClicked()

        return

    def clearReporting(self):
        """

        """
        self.w_report.clear()

    def resolutionChanged(self):
        """

        """
        granularity = 120
        calculate_grid_cell(self, granularity)

    def studyTextChanged(self):
        """

        """
        study_text_changed(self)

    def bboxTextChanged(self):
        """

        """
        try:
            bbox = list([float(self.w_ll_lon.text()), float(self.w_ll_lat.text()),
                float(self.w_ur_lon.text()), float(self.w_ur_lat.text())])
            area = calculate_area(bbox)
            self.w_bbox.setText(format_bbox(bbox, area))
            self.sttngs['bbox'] = bbox
        except ValueError as e:
            pass

    def runEcosseClicked(self):
        """
        components of the command string have been checked at startup
        """
        if not write_runsites_cnfg_fn(self):
            return

        curr_dir = getcwd()
        chdir(self.settings['log_dir'])

        stdout_path = join(self.sttngs['sims_dir'], 'stdout.txt')
        runsites_py = self.sttngs['runsites_py']
        runsites_cnfg_fn = self.sttngs['runsites_cnfg_fn']

        # run the make simulations script
        # ===============================
        print('Working dir: ' + getcwd())
        QApplication.processEvents()
        command_line = [self.sttngs['python_exe'], runsites_py, runsites_cnfg_fn]
        start_time = time()

        try:
            # new_inst = Popen(command_line, shell=False, stdin=PIPE, stdout=open(stdout_path, 'w'), stderr=STDOUT)
            new_inst = Popen(command_line, stderr=STDOUT)
            if new_inst.stdin is not None:
                print('Launched: ' + runsites_py + ' with process id: ' + str(new_inst.pid))
                QApplication.processEvents()

        except OSError as err:
            mess = ERROR_STR + 'Run sites script ' + runsites_py
            print(mess + ' could not be launched due to error ' + str(err))
            QApplication.processEvents()

        chdir(curr_dir)
        '''
        scnds_elapsed = round(time() - start_time)
        print('Time taken: ' + str(timedelta(seconds=scnds_elapsed)))
        QApplication.processEvents()
        '''
        return

    def saveClicked(self):
        """

        """
        # check for spaces
        # ================
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
        else:
            if study.find(' ') >= 0:
                print('*** study name must not have spaces ***')
            else:
                save_clicked(self)
                build_and_display_studies(self, self.sttngs['glbl_ecsse_str'])

        return

    def cancelClicked(self):
        """

        """
        exit_clicked(self, write_config_flag = False)

    def exitClicked(self):
        """
        exit cleanly
        """
        # check for spaces
        # ================
        study = self.w_study.text()
        if study == '':
            print('study cannot be blank')
        else:
            if study.find(' ') >= 0:
                print('*** study name must not have spaces ***')
            else:
                exit_clicked(self)

    def changeConfigFile(self):
        """
        permits change of configuration file
        """
        change_config_file(self)

    def fetchHwsdDrvrFn(self):
        """

        """
        fname = self.w_hwsd_drvr_fn.text()
        fname, dummy = QFileDialog.getOpenFileName(self, 'Select CSV HWSD driver file', fname, 'NetCDF file (*.csv)')
        if fname != '':
            fname = normpath(fname)
            make_hwsd_drvr_df(self, fname)

def main():
    """

    """
    app = QApplication(sys.argv)  # create QApplication object
    form = Form() # instantiate form
    # display the GUI and start the event loop if we're not running batch mode
    form.show()             # paint form
    sys.exit(app.exec_())   # start event loop

if __name__ == '__main__':
    main()
