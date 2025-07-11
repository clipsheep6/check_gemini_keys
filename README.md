# Gemini API Key Checker

![Python Version](https://img.shields.io/badge/python-3.7+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

一个高效、可靠的 Python 脚本，用于批量并发校验 Google Gemini API Key 的可用性。

## ✨ 功能特性

- **⚡ 并发检测**: 使用多线程并发检查，极大提升处理大量 Key 的速度。
- **🔄 flexible I/O**: 支持从文件或标准输入流（管道）读取 Keys，并将结果输出到文件或标准输出流。
- **📝 多种输出格式**: 可将可用的 Keys 输出为纯文本列表（每行一个）或 JSON 数组格式。
- **🔧 模型可配置**: 默认使用 `gemini-1.5-flash-latest` 进行快速验证，并可通过参数轻松切换到其他模型。
- **📊 清晰的进度与报告**: 提供实时进度条，并将无效 Key 的失败原因（包含HTTP错误码）打印到标准错误流，不污染结果输出。
- **🛡️ 稳健的错误处理**: 精准捕获并报告因权限、额度、模型名称错误等导致的校验失败。

## ⚙️ 安装与准备

### 1. 先决条件
- Python 3.7 或更高版本

### 2. 安装
1.  克隆本仓库到本地：
    ```bash
    git clone https://github.com/your-username/gemini-key-checker.git
    cd gemini-key-checker
    ```

2.  安装所需的依赖库：
    ```bash
    pip install -r requirements.txt
    ```

## 🚀 使用方法

### 查看帮助信息
```bash
python check_gemini_keys.py --help
```

### 示例

假设你有一个名为 `keys.txt` 的文件，内容如下：
```
AIzaSy...VALID_KEY_1...
AIzaSy...INVALID_KEY_2...
AIzaSy...VALID_KEY_3...
```

**1. 基本用法：从文件读取，将可用 Key 输出到控制台**
```bash
python check_gemini_keys.py -i keys.txt
```
> **输出 (stdout):**
> ```
> AIzaSy...VALID_KEY_1...
> AIzaSy...VALID_KEY_3...
> ```

**2. 保存结果：将可用 Key 保存到文件**
```bash
python check_gemini_keys.py -i keys.txt -o valid_keys.txt
```
> 这将在控制台显示进度，并将可用的 Keys 写入 `valid_keys.txt` 文件。

**3. 使用管道 (Piping)**
```bash
cat keys.txt | python check_gemini_keys.py
```

**4. 转换格式：输出为 JSON 数组**
```bash
python check_gemini_keys.py -i keys.txt -o valid_keys.json --format json_array
```
> `valid_keys.json` 文件内容将会是：
> ```json
> [
>   "AIzaSy...VALID_KEY_1...",
>   "AIzaSy...VALID_KEY_3..."
> ]
> ```

**5. 高级用法：指定模型和并发数**
```bash
python check_gemini_keys.py -i keys.txt -m gemini-2.0-flash -w 20
```
> 使用 `gemini-2.0-flash` 模型和 20 个并发线程进行检查。


## 📜 理解输出

本脚本巧妙地利用了标准输出 (`stdout`) 和标准错误 (`stderr`)：

- **标准输出 (`stdout`)**: 只包含**最终的、可用的 Key 列表**。这种干净的输出使其非常适合与其他脚本进行管道连接或重定向。
- **标准错误 (`stderr`)**: 显示所有**辅助信息**，包括进度条、运行状态和详细的错误报告。

**失败原因示例 (显示在 `stderr` 中):**
```
-> Key [AIzaSyIN...] 失败: Permission Denied (Code: 403): Invalid API Key...
-> Key [AIzaSyQU...] 失败: Resource Exhausted (Code: 429): Quota limit may have been reached.
-> Key [AIzaSyAN...] 失败: Invalid Argument (Code: 400): Check if model name '...' is correct...
```

> [!NOTE]
> 如果您拥有访问gemini其他私有模型的权限，例如您可以通过 `-m gemini-2.5-pro` 参数来指定它。

## 📄 许可证

本项目采用 MIT 许可证。详情请参阅 [LICENSE](LICENSE) 文件。
