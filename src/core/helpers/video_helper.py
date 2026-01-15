import os
import cv2
import streamlit as st
import tempfile
import subprocess
from datetime import timedelta
import shutil
from src.core.utils.file_utils import sanitize_filename, safe_join

def get_video_info(video_path):
    """
    获取视频信息
    Get video information
    
    Args:
        video_path (str): 视频文件路径
        
    Returns:
        dict: 包含视频信息的字典
    """
    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        
        # 获取视频属性
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 检查fps是否为0，如果是则使用默认值30
        if fps == 0:
            st.warning(f"视频帧率获取失败，使用默认值30fps / Failed to get video FPS, using default value 30fps")
            fps = 30
            
        duration = total_frames / fps
        
        return {
            'fps': fps,
            'width': frame_width,
            'height': frame_height,
            'total_frames': total_frames,
            'duration': duration,
            'duration_str': str(timedelta(seconds=int(duration)))
        }
    except Exception as e:
        st.error(f"获取视频信息失败 / Failed to get video info: {str(e)}")
        return None
    finally:
        if cap is not None:
            cap.release()

def preview_original_frame(video_path, x=None, y=None, width=None, height=None):
    """
    预览带裁剪框的原始帧
    Preview original frame with crop box
    
    Args:
        video_path (str): 视频文件路径
        x (int, optional): 裁剪起始X坐标
        y (int, optional): 裁剪起始Y坐标
        width (int, optional): 裁剪宽度
        height (int, optional): 裁剪高度
        
    Returns:
        numpy.ndarray: 带裁剪框的原始帧图像
    """
    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 使用中间帧作为预览
        cap.set(cv2.CAP_PROP_POS_FRAMES, total_frames // 2)
        ret, frame = cap.read()
        
        if ret and all(v is not None for v in [x, y, width, height]):
            frame_with_rect = frame.copy()
            cv2.rectangle(frame_with_rect, (x, y), (x + width, y + height), (0, 255, 0), 2)
            frame_with_rect_rgb = cv2.cvtColor(frame_with_rect, cv2.COLOR_BGR2RGB)
            return frame_with_rect_rgb
    except Exception as e:
        st.error(f"预览帧失败 / Failed to preview frame: {str(e)}")
    finally:
        if cap is not None:
            cap.release()
    return None

def preview_cropped_frames(video_path, x=None, y=None, width=None, height=None):
    """
    预览视频的第一帧、中间帧和最后一帧的裁剪效果
    Preview cropped first, middle and last frames of the video
    
    Args:
        video_path (str): 视频文件路径
        x (int, optional): 裁剪起始X坐标
        y (int, optional): 裁剪起始Y坐标
        width (int, optional): 裁剪宽度
        height (int, optional): 裁剪高度
    """
    cap = None
    try:
        cap = cv2.VideoCapture(video_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # 获取三个关键帧的位置
        frame_positions = [0, total_frames // 2, total_frames - 1]
        frame_names = ["第一帧 / First Frame", "中间帧 / Middle Frame", "最后一帧 / Last Frame"]
        
        # 创建三列显示裁剪预览
        preview_cols = st.columns(3)
        
        for idx, (pos, name) in enumerate(zip(frame_positions, frame_names)):
            # 跳转到指定帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, pos)
            ret, frame = cap.read()
            
            if ret:
                # 如果提供了裁剪参数，显示裁剪区域
                if all(v is not None for v in [x, y, width, height]):
                    frame_height, frame_width = frame.shape[:2]
                    x0 = max(0, min(x, frame_width - 1))
                    y0 = max(0, min(y, frame_height - 1))
                    w0 = min(width, frame_width - x0)
                    h0 = min(height, frame_height - y0)
                    if w0 <= 0 or h0 <= 0:
                        with preview_cols[idx]:
                            st.warning("裁剪区域无效 / Invalid crop area")
                        continue
                    # 裁剪并显示裁剪后的区域
                    cropped_frame = frame[y0:y0+h0, x0:x0+w0]
                    cropped_frame_rgb = cv2.cvtColor(cropped_frame, cv2.COLOR_BGR2RGB)
                    with preview_cols[idx]:
                        st.image(cropped_frame_rgb, caption=name, use_container_width=True)
                else:
                    # 如果没有裁剪参数，显示原始帧
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    with preview_cols[idx]:
                        st.image(frame_rgb, caption=name, use_container_width=True)
        
    except Exception as e:
        st.error(f"预览帧失败 / Failed to preview frame: {str(e)}")
    finally:
        if cap is not None:
            cap.release()

def crop_video_files(folder_path, selected_files, start_time, duration, target_size=None, target_fps=None):
    """
    裁剪选定的视频文件
    Crop selected video files
    
    Args:
        folder_path (str): 工作目录路径
        selected_files (list): 选定的视频文件列表
        start_time (float): 开始时间（秒）
        duration (float): 持续时间（秒）
        target_size (tuple, optional): 目标分辨率 (宽, 高)
        target_fps (int, optional): 目标帧率
    """
    # 创建输出目录
    output_directory = os.path.join(folder_path, 'cropped')
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    
    for video_path in selected_files:
        cap = None
        out = None
        temp_output = None
        try:
            # 显示处理进度
            st.write(f"正在处理 / Processing: {os.path.basename(video_path)}")
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            
            # 获取视频属性
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            
            # 使用目标参数（如果提供）
            output_fps = target_fps if target_fps else fps
            if target_size:
                output_width, output_height = target_size
            else:
                output_width, output_height = frame_width, frame_height
            
            # 计算开始帧和结束帧
            start_frame = int(start_time * fps)
            end_frame = int((start_time + duration) * fps)
            
            # 设置输出文件名
            video_name = os.path.basename(video_path)
            output_name = f"cropped_{video_name}"
            output_path = os.path.join(output_directory, output_name)
            
            # 创建临时文件
            temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4').name
            
            # 创建视频写入器
            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(temp_output, fourcc, output_fps, (output_width, output_height))
            
            # 跳转到开始帧
            cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
            
            # 读取并写入帧
            frame_count = 0
            total_frames = end_frame - start_frame
            
            while cap.isOpened() and frame_count < total_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 调整帧大小（如果需要）
                if target_size:
                    frame = cv2.resize(frame, (output_width, output_height))
                
                out.write(frame)
                frame_count += 1
                
                # 更新进度
                progress = int((frame_count / total_frames) * 100)
                progress_bar.progress(progress)
                status_text.text(f"处理进度 / Progress: {progress}% ({frame_count}/{total_frames} frames)")
            
            # 使用ffmpeg重新编码以确保兼容性
            subprocess.run(
                [
                    "ffmpeg",
                    "-i",
                    temp_output,
                    "-c:v",
                    "libx264",
                    "-preset",
                    "medium",
                    "-crf",
                    "23",
                    output_path,
                ],
                check=True,
            )
            os.remove(temp_output)
            
            st.success(f"视频裁剪完成 / Video cropped: {output_name}")
            
            # 显示输出视频信息
            output_info = get_video_info(output_path)
            if output_info:
                st.info(f"""
                输出视频信息 / Output Video Info:
                - 分辨率 / Resolution: {output_info['width']}x{output_info['height']}
                - 帧率 / FPS: {output_info['fps']}
                - 时长 / Duration: {output_info['duration_str']}
                """)
            
        except Exception as e:
            st.error(f"视频裁剪失败 / Failed to crop video {video_path}: {str(e)}")
            continue
        finally:
            if cap is not None:
                cap.release()
            if out is not None:
                out.release()
            if temp_output and os.path.exists(temp_output):
                try:
                    os.remove(temp_output)
                except OSError:
                    pass
            
    st.success("所有视频裁剪完成 / All videos cropped successfully")

def create_extract_script(video_path: str, x: int, y: int, width: int, height: int, start: float, end: float, output_directory: str, deviceID: int = 0) -> str:
    """生成使用GPU的视频裁剪脚本
    Generate a video cropping script using GPU
    
    Args:
        video_path (str): 输入视频路径
        x (int): 裁剪起始X坐标
        y (int): 裁剪起始Y坐标
        width (int): 裁剪宽度
        height (int): 裁剪高度
        start (float): 开始时间（分钟）
        end (float): 结束时间（分钟）
        output_directory (str): 输出目录
        deviceID (int): GPU设备ID
        
    Returns:
        str: 生成的脚本路径
    """
    import datetime
    
    # 转换时间格式
    start_time = str(datetime.timedelta(minutes=start))
    duration = str(datetime.timedelta(minutes=(end - start)))
    
    # 生成输出文件名
    video_base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_filename = f'{video_base_name}_{x}_{y}_{start}_{end}.mp4'
    output_full_path = os.path.join(output_directory, output_filename)
    
    # 生成脚本文件名
    script_filename = f"{video_base_name}_{x}_{y}_{start}_{end}.py"
    script_path = os.path.join(output_directory, script_filename)
    
    # 处理路径，确保使用正确的路径分隔符
    video_path = video_path.replace('\\', '/')
    output_full_path = output_full_path.replace('\\', '/')
    
    # 写入脚本内容
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('import subprocess\n\n')
        f.write(f"video_path = {video_path!r}\n")
        f.write(f"output_path = {output_full_path!r}\n")
        f.write(f"start_time = {start_time!r}\n")
        f.write(f"duration = {duration!r}\n")
        f.write(f"device_id = {deviceID}\n\n")
        f.write("cmd = [\n")
        f.write("    'ffmpeg',\n")
        f.write("    '-hwaccel', 'cuda',\n")
        f.write("    '-hwaccel_device', str(device_id),\n")
        f.write("    '-c:v', 'h264_cuvid',\n")
        f.write("    '-ss', start_time,\n")
        f.write("    '-t', duration,\n")
        f.write("    '-i', video_path,\n")
        f.write(f"    '-vf', 'crop={width}:{height}:{x}:{y},fps=30',\n")
        f.write("    '-c:v', 'h264_nvenc',\n")
        f.write("    '-gpu', str(device_id),\n")
        f.write("    '-an',\n")
        f.write("    output_path,\n")
        f.write("]\n")
        f.write("subprocess.run(cmd, check=True)\n")
    
    return script_path

def create_extract_script_CPU(video_path: str, x: int, y: int, width: int, height: int, start: float, end: float, output_directory: str) -> str:
    """生成使用CPU的视频裁剪脚本
    Generate a video cropping script using CPU
    
    Args:
        video_path (str): 输入视频路径
        x (int): 裁剪起始X坐标
        y (int): 裁剪起始Y坐标
        width (int): 裁剪宽度
        height (int): 裁剪高度
        start (float): 开始时间（分钟）
        end (float): 结束时间（分钟）
        output_directory (str): 输出目录
        
    Returns:
        str: 生成的脚本路径
    """
    import datetime
    
    # 转换时间格式
    start_time = str(datetime.timedelta(minutes=start))
    duration = str(datetime.timedelta(minutes=(end - start)))
    
    # 生成输出文件名
    video_base_name = os.path.splitext(os.path.basename(video_path))[0]
    output_filename = f'{video_base_name}_{x}_{y}_{start}_{end}.mp4'
    output_full_path = os.path.join(output_directory, output_filename)
    
    # 生成脚本文件名
    script_filename = f"{video_base_name}_{x}_{y}_{start}_{end}.py"
    script_path = os.path.join(output_directory, script_filename)
    
    # 处理路径，确保使用正确的路径分隔符
    video_path = video_path.replace('\\', '/')
    output_full_path = output_full_path.replace('\\', '/')
    
    # 写入脚本内容
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write('import subprocess\n\n')
        f.write(f"video_path = {video_path!r}\n")
        f.write(f"output_path = {output_full_path!r}\n")
        f.write(f"start_time = {start_time!r}\n")
        f.write(f"duration = {duration!r}\n\n")
        f.write("cmd = [\n")
        f.write("    'ffmpeg',\n")
        f.write("    '-ss', start_time,\n")
        f.write("    '-t', duration,\n")
        f.write("    '-i', video_path,\n")
        f.write(f"    '-vf', 'crop={width}:{height}:{x}:{y},fps=30',\n")
        f.write("    '-c:v', 'libx264',\n")
        f.write("    '-an',\n")
        f.write("    output_path,\n")
        f.write("]\n")
        f.write("subprocess.run(cmd, check=True)\n")
    
    return script_path

def move_selected_files(dest_folder_path, selected_files, source_folder_path):
    """移动选定的文件到目标目录
    Move selected files to destination directory
    
    Args:
        dest_folder_path (str): 目标目录路径
        selected_files (list): 选定的文件列表
        source_folder_path (str): 源目录路径
    """
    if not os.path.exists(dest_folder_path):
        os.makedirs(dest_folder_path)
        st.success(f"创建目录成功 / Created directory: {dest_folder_path}")
    
    files_moved = 0
    for filename in selected_files:
        try:
            safe_name = sanitize_filename(filename)
            src_path = safe_join(source_folder_path, safe_name)
            dest_path = safe_join(dest_folder_path, safe_name)
        except ValueError:
            st.error(f"文件名不合法 / Invalid filename: {filename}")
            continue
        shutil.move(src_path, dest_path)
        files_moved += 1
    
    if files_moved > 0:
        st.success(f"✅ 已移动 {files_moved} 个文件到 {dest_folder_path}")
    else:
        st.info("没有选择要移动的文件 / No files selected to move") 
