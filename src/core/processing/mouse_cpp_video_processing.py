import os
import pandas as pd
import numpy as np
import streamlit as st

def process_mouse_cpp_video(video_path, threshold=0.999, min_duration=15, max_duration=35):
    """
    处理小鼠CPP视频的分析结果
    Process mouse CPP video analysis results
    
    Args:
        video_path (str): 视频文件路径
        threshold (float): 置信度阈值
        min_duration (int): 最小持续时间（帧）
        max_duration (int): 最大持续时间（帧）
    """
    try:
        # 获取CSV文件路径
        csv_path = os.path.splitext(video_path)[0] + 'DLC_resnet50_Mouse_CPPFeb24shuffle1_500000.csv'
        if not os.path.exists(csv_path):
            st.error(f"未找到CSV文件 / CSV file not found: {csv_path}")
            return
            
        # 读取CSV文件
        df = pd.read_csv(csv_path, header=[1, 2])
        
        # 处理数据
        results = analyze_cpp_behavior(df, threshold, min_duration, max_duration)
        
        # 保存结果
        save_results(results, os.path.splitext(video_path)[0] + '_analysis.csv')
        
    except Exception as e:
        st.error(f"处理视频失败 / Failed to process video: {str(e)}")

def analyze_cpp_behavior(df, threshold, min_duration, max_duration):
    """
    分析CPP行为
    Analyze CPP behavior
    
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
    
    # 检测位置
    position_data = detect_position(coords, threshold)
    
    # 分析停留时间
    position_bouts = analyze_bout_duration(position_data, min_duration, max_duration)
    
    return pd.DataFrame(position_bouts)

def detect_position(coords, threshold):
    """
    检测小鼠位置
    Detect mouse position
    
    Args:
        coords (dict): 关键点坐标和置信度
        threshold (float): 置信度阈值
        
    Returns:
        dict: 位置数据
    """
    # 检查置信度
    valid_frames = np.logical_and.reduce([
        coords[point]['likelihood'] > threshold
        for point in coords.keys()
    ])
    
    # 计算身体中心点
    center_x = (coords['head']['x'] + coords['body']['x']) / 2
    center_y = (coords['head']['y'] + coords['body']['y']) / 2
    
    # 判断所在区域（假设左侧为drug区域，右侧为saline区域）
    in_drug_area = center_x < 375  # 假设750x500的视频，中线在375
    
    return {
        'valid_frames': valid_frames,
        'in_drug_area': in_drug_area,
        'center_x': center_x,
        'center_y': center_y
    }

def analyze_bout_duration(position_data, min_duration, max_duration):
    """
    分析停留时间
    Analyze stay duration
    
    Args:
        position_data (dict): 位置数据
        min_duration (int): 最小持续时间
        max_duration (int): 最大持续时间
        
    Returns:
        list: 行为片段列表
    """
    bouts = []
    start_frame = None
    current_area = None
    
    for i in range(len(position_data['valid_frames'])):
        if position_data['valid_frames'][i]:
            area = 'drug' if position_data['in_drug_area'][i] else 'saline'
            
            if start_frame is None:
                start_frame = i
                current_area = area
            elif area != current_area:
                duration = i - start_frame
                if min_duration <= duration <= max_duration:
                    bouts.append({
                        'start_frame': start_frame,
                        'end_frame': i,
                        'duration': duration,
                        'area': current_area,
                        'center_x': float(position_data['center_x'][i]),
                        'center_y': float(position_data['center_y'][i])
                    })
                start_frame = i
                current_area = area
                
    if start_frame is not None:
        duration = len(position_data['valid_frames']) - start_frame
        if min_duration <= duration <= max_duration:
            last_idx = len(position_data['valid_frames']) - 1
            bouts.append({
                'start_frame': start_frame,
                'end_frame': len(position_data['valid_frames']),
                'duration': duration,
                'area': current_area,
                'center_x': float(position_data['center_x'][last_idx]),
                'center_y': float(position_data['center_y'][last_idx])
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

def process_cpp_files(folder_path, threshold=0.999, min_duration=15, max_duration=35):
    """
    处理文件夹中的所有CPP视频
    Process all CPP videos in the folder
    
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
            process_mouse_cpp_video(video_path, threshold, min_duration, max_duration)
            
    except Exception as e:
        st.error(f"处理文件夹失败 / Failed to process folder: {str(e)}") 
