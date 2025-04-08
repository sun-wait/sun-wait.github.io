# UI自动化 (UIAutomator) API 参考

本文档提供了 customLib 库中 UI 自动化模块的详细 API 参考，包括各个类和方法的描述、参数说明和使用示例。

## BasePage

`BasePage` 类是所有页面对象的基类，提供了基本的 UI 元素查找和操作方法。

### 主要方法

#### `__init__(device)`

构造函数，初始化 BasePage 对象。

**参数**：

- `device` (Device): 设备对象

**示例**：

```python
from customLib.uiautomator.pages.BasePage import BasePage
from customLib.common.DeviceUtil import DeviceUtil

# 获取设备对象
device = DeviceUtil.getDevice()

# 创建基础页面对象
base_page = BasePage(device)
```

#### `find_element_by_id(resource_id, timeout=10)`

通过资源 ID 查找元素。

**参数**：

- `resource_id` (str): 资源 ID
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：元素对象，未找到则返回 None

**示例**：

```python
# 通过 ID 查找元素
element = base_page.find_element_by_id("com.example.app:id/button_login")
if element:
    element.click()
```

#### `find_element_by_text(text, timeout=10)`

通过文本内容查找元素。

**参数**：

- `text` (str): 文本内容
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：元素对象，未找到则返回 None

**示例**：

```python
# 通过文本查找元素
element = base_page.find_element_by_text("登录")
if element:
    element.click()
```

#### `find_element_by_description(description, timeout=10)`

通过内容描述查找元素。

**参数**：

- `description` (str): 内容描述
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：元素对象，未找到则返回 None

**示例**：

```python
# 通过描述查找元素
element = base_page.find_element_by_description("登录按钮")
if element:
    element.click()
```

#### `find_element_by_xpath(xpath, timeout=10)`

通过 XPath 查找元素。

**参数**：

- `xpath` (str): XPath 表达式
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：元素对象，未找到则返回 None

**示例**：

```python
# 通过 XPath 查找元素
element = base_page.find_element_by_xpath("//android.widget.Button[@text='登录']")
if element:
    element.click()
```

#### `click_element_by_id(resource_id, timeout=10)`

点击指定 ID 的元素。

**参数**：

- `resource_id` (str): 资源 ID
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：布尔值，表示操作是否成功

**示例**：

```python
# 点击指定 ID 的元素
success = base_page.click_element_by_id("com.example.app:id/button_login")
print(f"点击结果: {'成功' if success else '失败'}")
```

#### `click_element_by_text(text, timeout=10)`

点击指定文本的元素。

**参数**：

- `text` (str): 文本内容
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：布尔值，表示操作是否成功

**示例**：

```python
# 点击指定文本的元素
success = base_page.click_element_by_text("登录")
print(f"点击结果: {'成功' if success else '失败'}")
```

#### `input_text(resource_id, text, timeout=10)`

在指定 ID 的输入框中输入文本。

**参数**：

- `resource_id` (str): 资源 ID
- `text` (str): 要输入的文本
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：布尔值，表示操作是否成功

**示例**：

```python
# 在输入框中输入文本
success = base_page.input_text("com.example.app:id/edit_username", "testuser")
print(f"输入结果: {'成功' if success else '失败'}")
```

#### `swipe(start_x, start_y, end_x, end_y, steps=10)`

执行滑动操作。

**参数**：

- `start_x` (int): 起始点 X 坐标
- `start_y` (int): 起始点 Y 坐标
- `end_x` (int): 结束点 X 坐标
- `end_y` (int): 结束点 Y 坐标
- `steps` (int): 滑动步数，默认为 10

**示例**：

```python
# 执行滑动操作
base_page.swipe(500, 1000, 500, 200)
```

#### `swipe_up(steps=10)`

向上滑动。

**参数**：

- `steps` (int): 滑动步数，默认为 10

**示例**：

```python
# 向上滑动
base_page.swipe_up()
```

#### `swipe_down(steps=10)`

向下滑动。

**参数**：

- `steps` (int): 滑动步数，默认为 10

**示例**：

```python
# 向下滑动
base_page.swipe_down()
```

#### `swipe_left(steps=10)`

向左滑动。

**参数**：

- `steps` (int): 滑动步数，默认为 10

**示例**：

```python
# 向左滑动
base_page.swipe_left()
```

#### `swipe_right(steps=10)`

向右滑动。

**参数**：

- `steps` (int): 滑动步数，默认为 10

**示例**：

```python
# 向右滑动
base_page.swipe_right()
```

#### `wait_for_element_by_id(resource_id, timeout=10)`

等待指定 ID 的元素出现。

**参数**：

- `resource_id` (str): 资源 ID
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：布尔值，表示元素是否出现

**示例**：

```python
# 等待元素出现
is_present = base_page.wait_for_element_by_id("com.example.app:id/text_welcome", 15)
print(f"元素是否出现: {'是' if is_present else '否'}")
```

