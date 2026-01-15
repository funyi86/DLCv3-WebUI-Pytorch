"""Helpers for orchestrating DeepLabCut batch analysis across GPUs."""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Dict, List, Optional, Tuple

import streamlit as st


def create_and_start_analysis(
    folder_path: str,
    selected_files: List[str],
    config_path: str,
    gpu_count: int,
    current_time: str,
    selected_gpus: Optional[List[int]] = None,
) -> None:
    """Spawn DeepLabCut analysis jobs across the requested GPUs."""
    try:
        gpu_indices = list(range(gpu_count)) if selected_gpus is None else list(selected_gpus)
        use_cpu = False
        if not gpu_indices:
            use_cpu = True
            if gpu_count <= 0:
                st.warning(
                    "⚠️ 未检测到可用 GPU，将使用 CPU 运行 / No GPUs detected. Falling back to CPU."
                )
            else:
                st.warning(
                    "⚠️ 未选择 GPU，将使用 CPU 运行 / No GPUs selected. Falling back to CPU."
                )
            gpu_indices = [0]

        if use_cpu:
            st.write(f"调试信息 / Debug: {len(selected_files)} 个文件使用 CPU")
        else:
            st.write(
                f"调试信息 / Debug: {len(selected_files)} 个文件使用 {len(gpu_indices)} 个GPU"
            )

        if len(selected_files) < len(gpu_indices):
            st.warning(
                "文件数量少于GPU数量，部分GPU将不会被使用 / Not enough files for the number of GPUs. Some GPUs will not be used."
            )
            gpu_indices = gpu_indices[: len(selected_files)]

        if not selected_files:
            st.warning("未选择视频文件 / No videos selected for analysis")
            return

        files_per_gpu = len(selected_files) // len(gpu_indices)
        remaining_files = len(selected_files) % len(gpu_indices)

        file_groups: List[List[str]] = []
        start = 0
        for index in range(len(gpu_indices)):
            end = start + files_per_gpu + (1 if index < remaining_files else 0)
            file_groups.append(selected_files[start:end])
            start = end

        processes: List[Tuple[subprocess.Popen, str]] = []

        for group_num, files_group in enumerate(file_groups):
            if not files_group:
                continue

            gpu_index = gpu_indices[group_num]
            run_py_path = os.path.join(folder_path, f"run_gpu{gpu_index}.py")
            start_script_path = os.path.join(folder_path, f"start_analysis_gpu{gpu_index}.py")
            log_file_path = os.path.join(folder_path, f"output_gpu{gpu_index}.log")

            if use_cpu:
                analyze_videos_code = (
                    f"deeplabcut.analyze_videos(r'{config_path}', {files_group}, "
                    "videotype='mp4', shuffle=1, trainingsetindex=0, "
                    "save_as_csv=True)"
                )
            else:
                analyze_videos_code = (
                    f"deeplabcut.analyze_videos(r'{config_path}', {files_group}, "
                    "videotype='mp4', shuffle=1, trainingsetindex=0, "
                    f"gputouse={gpu_index}, save_as_csv=True)"
                )
            create_labeled_video_code = (
                f"deeplabcut.create_labeled_video(r'{config_path}', {files_group})"
            )

            run_content = (
                "import deeplabcut\n\n"
                f"{analyze_videos_code}\n\n"
                f"{create_labeled_video_code}\n"
            )
            with open(run_py_path, "w", encoding="utf-8") as handle:
                handle.write(run_content)

            start_content = (
                "import subprocess\n"
                "import sys\n\n"
                f"subprocess.run([sys.executable, r'{run_py_path}'], check=True)\n"
            )
            with open(start_script_path, "w", encoding="utf-8") as handle:
                handle.write(start_content)

            with open(log_file_path, "w", encoding="utf-8") as log_file:
                process = subprocess.Popen(
                    [sys.executable, start_script_path],
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    text=True,
                    cwd=folder_path,
                )
                device_label = "CPU" if use_cpu else f"GPU {gpu_index}"
                processes.append((process, device_label))

            st.success(
                f"✅ 已在{device_label}上启动分析任务 / Analysis task started on {device_label}"
            )

        for process, device_label in processes:
            process.wait()
            if process.returncode != 0:
                st.error(
                    f"❌ {device_label}上的分析任务出错 / Error encountered while running analysis on {device_label}"
                )

        general_log_path = os.path.join(folder_path, "general_log.txt")
        with open(general_log_path, "a", encoding="utf-8") as general_log:
            for _, device_label in processes:
                general_log.write(
                    f"[{current_time}] 在{device_label}上启动了分析 / Analysis started on {device_label}\n"
                )

    except Exception as exc:  # pragma: no cover - operational logging
        st.error(f"❌ 创建分析任务失败 / Failed to create analysis task: {exc}")
        raise


def fetch_last_lines_of_logs(
    folder_path: str,
    gpu_count: int = 1,
    num_lines: int = 20,
) -> Dict[str, str]:
    """Return the tail of each GPU log file."""
    last_lines: Dict[str, str] = {}
    encodings = ["utf-8", "gbk", "gb2312", "iso-8859-1"]

    group_total = gpu_count if gpu_count > 0 else 1
    for group_num in range(group_total):
        log_file_path = os.path.join(folder_path, f"output_gpu{group_num}.log")
        content = f"未找到日志文件 / Log file not found: {log_file_path}"

        if os.path.exists(log_file_path):
            for encoding in encodings:
                try:
                    with open(log_file_path, "r", encoding=encoding) as log_file:
                        lines = log_file.readlines()
                        content = "".join(lines[-num_lines:]) if lines else "没有日志记录 / No entries in log."
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as exc:
                    content = f"读取日志文件时出错 / Error reading log file: {exc}"
                    break

        last_lines[f"GPU{group_num} 日志 / Log"] = content

    return last_lines
