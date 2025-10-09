import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from scipy.signal import butter, filtfilt, savgol_filter, find_peaks
from collections import Counter
import time
import traceback
from matplotlib.ticker import FuncFormatter
from scipy.interpolate import interp1d
from typing import Optional

from .trajectory_processing import (
    filter_low_likelihood,
    filter_extreme_jumps,
    filter_unreasonable_speed,
    filter_unreasonable_position,
    interpolate_missing_points,
    smooth_trajectory,
    detect_grab_trajectories,
    plot_trajectory_with_events,
    format_timestamp
)

def process_mouse_catch_video(
    video_path: str,
    csv_path: Optional[str] = None,
    threshold: float = 0.6,
    speed_threshold: float = 100.0,  # 速度阈值参数，单位：像素/帧
    min_duration_sec: float = 0.5,   # 最小持续时间，默认0.5秒
    max_duration_sec: float = 1.0,   # 最大持续时间，默认1秒
    fps: float = 120.0               # 帧率，默认120fps
):
    """
    X
    
    Args:
        video_path (str): 原始视频文件路径。
        csv_path (str, optional): CSV文件路径。如果未提供，将自动查找与视频同名的CSV文件。
        threshold (float): 关键点置信度阈值(如0.6)。
        speed_threshold (float): 两帧之间最大允许的速度阈值(像素/帧)。
        min_duration_sec (float): 最小持续时间(秒)。
        max_duration_sec (float): 最大持续时间(秒)。
        fps (float): 视频帧率。
    """
    try:
        video_dir = os.path.dirname(video_path)
        video_name = os.path.splitext(os.path.basename(video_path))[0]
        
        # 1. 确定CSV文件路径
        if csv_path is None:
            csv_files = [f for f in os.listdir(video_dir) if f.startswith(video_name) and f.endswith('.csv')]
            if not csv_files:
                st.error(f"未找到对应的CSV文件 / No corresponding CSV file for: {video_name}")
                return
            csv_path = os.path.join(video_dir, csv_files[0])
        
        if not os.path.exists(csv_path):
            st.error(f"指定的CSV文件不存在: {csv_path} / Specified CSV file does not exist")
            return
        
        st.info(f"正在处理CSV文件: {os.path.basename(csv_path)} / Processing CSV file")
        
        # 读取CSV文件
        try:
            # 首先尝试直接读取，不指定header
            df = pd.read_csv(csv_path)
            
            # 检查是否为DLC格式
            if 'bodyparts' in df.iloc[0].values and 'coords' in df.iloc[1].values:
                st.success("检测到DLC格式CSV / Detected DLC format CSV")
                
                # 提取实际的数据，跳过前3行header
                data_df = pd.read_csv(csv_path, skiprows=3)
                
                # 获取x, y, likelihood列的索引
                x_idx = 1  # 第二列是x坐标
                y_idx = 2  # 第三列是y坐标
                likelihood_idx = 3  # 第四列是likelihood
                
                # 提取坐标数据
                x = data_df.iloc[:, x_idx].values.astype(float)
                y = data_df.iloc[:, y_idx].values.astype(float)
                likelihood = data_df.iloc[:, likelihood_idx].values.astype(float)
                
                # 创建模拟的DataFrame结构以适配现有代码
                analysis_df = pd.DataFrame({
                    'x': x,
                    'y': y,
                    'likelihood': likelihood
                })
                
                st.success("成功提取坐标数据 / Successfully extracted coordinate data")
            else:
                st.error("不是标准的DLC格式CSV文件 / Not a standard DLC format CSV file")
                return
                
        except Exception as e:
            st.error(f"读取CSV文件失败: {str(e)} / Failed to read CSV file: {str(e)}")
            return
        
        # 2. 数据预处理和分析
        st.info("开始数据分析 / Starting data analysis")
        results_df, analysis_context = analyze_catch_behavior(
            analysis_df,
            threshold=threshold,
            speed_threshold=speed_threshold,
            min_duration_sec=min_duration_sec,
            max_duration_sec=max_duration_sec,
            fps=fps
        )
        
        if results_df.empty and not analysis_context:
            st.warning("分析未产生有效结果，无法继续 / Analysis did not produce valid results")
            return
        
        # 3. 保存分析数据
        results_dir = os.path.join(video_dir, f"{video_name}_results")
        os.makedirs(results_dir, exist_ok=True)
        
        # 创建轨迹数据目录
        trajectories_dir = os.path.join(results_dir, "trajectories")
        os.makedirs(trajectories_dir, exist_ok=True)
        
        # 即使结果为空，也保存一个空的结果文件
        if not results_df.empty:
            results_df.to_csv(os.path.join(results_dir, "catch_analysis_results.csv"), index=False)
            st.success(f"已保存分析结果到CSV / Analysis results saved to CSV")
            
            # 保存每个轨迹的详细数据
            for i, result in enumerate(analysis_context.get('results', []), 1):
                start_f = result['start_frame']
                end_f = result['end_frame']
                
                # 提取轨迹段的x,y坐标
                trajectory_data = pd.DataFrame({
                    'frame': range(start_f, end_f + 1),
                    'time': [f/fps for f in range(start_f, end_f + 1)],
                    'x': analysis_context['x_smooth'][start_f:end_f + 1],
                    'y': analysis_context['y_smooth'][start_f:end_f + 1]
                })
                
                # 保存轨迹数据
                trajectory_file = os.path.join(trajectories_dir, f"trajectory_{i}.csv")
                trajectory_data.to_csv(trajectory_file, index=False)
            
            # 验证轨迹文件数量与分析结果数量是否一致
            trajectory_files = [f for f in os.listdir(trajectories_dir) if f.startswith('trajectory_') and f.endswith('.csv')]
            if len(trajectory_files) != len(results_df):
                st.warning(f"⚠️ 轨迹文件数量({len(trajectory_files)})与分析结果数量({len(results_df)})不一致！")
            else:
                st.success(f"已保存{len(analysis_context.get('results', []))}个轨迹的详细数据，与分析结果数量一致")
        else:
            empty_df = pd.DataFrame(columns=[
                'start_time', 'peak_time', 'end_time',
                'start_frame', 'peak_frame', 'end_frame',
                'trajectory_distance', 'horizontal_displacement',
                'average_speed', 'lift_height', 'left_to_right_distance',
                'left_to_right_speed', 'left_to_right_acceleration_mean',
                'left_to_right_acceleration_max', 'left_to_right_smoothness',
                'right_to_left_distance', 'right_to_left_speed',
                'right_to_left_acceleration_mean', 'right_to_left_acceleration_max',
                'right_to_left_smoothness', 'max_height', 'duration',
                'start_pos_x', 'start_pos_y', 'end_pos_x', 'end_pos_y'
            ])
            empty_df.to_csv(os.path.join(results_dir, "catch_analysis_results.csv"), index=False)
            st.warning("保存了空的分析结果 / Saved empty analysis results")
        
        # 4. 生成可视化图表
        figure_dir = os.path.join(results_dir, "figures")
        os.makedirs(figure_dir, exist_ok=True)
        
        try:
            plot_analysis_results(
                analysis_context,
                figure_dir=figure_dir,
                fps=fps
            )
            st.success("已生成可视化图表 / Visualization charts generated")
        except Exception as vis_error:
            st.error(f"生成可视化失败: {str(vis_error)} / Failed to generate visualizations")
        
        # 5. 在Streamlit中显示可视化
        st.success(f"分析完成! / Analysis done. 结果已保存至 {results_dir}")
        st.subheader("📊 分析结果 / Analysis Results")
        
        # 显示图表
        trajectory_png = os.path.join(figure_dir, "catch_trajectory.png")
        velocity_png = os.path.join(figure_dir, "catch_velocity.png")
        height_png = os.path.join(figure_dir, "catch_height.png")
        
        col1, col2 = st.columns(2)
        with col1:
            if os.path.exists(trajectory_png):
                st.image(trajectory_png, caption="抓取轨迹 / Catch Trajectory")
            else:
                st.info("未生成轨迹图 / No trajectory chart generated")
                
            if os.path.exists(height_png):
                st.image(height_png, caption="高度变化 / Height Change")
            else:
                st.info("未生成高度图 / No height chart generated")
        with col2:
            if os.path.exists(velocity_png):
                st.image(velocity_png, caption="速度分析 / Velocity Analysis")
            else:
                st.info("未生成速度图 / No velocity chart generated")
        
        # 显示结果表格
        if not results_df.empty:
            st.subheader("🎯 抓取行为分析结果 / Catch Behavior Analysis")
            st.dataframe(results_df)
        else:
            st.warning("未发现有效的抓取行为 / No valid catch behaviors detected")
    
    except Exception as e:
        st.error(f"处理视频失败 / Failed to process video: {str(e)}")
        st.error(traceback.format_exc())

