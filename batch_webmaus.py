import os
import requests

def batch_process_webmaus(audio_dir, output_format='emuDB'):
    """
    自动化调用 BAS Web Services 的 runMAUS 接口。
    output_format: 'emuDB' 会生成 JSON; 'TextGrid' 会生成 Praat 的 TextGrid
    """
    # 官方的 runMAUS API 接口地址
    url = "https://clarin.phonetik.uni-muenchen.de/BASWebServices/services/runMAUS"
    
    print(f"开始批量处理文件夹: {audio_dir}")
    success_count = 0
    failed_files = []
    print(f"目标输出格式: {output_format}\n")
    
    # 遍历文件夹下的所有文件
    for filename in os.listdir(audio_dir):
        if filename.endswith(".wav"):
            base_name = os.path.splitext(filename)[0]
            wav_path = os.path.join(audio_dir, filename)
            par_path = os.path.join(audio_dir, f"{base_name}.par")
            
            # 必须保证 wav 和配套的原始 par (带 ORT 文本) 都存在
            if not os.path.exists(par_path):
                print(f" 找不到 {filename} 对应的 .par 文件，跳过此文件。")
                failed_files.append(f"{base_name} (原因: 找不到配套的 .par 文件)")
                continue
                
            print(f"正在上传并处理: {base_name} ...")
            
            # 准备要上传的文件 (对应网页上的拖拽动作)
            files = {
                'SIGNAL': open(wav_path, 'rb'),
                'BPF': open(par_path, 'rb')
            }
            
            # 设置 WebMAUS 参数 (对应网页上的选项)
            data = {
                'LANGUAGE': 'deu-DE',  # 设置语言为德语
                'OUTFORMAT': output_format  # emuDB 对应 JSON, TextGrid 对应 Praat 文件
            }
            
            try:
                # 发送 POST 请求给 BAS 服务器
                response = requests.post(url, files=files, data=data)
                
                # BAS 服务器处理成功后会返回一段 XML 代码，里面包含了最终文件的下载链接
                if response.status_code == 200 and "<downloadLink>" in response.text:
                    response_text = response.text
                    
                    # 提取下载链接
                    link_start = response_text.find("<downloadLink>") + len("<downloadLink>")
                    link_end = response_text.find("</downloadLink>")
                    download_url = response_text[link_start:link_end]
                    
                    # 下载生成好的文件
                    result_response = requests.get(download_url)
                    
                    # 决定保存的文件后缀
                    ext = "_annot.json" if output_format == 'emuDB' else "_WebMAUS.TextGrid"
                    output_file_name = f"{base_name}{ext}"
                    output_path = os.path.join(audio_dir, output_file_name)
                    
                    # 保存到本地
                    with open(output_path, 'wb') as f:
                        f.write(result_response.content)
                        
                    print(f" 成功下载: {output_file_name}")
                    success_count += 1
                else:
                    print(f" 服务器处理失败，报错信息:\n{response.text}")
                    failed_files.append(f"{base_name} (原因: BAS服务器处理异常，请手动测试)")
                    
            except Exception as e:
                print(f" 请求发生网络错误: {e}")
                failed_files.append(f"{base_name} (原因: 网络请求报错 -> {str(e)})")
                
            finally:
                # 无论成功失败，处理完都把占用内存的文件关闭
                files['SIGNAL'].close()
                files['BPF'].close()
    #  在这里输出最终报告 
    print("\n" + "=" * 40)
    print(f" 批量任务全部结束！")
    print(f"统计结果 -> 成功: {success_count} 个 | 失败: {len(failed_files)} 个")
    
    if failed_files:
        log_file_name = f"error_log_{output_format}.txt"
        log_path = os.path.join(audio_dir, log_file_name)
        
        with open(log_path, 'w', encoding='utf-8') as log_file:
            log_file.write("以下音频文件未能成功处理，需要手动排查：\n")
            log_file.write("-" * 50 + "\n")
            for item in failed_files:
                log_file.write(f"- {item}\n")
                
        print(f"已将失败名单保存在: {log_path}")
    print("=" * 40 + "\n")

if __name__ == '__main__':
    # 实际文件夹路径
    my_folder_path = r'C:\Users\dkl31\Desktop\001 von SC2' 
    
    # 第一次运行：批量获取用来跑代码的 JSON 文件 (Hypothesis 1)
    batch_process_webmaus(my_folder_path, output_format='emuDB')
    
    print("-" * 40)
    
    # 第二次运行：顺手把用来做手工标注的 TextGrid 也批量下好
    # batch_process_webmaus(my_folder_path, output_format='TextGrid')
    
    print("\n 全部自动化任务结束！")