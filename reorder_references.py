#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
重新排序参考文献编号
按照在论文正文中首次出现的顺序重新编号所有引用
"""

import re
import os

# 当前参考文献列表（旧编号 -> 文献内容）
OLD_REFERENCES = {
    1: "Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Lukasz Kaiser, Illia Polosukhin. Attention Is All You Need[C]//Advances in Neural Information Processing Systems. 2017, 30: 5998-6008.",
    2: "Jacob Devlin, Ming-Wei Chang, Kenton Lee, Kristina Toutanova. BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding[C]//Proceedings of the 2019 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long and Short Papers). Minneapolis, Minnesota: Association for Computational Linguistics, 2019: 4171-4186.",
    3: "Hugo Touvron, Louis Martin, Kevin Stone, Peter Albert, Amjad Almahairi, Yasmine Babaei, Nikolay Bashlykov, Soumya Batra, Prajjwal Bhargava, Shruti Bhosale, et al. Llama 2: Open Foundation and Fine-Tuned Chat Models[J]. arXiv preprint arXiv:2307.09288, 2023.",
    4: "Abhimanyu Dubey, Abhinav Jauhri, Abhinav Pandey, Abhishek Kadian, Ahmad Al-Dahle, Aiesha Letman, Akhil Mathur, Alan Schelten, Amy Yang, Angela Fan, et al. The Llama 3 Herd of Models[J]. arXiv preprint arXiv:2407.21783, 2024.",
    5: "Edward J. Hu, Yelong Shen, Phillip Wallis, Zeyuan Allen-Zhu, Yuanzhi Li, Shean Wang, Lu Wang, Weizhu Chen. LoRA: Low-Rank Adaptation of Large Language Models[C]//International Conference on Learning Representations. 2022.",
    6: "Tim Dettmers, Artidoro Pagnoni, Ari Holtzman, Luke Zettlemoyer. QLoRA: Efficient Finetuning of Quantized LLMs[C]//Advances in Neural Information Processing Systems. 2023, 36.",
    7: "Yaowei Zheng, Richong Zhang, Junhao Zhang, Yanhan Ye, Zheyan Luo. LlamaFactory: Unified Efficient Fine-Tuning of 100+ Language Models[C]//Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 3: System Demonstrations). Bangkok, Thailand: Association for Computational Linguistics, 2024: 400-410.",
    8: "Tom B. Brown, Benjamin Mann, Nick Ryder, Melanie Subbiah, Jared Kaplan, Prafulla Dhariwal, Arvind Neelakantan, Pranav Shyam, Girish Sastry, Amanda Askell, et al. Language Models are Few-Shot Learners[C]//Advances in Neural Information Processing Systems. 2020, 33: 1877-1901.",
    9: "Alec Radford, Jeffrey Wu, Rewon Child, David Luan, Dario Amodei, Ilya Sutskever. Language Models are Unsupervised Multitask Learners[R]. OpenAI, 2019.",
    10: "赵鑫, 李军辉, 周昆, 等. 大语言模型综述[J]. 中国科学: 信息科学, 2023, 53(11): 2103-2144.",
    11: "Roy Thomas Fielding. Architectural Styles and the Design of Network-based Software Architectures[D]. Irvine: University of California, 2000.",
    12: "Michael Jones, John Bradley, Nat Sakimura. JSON Web Token (JWT)[S]. RFC 7519, 2015.",
    13: "Ian Goodfellow, Yoshua Bengio, Aaron Courville. Deep Learning[M]. Cambridge: MIT Press, 2016.",
    14: "Diederik P. Kingma, Jimmy Ba. Adam: A Method for Stochastic Optimization[C]//International Conference on Learning Representations. 2015.",
    15: "Kaiming He, Xiangyu Zhang, Shaoqing Ren, Jian Sun. Deep Residual Learning for Image Recognition[C]//Proceedings of the IEEE Conference on Computer Vision and Pattern Recognition. 2016: 770-778.",
    16: "Nitish Srivastava, Geoffrey Hinton, Alex Krizhevsky, Ilya Sutskever, Ruslan Salakhutdinov. Dropout: A Simple Way to Prevent Neural Networks from Overfitting[J]. Journal of Machine Learning Research, 2014, 15(1): 1929-1958.",
    17: "Sergey Ioffe, Christian Szegedy. Batch Normalization: Accelerating Deep Network Training by Reducing Internal Covariate Shift[C]//International Conference on Machine Learning. 2015: 448-456.",
    18: "Yann LeCun, Yoshua Bengio, Geoffrey Hinton. Deep Learning[J]. Nature, 2015, 521(7553): 436-444.",
    19: "Dzmitry Bahdanau, Kyunghyun Cho, Yoshua Bengio. Neural Machine Translation by Jointly Learning to Align and Translate[C]//International Conference on Learning Representations. 2015.",
    20: "Ilya Sutskever, Oriol Vinyals, Quoc V. Le. Sequence to Sequence Learning with Neural Networks[C]//Advances in Neural Information Processing Systems. 2014, 27: 3104-3112.",
    21: "Tomas Mikolov, Ilya Sutskever, Kai Chen, Greg Corrado, Jeffrey Dean. Efficient Estimation of Word Representations in Vector Space[C]//International Conference on Learning Representations. 2013.",
    22: "Jeffrey Pennington, Richard Socher, Christopher Manning. GloVe: Global Vectors for Word Representation[C]//Proceedings of the 2014 Conference on Empirical Methods in Natural Language Processing. 2014: 1532-1543.",
    23: "Matthew E. Peters, Mark Neumann, Mohit Iyyer, Matt Gardner, Christopher Clark, Kenton Lee, Luke Zettlemoyer. Deep Contextualized Word Representations[C]//Proceedings of the 2018 Conference of the North American Chapter of the Association for Computational Linguistics: Human Language Technologies, Volume 1 (Long Papers). 2018: 2227-2237.",
    24: "Jason Wei, Maarten Bosma, Vincent Zhao, Kelvin Guu, Adams Wei Yu, Brian Lester, Nan Du, Andrew M. Dai, Quoc V. Le. Finetuned Language Models Are Zero-Shot Learners[C]//International Conference on Learning Representations. 2022.",
    25: "Liam Reynolds, Kyle McDonell. Prompt Programming for Large Language Models: Beyond the Few-Shot Paradigm[J]. arXiv preprint arXiv:2102.07350, 2021.",
    26: "Geoffrey Hinton, Oriol Vinyals, Jeff Dean. Distilling the Knowledge in a Neural Network[J]. arXiv preprint arXiv:1503.02531, 2015.",
    27: "Song Han, Huizi Mao, William J. Dally. Deep Compression: Compressing Deep Neural Networks with Pruning, Trained Quantization and Huffman Coding[C]//International Conference on Learning Representations. 2016.",
    28: "Jimmy Lei Ba, Jamie Ryan Kiros, Geoffrey E. Hinton. Layer Normalization[J]. arXiv preprint arXiv:1607.06450, 2016.",
    29: "Jason Yosinski, Jeff Clune, Yoshua Bengio, Hod Lipson. How Transferable are Features in Deep Neural Networks?[C]//Advances in Neural Information Processing Systems. 2014, 27: 3320-3328.",
    30: "Barret Zoph, Quoc V. Le. Neural Architecture Search with Reinforcement Learning[C]//International Conference on Learning Representations. 2017.",
}

# 章节文件列表（按阅读顺序）
CHAPTER_FILES = [
    '论文第一章综述.TXT',
    '论文第二章需求分析.TXT',
    '论文第三章系统总体设计.TXT',
    '论文第四章系统详细设计与实现.TXT',
    '论文第五章系统测试.TXT',
    '论文第六章系统部署与运维.TXT',
    '论文第七章结论.TXT',
]

def find_citations_in_order(base_dir):
    """按顺序找出所有引用的文献编号"""
    citation_order = []
    seen = set()
    
    for filename in CHAPTER_FILES:
        filepath = os.path.join(base_dir, filename)
        if not os.path.exists(filepath):
            print(f"警告: 文件 {filename} 不存在")
            continue
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 查找所有引用 [数字]
        citations = re.findall(r'\[(\d+)\]', content)
        
        for cit in citations:
            cit_num = int(cit)
            if cit_num not in seen and cit_num in OLD_REFERENCES:
                citation_order.append(cit_num)
                seen.add(cit_num)
                print(f"找到文献 [{cit_num}] 在 {filename}")
    
    return citation_order

def create_new_reference_mapping(citation_order):
    """创建旧编号到新编号的映射"""
    old_to_new = {}
    for new_num, old_num in enumerate(citation_order, 1):
        old_to_new[old_num] = new_num
    return old_to_new

def update_chapter_file(filepath, old_to_new):
    """更新章节文件中的引用编号"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 替换所有引用编号
    def replace_citation(match):
        old_num = int(match.group(1))
        if old_num in old_to_new:
            return f'[{old_to_new[old_num]}]'
        return match.group(0)
    
    new_content = re.sub(r'\[(\d+)\]', replace_citation, content)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print(f"已更新: {filepath}")