def analyze_catch_behavior(
    df: pd.DataFrame,
    threshold: float,
    speed_threshold: float,
    min_duration_sec: float,
    max_duration_sec: float,
    fps: float = 120.0
):
    """
    分析抓取行为数据，包括预处理、轨迹提取和运动参数计算。
    
    Args:
        df: 包含x, y, likelihood列的DataFrame
        threshold: 置信度阈值
        speed_threshold: 速度阈值（像素/秒）
        min_duration_sec: 最小持续时间（秒）
        max_duration_sec: 最大持续时间（秒）
        fps: 视频帧率
    """
    try:
        # 记录原始帧数
        original_frames = len(df)
        st.info(f"原始帧数: {original_frames} (总时长: {original_frames/fps:.2f}秒)")
        
        # 1. 数据预处理
        # 检查必要的列是否存在
        required_columns = ['x', 'y', 'likelihood']
        if not all(col in df.columns for col in required_columns):
            st.error(f"缺少必要的列: {', '.join(required_columns)}")
            return pd.DataFrame(), {}
        
        # 第一步：过滤低置信度点
        df_filtered = filter_low_likelihood(df, threshold)
        st.info(f"置信度过滤后有效点数: {df_filtered['x'].notna().sum()}")
        
        # 第二步：过滤不合理位置点
        df_filtered = filter_unreasonable_position(df_filtered)
        st.info(f"位置过滤后有效点数: {df_filtered['x'].notna().sum()}")
        
        # 第三步：粗过滤极端跳变
        df_filtered = filter_extreme_jumps(df_filtered, extreme_dist=200.0)
        st.info(f"极端跳变过滤后有效点数: {df_filtered['x'].notna().sum()}")
        
        # 第四步：过滤不合理速度
        df_filtered = filter_unreasonable_speed(df_filtered, speed_threshold, fps)
        st.info(f"速度过滤后有效点数: {df_filtered['x'].notna().sum()}")
        
        # 第五步：插值处理
        df_interpolated = interpolate_missing_points(df_filtered)
        
        # 第六步：平滑处理
        df_smooth = smooth_trajectory(df_interpolated, window_length=7, polyorder=2)
        
        # 第七步：检测抓取事件
        events = detect_grab_trajectories(
            df_smooth, 
            fps=fps,
            barrier_region=(330, 450, 250, 400),
            start_region=(200, 300, 350, 450),
            max_back_time=0.5,
            max_forward_time=0.2
        )
        
        # 生成结果数据
        results = []
        for event in events:
            start_f = event['i_start']
            end_f = event['i_end']
            duration = (end_f - start_f) / fps
            
            # 提取轨迹段
            segment = df_smooth.iloc[start_f:end_f+1]
            x_vals = segment['x'].values
            y_vals = segment['y'].values
            
            # 找到实际的峰值（最高点）
            peak_idx = np.argmin(y_vals)  # y坐标最小值对应最高点
            peak_frame = start_f + peak_idx
            peak_t = peak_frame / fps
            peak_timestamp = format_timestamp(peak_t)
            
            # 计算运动参数
            distance = np.abs(x_vals[-1] - x_vals[0])
            height_change = np.max(np.abs(y_vals - y_vals[0]))
            
            # 计算水平位移和平均速度
            horizontal_displacement = np.abs(x_vals[-1] - x_vals[0])
            average_speed = distance / duration if duration > 0 else 0
            
            # 计算抬起高度（相对于起始点的最大高度变化）
            lift_height = np.abs(np.min(y_vals) - y_vals[0])  # y坐标向下为正，所以用min
            
            # 计算速度和加速度
            speeds = np.sqrt(np.diff(x_vals)**2 + np.diff(y_vals)**2) * fps
            mean_speed = np.mean(speeds)
            max_speed = np.max(speeds)
            
            accelerations = np.diff(speeds) * fps
            mean_acc = np.mean(accelerations)
            max_acc = np.max(np.abs(accelerations))
            
            # 计算平滑度
            if len(accelerations) > 2:
                smoothness = -np.log(np.mean(np.square(np.diff(accelerations))))
            else:
                smoothness = 0
            
            result = {
                'start_time': format_timestamp(event['start_time']),
                'peak_time': peak_timestamp,
                'end_time': format_timestamp(event['end_time']),
                'start_frame': start_f,
                'peak_frame': peak_frame,
                'end_frame': end_f,
                'trajectory_distance': distance,
                'horizontal_displacement': horizontal_displacement,
                'average_speed': average_speed,
                'lift_height': lift_height,
                'left_to_right_distance': distance,
                'left_to_right_speed': mean_speed,
                'left_to_right_acceleration_mean': mean_acc,
                'left_to_right_acceleration_max': max_acc,
                'left_to_right_smoothness': smoothness,
                'right_to_left_distance': 0.0,
                'right_to_left_speed': 0.0,
                'right_to_left_acceleration_mean': 0.0,
                'right_to_left_acceleration_max': 0.0,
                'right_to_left_smoothness': 0.0,
                'max_height': height_change,
                'duration': duration,
                'start_pos_x': x_vals[0],
                'start_pos_y': y_vals[0],
                'end_pos_x': x_vals[-1],
                'end_pos_y': y_vals[-1]
            }
            results.append(result)
        
        # 创建分析上下文
        analysis_context = {
            'x_smooth': df_smooth['x'].values,
            'y_smooth': df_smooth['y'].values,
            'speeds_smooth': np.diff(df_smooth['x'].values) * fps,  # 简化为x方向速度
            'accelerations_smooth': np.diff(np.diff(df_smooth['x'].values)) * fps * fps,
            'events': [(e['i_start'], e['i_end'], (e['i_end'] - e['i_start'])/fps, 
                       df_smooth['x'].values[e['i_end']] - df_smooth['x'].values[e['i_start']]) 
                      for e in events],
            'results': results
        }
            
        return pd.DataFrame(results), analysis_context
        
    except Exception as e:
        st.error(f"数据处理失败: {str(e)}")
        st.error(traceback.format_exc())
        return pd.DataFrame(), {}

