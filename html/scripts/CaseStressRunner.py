from customLib.common.CommandExcutor import CommandExcutor, SshExecutor
from customLib.common.DeviceUtil import DeviceUtil
from customLib.common.Utils import FileUtil
from customLib.common.TimeUtil import TimeUtil
from customLib.common.VehicleTypeManager import VehicleTypeManager
from constant.Constant import Constant
from constant.EventConstant import EventConstant
from customLib.event.EventEmitter import EventEmitter
from customLib.loggers.modules.display.DisplayLogger import DisplayLogger
from customLib.loggers.UsbLogger import UsbLogger
from customLib.loggers.system.VipSocHeart import VipSocHeart
from customLib.opencv.Camera import VideoRecorderTask
from customLib.performance.BaseScenarioRunner import BaseScenarioRunner
from customLib.performance.system_pressure.ExceptionChecker import ExceptionChecker
from customLib.performance.system_pressure.SystemServiceChecker import SystemServiceChecker
from config.ConfigParser import ConfigParser
from customLib.common.Utils import LogUtil
from customAPI.case_decorator.LifeCycle import setup, teardown


import importlib
import random
import sys
import time


SCENARIO = "CaseStressRunner"
HIGH_PRESSURE_FOLDER = "case_pressure_test"
CASE_PATH = Constant.MEMORY_CPU_PATH + HIGH_PRESSURE_FOLDER

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

GET_IVI_DATETIME_CMD = "adb shell date"
SET_STRESS_AUTOMATION_PROPERTY_CMD = "adb shell setprop test.automation.stress {}"
GET_STRESS_AUTOMATION_PROPERTY_CMD = "adb shell getprop test.automation.stress"

MONKEY_RUN_TIMES = 19000  # about 2 hours
PULL_OUT_LOGS_TIMEOUT_DEFAULT = 60  # 60 secs
PULL_OUT_DLT_TIMEOUT = 2000  # 2000 secs
MINI_DUMP_TIMEOUT = 3000  # 3000 secs
EXECUTE_INC_LOG_CMD_TIMEOUT = 30  # 30 secs
CASE_DURATION = 3600 * 24 * 3  # 3 days

CAMERA_INDEX = "1"
CAMERA_RECORD_DURATION = "20"  # 20 minutes
CAMREA_API_TIMEOUT = "5"  # 5 secs

THEME_SWITCH_INTERVAL = 5 * 60  # 5 minutes

START_MONKEY = True
SINGLE_APP_MONKEY_PACKAGE_ACTIVITY = None


