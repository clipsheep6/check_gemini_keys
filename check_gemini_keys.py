#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import sys
import os
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

# 尝试导入必要的库，如果失败则给出安装提示
try:
    import google.generativeai as genai
    from google.api_core import exceptions
    from tqdm import tqdm
except ImportError:
    print("错误：缺少必要的库。请使用以下命令安装：")
    print("pip install -r requirements.txt")
    sys.exit(1)

# 全局设置，防止多次打印 API Key 相关的警告
os.environ['GRPC_VERBOSITY'] = 'ERROR'
os.environ['GLOG_minloglevel'] = '2'

def check_key(api_key: str, model_name: str) -> tuple[str, bool, str]:
    """
    检查单个 Gemini API Key 的可用性，并在失败时返回错误码。

    通过尝试创建一个简单的生成内容请求来验证。

    Args:
        api_key: 需要检查的 API Key。
        model_name: 用于测试的模型名称。

    Returns:
        一个元组 (api_key, is_valid, reason)，
        其中 is_valid 是布尔值，reason 是包含错误码的验证结果描述。
    """
    if not api_key or not api_key.strip():
        return api_key, False, "Key is empty"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(model_name)
        # 执行一个非常轻量级的调用来确认权限和API可用性
        model.generate_content(
            "Hi",
            generation_config={'max_output_tokens': 1},
            request_options={'timeout': 10} # 设置10秒超时
        )
        return api_key, True, "Valid"
    except exceptions.PermissionDenied:
        # HTTP 403: Key 无效、无权限或项目未启用 API
        return api_key, False, "Permission Denied (Code: 403): Invalid API Key, permission issue, or API not enabled."
    except exceptions.InvalidArgument:
        # HTTP 400: 通常是模型名称错误或 Key 格式不正确
        return api_key, False, f"Invalid Argument (Code: 400): Check if model name '{model_name}' is correct or Key is malformed."
    except exceptions.ResourceExhausted:
        # HTTP 429: 用量超额
        return api_key, False, "Resource Exhausted (Code: 429): Quota limit may have been reached."
    except exceptions.GoogleAPICallError as e:
        # 捕获其他所有 Google API 相关的错误
        code = e.code if hasattr(e, 'code') else 'N/A'
        return api_key, False, f"Google API Error (Code: {code}): {type(e).__name__}"
    except Exception as e:
        # 捕获非 Google API 的异常，如网络连接问题
        return api_key, False, f"An unexpected error occurred: {type(e).__name__}"

def main():
    """
    主执行函数：解析参数，读取输入，并发检查，格式化输出。
    """
    parser = argparse.ArgumentParser(
        description="校验 Google Gemini API Key 的可用性，并可选择输出格式。",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
使用示例:
  1. 从文件读取，将可用 Key 输出到控制台:
     python %(prog)s -i keys.txt

  2. 从文件读取，将可用 Key 保存到文件:
     python %(prog)s -i keys.txt -o valid_keys.txt

  3. 通过管道从控制台读取，输出到控制台:
     cat keys.txt | python %(prog)s

  4. 输出为 JSON 数组格式并保存到文件:
     python %(prog)s -i keys.txt -o valid_keys.json --format json_array

  5. 使用不同的模型和更高的并发数进行检查:
     python %(prog)s -i keys.txt -m gemini-2.0-flash-lite -w 30
"""
    )
    parser.add_argument(
        '-i', '--input-file', type=str,
        help='包含 API Keys 的输入文件路径 (每行一个)。\n如果未提供，则从标准输入读取。'
    )
    parser.add_argument(
        '-o', '--output-file', type=str,
        help='用于存储可用 API Keys 的输出文件路径。\n如果未提供，则输出到标准控制台。'
    )
    parser.add_argument(
        '-m', '--model', type=str, default='gemini-2.0-flash-lite',
        help='用于测试的 Gemini 模型名称。例如 gemini-2.5-flash，gemini-2.5-pro等'
    )
    parser.add_argument(
        '--format', choices=['list', 'json_array'], default='list',
        help='输出格式。\nlist: 每行一个Key (默认)。\njson_array: 输出为JSON数组字符串，例如 ["key1", "key2"]。'
    )
    parser.add_argument(
        '-w', '--workers', type=int, default=20,
        help='并发检查的线程数 (默认为 20)。'
    )
    args = parser.parse_args()

    # --- 1. 读取输入 ---
    try:
        if args.input_file:
            with open(args.input_file, 'r', encoding='utf-8') as f:
                keys_to_check = f.readlines()
        else:
            if sys.stdin.isatty():
                parser.print_help()
                sys.exit("\n错误: 请通过 -i 参数提供输入文件，或通过管道提供输入。")
            keys_to_check = sys.stdin.readlines()

        keys_to_check = [key.strip() for key in keys_to_check if key.strip()]
        if not keys_to_check:
            print("输入中未找到任何有效的 API Key。", file=sys.stderr)
            sys.exit(0)

    except FileNotFoundError:
        print(f"错误: 输入文件 '{args.input_file}' 未找到。", file=sys.stderr)
        sys.exit(1)

    # --- 2. 并发检查 ---
    valid_keys = []
    print(f"开始检查 {len(keys_to_check)} 个 Key，使用模型 '{args.model}'，并发数: {args.workers}...", file=sys.stderr)

    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        future_to_key = {executor.submit(check_key, key, args.model): key for key in keys_to_check}
        progress_bar = tqdm(as_completed(future_to_key), total=len(keys_to_check), desc="检查进度", unit="key", file=sys.stderr)

        for future in progress_bar:
            key, is_valid, reason = future.result()
            if is_valid:
                valid_keys.append(key)
            else:
                key_prefix = key[:8]
                progress_bar.write(f"  -> Key [{key_prefix}...] 失败: {reason}", file=sys.stderr)

    # --- 3. 格式化输出 ---
    if not valid_keys:
        output_data = ""
        print("\n检查完成，未找到可用的 Key。", file=sys.stderr)
    else:
        print(f"\n检查完成，找到 {len(valid_keys)} 个可用的 Key。", file=sys.stderr)
        if args.format == 'json_array':
            output_data = json.dumps(valid_keys, indent=2)
        else: # 'list' format
            output_data = "\n".join(valid_keys)

    # --- 4. 写入输出 ---
    if output_data:
        if args.output_file:
            try:
                with open(args.output_file, 'w', encoding='utf-8') as f:
                    f.write(output_data)
                    if args.format == 'list':
                        f.write('\n')
                print(f"结果已保存到: {args.output_file}", file=sys.stderr)
            except IOError as e:
                print(f"错误: 无法写入文件 '{args.output_file}': {e}", file=sys.stderr)
        else:
            print(output_data)

if __name__ == '__main__':
    main()
