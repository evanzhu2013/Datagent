import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import folium
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
import os

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'Microsoft YaHei']  # 优先使用系统支持的中文字体
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

class PollutionTracer:
    def __init__(self, data_path):
        self.data = pd.read_excel(data_path)
        self.output_dir = 'reports/trace'
        os.makedirs(self.output_dir, exist_ok=True)
        
        # 数据预处理
        self.preprocess_data()
    
    def preprocess_data(self):
        """数据预处理"""
        # 处理经纬度数据
        self.data['经度'] = pd.to_numeric(self.data['经度'], errors='coerce')
        self.data['纬度'] = pd.to_numeric(self.data['纬度'], errors='coerce')
        
        # 处理污染物数据
        pollution_cols = ['入河废污水量(万吨年)', '入河主要污染物量（吨年）', 
                        '氨氮入河量（吨年）', '总磷入河量（吨年）', '总氮入河量（吨年）']
        for col in pollution_cols:
            self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
    
    def spatial_clustering(self):
        """空间聚类分析"""
        # 准备数据
        coords = self.data[['经度', '纬度']].values
        coords = StandardScaler().fit_transform(coords)
        
        # 使用DBSCAN进行聚类
        dbscan = DBSCAN(eps=0.3, min_samples=3)
        clusters = dbscan.fit_predict(coords)
        self.data['cluster'] = clusters
        
        return clusters
    
    def pollution_analysis(self):
        """污染物排放分析"""
        # 计算每个企业的总污染物排放量
        self.data['total_pollution'] = self.data[
            ['入河主要污染物量（吨年）', '氨氮入河量（吨年）', 
             '总磷入河量（吨年）', '总氮入河量（吨年）']
        ].sum(axis=1)
        
        # 按企业分组统计
        company_stats = self.data.groupby('设置单位名称').agg({
            'total_pollution': 'sum',
            '入河废污水量(万吨年)': 'sum',
            '排污口类型名称': lambda x: x.mode()[0] if not x.mode().empty else None
        }).reset_index()
        
        # 按污染物排放量排序
        company_stats = company_stats.sort_values('total_pollution', ascending=False)
        
        return company_stats
    
    def generate_trace_report(self):
        """生成溯源报告"""
        # 进行空间聚类
        clusters = self.spatial_clustering()
        
        # 进行污染物分析
        company_stats = self.pollution_analysis()
        
        # 生成报告
        with open(f'{self.output_dir}/trace_report.md', 'w', encoding='utf-8') as f:
            f.write('# 南水北调中线水源区污染源溯源分析报告\n\n')
            
            # 主要污染源分析
            f.write('## 1. 主要污染源分析\n\n')
            f.write('### 1.1 污染物排放量排名前10的企业\n\n')
            f.write(company_stats.head(10).to_markdown(index=False))
            f.write('\n\n')
            
            # 空间聚类分析
            f.write('## 2. 污染源空间分布分析\n\n')
            cluster_info = self.data.groupby('cluster').agg({
                '设置单位名称': 'count',
                'total_pollution': 'sum'
            }).reset_index()
            
            f.write('### 2.1 污染源聚集区统计\n\n')
            f.write(cluster_info.to_markdown(index=False))
            f.write('\n\n')
            
            # 详细聚类信息
            f.write('### 2.2 各聚集区详细信息\n\n')
            for cluster_id in np.unique(clusters):
                if cluster_id == -1:  # 噪声点
                    continue
                    
                cluster_data = self.data[self.data['cluster'] == cluster_id]
                f.write(f'#### 聚集区 {cluster_id}\n\n')
                f.write(f'- 企业数量: {len(cluster_data)}\n')
                f.write(f'- 总污染物排放量: {cluster_data["total_pollution"].sum():.2f} 吨/年\n')
                f.write('- 主要企业:\n')
                
                # 按污染物排放量排序
                top_companies = cluster_data.sort_values('total_pollution', ascending=False).head(5)
                for _, row in top_companies.iterrows():
                    f.write(f'  - {row["设置单位名称"]}: {row["total_pollution"]:.2f} 吨/年\n')
                f.write('\n')
        
        # 生成可视化
        self._generate_visualizations()
    
    def _generate_visualizations(self):
        """生成可视化图表"""
        # 1. 污染物排放量分布图
        plt.figure(figsize=(12, 6))
        self.data['total_pollution'].hist(bins=50)
        plt.title('污染物排放量分布', fontsize=14)
        plt.xlabel('排放量 (吨/年)', fontsize=12)
        plt.ylabel('频数', fontsize=12)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/pollution_distribution.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. 空间聚类图
        plt.figure(figsize=(12, 8))
        for cluster_id in np.unique(self.data['cluster']):
            if cluster_id == -1:
                color = 'gray'
                label = '噪声点'
            else:
                color = plt.cm.tab20(cluster_id % 20)
                label = f'聚集区 {cluster_id}'
            
            cluster_data = self.data[self.data['cluster'] == cluster_id]
            plt.scatter(cluster_data['经度'], cluster_data['纬度'], 
                       c=[color], label=label, alpha=0.6)
        
        plt.title('污染源空间分布', fontsize=14)
        plt.xlabel('经度', fontsize=12)
        plt.ylabel('纬度', fontsize=12)
        plt.xticks(fontsize=10)
        plt.yticks(fontsize=10)
        plt.legend(fontsize=10)
        plt.grid(True)
        plt.tight_layout()
        plt.savefig(f'{self.output_dir}/spatial_clusters.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. 生成交互式地图
        self._generate_interactive_map()
    
    def _generate_interactive_map(self):
        """生成交互式地图"""
        m = folium.Map(location=[34, 111], zoom_start=7)
        
        # 添加聚类标记
        for cluster_id in np.unique(self.data['cluster']):
            if cluster_id == -1:
                continue
                
            cluster_data = self.data[self.data['cluster'] == cluster_id]
            center_lat = cluster_data['纬度'].mean()
            center_lon = cluster_data['经度'].mean()
            
            # 添加聚类中心标记
            folium.CircleMarker(
                location=[center_lat, center_lon],
                radius=10,
                color='red',
                fill=True,
                fill_color='red',
                popup=f'聚集区 {cluster_id}<br>企业数量: {len(cluster_data)}<br>总排放量: {cluster_data["total_pollution"].sum():.2f} 吨/年'
            ).add_to(m)
            
            # 添加企业标记
            for _, row in cluster_data.iterrows():
                folium.Marker(
                    location=[row['纬度'], row['经度']],
                    popup=f"企业: {row['设置单位名称']}<br>排放量: {row['total_pollution']:.2f} 吨/年<br>类型: {row['排污口类型名称']}"
                ).add_to(m)
        
        m.save(f'{self.output_dir}/pollution_map.html')

if __name__ == '__main__':
    tracer = PollutionTracer('南水北调中线水源区排污口.xlsx')
    tracer.generate_trace_report() 