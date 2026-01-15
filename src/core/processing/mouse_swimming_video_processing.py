import os
import pandas as pd
import numpy as np
import streamlit as st

def process_mouse_swimming_video(video_path, threshold=0.999, min_duration=15, max_duration=35):
    """
    处理小鼠游泳视频的分析结果
    Process mouse swimming video analysis results
    
    Args:
        video_path (str): 视频文件路径
        threshold (float): 置信度阈值
        min_duration (int): 最小持续时间（帧）
        max_duration (int): 最大持续时间（帧）
    """
    try:
        # 获取CSV文件路径
        csv_path = os.path.splitext(video_path)[0] + 'DLC_resnet50_Mouse_SwimmingFeb24shuffle1_500000.csv'
        if not os.path.exists(csv_path):
            st.error(f"未找到CSV文件 / CSV file not found: {csv_path}")
            return
            
        # 读取CSV文件
        df = pd.read_csv(csv_path, header=[1, 2])
        
        # 处理数据
        results = analyze_swimming_behavior(df, threshold, min_duration, max_duration)
        
        # 保存结果
        save_results(results, os.path.splitext(video_path)[0] + '_analysis.csv')
        
    except Exception as e:
        st.error(f"处理视频失败 / Failed to process video: {str(e)}")

def analyze_swimming_behavior(df, threshold, min_duration, max_duration):
    """
    分析游泳行为
    Analyze swimming behavior
    
    Args:
        df (pd.DataFrame): 原始数据
        threshold (float): 置信度阈值
        min_duration (int): 最小持续时间
        max_duration (int): 最大持续时间
        
    Returns:
        pd.DataFrame: 分析结果
    """
    # 提取关键点坐标和置信度
    points = ['nose', 'head', 'body', 'tail']
    coords = {}
    for point in points:
        coords[point] = {
            'x': df[point]['x'].values,
            'y': df[point]['y'].values,
            'likelihood': df[point]['likelihood'].values
        }
    
    # 检测游泳行为
    swimming_frames = detect_swimming_frames(coords, threshold)
    
    # 分析行为持续时间
    swimming_bouts = analyze_bout_duration(swimming_frames, min_duration, max_duration)
    
    return pd.DataFrame(swimming_bouts)

def detect_swimming_frames(coords, threshold):
    """
    检测游泳行为的帧
    Detect frames with swimming behavior
    
    Args:
        coords (dict): 关键点坐标和置信度
        threshold (float): 置信度阈值
        
    Returns:
        np.array: 游泳行为的帧索引
    """
    # 检查置信度
    valid_frames = np.logical_and.reduce([
        coords[point]['likelihood'] > threshold
        for point in coords.keys()
    ])
    
    # 计算身体弯曲度
    body_angles = calculate_body_angles(coords)
    
    # 根据身体弯曲度判断游泳行为
    swimming_frames = np.logical_and(
        valid_frames,
        body_angles > 30  # 角度阈值
    )
    
    return swimming_frames

def calculate_body_angles(coords):
    """
    计算身体弯曲角度
    Calculate body bending angles
    
    Args:
        coords (dict): 关键点坐标
        
    Returns:
        np.array: 身体弯曲角度
    """
    # 计算向量
    head_body = np.array([
        coords['body']['x'] - coords['head']['x'],
        coords['body']['y'] - coords['head']['y']
    ])
    
    body_tail = np.array([
        coords['tail']['x'] - coords['body']['x'],
        coords['tail']['y'] - coords['body']['y']
    ])
    
    # 计算角度
    dot_product = (head_body[0] * body_tail[0] + head_body[1] * body_tail[1])
    magnitudes = np.sqrt(
        (head_body[0]**2 + head_body[1]**2) *
        (body_tail[0]**2 + body_tail[1]**2)
    )

    cos_angle = np.ones_like(dot_product, dtype=float)
    np.divide(dot_product, magnitudes, out=cos_angle, where=magnitudes != 0)
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    angles = np.arccos(cos_angle)
    return np.degrees(angles)

def analyze_bout_duration(swimming_frames, min_duration, max_duration):
    """
    分析行为持续时间
    Analyze behavior bout duration
    
    Args:
        swimming_frames (np.array): 游泳行为的帧
        min_duration (int): 最小持续时间
        max_duration (int): 最大持续时间
        
    Returns:
        list: 行为片段列表
    """
    bouts = []
    start_frame = None
    
    for i in range(len(swimming_frames)):
        if swimming_frames[i]:
            if start_frame is None:
                start_frame = i
        elif start_frame is not None:
            duration = i - start_frame
            if min_duration <= duration <= max_duration:
                bouts.append({
                    'start_frame': start_frame,
                    'end_frame': i,
                    'duration': duration
                })
            start_frame = None
            
    if start_frame is not None:
        duration = len(swimming_frames) - start_frame
        if min_duration <= duration <= max_duration:
            bouts.append({
                'start_frame': start_frame,
                'end_frame': len(swimming_frames),
                'duration': duration
            })

    return bouts

def save_results(results, output_path):
    """
    保存分析结果
    Save analysis results
    
    Args:
        results (pd.DataFrame): 分析结果
        output_path (str): 输出文件路径
    """
    try:
        results.to_csv(output_path, index=False)
        st.success(f"结果已保存 / Results saved: {output_path}")
    except Exception as e:
        st.error(f"保存结果失败 / Failed to save results: {str(e)}")

def process_swimming_files(folder_path, threshold=0.999, min_duration=15, max_duration=35):
    """
    处理文件夹中的所有游泳视频
    Process all swimming videos in the folder
    
    Args:
        folder_path (str): 文件夹路径
        threshold (float): 置信度阈值
        min_duration (int): 最小持续时间
        max_duration (int): 最大持续时间
    """
    try:
        # 获取所有视频文件
        video_files = [f for f in os.listdir(folder_path) if f.endswith('.mp4')]
        
        if not video_files:
            st.warning("未找到视频文件 / No video files found")
            return
            
        # 处理每个视频
        for video_file in video_files:
            video_path = os.path.join(folder_path, video_file)
            process_mouse_swimming_video(video_path, threshold, min_duration, max_duration)
            
    except Exception as e:
        st.error(f"处理文件夹失败 / Failed to process folder: {str(e)}") 