def create_new_reference_file(base_dir, citation_order):
    """创建新的参考文献文件"""
    output_path = os.path.join(base_dir, '论文参考文献.TXT')
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('参考文献\n\n')
        
        for new_num, old_num in enumerate(citation_order, 1):
            ref_text = OLD_REFERENCES[old_num]
            f.write(f'[{new_num}] {ref_text}\n\n')
    
    print(f"已创建新的参考文献文件: {output_path}")

def main():
    base_dir = os.path.dirname(__file__)
    
    print("=" * 60)
    print("开始重新排序参考文献...")
    print("=" * 60)
    
    # 1. 找出引用顺序
    print("\n步骤1: 扫描所有章节，找出引用顺序...")
    citation_order = find_citations_in_order(base_dir)
    
    print(f"\n找到 {len(citation_order)} 个被引用的文献")
    print(f"引用顺序: {citation_order}")
    
    # 2. 创建映射
    print("\n步骤2: 创建旧编号到新编号的映射...")
    old_to_new = create_new_reference_mapping(citation_order)
    print("映射关系:")
    for old, new in sorted(old_to_new.items()):
        print(f"  [{old}] -> [{new}]")
    
    # 3. 更新所有章节文件
    print("\n步骤3: 更新所有章节文件的引用编号...")
    for filename in CHAPTER_FILES:
        filepath = os.path.join(base_dir, filename)
        if os.path.exists(filepath):
            update_chapter_file(filepath, old_to_new)
    
    # 4. 创建新的参考文献文件
    print("\n步骤4: 创建新的参考文献文件...")
    create_new_reference_file(base_dir, citation_order)
    
    print("\n" + "=" * 60)
    print("参考文献重新排序完成！")
    print("=" * 60)

if __name__ == '__main__':
    main()