def plot_analysis_results(analysis_context, figure_dir, fps=120.0):
    """
    Generate visualization charts for analysis results
    
    Args:
        analysis_context: Analysis context data
        figure_dir: Directory to save figures
        fps: Video frame rate, default 120.0
    """
    try:
        if len(analysis_context['x_smooth']) > 0 and len(analysis_context['y_smooth']) > 0:
            # Create 2x2 subplot layout
            fig = plt.figure(figsize=(20, 15))
            gs = plt.GridSpec(2, 2)
            
            # Trajectory plot (upper left)
            ax1 = plt.subplot(gs[0, 0])
            
            # 设置坐标轴范围
            ax1.set_xlim(0, 500)
            ax1.set_ylim(500, 0)  # 交换y轴的范围，使原点在左上角
            
            # Plot background trajectory
            ax1.plot(analysis_context['x_smooth'], analysis_context['y_smooth'], 
                    'gray', linestyle='--', alpha=0.2, label='Full Trajectory')
            
            valid_catches = 0
            heights = []  # Store all lift heights
            speeds = []   # Store all speeds
            
            if analysis_context['events'] and analysis_context['results']:
                colors = plt.cm.rainbow(np.linspace(0, 1, len(analysis_context['events'])))
                legend_handles = []
                legend_labels = []
                
                for i, ((start_f, end_f, _, _), result, color) in enumerate(zip(analysis_context['events'], 
                                                                              analysis_context['results'], 
                                                                              colors)):
                    x_segment = analysis_context['x_smooth'][start_f:end_f+1]
                    y_segment = analysis_context['y_smooth'][start_f:end_f+1]
                    
                    # Collect data for distribution plots
                    heights.append(result['lift_height'])
                    speeds.append(result['average_speed'])
                    
                    line, = ax1.plot(x_segment, y_segment, '-', color=color, linewidth=2)
                    legend_handles.append(line)
                    legend_labels.append(f'Catch #{valid_catches+1}')
                    
                    ax1.scatter(x_segment[0], y_segment[0], color='green', s=100, marker='o')
                    ax1.scatter(x_segment[-1], y_segment[-1], color='red', s=100, marker='o')
                    
                    valid_catches += 1
                
                legend_handles.extend([
                    plt.scatter([], [], color='green', s=100, marker='o'),
                    plt.scatter([], [], color='red', s=100, marker='o')
                ])
                legend_labels.extend(['Start', 'End'])
            
            ax1.set_xlabel('X Position (pixels)', fontsize=12)
            ax1.set_ylabel('Y Position (pixels)', fontsize=12)
            ax1.set_title(f'Catch Trajectories (n={valid_catches})', fontsize=14)
            ax1.grid(True, linestyle='--', alpha=0.3)
            
            if 'legend_handles' in locals():
                ax1.legend(legend_handles, legend_labels, 
                         bbox_to_anchor=(1.05, 1.0),
                         loc='upper left',
                         fontsize=10)
            
            # Velocity plot (upper right)
            ax2 = plt.subplot(gs[0, 1])
            time_points = np.arange(len(analysis_context['speeds_smooth'])) / fps
            ax2.plot(time_points, analysis_context['speeds_smooth'], 'g-', 
                    label='Velocity')
            ax2.set_xlabel('Time (s)', fontsize=12)
            ax2.set_ylabel('Velocity (pixels/s)', fontsize=12)
            ax2.set_title('Velocity Time Series', fontsize=14)
            ax2.grid(True, linestyle='--', alpha=0.3)
            ax2.legend(fontsize=10)
            
            # Lift height distribution (lower left)
            ax3 = plt.subplot(gs[1, 0])
            if heights:
                ax3.hist(heights, bins='auto', color='skyblue', alpha=0.7)
                ax3.axvline(np.mean(heights), color='r', linestyle='--', 
                          label=f'Mean: {np.mean(heights):.1f}px')
            ax3.set_xlabel('Lift Height (pixels)', fontsize=12)
            ax3.set_ylabel('Count', fontsize=12)
            ax3.set_title('Lift Height Distribution', fontsize=14)
            ax3.grid(True, linestyle='--', alpha=0.3)
            ax3.legend(fontsize=10)
            
            # Speed distribution (lower right)
            ax4 = plt.subplot(gs[1, 1])
            if speeds:
                ax4.hist(speeds, bins='auto', color='lightgreen', alpha=0.7)
                ax4.axvline(np.mean(speeds), color='r', linestyle='--', 
                          label=f'Mean: {np.mean(speeds):.1f}px/s')
            ax4.set_xlabel('Average Speed (pixels/s)', fontsize=12)
            ax4.set_ylabel('Count', fontsize=12)
            ax4.set_title('Speed Distribution', fontsize=14)
            ax4.grid(True, linestyle='--', alpha=0.3)
            ax4.legend(fontsize=10)
            
            plt.tight_layout()
                
            # Save figure
            plt.savefig(os.path.join(figure_dir, 'catch_analysis.png'), 
                           bbox_inches='tight', dpi=300)
            plt.close(fig)
            
            st.info(f"Detected {valid_catches} valid catch behaviors")
        else:
            st.warning("Insufficient trajectory data")
    except Exception as e:
        st.error(f"Failed to generate analysis charts: {str(e)}")