#### `wait_for_element_by_text(text, timeout=10)`

等待指定文本的元素出现。

**参数**：

- `text` (str): 文本内容
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：布尔值，表示元素是否出现

**示例**：

```python
# 等待元素出现
is_present = base_page.wait_for_element_by_text("欢迎回来", 15)
print(f"元素是否出现: {'是' if is_present else '否'}")
```

#### `is_element_displayed_by_id(resource_id, timeout=5)`

检查指定 ID 的元素是否显示。

**参数**：

- `resource_id` (str): 资源 ID
- `timeout` (int): 超时时间（秒），默认为 5

**返回值**：布尔值，表示元素是否显示

**示例**：

```python
# 检查元素是否显示
is_displayed = base_page.is_element_displayed_by_id("com.example.app:id/text_welcome")
print(f"元素是否显示: {'是' if is_displayed else '否'}")
```

#### `is_element_displayed_by_text(text, timeout=5)`

检查指定文本的元素是否显示。

**参数**：

- `text` (str): 文本内容
- `timeout` (int): 超时时间（秒），默认为 5

**返回值**：布尔值，表示元素是否显示

**示例**：

```python
# 检查元素是否显示
is_displayed = base_page.is_element_displayed_by_text("欢迎回来")
print(f"元素是否显示: {'是' if is_displayed else '否'}")
```

## ElementLocator

`ElementLocator` 类提供了多种元素定位策略。

### 主要方法

#### `getInstance()`

获取 ElementLocator 的单例实例。

**返回值**：ElementLocator 实例

**示例**：

```python
from customLib.uiautomator.locators.ElementLocator import ElementLocator

# 获取单例实例
locator = ElementLocator.getInstance()
```

#### `find_element_by_id(device, resource_id, timeout=10)`

通过资源 ID 查找元素。

**参数**：

- `device` (Device): 设备对象
- `resource_id` (str): 资源 ID
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：元素对象，未找到则返回 None

**示例**：

```python
# 获取设备对象
device = DeviceUtil.getDevice()

# 通过 ID 查找元素
element = ElementLocator.getInstance().find_element_by_id(device, "com.example.app:id/button_login")
if element:
    element.click()
```

#### `find_element_by_text(device, text, timeout=10)`

通过文本内容查找元素。

**参数**：

- `device` (Device): 设备对象
- `text` (str): 文本内容
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：元素对象，未找到则返回 None

**示例**：

```python
# 通过文本查找元素
element = ElementLocator.getInstance().find_element_by_text(device, "登录")
if element:
    element.click()
```

#### `find_element_by_image(device, image_path, threshold=0.8, timeout=10)`

通过图像匹配查找元素。

**参数**：

- `device` (Device): 设备对象
- `image_path` (str): 图像路径
- `threshold` (float): 匹配阈值，默认为 0.8
- `timeout` (int): 超时时间（秒），默认为 10

**返回值**：元素坐标，未找到则返回 None

**示例**：

```python
# 通过图像匹配查找元素
position = ElementLocator.getInstance().find_element_by_image(device, "button_image.png")
if position:
    x, y = position
    device.click(x, y)
```

## KeyOperation

`KeyOperation` 类提供按键操作功能。

### 主要方法

#### `getInstance()`

获取 KeyOperation 的单例实例。

**返回值**：KeyOperation 实例

**示例**：

```python
from customLib.uiautomator.key.KeyOperation import KeyOperation

# 获取单例实例
key_op = KeyOperation.getInstance()
```

#### `press_home(device)`

按下 Home 键。

**参数**：

- `device` (Device): 设备对象

**示例**：

```python
# 按下 Home 键
KeyOperation.getInstance().press_home(device)
```

#### `press_back(device)`

按下返回键。

**参数**：

- `device` (Device): 设备对象

**示例**：

```python
# 按下返回键
KeyOperation.getInstance().press_back(device)
```

#### `press_recent(device)`

按下最近任务键。

**参数**：

- `device` (Device): 设备对象

**示例**：

```python
# 按下最近任务键
KeyOperation.getInstance().press_recent(device)
```

#### `press_power(device)`

按下电源键。

**参数**：

- `device` (Device): 设备对象

**示例**：

```python
# 按下电源键
KeyOperation.getInstance().press_power(device)
```

#### `press_volume_up(device)`

按下音量增大键。

**参数**：

- `device` (Device): 设备对象

**示例**：

```python
# 按下音量增大键
KeyOperation.getInstance().press_volume_up(device)
```

#### `press_volume_down(device)`

按下音量减小键。

**参数**：

- `device` (Device): 设备对象

**示例**：

```python
# 按下音量减小键
KeyOperation.getInstance().press_volume_down(device)
```

## WifiManager

`WifiManager` 类用于管理 WIFI 连接。

### 主要方法

#### `getInstance()`

获取 WifiManager 的单例实例。

**返回值**：WifiManager 实例

**示例**：

