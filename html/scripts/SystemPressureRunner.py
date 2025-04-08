from customLib.common.CommandExcutor import CommandExcutor, SshExecutor
from customLib.common.DeviceUtil import DeviceUtil
from customLib.common.Utils import FileUtil
from customLib.common.TimeUtil import TimeUtil
from customLib.common.VehicleTypeManager import VehicleTypeManager
from constant.Constant import Constant
from constant.DisplayConstant import DisplayConstant
from constant.EventConstant import EventConstant
from customLib.cluster.ClusterGeneralManager import ThemesManager
from customLib.cluster.MessageSender import ClusterModule
from customLib.event.EventEmitter import EventEmitter
from customLib.loggers.modules.display.DisplayLogger import DisplayLogger
from customLib.loggers.UsbLogger import UsbLogger
from customLib.loggers.system.VipSocHeart import VipSocHeart
from customLib.opencv.Camera import VideoRecorderTask
from customLib.performance.BaseScenarioRunner import BaseScenarioRunner
from customLib.performance.system_pressure.ClusterFunctionThread import ClusterFunctionThread
from customLib.performance.system_pressure.ExceptionChecker import ExceptionChecker
from customLib.performance.MonkeyMonitor import MonkeyMonitor
from customLib.performance.system_pressure.SystemServiceChecker import SystemServiceChecker
from config.ConfigParser import ConfigParser
from customLib.common.Utils import LogUtil
from customLib.canbus.CanBusClient import CanBusClient
from customAPI.case_decorator.LifeCycle import setup, teardown
from customAPI.case_reporter.CaseReporter import CloudTestReporter


import sys
import threading
import time

START_DUMP_SCRIPT_CMD = "sh /var/dumpLogs.sh"

PULL_OUT_COREDUMP_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:{} {}"
PULL_OUT_HAM_COREDUMP_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:{} {}"
PULL_OUT_ERROR_MEMORY_LOG_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:{} {}"
PULL_OUT_MISC_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:{} {}"
PULL_OUT_DLT_RAW_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:{} {}"
PULL_OUT_DUMP_LOGS_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:/ota_update/qnx_misc_dump {}"
PULL_OUT_PERSIST_EM_FOLDER_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:/persist/em {}"

GENERATE_MINI_DUMP_CMD = f"ssh -o StrictHostKeyChecking=no root@{DeviceUtil.getSshAddress()} /bin/log_collector"
PULL_OUT_MINI_DUMP_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:/var/log/sbldump.bin {}"
DELETE_REMOTE_MINI_DUMP_CMD = f'ssh -o StrictHostKeyChecking=no root@{DeviceUtil.getSshAddress()} "rm -rf /var/log/sbldump.bin"'

EXECUTE_INC_LOG_CMD = f'ssh -o StrictHostKeyChecking=no root@{DeviceUtil.getSshAddress()} "inc_logger --tx_channel 0 --rx_channel 0 --log_duration 5 --log_file /var/log/inc_log.txt"'
PULL_OUT_INC_LOG_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:/var/log/inc_log.txt {}"
DELETE_REMOTE_INC_CMD = f'ssh -o StrictHostKeyChecking=no root@{DeviceUtil.getSshAddress()} "rm -rf /var/log/inc_log.txt"'

EXECUTE_EM_TRACE_CMD = f'ssh -o StrictHostKeyChecking=no root@{DeviceUtil.getSshAddress()} "em_trace -f /var/log/em_trace.txt"'
PULL_OUT_EM_TRACE_CMD = "scp -o StrictHostKeyChecking=no -r root@{}:/var/log/em_trace.txt {}"
DELETE_REMOTE_EM_TRACE_CMD = f'ssh -o StrictHostKeyChecking=no root@{DeviceUtil.getSshAddress()} "rm -rf /var/log/em_trace.txt"'

GET_VCU_BACKLIGHT_CMD = 'ssh -o StrictHostKeyChecking=no root@{} "fidm_brightness_test_ctl -r {}"'

