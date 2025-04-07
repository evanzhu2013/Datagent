import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import folium
import os
from datetime import datetime
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS']  # 设置中文字体

class DataAnalyzer:
    def __init__(self, data_path):
        self.data = pd.read_excel(data_path)
        self.report_dir = 'reports'
        self.images_dir = f'{self.report_dir}/images'
        
        # 创建必要的目录
        os.makedirs(self.report_dir, exist_ok=True)
        os.makedirs(self.images_dir, exist_ok=True)
        
        # 数据预处理
        self.preprocess_data()
        
    def preprocess_data(self):
        """数据预处理"""
        # 转换数据类型
        numeric_cols = ['COD（mg/L）', '氨氮（mg/L）', '总磷（mg/L ）', 'pH', '流量（m3/d）']
        for col in numeric_cols:
            if col in self.data.columns:
                self.data[col] = pd.to_numeric(self.data[col], errors='coerce')
        
        # 处理经纬度数据
        self.data['地理位置经度'] = pd.to_numeric(self.data['地理位置经度'], errors='coerce')
        self.data['地理位置纬度'] = pd.to_numeric(self.data['地理位置纬度'], errors='coerce')
        
    def basic_info(self):
        """数据基本信息分析"""
        info = {
            'shape': self.data.shape,
            'columns': self.data.columns.tolist(),
            'dtypes': self.data.dtypes,
            'describe': self.data.describe()
        }
        return info
    
    def missing_analysis(self):
        """缺失值分析"""
        missing = self.data.isnull().sum()
        missing_percent = (missing / len(self.data)) * 100
        
        # 生成缺失值可视化
        plt.figure(figsize=(12, 6))
        missing_percent.plot(kind='bar')
        plt.title('数据缺失率分析')
        plt.xlabel('字段名')
        plt.ylabel('缺失率 (%)')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{self.images_dir}/missing_analysis.png')
        plt.close()
        
        return pd.DataFrame({
            'missing_count': missing,
            'missing_percent': missing_percent
        })
    
    def outlier_analysis(self):
        """异常值分析"""
        numeric_cols = ['COD（mg/L）', '氨氮（mg/L）', '总磷（mg/L ）', 'pH', '流量（m3/d）']
        outliers = {}
        
        # 生成箱线图
        plt.figure(figsize=(12, 6))
        valid_cols = [col for col in numeric_cols if col in self.data.columns]
        self.data[valid_cols].boxplot()
        plt.title('水质指标箱线图')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{self.images_dir}/outliers_boxplot.png')
        plt.close()
        
        for col in numeric_cols:
            if col in self.data.columns:
                Q1 = self.data[col].quantile(0.25)
                Q3 = self.data[col].quantile(0.75)
                IQR = Q3 - Q1
                outliers[col] = self.data[
                    (self.data[col] < (Q1 - 1.5 * IQR)) | 
                    (self.data[col] > (Q3 + 1.5 * IQR))
                ].shape[0]
        return outliers
    
    def generate_statistics(self):
        """生成统计表格"""
        # 表1: 省际分布
        province_dist = self.data.groupby('省').size().reset_index(name='数量')
        
        # 生成省际分布饼图
        plt.figure(figsize=(8, 8))
        plt.pie(province_dist['数量'], labels=province_dist['省'], autopct='%1.1f%%')
        plt.title('排污口省际分布')
        plt.savefig(f'{self.images_dir}/province_dist.png')
        plt.close()
        
        # 表2: 排口类型统计
        type_dist = self.data['排污口类型'].value_counts().reset_index()
        type_dist.columns = ['类型', '数量']
        
        # 生成排口类型柱状图
        plt.figure(figsize=(10, 6))
        plt.bar(type_dist['类型'], type_dist['数量'])
        plt.title('排污口类型分布')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(f'{self.images_dir}/type_dist.png')
        plt.close()
        
        # 表3: 排放特征统计
        feature_dist = self.data['排水特征-主要特征'].value_counts().reset_index()
        feature_dist.columns = ['特征', '数量']
        
        # 生成排放特征饼图
        plt.figure(figsize=(8, 8))
        plt.pie(feature_dist['数量'], labels=feature_dist['特征'], autopct='%1.1f%%')
        plt.title('排放特征分布')
        plt.savefig(f'{self.images_dir}/feature_dist.png')
        plt.close()
        
        # 表4: 入河方式统计
        discharge_dist = self.data['入河方式'].value_counts().reset_index()
        discharge_dist.columns = ['方式', '数量']
        
        return {
            'province_dist': province_dist,
            'type_dist': type_dist,
            'feature_dist': feature_dist,
            'discharge_dist': discharge_dist
        }
    
    def generate_map(self):
        """生成地理分布地图"""
        try:
            # 过滤掉缺失的经纬度数据
            map_data = self.data.dropna(subset=['地理位置经度', '地理位置纬度'])
            
            if len(map_data) == 0:
                print("警告：没有有效的经纬度数据用于生成地图")
                return
            
            # 创建地图
            m = folium.Map(location=[34, 111], zoom_start=7)
            
            # 添加排污口标记
            for _, row in map_data.iterrows():
                folium.Marker(
                    location=[row['地理位置纬度'], row['地理位置经度']],
                    popup=f"名称: {row['排污口名称']}<br>类型: {row['排污口类型']}<br>特征: {row['排水特征-主要特征']}"
                ).add_to(m)
            
            # 保存地图
            m.save(f'{self.images_dir}/pollution_map.html')
        except Exception as e:
            print(f"生成地图时出错: {str(e)}")
    
    def generate_report(self):
        """生成分析报告"""
        # 生成地图
        self.generate_map()
            
        with open(f'{self.report_dir}/analysis_report.md', 'w', encoding='utf-8') as f:
            f.write('# 南水北调中线水源区排污口数据分析报告\n\n')
            
            # 基本信息
            f.write('## 1. 数据基本信息\n\n')
            f.write(f'数据维度: {self.data.shape}\n\n')
            f.write('数据列名:\n')
            for col in self.data.columns:
                f.write(f'- {col}\n')
            
            # 缺失值分析
            f.write('\n## 2. 缺失值分析\n\n')
            missing_df = self.missing_analysis()
            f.write(missing_df.to_markdown())
            f.write('\n\n![缺失值分析](images/missing_analysis.png)\n')
            
            # 异常值分析
            f.write('\n## 3. 异常值分析\n\n')
            outliers = self.outlier_analysis()
            for col, count in outliers.items():
                f.write(f'- {col}: {count}个异常值\n')
            f.write('\n\n![异常值分析](images/outliers_boxplot.png)\n')
            
            # 统计结果
            f.write('\n## 4. 统计结果\n\n')
            stats = self.generate_statistics()
            
            # 省际分布
            f.write('### 4.1 省际分布\n\n')
            f.write(stats['province_dist'].to_markdown(index=False))
            f.write('\n\n![省际分布](images/province_dist.png)\n')
            
            # 排口类型
            f.write('\n### 4.2 排口类型统计\n\n')
            f.write(stats['type_dist'].to_markdown(index=False))
            f.write('\n\n![排口类型分布](images/type_dist.png)\n')
            
            # 排放特征
            f.write('\n### 4.3 排放特征统计\n\n')
            f.write(stats['feature_dist'].to_markdown(index=False))
            f.write('\n\n![排放特征分布](images/feature_dist.png)\n')
            
            # 入河方式
            f.write('\n### 4.4 入河方式统计\n\n')
            f.write(stats['discharge_dist'].to_markdown(index=False))
            
            # 冷却水排放情况
            f.write('\n### 4.5 冷却水排放情况\n\n')
            cooling_water = self.data[self.data['排水特征-主要特征'].str.contains('冷却水', na=False)]
            if not cooling_water.empty:
                f.write(f'冷却水排放口数量: {len(cooling_water)}\n\n')
                f.write('按省份分布:\n')
                f.write(cooling_water['省'].value_counts().to_markdown())
            else:
                f.write('未发现冷却水排放口\n')
            
            # 数据质量评估
            f.write('\n## 5. 数据质量评估\n\n')
            f.write('### 5.1 数据完整性\n\n')
            f.write('- 基本信息（省、市、县、排污口名称等）完整性较好\n')
            f.write('- 水质指标（COD、氨氮、总磷等）数据缺失严重\n')
            f.write('- 地理位置信息部分缺失\n\n')
            
            f.write('### 5.2 数据准确性\n\n')
            f.write('- 经纬度数据存在格式问题，需要进一步清洗\n')
            f.write('- 入河方式数据可能存在异常值\n\n')
            
            f.write('### 5.3 建议\n\n')
            f.write('1. 补充水质监测数据\n')
            f.write('2. 完善地理位置信息\n')
            f.write('3. 规范入河方式数据格式\n')

if __name__ == '__main__':
    analyzer = DataAnalyzer('南水北调中线水源区排污口.xlsx')
    analyzer.generate_report() 