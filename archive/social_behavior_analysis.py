import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import streamlit as st
import traceback
from typing import Dict, Tuple

class SocialBehaviorAnalyzer:
    def __init__(self, 
                 likelihood_threshold: float = 0.6,
                 interpolation_method: str = "linear",
                 smoothing_window: int = 5,
                 fps: float = 30.0,
                 interaction_distance: float = 100.0,
                 facing_threshold: float = 45.0,
                 chasing_distance_max: float = 150.0,
                 chasing_rel_speed_neg: float = -10.0,
                 avoiding_rel_speed_pos: float = 10.0):
        """
        初始化分析器, 定义各种阈值和参数
        """
        self.LIKELIHOOD_THRESHOLD = likelihood_threshold
        self.INTERPOLATION_METHOD = interpolation_method
        self.SMOOTHING_WINDOW = smoothing_window
        self.FPS = fps
        
        self.INTERACTION_DISTANCE = interaction_distance
        self.FACING_THRESHOLD = facing_threshold
        
        # 针对追逐/逃避等行为
        self.CHASING_DISTANCE_MAX = chasing_distance_max
        self.CHASING_REL_SPEED_NEG = chasing_rel_speed_neg
        self.AVOIDING_REL_SPEED_POS = avoiding_rel_speed_pos

    def process_dlc_social_csv(self, input_csv: str, output_dir: str) -> None:
        """
        处理DeepLabCut输出的社交行为CSV文件,
        包括读取 -> 分析 -> 保存结果 -> 生成可视化.
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            if not os.path.exists(input_csv):
                st.error(f"CSV文件不存在 / CSV file does not exist: {input_csv}")
                return
            if os.path.getsize(input_csv) == 0:
                st.error(f"CSV文件为空 / CSV file is empty: {input_csv}")
                return
            
            # 读取 CSV
            df = pd.read_csv(input_csv, header=[0,1,2,3])
            st.success("成功读取CSV文件 / Successfully read CSV file")
            
            # 分析并得到结果
            events_df, processed_df = self._analyze_behavior(df)
            
            # 保存事件结果
            events_path = os.path.join(output_dir, "behavior_events.csv")
            events_df.to_csv(events_path, index=False)
            
            # 保存处理后(如平滑/插值)的完整数据(如需)
            processed_path = os.path.join(output_dir, "processed_data.csv")
            processed_df.to_csv(processed_path, index=False)
            
            # 可视化
            fig_dir = os.path.join(output_dir, "figures")
            os.makedirs(fig_dir, exist_ok=True)
            self._generate_visualizations(processed_df, events_df, fig_dir)
            
        except Exception as e:
            st.error(f"处理CSV文件时出错 / Error processing CSV file: {str(e)}")
            st.error(f"错误详情 / Error details:\n{traceback.format_exc()}")

    def _analyze_behavior(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        分析行为数据:
         1) 置信度过滤+插值+平滑
         2) 距离/速度/角度计算
         3) 行为区间(Interacting/Chasing/Avoiding)检测
         4) 返回 (事件DataFrame, 处理后DataFrame)
        """
        # 1. 数据预处理
        processed_df = df.copy()
        scorer = df.columns.levels[0][0]  # 获取scorer名称
        
        # 2. 提取和处理每个关键点的数据
        data: Dict[str, Dict[str, Dict[str, np.ndarray]]] = {}
        for individual in ['individual1', 'individual2']:
            data[individual] = {}
            for bp in ['Mouth', 'left-ear', 'right-ear']:
                # 提取坐标和置信度
                x = df[(scorer, individual, bp, 'x')].values
                y = df[(scorer, individual, bp, 'y')].values
                likelihood = df[(scorer, individual, bp, 'likelihood')].values
                
                # 置信度过滤
                mask_low = likelihood < self.LIKELIHOOD_THRESHOLD
                x[mask_low] = np.nan
                y[mask_low] = np.nan
                
                # 插值和平滑
                x = pd.Series(x).interpolate(method=self.INTERPOLATION_METHOD)
                y = pd.Series(y).interpolate(method=self.INTERPOLATION_METHOD)
                
                x = x.rolling(window=self.SMOOTHING_WINDOW, center=True, min_periods=1).mean()
                y = y.rolling(window=self.SMOOTHING_WINDOW, center=True, min_periods=1).mean()
                
                data[individual][bp] = {
                    'x': x.values,
                    'y': y.values,
                    'likelihood': likelihood
                }
        
        # 3. 计算特征
        # 计算两只小鼠之间的距离
        dist_mouth = np.sqrt(
            (data['individual1']['Mouth']['x'] - data['individual2']['Mouth']['x'])**2 +
            (data['individual1']['Mouth']['y'] - data['individual2']['Mouth']['y'])**2
        )
        
        # 计算速度
        def compute_speed(x, y, fps):
            dx = np.diff(x)
            dy = np.diff(y)
            speed = np.sqrt(dx**2 + dy**2) * fps
            return np.append(speed, speed[-1])  # 补充最后一帧
        
        speed_mouse1 = compute_speed(data['individual1']['Mouth']['x'], 
                                   data['individual1']['Mouth']['y'], 
                                   self.FPS)
        speed_mouse2 = compute_speed(data['individual2']['Mouth']['x'], 
                                   data['individual2']['Mouth']['y'], 
                                   self.FPS)
        
        # 计算相对速度
        rel_speed = speed_mouse2 - speed_mouse1
        
        # 计算头部朝向角度
        def compute_head_angle(data, individual):
            dx = data[individual]['right-ear']['x'] - data[individual]['left-ear']['x']
            dy = data[individual]['right-ear']['y'] - data[individual]['left-ear']['y']
            return np.degrees(np.arctan2(dy, dx))
        
        angle_mouse1 = compute_head_angle(data, 'individual1')
        angle_mouse2 = compute_head_angle(data, 'individual2')
        
        # 4. 行为判定
        # 交互行为
        interaction_mask = dist_mouth < self.INTERACTION_DISTANCE
        
        # 追逐行为
        chasing_mask = (dist_mouth < self.CHASING_DISTANCE_MAX) & \
                      (rel_speed < self.CHASING_REL_SPEED_NEG)
        
        # 逃避行为
        avoiding_mask = (dist_mouth < self.CHASING_DISTANCE_MAX) & \
                       (rel_speed > self.AVOIDING_REL_SPEED_POS)
        
        # 5. 生成处理后的数据框
        processed_data = {
            'frame': np.arange(len(dist_mouth)),
            'distance': dist_mouth,
            'speed_mouse1': speed_mouse1,
            'speed_mouse2': speed_mouse2,
            'relative_speed': rel_speed,
            'angle_mouse1': angle_mouse1,
            'angle_mouse2': angle_mouse2,
            'is_interacting': interaction_mask,
            'is_chasing': chasing_mask,
            'is_avoiding': avoiding_mask
        }
        processed_df = pd.DataFrame(processed_data)
        
        # 6. 检测行为事件（合并连续帧）
        def detect_events(mask, behavior_type):
            events = []
            if not any(mask):
                return events
            
            start_idx = None
            for i in range(len(mask)):
                if mask[i] and start_idx is None:
                    start_idx = i
                elif not mask[i] and start_idx is not None:
                    duration = (i - start_idx) / self.FPS
                    if duration >= 2.0:  # 只记录持续2秒以上的行为
                        events.append({
                            'Behavior': behavior_type,
                            'Start_frame': start_idx,
                            'End_frame': i-1,
                            'Start_s': start_idx / self.FPS,
                            'End_s': (i-1) / self.FPS,
                            'Duration_s': duration
                        })
                    start_idx = None
            
            # 处理最后一段
            if start_idx is not None:
                duration = (len(mask) - start_idx) / self.FPS
                if duration >= 2.0:
                    events.append({
                        'Behavior': behavior_type,
                        'Start_frame': start_idx,
                        'End_frame': len(mask)-1,
                        'Start_s': start_idx / self.FPS,
                        'End_s': (len(mask)-1) / self.FPS,
                        'Duration_s': duration
                    })
            
            return events
        
        # 检测各类行为事件
        events = []
        events.extend(detect_events(interaction_mask, 'Interacting'))
        events.extend(detect_events(chasing_mask, 'Chasing'))
        events.extend(detect_events(avoiding_mask, 'Avoiding'))
        
        # 按开始时间排序
        events.sort(key=lambda x: x['Start_s'])
        events_df = pd.DataFrame(events)
        
        return events_df, processed_df

    def _generate_visualizations(self, processed_df: pd.DataFrame, events_df: pd.DataFrame, fig_dir: str) -> None:
        """
        生成可视化结果并保存:
        1. 距离随时间变化
        2. 速度分布
        3. 距离分布
        4. 角度随时间变化
        5. 行为事件时间线
        """
        plt.style.use('seaborn')
        
        # 1. 距离随时间变化
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(processed_df['frame'] / self.FPS, processed_df['distance'], 
                color='steelblue', label='Mouse Distance')
        ax.axhline(y=self.INTERACTION_DISTANCE, color='r', linestyle='--', 
                  label=f'Interaction Threshold ({self.INTERACTION_DISTANCE}px)')
        
        # 标记行为事件
        colors = {'Interacting': 'green', 'Chasing': 'red', 'Avoiding': 'orange'}
        for _, event in events_df.iterrows():
            ax.axvspan(event['Start_s'], event['End_s'], 
                      alpha=0.2, color=colors[event['Behavior']], 
                      label=f"{event['Behavior']}")
        
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Distance (pixels)')
        ax.set_title('Distance Between Mice Over Time')
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        ax.legend(by_label.values(), by_label.keys())
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, 'distance_over_time.png'), dpi=300)
        plt.close()
        
        # 2. 速度分布
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(processed_df['speed_mouse1'], bins=50, alpha=0.5, 
                label='Mouse 1', color='blue')
        ax.hist(processed_df['speed_mouse2'], bins=50, alpha=0.5, 
                label='Mouse 2', color='orange')
        ax.set_xlabel('Speed (pixels/s)')
        ax.set_ylabel('Count')
        ax.set_title('Speed Distribution')
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, 'speed_distribution.png'), dpi=300)
        plt.close()
        
        # 3. 距离分布
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.hist(processed_df['distance'], bins=50, color='steelblue')
        ax.axvline(x=self.INTERACTION_DISTANCE, color='r', linestyle='--', 
                   label=f'Interaction Threshold ({self.INTERACTION_DISTANCE}px)')
        ax.set_xlabel('Distance (pixels)')
        ax.set_ylabel('Count')
        ax.set_title('Distance Distribution')
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, 'distance_distribution.png'), dpi=300)
        plt.close()
        
        # 4. 角度随时间变化
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(processed_df['frame'] / self.FPS, processed_df['angle_mouse1'], 
                label='Mouse 1', color='blue', alpha=0.7)
        ax.plot(processed_df['frame'] / self.FPS, processed_df['angle_mouse2'], 
                label='Mouse 2', color='orange', alpha=0.7)
        ax.set_xlabel('Time (s)')
        ax.set_ylabel('Head Angle (degrees)')
        ax.set_title('Head Angles Over Time')
        ax.legend()
        plt.tight_layout()
        plt.savefig(os.path.join(fig_dir, 'head_angle_over_time.png'), dpi=300)
        plt.close()
        
        # 5. 行为事件时间线
        if not events_df.empty:
            fig, ax = plt.subplots(figsize=(12, 4))
            behaviors = events_df['Behavior'].unique()
            y_positions = {b: i for i, b in enumerate(behaviors)}
            
            for _, event in events_df.iterrows():
                ax.barh(y=y_positions[event['Behavior']], 
                       width=event['Duration_s'],
                       left=event['Start_s'],
                       color=colors[event['Behavior']],
                       alpha=0.6)
            
            ax.set_yticks(list(y_positions.values()))
            ax.set_yticklabels(list(y_positions.keys()))
            ax.set_xlabel('Time (s)')
            ax.set_title('Behavior Events Timeline')
            plt.tight_layout()
            plt.savefig(os.path.join(fig_dir, 'behavior_timeline.png'), dpi=300)
            plt.close()

    # ========== 其它你需要的内部辅助函数可写在下面 ==========
