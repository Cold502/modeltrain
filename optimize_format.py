# -*- coding: utf-8 -*-
"""根据论文案例和模板优化论文格式"""

def optimize_format():
    file_path = r'd:\Desktop\modeltrain\论文第二版.txt'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 格式优化1: 摘要页码改为罗马数字
    content = content.replace('摘  要\tI', '摘  要\tⅠ')
    
    # 格式优化2: 统一括号格式为半角
    # 在目录中，括号应该是半角
    lines = content.split('\n')
    new_lines = []
    in_toc = False
    
    for i, line in enumerate(lines):
        if '目  录' in line:
            in_toc = True
        elif line.strip().startswith('================') and in_toc:
            in_toc = False
        
        # 在目录区域，将全角括号替换为半角括号
        if in_toc and '（' in line and '）' in line:
            # 只替换目录中的括号，正文保持全角
            if line.strip() and not line.strip().startswith('摘'):
                line = line.replace('（', '(').replace('）', ')')
        
        new_lines.append(line)
    
    content = '\n'.join(new_lines)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("论文格式优化完成！")

if __name__ == '__main__':
    optimize_format()
