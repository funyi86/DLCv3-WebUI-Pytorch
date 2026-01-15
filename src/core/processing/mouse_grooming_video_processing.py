import os
import pandas as pd
import numpy as np
import streamlit as st

def process_mouse_grooming_video(video_path, threshold=0.999, min_duration=15, max_duration=35):
    """
    处理小鼠梳理行为视频的分析结果
    Process mouse grooming video analysis results
    
    Args:
        video_path (str): 视频文件路径
        threshold (float): 置信度阈值
        min_duration (int): 最小持续时间（帧）
        max_duration (int): 最大持续时间（帧）
    """
    try:
        # 获取CSV文件路径
        csv_path = os.path.splitext(video_path)[0] + 'DLC_resnet50_Mouse_GroomingFeb24shuffle1_500000.csv'
        if not os.path.exists(csv_path):
            st.error(f"未找到CSV文件 / CSV file not found: {csv_path}")
            return
            
        # 读取CSV文件
        df = pd.read_csv(csv_path, header=[1, 2])
        
        # 处理数据
        results = analyze_grooming_behavior(df, threshold, min_duration, max_duration)
        
        # 保存结果
        save_results(results, os.path.splitext(video_path)[0] + '_analysis.csv')
        
    except Exception as e:
        st.error(f"处理视频失败 / Failed to process video: {str(e)}")

def analyze_grooming_behavior(df, threshold, min_duration, max_duration):
    """
    分析梳理行为
    Analyze grooming behavior
    
    Args:
        df (pd.DataFrame): 原始数据
        threshold (float): 置信度阈值
        min_duration (int): 最小持续时间
        max_duration (int): 最大持续时间
        
    Returns:
        pd.DataFrame: 分析结果
    """
    # 提取关键点坐标和置信度
    points = ['nose', 'leftPaw', 'rightPaw', 'mouth']
    coords = {}
    for point in points:
        coords[point] = {
            'x': df[point]['x'].values,
            'y': df[point]['y'].values,
            'likelihood': df[point]['likelihood'].values
        }
    
    # 检测梳理行为
    grooming_frames = detect_grooming_frames(coords, threshold)
    
    # 分析行为持续时间
    grooming_bouts = analyze_bout_duration(grooming_frames, min_duration, max_duration)
    
    return pd.DataFrame(grooming_bouts)

def detect_grooming_frames(coords, threshold):
    """
    检测梳理行为的帧
    Detect frames with grooming behavior
    
    Args:
        coords (dict): 关键点坐标和置信度
        threshold (float): 置信度阈值
        
    Returns:
        np.array: 梳理行为的帧索引
    """
    # 检查置信度
    valid_frames = np.logical_and.reduce([
        coords[point]['likelihood'] > threshold
        for point in coords.keys()
    ])
    
    # 计算爪子和嘴部的距离
    paw_mouth_dist = np.minimum(
        np.sqrt(
            (coords['leftPaw']['x'] - coords['mouth']['x'])**2 +
            (coords['leftPaw']['y'] - coords['mouth']['y'])**2
        ),
        np.sqrt(
            (coords['rightPaw']['x'] - coords['mouth']['x'])**2 +
            (coords['rightPaw']['y'] - coords['mouth']['y'])**2
        )
    )
    
    # 根据距离判断梳理行为
    grooming_frames = np.logical_and(
        valid_frames,
        paw_mouth_dist < 30  # 距离阈值
    )
    
    return grooming_frames

def analyze_bout_duration(grooming_frames, min_duration, max_duration):
    """
    分析行为持续时间
    Analyze behavior bout duration
    
    Args:
        grooming_frames (np.array): 梳理行为的帧
        min_duration (int): 最小持续时间
        max_duration (int): 最大持续时间
        
    Returns:
        list: 行为片段列表
    """
    bouts = []
    start_frame = None
    
    for i in range(len(grooming_frames)):
        if grooming_frames[i]:
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
        duration = len(grooming_frames) - start_frame
        if min_duration <= duration <= max_duration:
            bouts.append({
                'start_frame': start_frame,
                'end_frame': len(grooming_frames),
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

def process_grooming_files(folder_path, threshold=0.999, min_duration=15, max_duration=35):
    """
    处理文件夹中的所有梳理行为视频
    Process all grooming videos in the folder
    
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
            process_mouse_grooming_video(video_path, threshold, min_duration, max_duration)
            
    except Exception as e:
        st.error(f"处理文件夹失败 / Failed to process folder: {str(e)}") 