```python
from customLib.uiautomator.network.WifiManager import WifiManager

# 获取单例实例
wifi_manager = WifiManager.getInstance()
```

#### `connect(ssid, password)`

连接到指定的 WIFI 网络。

**参数**：

- `ssid` (str): WIFI 网络名称
- `password` (str): WIFI 密码

**返回值**：布尔值，表示连接是否成功

**示例**：

```python
# 连接 WIFI 网络
success = WifiManager.getInstance().connect("TestWiFi", "password123")
print(f"连接结果: {'成功' if success else '失败'}")
```

#### `disconnect()`

断开当前 WIFI 连接。

**返回值**：布尔值，表示断开是否成功

**示例**：

```python
# 断开 WIFI 连接
success = WifiManager.getInstance().disconnect()
print(f"断开结果: {'成功' if success else '失败'}")
```

#### `is_wifi_enabled()`

检查 WIFI 是否启用。

**返回值**：布尔值，表示 WIFI 是否启用

**示例**：

```python
# 检查 WIFI 是否启用
is_enabled = WifiManager.getInstance().is_wifi_enabled()
print(f"WIFI 是否启用: {'是' if is_enabled else '否'}")
```

#### `enable_wifi()`

启用 WIFI。

**返回值**：布尔值，表示启用是否成功

**示例**：

```python
# 启用 WIFI
success = WifiManager.getInstance().enable_wifi()
print(f"启用结果: {'成功' if success else '失败'}")
```

#### `disable_wifi()`

禁用 WIFI。

**返回值**：布尔值，表示禁用是否成功

**示例**：

```python
# 禁用 WIFI
success = WifiManager.getInstance().disable_wifi()
print(f"禁用结果: {'成功' if success else '失败'}")
```

## 页面对象示例

以下是一个页面对象的示例，展示如何使用 BasePage 类创建自定义页面对象。

### `HomePage` 类

```python
from customLib.uiautomator.pages.BasePage import BasePage

class HomePage(BasePage):
    # 元素 ID 常量
    MENU_BUTTON_ID = "com.example.app:id/menu_button"
    SETTINGS_BUTTON_ID = "com.example.app:id/settings_button"
    USER_INFO_ID = "com.example.app:id/user_info"
  
    def __init__(self, device):
        super().__init__(device)
  
    def open_menu(self):
        """打开菜单"""
        return self.click_element_by_id(self.MENU_BUTTON_ID)
  
    def open_settings(self):
        """打开设置页面"""
        if self.open_menu():
            return self.click_element_by_id(self.SETTINGS_BUTTON_ID)
        return False
  
    def get_user_info(self):
        """获取用户信息"""
        element = self.find_element_by_id(self.USER_INFO_ID)
        if element:
            return element.get_text()
        return None
  
    def wait_for_home_page(self, timeout=20):
        """等待首页加载完成"""
        return self.wait_for_element_by_id(self.MENU_BUTTON_ID, timeout)
```

### 使用页面对象

```python
from customLib.uiautomator.pages.HomePage import HomePage
from customLib.common.DeviceUtil import DeviceUtil

# 获取设备对象
device = DeviceUtil.getDevice()

# 创建首页对象
home_page = HomePage(device)

# 等待首页加载
if home_page.wait_for_home_page():
    print("首页加载完成")
  
    # 打开设置页面
    if home_page.open_settings():
        print("设置页面已打开")
  
    # 获取用户信息
    user_info = home_page.get_user_info()
    if user_info:
        print(f"用户信息: {user_info}")
```

## UI Watcher 示例

以下是一个 UI Watcher 的示例，展示如何处理弹窗和通知。

### `DialogWatcher` 类

```python
from customLib.uiautomator.watcher.BaseWatcher import BaseWatcher

class DialogWatcher(BaseWatcher):
    def __init__(self, device):
        super().__init__(device)
        self.register_watchers()
  
    def register_watchers(self):
        """注册监视器"""
        # 注册处理权限弹窗的监视器
        self.device.watcher("permission_dialog").when(
            text="允许"
        ).click(
            text="允许"
        )
      
        # 注册处理更新提示的监视器
        self.device.watcher("update_dialog").when(
            text="发现新版本"
        ).click(
            text="稍后再说"
        )
      
        # 注册处理通知的监视器
        self.device.watcher("notification").when(
            text="新消息"
        ).press(
            "back"
        )
  
    def start(self):
        """启动监视器"""
        self.device.watchers.run()
  
    def stop(self):
        """停止监视器"""
        self.device.watchers.remove_all()
```

### 使用 UI Watcher

```python
from customLib.uiautomator.watcher.DialogWatcher import DialogWatcher
from customLib.common.DeviceUtil import DeviceUtil

# 获取设备对象
device = DeviceUtil.getDevice()

# 创建对话框监视器
dialog_watcher = DialogWatcher(device)

try:
    # 启动监视器
    dialog_watcher.start()
  
    # 执行测试操作
    # ...
  
finally:
    # 停止监视器
    dialog_watcher.stop()
```
