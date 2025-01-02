from PIL import Image
import os
from psd_tools import PSDImage
import numpy as np
from PIL import ImageStat

class TemplateAnalyzer:
    def __init__(self, template_image):
        self.template = template_image
        self.width, self.height = template_image.size
        
    def find_text_regions(self):
        """检测模板中的文字区域"""
        try:
            # 转换为灰度图
            gray = self.template.convert('L')
            # 转换为numpy数组
            img_array = np.array(gray)
            
            # 分析每行的像素值
            row_means = np.mean(img_array, axis=1)
            
            # 找到内容区域（非空白区域）
            content_rows = np.where(row_means < 250)[0]  # 调整阈值可能需要根据实际模板
            
            if len(content_rows) > 0:
                top_content = content_rows[0]
                bottom_content = content_rows[-1]
                
                # 返回完整的安全区域信息
                return {
                    'top_margin': int(top_content),
                    'bottom_margin': int(self.height - bottom_content),
                    'safe_height': int(bottom_content - top_content),
                    'total_height': self.height,
                    'success': True
                }
            
            # 如果没有检测到内容，返回默认值
            return {
                'top_margin': int(self.height * 0.2),  # 默认上边距20%
                'bottom_margin': int(self.height * 0.2),  # 默认下边距20%
                'safe_height': int(self.height * 0.6),  # 默认安全高度60%
                'total_height': self.height,
                'success': False
            }
            
        except Exception as e:
            print(f"分析模板时出错: {str(e)}")
            # 发生错误时返回保守的默认值
            return {
                'top_margin': int(self.height * 0.25),  # 更保守的边距
                'bottom_margin': int(self.height * 0.25),
                'safe_height': int(self.height * 0.5),
                'total_height': self.height,
                'success': False
            }

def process_image(psd_path, template_path, output_path):
    try:
        # 打开PSD文件并转换为PIL Image
        psd = PSDImage.open(psd_path)
        product_img = psd.composite()
        
        # 打开模板图片
        template = Image.open(template_path)
        
        # 分析模板
        analyzer = TemplateAnalyzer(template)
        safe_region = analyzer.find_text_regions()
        
        # 创建新图像(使用模板尺寸)
        canvas_size = template.size
        final_image = Image.new('RGBA', canvas_size)
        
        # 设置边距和安全区域
        EXTRA_MARGIN = 20  # 额外安全边距
        top_margin = safe_region['top_margin']
        bottom_margin = safe_region['bottom_margin']
        safe_height = safe_region['safe_height']
        
        # 计算可用区域
        max_height = safe_height - (EXTRA_MARGIN * 2)
        max_width = canvas_size[0] - (EXTRA_MARGIN * 2)
        
        # 保持原始比例调整大小
        product_ratio = product_img.width / product_img.height
        if max_width / max_height > product_ratio:
            new_height = max_height
            new_width = int(new_height * product_ratio)
        else:
            new_width = max_width
            new_height = int(new_width / product_ratio)
        
        # 调整产品图片大小
        product_img = product_img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # 计算居中位置
        pos_x = (canvas_size[0] - new_width) // 2
        pos_y = top_margin + EXTRA_MARGIN
        
        # 确保不超出安全区域
        pos_y = max(top_margin + EXTRA_MARGIN, 
                   min(pos_y, canvas_size[1] - bottom_margin - new_height - EXTRA_MARGIN))
        
        # 先放置模板（底层）
        final_image.paste(template, (0, 0), template if template.mode == 'RGBA' else None)
        
        # 再放置产品图（上层）
        final_image.paste(product_img, (pos_x, pos_y), product_img if product_img.mode == 'RGBA' else None)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(os.path.abspath(output_path))
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # 保存结果
        final_image.save(output_path, 'PNG')
        
        return True
        
    except Exception as e:
        print(f"处理图片时出错: {str(e)}")
        raise Exception(f"处理图片时出错: {str(e)}") 