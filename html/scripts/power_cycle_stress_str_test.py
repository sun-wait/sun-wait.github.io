from constant.PowerCycleConstant import PowerCycleConstant
from customLib.common.Utils import LogUtil
from customLib.common.TimeUtil import TimeUtil
from customLib.powercycle.PowerCycleScenario import PowerCycleScenario, PowerCycleError
from customAPI.case_decorator.LifeCycle import teardown as teardown_deco
from customAPI.case_reporter.CaseReporter import CloudTestReporter
from customLib.performance.MonkeyMonitor import MonkeyMonitor
from customLib.cluster.MessageSender import ClusterModule
from customLib.performance.system_pressure.ClusterFunctionThread import ClusterFunctionThread
from customAPI.uiautomator.presenter.BasicModulePresenter import BaseBasicModulePresenter

import time

TEST_DURATION = 24*60*60  # 1 day


class STRStressRunner(PowerCycleScenario):

    def __init__(self):
        super().__init__()
        # initialize stress thread
        self._telltaleTask = self._warningTask = self._adasTask = self._guageTask = self._climateTask = self._ambientLightTask = self._chimeTask = None
        self._monkey_monitor = None

    def start_cluster_functions(self):
        # telltale functions
        self._telltaleTask = ClusterFunctionThread(ClusterModule.Telltale.value)
        self._telltaleTask.start()
        # warning functions
        # self._warningTask = ClusterFunctionThread(ClusterModule.Warning.value)
        # self._warningTask.start()
        # guage functions
        self._guageTask = ClusterFunctionThread(ClusterModule.Guage.value)
        self._guageTask.start()
        # adas functions
        self._adasTask = ClusterFunctionThread(ClusterModule.Adas.value)
        self._adasTask.start()
        # climate functions
        self._climateTask = ClusterFunctionThread(ClusterModule.Climate.value)
        self._climateTask.start()
        # ambient light functions
        self._ambientLightTask = ClusterFunctionThread(ClusterModule.AmbientLight.value)
        self._ambientLightTask.start()
        # chime functions
        self._chimeTask = ClusterFunctionThread(ClusterModule.Chime.value)
        self._chimeTask.start()

    def stop_cluster_functions(self):
        if self._telltaleTask is not None:
            self._telltaleTask.stopTask()
            self._telltaleTask.resetAllFuntions()
            self._telltaleTask = None
        if self._warningTask is not None:
            self._warningTask.stopTask()
            self._warningTask.resetAllFuntions()
            self._warningTask = None
        if self._adasTask is not None:
            self._adasTask.stopTask()
            self._adasTask.resetAllFuntions()
            self._adasTask = None
        if self._guageTask is not None:
            self._guageTask.stopTask()
            self._guageTask.resetAllFuntions()
            self._guageTask = None
        if self._climateTask is not None:
            self._climateTask.stopTask()
            self._climateTask.resetAllFuntions()
            self._climateTask = None
        if self._ambientLightTask is not None:
            self._ambientLightTask.stopTask()
            self._ambientLightTask.resetAllFuntions()
            self._ambientLightTask = None
        if self._chimeTask is not None:
            self._chimeTask.stopTask()
            self._chimeTask.resetAllFuntions()
            self._chimeTask = None

    def start_monkey_test(self):
        # back to launcher
        BaseBasicModulePresenter.getPresenter().enter_launcher_page()
        # start monkey
        self._monkey_monitor = MonkeyMonitor(monkeyLogFolder=self._cycle_folder_name)
        self._monkey_monitor.start()

    def stop_monkey_test(self):
        if self._monkey_monitor is not None:
            self._monkey_monitor.stopTask()
            self._monkey_monitor = None

    def teardown(self):
        # stop stress test here
        self.stop_cluster_functions()
        self.stop_monkey_test()
        # /stop stress test here
        super().teardown()
        # 云测报告结果上传
        CloudTestReporter.addReport(TimeUtil.getCurrentDateTime(), "power_cycle", self._test_result, reason="na" if self._test_result else "exceptionChecker find error.")

    def __exit__(self, exc_type, exc_val, exc_tb):
        # stop stress test here
        self.stop_cluster_functions()
        self.stop_monkey_test()
        # /stop stress test here
        super().__exit__(exc_type, exc_val, exc_tb)

    @teardown_deco
    def main(self):
        # setup
        self.power_cycle_pre_work()
        # start test
        test_start = time.time()
        try:
            while time.time() - test_start <= TEST_DURATION:
                with self:
                    # put stress test here, now sleep 3 minutes for silent scenario
                    self.start_cluster_functions()
                    self.start_monkey_test()
                    time.sleep(3 * 60)
                    # /put stress test here, now sleep 3 minutes for silent scenario
                    self._wakeup_type = PowerCycleConstant.WakeupType.SUSPEND_TO_RAM.value  # free to define if you need STR/Cold Boot/Pullback test
            else:
                LogUtil.get_logger().info(f"Power cycle finishes successfully")
                self._test_result = True
        except PowerCycleError as e:
            LogUtil.get_logger().info(f"Power cycle exception detected: {e}")
            return
        except KeyboardInterrupt:
            self._test_result = True
            LogUtil.get_logger().info("PowerCycle is stopped manually!!!")
        finally:
            self.teardown()


if __name__ == '__main__':
    test = STRStressRunner()
    test.main()
