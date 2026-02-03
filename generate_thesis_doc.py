#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""生成符合学位论文格式的Word文档"""

from docx import Document
from docx.shared import Pt, Cm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn

def set_chinese_font(run, font_name='宋体', font_size=12):
    """设置中文字体"""
    run.font.name = font_name
    run.font.size = Pt(font_size)
    run._element.rPr.rFonts.set(qn('w:eastAsia'), font_name)

def add_heading_custom(doc, text, level=1):
    """添加自定义格式的标题"""
    para = doc.add_paragraph()
    para.alignment = WD_ALIGN_PARAGRAPH.CENTER if level == 0 else WD_ALIGN_PARAGRAPH.LEFT
    run = para.add_run(text)
    
    if level == 0:  # 摘要、Abstract等顶级标题
        set_chinese_font(run, '黑体', 16)
        run.bold = True
    elif level == 1:  # 一级标题（章）
        set_chinese_font(run, '黑体', 16)
        run.bold = True
    elif level == 2:  # 二级标题
        set_chinese_font(run, '黑体', 14)
        run.bold = True
    elif level == 3:  # 三级标题
        set_chinese_font(run, '黑体', 12)
        run.bold = True
    
    para.paragraph_format.space_before = Pt(12)
    para.paragraph_format.space_after = Pt(6)
    para.paragraph_format.line_spacing = 1.5
    return para

def add_normal_paragraph(doc, text):
    """添加正文段落"""
    if not text or text.strip() == '':
        return
    
    para = doc.add_paragraph()
    run = para.add_run(text)
    set_chinese_font(run, '宋体', 12)
    
    para.paragraph_format.first_line_indent = Cm(0.74)  # 首行缩进2字符
    para.paragraph_format.line_spacing = 1.5
    para.paragraph_format.space_after = Pt(0)
    para.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    return para

def process_line(doc, line):
    """处理单行文本"""
    line = line.strip()
    
    if not line or line == '=' * len(line):
        return
    
    # 判断标题级别
    if line.startswith('摘  要') or line.startswith('Abstract') or line.startswith('参考文献') or line.startswith('致  谢') or line.startswith('附  录'):
        add_heading_custom(doc, line, level=0)
    elif line.startswith('一、') or line.startswith('二、') or line.startswith('三、') or line.startswith('四、') or line.startswith('五、') or line.startswith('六、'):
        add_heading_custom(doc, line, level=1)
    elif line.startswith('（一）') or line.startswith('（二）') or line.startswith('（三）') or line.startswith('（四）') or line.startswith('（五）') or line.startswith('（六）'):
        add_heading_custom(doc, line, level=2)
    elif line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.') or line.startswith('5.'):
        if len(line) < 30:  # 短行作为三级标题
            add_heading_custom(doc, line, level=3)
        else:
            add_normal_paragraph(doc, line)
    elif line.startswith('关键词：') or line.startswith('Keywords:'):
        para = doc.add_paragraph()
        run = para.add_run(line)
        set_chinese_font(run, '宋体', 12)
        run.bold = True
        para.alignment = WD_ALIGN_PARAGRAPH.LEFT
    elif line.startswith('附录A：') or line.startswith('附录B：') or line.startswith('附录C：'):
        add_heading_custom(doc, line, level=2)
    elif line.startswith('表') and '-' in line:  # 表格标题
        para = doc.add_paragraph()
        run = para.add_run(line)
        set_chinese_font(run, '宋体', 10.5)
        para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    else:
        add_normal_paragraph(doc, line)

def main():
    """主函数"""
    # 创建文档
    doc = Document()
    
    # 设置页面
    section = doc.sections[0]
    section.page_height = Cm(29.7)  # A4纸高度
    section.page_width = Cm(21)     # A4纸宽度
    section.top_margin = Cm(2.54)
    section.bottom_margin = Cm(2.54)
    section.left_margin = Cm(3.17)
    section.right_margin = Cm(3.17)
    
    # 读取论文内容
    with open('论文第三版.txt', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 按行处理
    lines = content.split('\n')
    for line in lines:
        process_line(doc, line)
    
    # 保存文档
    doc.save('论文第三版.DOC')
    print('论文第三版.DOC 已生成完成！')

if __name__ == '__main__':
    main()
