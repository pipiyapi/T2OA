from llm import llm,llm_split_prompt
from tqdm import tqdm  # 导入 tqdm 库

def chunk_text(text_path, chunk_size, split_text_path):
    # 合并 read_text 函数功能
    text_list = []
    with open(text_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            text_list.append(line)
    text = text_list

    split_tag = '。'
    combined_text = '\n'.join(text)  # 将所有行合并为一个字符串
    fixed_chunks = []
    start_index = 0

    # 按照固定长度分割文本
    while start_index < len(combined_text):
        end_index = start_index + chunk_size
        if end_index >= len(combined_text):
            fixed_chunks.append(combined_text[start_index:])
            break
        fixed_chunks.append(combined_text[start_index:end_index])
        start_index = end_index

    adjusted_chunks = []
    # 使用 tqdm 创建进度条
    progress_bar = tqdm(total=len(fixed_chunks) - 1, desc="Chunk 分块判断进度")
    i = 0
    while i < len(fixed_chunks) - 1:
        chunk1 = fixed_chunks[i]
        chunk2 = fixed_chunks[i + 1]
        chunk_combine = chunk1 + chunk2
        # 计算实际分割点的索引
        old_split_point = len(chunk1)
        period_count = 0
        split_index = 0
        char_dict = {}
        for index, char in enumerate(chunk_combine):
            if char == split_tag:
                char_dict[abs(old_split_point - index)] = index + 1
        sorted_indices = [char_dict[key] for key in sorted(char_dict.keys())]
        for j in sorted_indices:
            if period_count < 3:
                chunk1_temp = chunk_combine[:j]
                chunk2_temp = chunk_combine[j:]
                print(f"当前判断分割点{j}")
                if llm_split(chunk1_temp, chunk2_temp) == 1:
                    split_index = j
                    break
                period_count += 1
            else:
                split_index = sorted_indices[0]
                break
        # 调整 chunk1 并添加到调整后的块列表
        print(f"最终确定分割点{split_index}")
        adjusted_chunk1 = chunk_combine[:split_index]
        adjusted_chunks.append(adjusted_chunk1)
        # 更新 chunk2 的开头
        fixed_chunks[i + 1] = chunk_combine[split_index:]
        i += 1
        progress_bar.update(1)  # 更新进度条
    progress_bar.close()  # 关闭进度条

    # 处理最后一个块
    if fixed_chunks:
        adjusted_chunks.append(fixed_chunks[-1])

    # 将调整后的块写入文件
    with open(split_text_path, 'w', encoding='utf-8') as file:
        for i, chunk in enumerate(adjusted_chunks):
            if i > 0:
                file.write('\n---\n')
            file.write(chunk)

def llm_split(chunk1, chunk2):
    llm_split_assistant = llm_split_prompt | llm
    llm_result = llm_split_assistant.invoke({"chunk1": chunk1, "chunk2": chunk2}).content
    print(llm_result)
    return int(llm_result)

if __name__ == '__main__':
    # 修改调用方式，传入文本文件路径
    chunk_text("ner/data/绿色建筑评价标准_raw.txt", 500, "ner/data/绿色建筑评价标准_chunk.txt")