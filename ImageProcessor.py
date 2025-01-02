from psd_tools import PSDImage
from PIL import Image
import os

class ImageProcessor:
    def __init__(self):
        # 创建输出文件夹
        self.png_folder = 'png_output'
        self.final_folder = 'final_output'
        os.makedirs(self.png_folder, exist_ok=True)
        os.makedirs(self.final_folder, exist_ok=True)

    def validate_template(self, template_path):
        """验证模板图片是否有透明通道"""
        try:
            with Image.open(template_path) as template:
                if template.mode != 'RGBA':
                    raise ValueError("模板必须是带透明通道的PNG图片(RGBA格式)")
                return True
        except Exception as e:
            print(f"模板验证失败: {str(e)}")
            return False

    def remove_white_background(self, image):
        """去除图片中的白色背景"""
        # 确保图片在RGBA模式
        if image.mode != 'RGBA':
            image = image.convert('RGBA')
        
        # 获取图片数据
        data = image.getdata()
        
        # 创建新的像素数据，将白色背景转为透明
        new_data = []
        for item in data:
            # 检查像素是否接近白色（考虑到可能的轻微色差）
            if item[0] > 250 and item[1] > 250 and item[2] > 250:
                # 完全透明
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        
        # 更新图片数据
        image.putdata(new_data)
        return image

    def convert_psd_to_png(self, psd_path):
        """将PSD文件转换为PNG"""
        if not os.path.exists(psd_path):
            raise FileNotFoundError(f"找不到PSD文件: {psd_path}")
            
        try:
            # 打开PSD文件
            psd = PSDImage.open(psd_path)
            
            # 合并所有图层并确保使用RGBA模式
            image = psd.composite()
            if image.mode != 'RGBA':
                image = image.convert('RGBA')
            
            # 去除白色背景
            image = self.remove_white_background(image)
            
            # 生成输出文件名
            filename = os.path.basename(psd_path)
            png_name = os.path.splitext(filename)[0] + '.png'
            output_path = os.path.join(self.png_folder, png_name)
            
            # 保存为PNG，确保保留透明通道
            image.save(output_path, 'PNG', optimize=False)
            print(f"已转换: {psd_path} -> {output_path}")
            return output_path
            
        except Exception as e:
            import traceback
            print(f"\n处理 {psd_path} 时出错:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("详细错误信息:")
            print(traceback.format_exc())
            raise

    def apply_template(self, image_path, template_path):
        """应用模板到图片"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"找不到图片: {image_path}")
            
        if not self.validate_template(template_path):
            raise ValueError("无效的模板文件")
            
        try:
            # 加载配置
            config = TemplateConfig()
            
            # 打开图片和模板
            with Image.open(image_path) as img, Image.open(template_path) as template:
                # 创建画布
                canvas_size = (config.canvas_width, config.canvas_height)
                final_image = Image.new('RGB', canvas_size, (255, 255, 255))
                
                # 计算产品图的最大允许尺寸
                max_width = int(canvas_size[0] * config.product_area['max_width'])
                max_height = int(canvas_size[1] * config.product_area['max_height'])
                
                # 计算产品图的最佳尺寸（保持比例）
                width, height = img.size
                scale = min(max_width / width, max_height / height)
                new_size = (int(width * scale), int(height * scale))
                
                # 调整产品图大小
                product_img = img.resize(new_size, Image.LANCZOS)
                if product_img.mode != 'RGBA':
                    product_img = product_img.convert('RGBA')
                
                # 调整模板大小
                template = template.resize(canvas_size, Image.LANCZOS)
                if template.mode != 'RGBA':
                    template = template.convert('RGBA')
                
                # 计算产品图位置（基于配置的相对位置）
                pos_x = int(canvas_size[0] * config.product_area['x'] - new_size[0] / 2)
                pos_y = int(canvas_size[1] * config.product_area['y'] - new_size[1] / 2)
                
                # 确保不超出安全边距
                pos_x = max(config.margin, min(pos_x, canvas_size[0] - new_size[0] - config.margin))
                pos_y = max(config.margin, min(pos_y, canvas_size[1] - new_size[1] - config.margin))
                
                # 先放置模板（底层）
                final_image.paste(template, (0, 0), template)
                
                # 再放置产品图（上层）
                final_image.paste(product_img, (pos_x, pos_y), product_img)
                
                # 生成输出文件名
                filename = os.path.basename(image_path)
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(self.final_folder, f'final_{base_name}.jpg')
                
                # 保存为高质量JPG
                final_image.save(output_path, 'JPEG', quality=95)
                
                return output_path
                
        except Exception as e:
            import traceback
            print(f"\n处理 {image_path} 时出错:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("详细错误信息:")
            print(traceback.format_exc())
            raise

    def test_convert_single_psd(self, psd_path):
        """测试转换单个PSD文件"""
        print(f"\n开始测试转换: {psd_path}")
        print(f"文件是否存在: {os.path.exists(psd_path)}")
        
        try:
            print("尝试打开PSD文件...")
            psd = PSDImage.open(psd_path)
            print("PSD文件打开成功")
            
            print("尝试合并图层...")
            image = psd.composite()
            print("图层合并成功")
            
            print("准备保存PNG...")
            filename = os.path.basename(psd_path)
            png_name = os.path.splitext(filename)[0] + '.png'
            output_path = os.path.join(self.png_folder, png_name)
            
            print(f"保存到: {output_path}")
            image.save(output_path)
            print("保存成功")
            
            return output_path
            
        except Exception as e:
            import traceback
            print("\n发生错误:")
            print(f"错误类型: {type(e).__name__}")
            print(f"错误信息: {str(e)}")
            print("\n完整错误堆栈:")
            traceback.print_exc()
            return None

    def process_image(self, image_path, template_path):
        """处理任何格式的图片（JPG/PNG）"""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"找不到图片: {image_path}")
            
        if not self.validate_template(template_path):
            raise ValueError("无效的模板文件")
            
        try:
            # 打开图片和模板
            with Image.open(image_path) as img, Image.open(template_path) as template:
                # 创建一个透明背景的正方形画布
                size = max(800, 800)  # 确保尺寸至少800x800
                final_image = Image.new('RGBA', (size, size), (0, 0, 0, 0))  # 完全透明的背景
                
                # 计算居中位置
                product_size = min(size * 0.8, max(img.size))  # 产品图占画布80%
                scale = product_size / max(img.size)
                new_size = tuple(int(dim * scale) for dim in img.size)
                
                # 调整产品图大小并确保是RGBA模式
                img = img.resize(new_size, Image.LANCZOS)
                if img.mode != 'RGBA':
                    img = img.convert('RGBA')
                
                # 调整模板大小并确保是RGBA模式
                template = template.resize((size, size), Image.LANCZOS)
                if template.mode != 'RGBA':
                    template = template.convert('RGBA')
                
                # 计算居中位置
                pos_x = (size - new_size[0]) // 2
                pos_y = (size - new_size[1]) // 2
                
                # 先放置模板（底层）
                final_image.paste(template, (0, 0), template)
                
                # 再放置产品图（上层）
                final_image.paste(img, (pos_x, pos_y), img)
                
                # 生成输出文件名
                filename = os.path.basename(image_path)
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(self.final_folder, f'final_{base_name}.png')
                
                # 保存最终图片，确保保留透明通道
                final_image.save(output_path, 'PNG', optimize=True)
                print(f"已处理: {output_path}")
                return output_path
                
        except Exception as e:
            raise RuntimeError(f"处理失败 {image_path}: {str(e)}")

class TemplateConfig:
    """模板配置类"""
    def __init__(self):
        # 画布配置
        self.canvas_width = 600
        self.canvas_height = 600
        
        # 产品图片区域配置（相对画布的百分比）
        self.product_area = {
            'x': 0.55,  # 产品图片区域中心点在画布宽度55%处
            'y': 0.5,   # 产品图片区域中心点在画布高度50%处
            'max_width': 0.65,  # 产品图片最大宽度占画布65%
            'max_height': 0.65  # 产品图片最大高度占画布65%
        }
        
        # 安全边距（像素）
        self.margin = 20

def main():
    processor = ImageProcessor()
    
    while True:
        print("\n=== 图片处理工具 ===")
        print("1. 转换PSD到PNG")
        print("2. 应用模板")
        print("3. 一键处理（转换并应用模板）")
        print("4. 退出")
        print("5. 测试单个文件")
        print("6. 处理JPG文件")  # 新增选项
        
        choice = input("\n请选择操作 (1-6): ")
        
        if choice == '1':
            psd_files = [f for f in os.listdir('.') if f.endswith('.psd')]
            if not psd_files:
                print("当前文件夹没有找到PSD文件！")
                continue
                
            print("\n找到以下PSD文件：")
            for i, f in enumerate(psd_files, 1):
                print(f"{i}. {f}")
            
            failed_files = []
            for psd_file in psd_files:
                try:
                    processor.convert_psd_to_png(psd_file)
                except Exception as e:
                    import traceback
                    print(f"\n处理 {psd_file} 时出错:")
                    print(f"错误类型: {type(e).__name__}")
                    print(f"错误信息: {str(e)}")
                    print("详细错误信息:")
                    print(traceback.format_exc())
                    failed_files.append(psd_file)
                    
            if failed_files:
                print("\n以下文件处理失败:")
                for f in failed_files:
                    print(f"- {f}")
                    
        elif choice == '2':
            template_path = input("请输入模板图片路径: ")
            
            try:
                if not processor.validate_template(template_path):
                    continue
                    
                png_files = [f for f in os.listdir(processor.png_folder) if f.endswith('.png')]
                if not png_files:
                    print("没有找到PNG文件！请先转换PSD文件。")
                    continue
                
                failed_files = []
                for png_file in png_files:
                    try:
                        png_path = os.path.join(processor.png_folder, png_file)
                        processor.apply_template(png_path, template_path)
                    except Exception as e:
                        print(f"处理 {png_file} 时出错: {str(e)}")
                        failed_files.append(png_file)
                        
                if failed_files:
                    print("\n以下文件处理失败:")
                    for f in failed_files:
                        print(f"- {f}")
                        
            except Exception as e:
                print(f"模板处理出错: {str(e)}")
                
        elif choice == '3':
            template_path = input("请输入模板图片路径: ")
            if not os.path.exists(template_path):
                print("模板文件不存在！")
                continue
                
            psd_files = [f for f in os.listdir('.') if f.endswith('.psd')]
            if not psd_files:
                print("当前文件夹没有找到PSD文件！")
                continue
                
            for psd_file in psd_files:
                png_path = processor.convert_psd_to_png(psd_file)
                if png_path:
                    processor.apply_template(png_path, template_path)
                    
        elif choice == '4':
            print("感谢使用！")
            break
            
        elif choice == '5':
            psd_file = input("请输入要测试的PSD文件名: ")
            if not os.path.exists(psd_file):
                print(f"文件不存在: {psd_file}")
                continue
            
            result = processor.test_convert_single_psd(psd_file)
            if result:
                print(f"\n测试成功! 输出文件: {result}")
            else:
                print("\n测试失败!")
            
        elif choice == '6':
            template_path = input("请输入模板图片路径: ")
            if not os.path.exists(template_path):
                print("模板文件不存在！")
                continue
                
            jpg_files = [f for f in os.listdir('.') if f.lower().endswith(('.jpg', '.jpeg'))]
            if not jpg_files:
                print("当前文件夹没有找到JPG文件！")
                continue
                
            print("\n找到以下JPG文件：")
            for i, f in enumerate(jpg_files, 1):
                print(f"{i}. {f}")
            
            for jpg_file in jpg_files:
                try:
                    processor.process_image(jpg_file, template_path)
                except Exception as e:
                    print(f"处理 {jpg_file} 时出错: {str(e)}")
                    
        else:
            print("无效的选择，请重试。")

if __name__ == "__main__":
    main() 