GET_IVI_DATETIME_CMD = "adb shell date"
SET_STRESS_AUTOMATION_PROPERTY_CMD = "adb shell setprop test.automation.stress {}"
GET_STRESS_AUTOMATION_PROPERTY_CMD = "adb shell getprop test.automation.stress"

MONKEY_RUN_TIMES = 19000  # about 2 hours
PULL_OUT_LOGS_TIMEOUT_DEFAULT = 60  # 60 secs
PULL_OUT_DLT_TIMEOUT = 2000  # 2000 secs
MINI_DUMP_TIMEOUT = 3000  # 3000 secs
EXECUTE_INC_LOG_CMD_TIMEOUT = 30  # 30 secs
CASE_DURATION = 3600 * 24  # 1 days

CAMERA_INDEX = "1"
CAMERA_RECORD_DURATION = "20"  # 20 minutes
CAMREA_API_TIMEOUT = "5"  # 5 secs

THEME_SWITCH_INTERVAL = 5 * 60  # 5 minutes

START_MONKEY = True
SINGLE_APP_MONKEY_PACKAGE_ACTIVITY = None


class SystemPressureRunner(BaseScenarioRunner):

    def __init__(self):
        BaseScenarioRunner.__init__(self)
        self._isFinish = False
        self._videoRecordTask = None
        self._expChecker = None
        self._monkeyMonitor = None
        self._vipSocHeart = None
        self._sysServiceChecker = None
        self._themeSwitchTimer = None
        self._nightThemeState = False
        self._adassettingTask = None
        self._adasTask = None
        self._ambientlightTask = None
        self._chimeTask = None
        self._climateTask = None
        self._guageTask = None
        self._settingTask = None
        self._telltaleTask = None
        self._vehiclecontrolTask = None
        self._vehicleinfoTask = None
        self._warningTask = None
        self._caseFolder = None
        self._exception = False

    def startMonkeyTest(self, packageActivity=None):
        randomSeed = ConfigParser.getInstance().get("STRESS_RANDOM_SEED")
        vehicleProject = VehicleTypeManager.getInstance().getVehicleType()
        if vehicleProject == ('557', 'MY26', 'BEV'):
            self._monkeyMonitor = MonkeyMonitor(monkeyLogFolder=self._caseFolder, packageActivity=packageActivity, useWhitelist=False, randomSeed=randomSeed)
        else:
            self._monkeyMonitor = MonkeyMonitor(monkeyLogFolder=self._caseFolder, packageActivity=packageActivity, randomSeed=randomSeed)

        self._monkeyMonitor.start()

    def stopMonkeyTest(self):
        if self._monkeyMonitor is not None:
            self._monkeyMonitor.stopTask()
            self._monkeyMonitor = None

    def startClusterFunctions(self):
        randomSeed = ConfigParser.getInstance().get("STRESS_RANDOM_SEED")
        # adas setting functions
        # self._adassettingTask = ClusterFunctionThread(ClusterModule.AdasSetting.value, randomSeed=randomSeed)
        # self._adassettingTask.start()
        # adas functions
        self._adasTask = ClusterFunctionThread(ClusterModule.Adas.value, randomSeed=randomSeed)
        self._adasTask.start()
        # ambient light functions
        # self._ambientlightTask = ClusterFunctionThread(ClusterModule.AmbientLight.value, randomSeed=randomSeed)
        # self._ambientlightTask.start()
        # chime functions
        self._chimeTask = ClusterFunctionThread(ClusterModule.Chime.value, randomSeed=randomSeed)
        self._chimeTask.start()
        # climate functions
        # self._climateTask = ClusterFunctionThread(ClusterModule.Climate.value, randomSeed=randomSeed)
        # self._climateTask.start()
        # guage functions
        self._guageTask = ClusterFunctionThread(ClusterModule.Guage.value, randomSeed=randomSeed)
        self._guageTask.start()
        # setting functions
        # self._settingTask = ClusterFunctionThread(ClusterModule.Setting.value, randomSeed=randomSeed)
        # self._settingTask.start()
        # telltale functions
        self._telltaleTask = ClusterFunctionThread(ClusterModule.Telltale.value, randomSeed=randomSeed)
        self._telltaleTask.start()
        # vehicle control functions
        # self._vehiclecontrolTask = ClusterFunctionThread(ClusterModule.VehicleControl.value, randomSeed=randomSeed)
        # self._vehiclecontrolTask.start()
        # vehicle info functions
        # self._vehicleinfoTask = ClusterFunctionThread(ClusterModule.VehicleInfo.value, randomSeed=randomSeed)
        # self._vehicleinfoTask.start()
        # warning functions
        self._warningTask = ClusterFunctionThread(ClusterModule.Warning.value, randomSeed=randomSeed)
        self._warningTask.start()

    def stopClusterFunctions(self):
        if self._adassettingTask is not None:
            self._adassettingTask.stopTask()
            self._adassettingTask = None
        if self._adasTask is not None:
            self._adasTask.stopTask()
            self._adasTask = None
        if self._ambientlightTask is not None:
            self._ambientlightTask.stopTask()
            self._ambientlightTask = None
        if self._chimeTask is not None:
            self._chimeTask.stopTask()
            self._chimeTask = None
        if self._climateTask is not None:
            self._climateTask.stopTask()
            self._climateTask = None
        if self._guageTask is not None:
            self._guageTask.stopTask()
            self._guageTask = None
        if self._settingTask is not None:
            self._settingTask.stopTask()
            self._settingTask = None
        if self._telltaleTask is not None:
            self._telltaleTask.stopTask()
            self._telltaleTask = None
        if self._vehiclecontrolTask is not None:
            self._vehiclecontrolTask.stopTask()
            self._vehiclecontrolTask = None
        if self._vehicleinfoTask is not None:
            self._vehicleinfoTask.stopTask()
            self._vehicleinfoTask = None
        if self._warningTask is not None:
            self._warningTask.stopTask()
            self._warningTask = None

    def dumpQnxLogs(self):
        qnxLogFolder = FileUtil.generateAbsPath(self._caseFolder, "qnx_log")
        FileUtil.createFolder(qnxLogFolder)
        vehicleType = VehicleTypeManager.getInstance().getVehicleType()
        if vehicleType == ('557', 'MY26', 'BEV'):
            hamCoredumpsRemotePath = "/logdata/log/ham_coredumps"
            coredumpsRemotePath = "/logdata/log/coredumps"
            errMemLogRemotePath = "/logdata/log/errmemlog"
            miscRemotePath = "/logdata/log/misc"
            dltRemotePath = "/logdata/log/dlt_raw"
        else:
            hamCoredumpsRemotePath = "/var/log/ham_coredumps"
            coredumpsRemotePath = "/var/log/coredumps"
            errMemLogRemotePath = "/var/log/errmemlog"
            miscRemotePath = "/var/log/misc"
            dltRemotePath = "/var/log/dlt_raw"

        # pull out ham coredumps
        CommandExcutor.excute(PULL_OUT_HAM_COREDUMP_CMD.format(DeviceUtil.getSshAddress(), hamCoredumpsRemotePath, qnxLogFolder), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
        # pull out coredumps
        CommandExcutor.excute(PULL_OUT_COREDUMP_CMD.format(DeviceUtil.getSshAddress(), coredumpsRemotePath, qnxLogFolder), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
        # pull out errmemlog
        CommandExcutor.excute(PULL_OUT_ERROR_MEMORY_LOG_CMD.format(DeviceUtil.getSshAddress(), errMemLogRemotePath, qnxLogFolder), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
        # pull out misc
        CommandExcutor.excute(PULL_OUT_MISC_CMD.format(DeviceUtil.getSshAddress(), miscRemotePath, qnxLogFolder), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
        # pull out /persist/em/ folder
        CommandExcutor.excute(PULL_OUT_PERSIST_EM_FOLDER_CMD.format(DeviceUtil.getSshAddress(), qnxLogFolder), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
        # pull out dlt_raw
        CommandExcutor.excute(PULL_OUT_DLT_RAW_CMD.format(DeviceUtil.getSshAddress(), dltRemotePath, qnxLogFolder), timeout=PULL_OUT_DLT_TIMEOUT)

    def dumpMiniDumpLog(self):
        vehicleType = VehicleTypeManager.getInstance().getVehicleType()
        if vehicleType == ('557', 'MY26', 'BEV'):
            return

        CommandExcutor.excute(GENERATE_MINI_DUMP_CMD, timeout=MINI_DUMP_TIMEOUT)
        CommandExcutor.excute(PULL_OUT_MINI_DUMP_CMD.format(DeviceUtil.getSshAddress(), self._caseFolder), timeout=MINI_DUMP_TIMEOUT)
        CommandExcutor.excute(DELETE_REMOTE_MINI_DUMP_CMD, timeout=MINI_DUMP_TIMEOUT)

    def recordExceptionTime(self, file):
        try:
            iviDateTime = TimeUtil.getAndroidTimeStamp()
            qnxDateTime = TimeUtil.getQnxDateTime()
            localDateTime = TimeUtil.getCurrentDateTime()

            content = f"iviDateTime: {iviDateTime}\nqnxDateTime: {qnxDateTime}\nlocalDateTime: {localDateTime}"
            FileUtil.writeFile(file, content)
        except Exception as exp:
            LogUtil.get_logger().info(f"recordExceptionTime caught exp: {exp}")

    def getIncLogs(self):
        try:
            LogUtil.get_logger().info("start inc log...")
            CommandExcutor.excute(EXECUTE_INC_LOG_CMD, timeout=EXECUTE_INC_LOG_CMD_TIMEOUT)
            LogUtil.get_logger().info("end inc log...")
            CommandExcutor.excute(PULL_OUT_INC_LOG_CMD.format(DeviceUtil.getSshAddress(), self._caseFolder), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
            CommandExcutor.excute(DELETE_REMOTE_INC_CMD)
        except Exception as exp:
            LogUtil.get_logger().info(f"getIncLogs caught exp: {exp}")

    def getEmTrace(self):
        try:
            LogUtil.get_logger().info("start em trace...")
            CommandExcutor.excute(EXECUTE_EM_TRACE_CMD)
            LogUtil.get_logger().info("end em trace...")
            time.sleep(5)
            CommandExcutor.excute(PULL_OUT_EM_TRACE_CMD.format(DeviceUtil.getSshAddress(), self._caseFolder), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
            CommandExcutor.excute(DELETE_REMOTE_EM_TRACE_CMD)
        except Exception as exp:
            LogUtil.get_logger().info(f"getEmTrace caught exp: {exp}")

    def recordBacklight(self):
        try:
            vehicleProject = VehicleTypeManager.getInstance().getVehicleType()
            if vehicleProject == ('557', 'MY26', 'BEV'):
                LogUtil.get_logger().info("start record backlight for 557.")
                file = FileUtil.generateAbsPath(self._caseFolder, "vcu_backlight")
                CommandExcutor.startExcute(GET_VCU_BACKLIGHT_CMD.format(DeviceUtil.getSshAddress(),
                                                                        DisplayConstant.DisplayScreenBacklight.cluster.value), file, mode="a+")
                CommandExcutor.startExcute(GET_VCU_BACKLIGHT_CMD.format(DeviceUtil.getSshAddress(),
                                                                        DisplayConstant.DisplayScreenBacklight.center_control.value), file, mode="a+")
                CommandExcutor.startExcute(GET_VCU_BACKLIGHT_CMD.format(DeviceUtil.getSshAddress(),
                                                                        DisplayConstant.DisplayScreenBacklight.front_passenger.value), file, mode="a+")
                CommandExcutor.startExcute(GET_VCU_BACKLIGHT_CMD.format(DeviceUtil.getSshAddress(),
                                                                        DisplayConstant.DisplayScreenBacklight.ceiling.value), file, mode="a+")
        except Exception as exp:
            LogUtil.get_logger().info(f"recordBacklight caught exp: {exp}")

    def onExceptionFinish(self):
        LogUtil.get_logger().info("onExceptionFinish start")
        self._exception = True
        CloudTestReporter.addReport(TimeUtil.getCurrentDateTime(), "stress", False, reason="exceptionChecker find error.")
        self.stopExceptionChecker()
        self.stopClusterFunctions()
        self.stopMonkeyTest()
        self.recordExceptionTime(FileUtil.generateAbsPath(self._caseFolder, "exception_datetime"))
        # trigger inc_logger
        self.getIncLogs()
        # trigger em trace
        self.getEmTrace()
        # execute dumpLogs.sh and pull out log
        SshExecutor.execSshCommand(DeviceUtil.getSshAddress(), START_DUMP_SCRIPT_CMD)
        time.sleep(30)
        LogUtil.get_logger().info("start pull out qnx dump logs")
        CommandExcutor.excute(PULL_OUT_DUMP_LOGS_CMD.format(DeviceUtil.getSshAddress(), self._caseFolder), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
        # trigger display logs
        DisplayLogger.getInstance().startLog(self._caseFolder, asyncMode=False)
        # wait 1 minute
        time.sleep(60)
        self.stopRecordVideo()
        # record vcu backlight
        self.recordBacklight()
        self.onFinish()
        # pull out qnx logs
        LogUtil.get_logger().info("start pull out qnx logs")
        self.dumpQnxLogs()
        # pull out mini_dump log
        LogUtil.get_logger().info("start pull out mini_dump log")
        self.dumpMiniDumpLog()
        # trigger usblog
        LogUtil.get_logger().info("start pull out usblogs")
        UsbLogger.getInstance().startDump()
        LogUtil.get_logger().info("onExceptionFinish end")

    def startExceptionChecker(self, module):
        self._expChecker = ExceptionChecker(module=module)
        self._expChecker.start()

    def stopExceptionChecker(self):
        if self._expChecker is not None:
            self._expChecker.stopTask()
            self._expChecker = None

    def startSystemServiceChecker(self):
        self._sysServiceChecker = SystemServiceChecker(self._caseFolder)
        self._sysServiceChecker.start()

    def switchTheme(self):
        if self._nightThemeState:
            self._nightThemeState = False
        else:
            self._nightThemeState = True

        ThemesManager.getInstance().setNightTheme(self._nightThemeState)
        self.startThemeSwitchTimer()

    def startThemeSwitchTimer(self):
        self._themeSwitchTimer = threading.Timer(THEME_SWITCH_INTERVAL, self.switchTheme)
        self._themeSwitchTimer.start()

    def stopThemeSwitchTimer(self):
        if self._themeSwitchTimer is not None:
            self._themeSwitchTimer.cancel()
            self._themeSwitchTimer = None

    def stopSystemServiceChecker(self):
        if self._sysServiceChecker is not None:
            self._sysServiceChecker.stopTask()
            self._sysServiceChecker = None

    def startRecordVideo(self, videoPath):
        try:
            FileUtil.createFolder(videoPath)
            # AT.cameraStartBatchRecord(videoPath, CAMERA_INDEX, CAMERA_RECORD_DURATION, timeout=CAMREA_API_TIMEOUT)
            self._videoRecordTask = VideoRecorderTask(videoPath)
            self._videoRecordTask.start()
        except Exception as exp:
            LogUtil.get_logger().info(f"startRecordVideo caught exp: {exp}")

    def stopRecordVideo(self):
        try:
            # AT.cameraStopRecord(CAMERA_INDEX)
            if self._videoRecordTask is not None:
                self._videoRecordTask.stopRecord()
                self._videoRecordTask = None
        except Exception as exp:
            LogUtil.get_logger().info(f"stopRecordVideo caught exp: {exp}")

    def startVipSocHeart(self, caseFolder):
        try:
            self._vipSocHeart = VipSocHeart(caseFolder)
            self._vipSocHeart.start()
        except Exception as exp:
            LogUtil.get_logger().info(f"startVipSocHeart caught exp: {exp}")

    def stopVipSocHeart(self):
        try:
            if self._vipSocHeart is not None:
                self._vipSocHeart.stopTask()
                self._vipSocHeart = None
        except Exception as exp:
            LogUtil.get_logger().info(f"stopVipSocHeart caught exp: {exp}")

    def setStressProperty(self):
        try:
            retcode, response = CommandExcutor.excute(SET_STRESS_AUTOMATION_PROPERTY_CMD.format(1), shell=True)
            if retcode != Constant.ExcuteCommandResult.success.value:
                return False

            retcode, response = CommandExcutor.excute(GET_STRESS_AUTOMATION_PROPERTY_CMD, shell=True)
            if retcode != Constant.ExcuteCommandResult.success.value:
                return False

            stressPropertyValue = response.splitlines()[0].strip()
            LogUtil.get_logger().info(f"stressPropertyValue: {stressPropertyValue}")
            return stressPropertyValue == "1"
        except Exception as exp:
            LogUtil.get_logger().info(f"setStressProperty caught exp: {exp}")
            return False

    def clearStressProperty(self):
        try:
            CommandExcutor.excute(SET_STRESS_AUTOMATION_PROPERTY_CMD.format(0), shell=True)
        except Exception as exp:
            LogUtil.get_logger().info(f"clearStressProperty caught exp: {exp}")

    @setup(Constant.ScenarioType.stress.value)
    def setup(self, logFolder=None):
        self._caseFolder = logFolder
        ret = self.init(logFolder, Constant.ScenarioType.stress.value, CASE_DURATION, finishEvent=EventConstant.eventName.monkeyFinished.value)
        if not ret:
            LogUtil.get_logger().info("SystemPressureRunner, init failed...")
            sys.exit(0)

        # register exception event
        EventEmitter.getInstance().register(EventConstant.eventName.pressureExceptionEvent.value, self.onExceptionFinish, module=EventConstant.EventModule.performance.value)
        # set stress automation property to prevent notification
        ret = self.setStressProperty()
        if not ret:
            LogUtil.get_logger().info("set stress property failed...")
            sys.exit(0)

    def main(self):
        self.startRecordVideo(FileUtil.generateAbsPath(self._caseFolder, "video"))
        # start dump performance datas
        self.dumpDatas(appMonitor=True, dumpDmaMemInfo=True)
        # start vip soc heart
        self.startVipSocHeart(self._caseFolder)
        self.startSystemServiceChecker()
        self.startClusterFunctions()
        if START_MONKEY:
            self.startMonkeyTest(packageActivity=SINGLE_APP_MONKEY_PACKAGE_ACTIVITY)

        self.startExceptionChecker(EventConstant.EventModule.performance.value)
        self.startThemeSwitchTimer()
        self.waitFinish(durationSec=CASE_DURATION)

    @teardown
    def teardown(self):
        try:
            self.stopThemeSwitchTimer()
            self.stopVipSocHeart()
            self.stopExceptionChecker()
            self.stopClusterFunctions()
            self.stopMonkeyTest()
            self.stopRecordVideo()
            self.stopSystemServiceChecker()
            self.onFinish()

            EventEmitter.getInstance().unregister(EventConstant.eventName.pressureExceptionEvent.value, module=EventConstant.EventModule.performance.value)
            # reset stress automation property
            self.clearStressProperty()
        except Exception as exp:
            LogUtil.get_logger().info(f"SystemPressureRunner teardown caught exp: {exp}")
        finally:
            CanBusClient.getInstance().close()
            if not self._exception:
                CloudTestReporter.addReport(TimeUtil.getCurrentDateTime(), "stress", True)


if __name__ == '__main__':
    stress = SystemPressureRunner()
    try:
        stress.setup()
        stress.main()
    except KeyboardInterrupt:
        LogUtil.get_logger().info("SystemPressureRunner is stopped manually!!!")
    finally:
        stress.teardown()