class CaseStressRunner(BaseScenarioRunner):

    def __init__(self):
        BaseScenarioRunner.__init__(self)
        self._isFinish = False
        self._videoRecordTask = None
        self._expChecker = None
        self._monkeyMonitor = None
        self._vipSocHeart = None
        self._sysServiceChecker = None

    def info(self):
        pass

    def fakeInit(self, caseFolder, scenarioType, duration, wifiConnect=False, finishEvent=None, finishCallback=None):
        LogUtil.get_logger().info("CaseStressRunner fakeInit...")
        return True

    def fakeDumpDatas(self, scenario=None, caseFolder=None, appMonitor=False, dumpDmaMemInfo=False, ioPackage=None):
        LogUtil.get_logger().info("CaseStressRunner fakeDumpDatas...")
        return True

    def fakeWaitFinish(self, durationSec=0, finishEvent=None):
        LogUtil.get_logger().info("CaseStressRunner fakeWaitFinish...")
        pass

    def startRecordVideo(self, videoPath):
        try:
            FileUtil.createFolder(videoPath)
            # AT.cameraStartBatchRecord(videoPath, CAMERA_INDEX, CAMERA_RECORD_DURATION, timeout=CAMREA_API_TIMEOUT)
            self._videoRecordTask = VideoRecorderTask(videoPath)
            self._videoRecordTask.start()
        except Exception as exp:
            LogUtil.get_logger().info(f"startRecordVideo caught exp: {exp}")

    def startVipSocHeart(self, caseFolder):
        try:
            self._vipSocHeart = VipSocHeart(caseFolder)
            self._vipSocHeart.start()
        except Exception as exp:
            LogUtil.get_logger().info(f"startVipSocHeart caught exp: {exp}")

    def startSystemServiceChecker(self):
        self._sysServiceChecker = SystemServiceChecker(CASE_PATH)
        self._sysServiceChecker.start()

    def startExceptionChecker(self, module):
        self._expChecker = ExceptionChecker(module=module)
        self._expChecker.start()

    def startRandomCase(self, duration):
        # set random seed
        randomSeed = ConfigParser.getInstance().get("STRESS_RANDOM_SEED")
        random.seed(randomSeed)

        moduleInstance = None
        startTime = time.time()

        while time.time() - startTime < duration:
            try:
                baseCaseFolder = FileUtil.getProjectDir()
                senarioFolder = FileUtil.generateAbsPath(baseCaseFolder, "Configuration", "UserModule", "multi_scenario")
                modules = FileUtil.listDir(senarioFolder)
                LogUtil.get_logger().info(f"startRandomCase modules: {modules}")
                module = random.sample(modules, 1)[0]

                moduleFolder = FileUtil.generateAbsPath(senarioFolder, module)
                cases = FileUtil.listDir(moduleFolder)
                caseFile = random.sample(cases, 1)[0]
                if not caseFile.endswith(".py"):
                    LogUtil.get_logger().info(f"{caseFile} is not a standard python file.")
                    continue

                case = caseFile.split(".")[0]
                LogUtil.get_logger().info(f"ready to start {module} ====> {case}")

                importPath = f"ATScripts.UserModule.multi_scenario.{module}.{case}"
                importModule = importlib.import_module(importPath)
                moduleClass = getattr(importModule, "testApp")
                moduleInstance = moduleClass()
                moduleInstance.init = self.fakeInit
                moduleInstance.dumpDatas = self.fakeDumpDatas
                moduleInstance.waitFinish = self.fakeWaitFinish

                moduleInstance.setup()
                moduleInstance.main()
                moduleInstance.teardown()

                time.sleep(2)
            except Exception as exp:
                LogUtil.get_logger().info(f"startRandomCase caught exp: {exp}")
                continue
            finally:
                if moduleInstance is not None:
                    del moduleInstance
                    moduleInstance = None

    def stopExceptionChecker(self):
        if self._expChecker is not None:
            self._expChecker.stopTask()
            self._expChecker = None

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
            CommandExcutor.excute(PULL_OUT_INC_LOG_CMD.format(DeviceUtil.getSshAddress(), CASE_PATH), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
            CommandExcutor.excute(DELETE_REMOTE_INC_CMD)
        except Exception as exp:
            LogUtil.get_logger().info(f"getIncLogs caught exp: {exp}")

    def getEmTrace(self):
        try:
            LogUtil.get_logger().info("start em trace...")
            CommandExcutor.excute(EXECUTE_EM_TRACE_CMD)
            LogUtil.get_logger().info("end em trace...")
            time.sleep(5)
            CommandExcutor.excute(PULL_OUT_EM_TRACE_CMD.format(DeviceUtil.getSshAddress(), CASE_PATH), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
            CommandExcutor.excute(DELETE_REMOTE_EM_TRACE_CMD)
        except Exception as exp:
            LogUtil.get_logger().info(f"getEmTrace caught exp: {exp}")

    def stopRecordVideo(self):
        try:
            # AT.cameraStopRecord(CAMERA_INDEX)
            if self._videoRecordTask is not None:
                self._videoRecordTask.stopRecord()
                self._videoRecordTask = None
        except Exception as exp:
            LogUtil.get_logger().info(f"stopRecordVideo caught exp: {exp}")

    def dumpQnxLogs(self):
        qnxLogFolder = FileUtil.generateAbsPath(CASE_PATH, "qnx_log")
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
        CommandExcutor.excute(PULL_OUT_MINI_DUMP_CMD.format(DeviceUtil.getSshAddress(), CASE_PATH), timeout=MINI_DUMP_TIMEOUT)
        CommandExcutor.excute(DELETE_REMOTE_MINI_DUMP_CMD, timeout=MINI_DUMP_TIMEOUT)

    def stopVipSocHeart(self):
        try:
            if self._vipSocHeart is not None:
                self._vipSocHeart.stopTask()
                self._vipSocHeart = None
        except Exception as exp:
            LogUtil.get_logger().info(f"stopVipSocHeart caught exp: {exp}")

    def stopSystemServiceChecker(self):
        if self._sysServiceChecker is not None:
            self._sysServiceChecker.stopTask()
            self._sysServiceChecker = None

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

    def onExceptionFinish(self):
        LogUtil.get_logger().info("onExceptionFinish start")
        self.stopExceptionChecker()
        self.recordExceptionTime(FileUtil.generateAbsPath(CASE_PATH, "exception_datetime"))
        # trigger inc_logger
        self.getIncLogs()
        # trigger em trace
        self.getEmTrace()
        # execute dumpLogs.sh and pull out log
        SshExecutor.execSshCommand(DeviceUtil.getSshAddress(), START_DUMP_SCRIPT_CMD)
        time.sleep(30)
        LogUtil.get_logger().info("start pull out qnx dump logs")
        CommandExcutor.excute(PULL_OUT_DUMP_LOGS_CMD.format(DeviceUtil.getSshAddress(), CASE_PATH), timeout=PULL_OUT_LOGS_TIMEOUT_DEFAULT)
        # trigger display logs
        DisplayLogger.getInstance().startLog(CASE_PATH, asyncMode=False)
        # wait 1 minute
        time.sleep(60)
        self.stopRecordVideo()
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

    @setup(SCENARIO)
    def setup(self, logFolder=None):
        LogUtil.get_logger().info("CaseStressRunner setup...")
        ret = self.init(CASE_PATH, Constant.ScenarioType.worse_case.value, CASE_DURATION, finishEvent=EventConstant.eventName.monkeyFinished.value)
        if not ret:
            LogUtil.get_logger().info("CaseStressRunner, init failed...")
            sys.exit(0)

        # register exception event
        EventEmitter.getInstance().register(EventConstant.eventName.pressureExceptionEvent.value, self.onExceptionFinish, module=EventConstant.EventModule.performance.value)
        # set stress automation property to prevent notification
        ret = self.setStressProperty()
        if not ret:
            LogUtil.get_logger().info("set stress property failed...")
            sys.exit(0)

    def main(self):
        LogUtil.get_logger().info("CaseStressRunner main...")
        try:
            self.startRecordVideo(FileUtil.generateAbsPath(CASE_PATH, "video"))
            # start dump performance datas
            self.dumpDatas(appMonitor=True, dumpDmaMemInfo=True)
            # start vip soc heart
            self.startVipSocHeart(CASE_PATH)
            self.startSystemServiceChecker()
            self.startExceptionChecker(EventConstant.EventModule.performance.value)
            self.startRandomCase(CASE_DURATION)
        except Exception as exp:
            LogUtil.get_logger().info(f"main caught exp: {exp}")
        finally:
            self.waitFinish()

    @teardown
    def teardown(self):
        LogUtil.get_logger().info("CaseStressRunner teardown...")
        self.stopVipSocHeart()
        self.stopExceptionChecker()
        self.stopRecordVideo()
        self.stopSystemServiceChecker()
        self.onFinish()

        EventEmitter.getInstance().unregister(EventConstant.eventName.pressureExceptionEvent.value, module=EventConstant.EventModule.performance.value)
        # reset stress automation property
        self.clearStressProperty()


if __name__ == '__main__':
    stress = CaseStressRunner()
    try:
        stress.setup()
        stress.main()
    except KeyboardInterrupt:
        LogUtil.get_logger().info("CaseStressRunner is stopped manually!!!")
    finally:
        stress.teardown()
