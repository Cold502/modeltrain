#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生成论文初稿.TXT，包含目录和所有章节内容
"""

import os

def read_file(filepath):
    """读取文件内容"""
    if not os.path.exists(filepath):
        return []
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.readlines()

def main():
    """主函数"""
    base_dir = os.path.dirname(__file__)
    output_file = os.path.join(base_dir, '论文初稿.TXT')
    
    print("=" * 80)
    print("生成论文初稿.TXT...")
    print("=" * 80)
    
    with open(output_file, 'w', encoding='utf-8') as out:
        # 1. 封面信息
        out.write("\n\n\n")
        out.write(" " * 30 + "计算机学位论文\n\n\n")
        out.write(" " * 25 + "题目：___________________________\n\n")
        out.write(" " * 25 + "学号：___________________________\n\n")
        out.write(" " * 25 + "姓名：___________________________\n\n")
        out.write(" " * 25 + "指导教师：_______________________\n\n\n\n")
        
        # 2. 声明
        out.write("\n\n\n")
        out.write(" " * 35 + "声明\n\n")
        out.write("本人郑重声明：所提交的学位论文是本人在导师指导下进行的研究工作所取得的成果。\n")
        out.write("除文中已经注明引用的内容外，本论文不包含任何其他个人或集体已经发表或撰写过的研究成果。\n")
        out.write("对本文的研究做出重要贡献的个人和集体，均已在文中以明确方式标明。\n\n")
        out.write("本声明的法律责任由本人承担。\n\n\n")
        out.write(" " * 25 + "论文作者签名：___________\n")
        out.write(" " * 25 + "日期：___________________\n\n\n\n")
        
        # 3. 目录
        out.write("\n" * 3)
        out.write(" " * 35 + "目  录\n\n")
        
        toc_file = os.path.join(base_dir, '论文目录.TXT')
        if os.path.exists(toc_file):
            toc_lines = read_file(toc_file)
            for line in toc_lines:
                out.write(line)
            print("✓ 添加目录")
        
        out.write("\n" * 3)
        
        # 4. 摘要
        abstract_file = os.path.join(base_dir, '论文摘要.TXT')
        if os.path.exists(abstract_file):
            out.write("\n\n")
            for line in read_file(abstract_file):
                out.write(line)
            out.write("\n\n")
            print("✓ 添加摘要")
        
        # 5. 各章节
        chapters = [
            ('论文第一章综述.TXT', '一、综述'),
            ('论文第二章需求分析.TXT', '二、需求分析'),
            ('论文第三章系统总体设计.TXT', '三、系统总体设计'),
            ('论文第四章系统详细设计与实现.TXT', '四、系统详细设计与实现'),
            ('论文第五章系统测试.TXT', '五、系统测试'),
            ('论文第六章系统部署与运维.TXT', '六、系统部署与运维'),
            ('论文第七章结论.TXT', '七、结论'),
        ]
        
        for filename, title in chapters:
            filepath = os.path.join(base_dir, filename)
            if os.path.exists(filepath):
                out.write("\n\n")
                for line in read_file(filepath):
                    out.write(line)
                out.write("\n\n")
                print(f"✓ 添加{title}")
        
        # 6. 致谢
        thanks_file = os.path.join(base_dir, '论文致谢.TXT')
        if os.path.exists(thanks_file):
            out.write("\n\n")
            for line in read_file(thanks_file):
                out.write(line)
            out.write("\n\n")
            print("✓ 添加致谢")
        
        # 7. 参考文献
        ref_file = os.path.join(base_dir, '论文参考文献.TXT')
        if os.path.exists(ref_file):
            out.write("\n\n")
            for line in read_file(ref_file):
                out.write(line)
            print("✓ 添加参考文献")
    
    print("\n" + "=" * 80)
    print(f"完成！已生成: {output_file}")
    print("=" * 80)

if __name__ == '__main__':
    main()
